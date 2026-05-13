#!/usr/bin/env python3
"""Deliberation: LLM freely selects candidate responses, evaluates outcomes, picks best_action."""

import argparse
import json
import sys
from pathlib import Path
from openai import OpenAI
from action_space import enrich_action_payload

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"

DEFAULT_ALPHA = 0.4
DEFAULT_BETA = 0.5
DEFAULT_GAMMA = 0.1
MAX_RETRIES = 2
BASELINE = "hold_silent"
STAGE_ORDER = {"attention": 0, "interest": 1, "desire": 2, "action": 3}

# ── Action space ──────────────────────────────────────────────────────────────
# LLM selects response_ids from this vocabulary; action_cost is system-injected.

ACTION_SPACE: dict[str, dict] = {
    "hold_silent":                   {"cost": 0.00, "desc": "静默观察——屏幕保持极简 attract，不做任何主动介入。顾客感受：完全自主空间，零压力。"},
    "hold_ambient":                  {"cost": 0.05, "desc": "主动退出互动——回到 attract loop，数字人「不打扰您了」后静默。顾客感受：被放手，无追销感。"},
    "reassure_time_wait":            {"cost": 0.10, "desc": "消除时间焦虑——屏幕显示「为您保留中」小窗，数字人「您慢慢看」后退到背景。顾客感受：时间压力消除。"},
    "reassure_decision":             {"cost": 0.10, "desc": "降低决策压力——数字人「不用马上决定，可以先保留候选」。顾客感受：后悔风险降低。"},
    "reassure_alternatives":         {"cost": 0.10, "desc": "提示备选——数字人「还有其他选择，不用现在定」。顾客感受：不被锁定。"},
    "elicit_need_focus_open":        {"cost": 0.20, "desc": "开放式引导——三选一气泡（功能/价格/场景），数字人「您今天想先看哪一点？」"},
    "elicit_budget":                 {"cost": 0.20, "desc": "询问预算——数字人「您大概想花多少？」帮助缩小候选范围。"},
    "elicit_companion_opinion_open": {"cost": 0.20, "desc": "邀请同伴发言——数字人「这位朋友觉得哪款更合适？」引入同伴参与决策。"},
    "inform_attributes_brief":       {"cost": 0.25, "desc": "展示商品参数——屏幕列出主要规格、价格和适合人群。低打扰。"},
    "inform_price_brief":            {"cost": 0.25, "desc": "展示价格优惠——屏幕显示当前价格和优惠信息，直接解决价格疑虑。"},
    "inform_comparison_brief":       {"cost": 0.30, "desc": "弹出对比卡——双卡对比价格/规格/场景，无强 CTA。选择成本降低。"},
    "inform_demo_brief":             {"cost": 0.40, "desc": "短演示——关键功能 3D 动画（≤10s），数字人简短解说。直观了解功能亮点。"},
    "recommend_soft":                {"cost": 0.45, "desc": "软推荐——高亮某款商品，数字人「这款比较符合您关注的点」，无强 CTA。"},
    "recommend_firm":                {"cost": 0.65, "desc": "强推荐——单品全屏 + 「立即购买」CTA，数字人「这款最适合您，建议直接选」。推销感较强。"},
    "greet_close":                   {"cost": 0.00, "desc": "收尾致谢——订单确认页，数字人致谢，出货口出货。顾客感受：顺畅完成购买。"},
}


def build_action_space_desc() -> str:
    return "\n".join(f"- **{rid}**：{info['desc']}" for rid, info in ACTION_SPACE.items())


# ── Prompt ────────────────────────────────────────────────────────────────────

EXPERT_PROMPT = """你是一个 BDI 认知建模 + 零售行为领域的专家标注员，对 AIDA 购买阶段理论和顾客心理状态迁移有深入理解。

# 背景
智能零售设备内置摄像头持续观察顾客，可主动选择最合适的 response 与顾客互动。
任务：针对当前顾客状态，从下方动作空间中自主选出 3–5 个最相关候选，然后逐一推理 ActionOutcome。

# 动作空间（15 个 response_id）
{action_space_desc}

候选选择规则：
- **hold_silent 必须包含**（无介入基线，用于对比）
- Elicit / Inform / Recommend 每轮最多选一个（三者互斥）
- 候选应与顾客当前 AIDA 阶段和 BDI 状态高度相关，排除明显不适合当前阶段的动作
- 例：action 阶段不应出现 inform_attributes_brief；attention 阶段不应出现 recommend_firm

# 推理方法（每个候选走完整链路，先推理再填字段）
1. **BDI 因果链**：该 response 的具体行为→更新顾客哪个 belief？激活/抑制哪个 desire？intention 更靠近购买还是后退/放弃？
2. **AIDA 迁移**：基于 BDI 变化推断 next_aida_stage（推进一格≈+0.33，倒退为负，不变≈0）
3. **风险评估**：当前阶段时机是否合适？顾客感到被打扰/被推销，还是被理解？给出 risk / benefit
4. **量化**：
   - delta_stage：AIDA 推进量（范围 -1 ~ +1）
   - delta_mental：兴趣升降 + 犹豫降低 + 信任升降综合量（范围 -3 ~ +3，正=改善）
   - action_cost：直接从动作空间定义中读取对应数值，不得自行修改
5. **rationale**：把整条推理链压缩为一句话因果解释

# 一致性约束（输出必须满足）
- next_bdi.intention 必须与 next_aida_stage 语义一致（action 阶段 intention 应为准备操作/购买）
- risk=high 时 delta_mental 通常为负（顾客反感）
- benefit=high 时 delta_mental 不应明显为负
- hold_silent 的 delta_stage 应在 [-0.1, 0.3]
- 候选间最终 reward 之差 ≥ 0.20（需有足够区分度）

# 顾客 Manifest
{manifest_json}

# 输出格式（只输出 JSON，不附加解释或 Markdown）
{{
  "candidate_actions": ["hold_silent", "response_id_2", "response_id_3"],
  "outcomes": {{
    "hold_silent": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "risk": "low",
      "benefit": "low",
      "delta_stage": 0.0,
      "delta_mental": 0.0,
      "action_cost": 0.00,
      "rationale": "..."
    }},
    "response_id_2": {{"...": "..."}},
    "response_id_3": {{"...": "..."}}
  }}
}}"""

RETRY_PROMPT = """上一轮输出存在以下一致性问题，请逐条修正后重新输出完整 JSON：

{errors}

只输出修正后的 JSON，不附加解释。"""


# ── Validation ────────────────────────────────────────────────────────────────

def validate_outcomes(current_aida: str, candidates: list[str], outcomes: dict) -> list[str]:
    errors = []
    current_idx = STAGE_ORDER.get(current_aida, -1)

    if len(candidates) < 3:
        errors.append(f"候选数量不足：{len(candidates)} 个，需要至少 3 个")

    if BASELINE not in candidates:
        errors.append(f"缺少基线候选 {BASELINE}")

    for rid in candidates:
        if rid not in ACTION_SPACE:
            errors.append(f"未知 response_id：{rid}，必须是动作空间中的合法值")

    for rid in candidates:
        if rid not in outcomes:
            errors.append(f"缺少候选的 outcome：{rid}")

    for rid, oc in outcomes.items():
        next_stage = oc.get("next_aida_stage", "")
        next_idx = STAGE_ORDER.get(next_stage, -1)
        ds = float(oc.get("delta_stage", 0))
        dm = float(oc.get("delta_mental", 0))
        risk = oc.get("risk", "")
        benefit = oc.get("benefit", "")
        intention = oc.get("next_bdi", {}).get("intention", "")

        stage_delta = next_idx - current_idx
        if stage_delta > 0 and ds < -0.05:
            errors.append(f"[{rid}] 阶段推进 {current_aida}→{next_stage} 但 delta_stage={ds:.2f} 为负")
        elif stage_delta < 0 and ds > 0.05:
            errors.append(f"[{rid}] 阶段倒退 {current_aida}→{next_stage} 但 delta_stage={ds:.2f} 为正")

        if risk == "high" and dm > 0.3:
            errors.append(f"[{rid}] risk=high 但 delta_mental={dm:.2f} 为正——高风险动作不应改善心理状态")

        if benefit == "high" and dm < -0.5:
            errors.append(f"[{rid}] benefit=high 但 delta_mental={dm:.2f} 明显为负——矛盾")

        HESITATION_WORDS = ["再看", "再想", "考虑", "不确定", "犹豫"]
        if next_stage == "action" and any(w in intention for w in HESITATION_WORDS):
            errors.append(f"[{rid}] next_aida_stage=action 但 intention 含犹豫语义：「{intention}」")

        if rid == BASELINE and abs(ds) > 0.4:
            errors.append(f"[{BASELINE}] delta_stage={ds:.2f} 过大，沉默基线不应大幅改变顾客阶段")

    rewards = [
        compute_reward(
            float(outcomes[rid].get("delta_stage", 0)),
            float(outcomes[rid].get("delta_mental", 0)),
            ACTION_SPACE.get(rid, {}).get("cost", 0.0),
            DEFAULT_ALPHA, DEFAULT_BETA, DEFAULT_GAMMA,
        )
        for rid in candidates if rid in outcomes
    ]
    if len(rewards) > 1 and max(rewards) - min(rewards) < 0.20:
        r_str = ", ".join(f"{r:.2f}" for r in rewards)
        errors.append(f"Reward 分布过于集中 [{r_str}]，候选间缺乏区分度，请拉大 delta_stage / delta_mental 的差距")

    return errors


# ── Core ──────────────────────────────────────────────────────────────────────

def compute_reward(ds: float, dm: float, cost: float,
                   alpha: float, beta: float, gamma: float) -> float:
    return max(-1.0, min(1.0, alpha * ds + beta * dm - gamma * cost))


def attach_costs_and_rewards(candidates: list[str], outcomes: dict,
                              alpha: float, beta: float, gamma: float) -> None:
    for rid in candidates:
        if rid not in outcomes:
            continue
        oc = outcomes[rid]
        cost = ACTION_SPACE.get(rid, {}).get("cost", 0.0)
        oc["action_cost"] = cost  # override with system value
        oc["reward"] = compute_reward(
            float(oc.get("delta_stage", 0)),
            float(oc.get("delta_mental", 0)),
            cost, alpha, beta, gamma,
        )
        oc.update(enrich_action_payload(rid))


def deliberate(
    manifest: dict,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    model: str = "gpt-4.1",
) -> dict:
    client = OpenAI()

    prompt = EXPERT_PROMPT.format(
        action_space_desc=build_action_space_desc(),
        manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
    )

    messages = [{"role": "user", "content": prompt}]
    last_candidates: list[str] = []
    last_outcomes: dict = {}

    for attempt in range(MAX_RETRIES + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)

        candidates = parsed.get("candidate_actions", [])
        outcomes = parsed.get("outcomes", {})

        # enforce baseline
        if BASELINE not in candidates:
            candidates.insert(0, BASELINE)
        if BASELINE not in outcomes:
            outcomes[BASELINE] = {
                "next_aida_stage": manifest.get("aida_stage", "interest"),
                "next_bdi": manifest.get("bdi", {}),
                "risk": "low", "benefit": "low",
                "delta_stage": 0.0, "delta_mental": -0.05,
                "action_cost": 0.0,
                "rationale": "沉默不改变顾客状态，维持现状。",
            }

        attach_costs_and_rewards(candidates, outcomes, alpha, beta, gamma)
        errors = validate_outcomes(manifest.get("aida_stage", "interest"), candidates, outcomes)
        last_candidates, last_outcomes = candidates, outcomes

        if not errors:
            break

        if attempt < MAX_RETRIES:
            error_text = "\n".join(f"- {e}" for e in errors)
            print(f"[deliberate] attempt {attempt + 1} failed ({len(errors)} errors), retrying…",
                  file=sys.stderr)
            messages.append({"role": "assistant", "content": raw_content})
            messages.append({"role": "user", "content": RETRY_PROMPT.format(errors=error_text)})
        else:
            print(f"[deliberate] validation still failing after {MAX_RETRIES} retries, using best attempt",
                  file=sys.stderr)
            for e in errors:
                print(f"  ! {e}", file=sys.stderr)

    best_action = max(
        (rid for rid in last_candidates if rid in last_outcomes),
        key=lambda rid: last_outcomes[rid].get("reward", -999),
    )
    best_payload = enrich_action_payload(best_action)

    return {
        "candidate_actions": last_candidates,
        "outcomes": last_outcomes,
        "best_action": best_action,
        "response_id": best_payload["response_id"],
        "dialogue_act": best_payload["dialogue_act"],
        "act_params": best_payload["act_params"],
        "co_acts": best_payload["co_acts"],
        "realization": best_payload["terminal_realization"],
        "reward_weights": {"alpha": alpha, "beta": beta, "gamma": gamma},
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def find_missing_labeled() -> list[Path]:
    return [
        f for f in sorted(MANIFEST_DIR.glob("piwm_*.json"))
        if not (LABELED_DIR / f.name).exists()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Deliberation: LLM freely selects and evaluates candidate responses, picks best_action. "
                    "Run without arguments to batch-process all un-labeled manifests."
    )
    parser.add_argument("manifest", nargs="?",
                        help="Manifest JSON path (use - for stdin). Omit to batch all data/manifest/ → data/labeled/.")
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--beta",  type=float, default=DEFAULT_BETA)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--no-merge", action="store_true", help="Output only deliberation fields")
    parser.add_argument("--dry-run", action="store_true",
                        help="Single file: print prompt. Batch: list files that would be processed.")
    parser.add_argument("-o", "--output",
                        help=f"Output path (single-file mode only). Default: {LABELED_DIR}/<id>.json. Use '-' for stdout.")
    args = parser.parse_args()

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
            result = deliberate(manifest, alpha=args.alpha, beta=args.beta,
                                gamma=args.gamma, model=args.model)
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
            action_space_desc=build_action_space_desc(),
            manifest_json=json.dumps(manifest, ensure_ascii=False, indent=2),
        ))
        return

    result = deliberate(manifest, alpha=args.alpha, beta=args.beta,
                        gamma=args.gamma, model=args.model)
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
