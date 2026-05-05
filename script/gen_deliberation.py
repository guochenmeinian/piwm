#!/usr/bin/env python3
"""Deliberation: for each candidate action, predict BDI outcome + reward, then pick best_action."""

import argparse
import json
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"

DEFAULT_ALPHA = 0.4
DEFAULT_BETA = 0.5
DEFAULT_GAMMA = 0.1
MAX_RETRIES = 2

SILENCE_ACTION = "A0_silence"
STAGE_ORDER = {"attention": 0, "interest": 1, "desire": 2, "action": 3}

# ── Prompt ────────────────────────────────────────────────────────────────────

EXPERT_PROMPT = """你是一个 BDI 认知建模 + 零售行为领域的专家标注员，对 AIDA 购买阶段理论和 belief/desire/intention 状态迁移有深入理解。

# 任务
对下方顾客 manifest 做 Deliberation 推理：给出 4 个候选动作，并逐一预测每个动作的 ActionOutcome。

## 候选动作要求
- 第一个固定为 **"A0_silence"**（系统不介入，沉默观察）
- 其余 3 个根据当前 AIDA 阶段与 BDI 自行命名（格式 "Ai_<英文蛇形>"，如 "A1_highlight_best_match"）
- 3 个非沉默候选须代表不同策略方向（信息补充 / 比较引导 / 行动催化 / 降低风险 / 情感共鸣 / 转交人工等）
- 贴合当前阶段：attention 阶段不强推购买，action 阶段不做基础介绍

## ActionOutcome 推理方法（每个 candidate 都要走这套链路）
**先推理，再填字段。** 对每个动作按以下顺序思考：

1. **BDI 因果链**：该动作会改变顾客的哪个信念（belief）？激活还是抑制哪个欲望（desire）？
   会让 intention 更接近购买，还是后退？
2. **AIDA 迁移**：基于 BDI 变化，顾客最可能进入哪个 AIDA 阶段？
3. **风险评估**：该动作有多大概率让顾客感到被打扰、被推销、或失去信任？
4. **量化**：
   - `delta_stage`：AIDA 阶段变化量（推进一格 ≈ +0.33，倒退取负，不变 = 0）
   - `delta_mental`：兴趣升降 + 犹豫升降 + 信任升降的综合量（正=改善，负=恶化，范围 -3~+3）
   - `action_cost`：介入打扰成本（A0_silence=0，轻提示≈0.2，主动推荐≈0.4，强引导≈0.7+）
5. 把推理过程压缩为 `rationale`（一句话因果链）

## 一致性约束（你的输出必须满足）
- next_bdi.intention 必须与 next_aida_stage 语义一致
  （action 阶段的 intention 应是"准备购买/操作"而非"想再看看"）
- risk=high → delta_mental 通常为负（顾客反感）
- A0_silence 的 delta_stage 应在 [-0.1, 0.3] 之间（顾客自然微进或保持）
- 4 个动作的 reward 应有明显差异（避免所有 reward 都接近，失去比较意义）

# 顾客 Manifest
{manifest_json}

{action_space_section}

# 输出格式
只输出 JSON（不附加解释或 Markdown）：
{{
  "outcomes": {{
    "A0_silence": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "risk": "low",
      "benefit": "low",
      "delta_stage": 0.0,
      "delta_mental": 0.0,
      "action_cost": 0.0,
      "rationale": "..."
    }},
    "A1_xxx": {{ ... }},
    "A2_xxx": {{ ... }},
    "A3_xxx": {{ ... }}
  }}
}}
"""

RETRY_PROMPT = """上一轮输出存在以下一致性问题，请根据上面的因果推理规则逐条修正，然后重新输出完整 JSON：

{errors}

只输出修正后的 JSON，不要附加解释。"""


# ── Validation ────────────────────────────────────────────────────────────────

def validate_outcomes(current_aida: str, outcomes: dict) -> list[str]:
    errors = []
    current_idx = STAGE_ORDER.get(current_aida, -1)

    for action, oc in outcomes.items():
        next_stage = oc.get("next_aida_stage", "")
        next_idx = STAGE_ORDER.get(next_stage, -1)
        ds = float(oc.get("delta_stage", 0))
        dm = float(oc.get("delta_mental", 0))
        risk = oc.get("risk", "")
        benefit = oc.get("benefit", "")
        intention = oc.get("next_bdi", {}).get("intention", "")

        # delta_stage 方向必须与阶段迁移一致
        stage_delta = next_idx - current_idx
        if stage_delta > 0 and ds < -0.05:
            errors.append(
                f"[{action}] 阶段推进 {current_aida}→{next_stage} 但 delta_stage={ds:.2f} 为负"
            )
        elif stage_delta < 0 and ds > 0.05:
            errors.append(
                f"[{action}] 阶段倒退 {current_aida}→{next_stage} 但 delta_stage={ds:.2f} 为正"
            )

        # risk=high 时 delta_mental 不应为正
        if risk == "high" and dm > 0.3:
            errors.append(
                f"[{action}] risk=high 但 delta_mental={dm:.2f} 为正——高风险动作不应改善心理状态"
            )

        # benefit=high 时 delta_mental 不应为明显负值
        if benefit == "high" and dm < -0.5:
            errors.append(
                f"[{action}] benefit=high 但 delta_mental={dm:.2f} 明显为负——矛盾"
            )

        # action 阶段 intention 不应表示犹豫
        HESITATION_WORDS = ["再看", "再想", "考虑", "不确定", "犹豫", "不太确定"]
        if next_stage == "action" and any(w in intention for w in HESITATION_WORDS):
            errors.append(
                f"[{action}] next_aida_stage=action 但 intention 仍含犹豫语义：「{intention}」"
            )

        # A0_silence 阶段变化不能过大
        if action == SILENCE_ACTION and abs(ds) > 0.4:
            errors.append(
                f"[A0_silence] delta_stage={ds:.2f} 幅度过大，沉默基线不应大幅改变顾客阶段"
            )

    # reward 分布不能过于集中
    rewards = [oc.get("reward", 0) for oc in outcomes.values()]
    if len(rewards) > 1 and max(rewards) - min(rewards) < 0.25:
        r_str = ", ".join(f"{r:.2f}" for r in rewards)
        errors.append(
            f"Reward 分布过于集中 [{r_str}]，4 个候选缺乏区分度，请拉大差距"
        )

    return errors


# ── Core ──────────────────────────────────────────────────────────────────────

def compute_reward(ds: float, dm: float, cost: float,
                   alpha: float, beta: float, gamma: float) -> float:
    return max(-1.0, min(1.0, alpha * ds + beta * dm - gamma * cost))


def build_action_space_section(action_space: list[str]) -> str:
    if not action_space:
        return "# 动作空间\n（未指定，A0_silence 必须保留，其余 3 个由你自行命名）"
    lines = ["# 动作空间（A0_silence 必须保留；其余 3 个从下列选取，互不重复）"]
    lines += [f"- {a}" for a in action_space]
    return "\n".join(lines)


def _attach_rewards(outcomes: dict, alpha, beta, gamma) -> None:
    if SILENCE_ACTION in outcomes:
        outcomes[SILENCE_ACTION]["action_cost"] = 0.0
    for oc in outcomes.values():
        oc["reward"] = compute_reward(
            float(oc["delta_stage"]), float(oc["delta_mental"]),
            float(oc["action_cost"]), alpha, beta, gamma,
        )


def deliberate(
    manifest: dict,
    action_space: list[str] = None,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    model: str = "gpt-5.5",
) -> dict:
    client = OpenAI()
    current_aida = manifest.get("aida_stage", "interest")

    system_prompt = EXPERT_PROMPT.format(
        manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
        action_space_section=build_action_space_section(action_space or []),
    )

    messages = [{"role": "user", "content": system_prompt}]
    last_outcomes = None

    for attempt in range(MAX_RETRIES + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        outcomes = json.loads(raw_content)["outcomes"]
        _attach_rewards(outcomes, alpha, beta, gamma)

        errors = validate_outcomes(current_aida, outcomes)
        last_outcomes = outcomes

        if not errors:
            break

        if attempt < MAX_RETRIES:
            error_text = "\n".join(f"- {e}" for e in errors)
            print(f"[deliberate] attempt {attempt+1} failed ({len(errors)} errors), retrying…",
                  file=sys.stderr)
            messages.append({"role": "assistant", "content": raw_content})
            messages.append({"role": "user", "content": RETRY_PROMPT.format(errors=error_text)})
        else:
            print(f"[deliberate] validation still failing after {MAX_RETRIES} retries, using best attempt",
                  file=sys.stderr)
            for e in errors:
                print(f"  ! {e}", file=sys.stderr)

    candidate_actions = list(last_outcomes.keys())
    best_action = max(last_outcomes.items(), key=lambda kv: kv[1]["reward"])[0]

    return {
        "candidate_actions": candidate_actions,
        "outcomes": last_outcomes,
        "best_action": best_action,
        "reward_weights": {"alpha": alpha, "beta": beta, "gamma": gamma},
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def load_action_space(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def find_missing_labeled() -> list[Path]:
    """manifest files that don't have a corresponding labeled file yet."""
    return [
        f for f in sorted(MANIFEST_DIR.glob("piwm_*.json"))
        if not (LABELED_DIR / f.name).exists()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Deliberation: predict outcome per candidate action, pick best. "
                    "Run without arguments to batch-process all un-labeled manifests."
    )
    parser.add_argument(
        "manifest", nargs="?",
        help="Manifest JSON path (use - for stdin). Omit to batch all data/manifest/ → data/labeled/."
    )
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--beta",  type=float, default=DEFAULT_BETA)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--action-space", help="Action space file (one per line or JSON array)")
    parser.add_argument("--no-merge", action="store_true", help="Output only deliberation fields")
    parser.add_argument("--dry-run", action="store_true",
                        help="Single file: print prompt. Batch: list files that would be processed.")
    parser.add_argument("-o", "--output",
                        help=f"Output path (single-file mode only). Default: {LABELED_DIR}/<id>.json. Use '-' for stdout.")
    args = parser.parse_args()

    action_space = load_action_space(args.action_space) if args.action_space else None

    # ── batch mode ──
    if args.manifest is None:
        pending = find_missing_labeled()
        if not pending:
            print("All manifests already labeled.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} file(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        for f in pending:
            manifest = json.loads(f.read_text(encoding="utf-8"))
            result = deliberate(manifest, action_space,
                                alpha=args.alpha, beta=args.beta, gamma=args.gamma, model=args.model)
            output = result if args.no_merge else {**manifest, **result}
            out_path = LABELED_DIR / f.name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ {out_path.name}", file=sys.stderr)
        return

    # ── single-file mode ──
    if args.manifest == "-":
        manifest = json.load(sys.stdin)
    else:
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    if args.dry_run:
        print(EXPERT_PROMPT.format(
            manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
            action_space_section=build_action_space_section(action_space or []),
        ))
        return

    result = deliberate(manifest, action_space,
                        alpha=args.alpha, beta=args.beta, gamma=args.gamma, model=args.model)

    output = result if args.no_merge else {**manifest, **result}
    out = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out)
        return

    out_path = (Path(args.output) if args.output
                else LABELED_DIR / f"{manifest.get('session_id', 'unknown')}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
