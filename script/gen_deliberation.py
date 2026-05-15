#!/usr/bin/env python3
"""Deliberation: predict action-conditioned outcomes and derive preference labels."""

import argparse
import json
import sys
from pathlib import Path
from openai import OpenAI
from action_space import RESPONSE_COSTS, RESPONSE_DESCRIPTIONS, compute_preference_score, enrich_action_payload

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
DEFAULT_GAMMA = 0.2
MAX_RETRIES = 2
BASELINE = "hold_silent"
STAGE_ORDER = {"attention": 0, "interest": 1, "desire": 2, "action": 3}

# ── Candidate pools ───────────────────────────────────────────────────────────

AIDA_ALLOWED_RESPONSES: dict[str, list[str]] = {
    "attention": [
        "greet_open",
        "hold_silent",
        "hold_ambient",
        "elicit_need_focus_open",
        "inform_demo_brief",
    ],
    "interest": [
        "hold_silent",
        "elicit_need_focus_open",
        "inform_attributes_brief",
        "inform_price_brief",
        "inform_comparison_brief",
        "inform_demo_brief",
        "recommend_soft",
    ],
    "desire": [
        "hold_silent",
        "inform_price_brief",
        "inform_comparison_brief",
        "reassure_decision",
        "reassure_time_wait",
        "recommend_soft",
        "recommend_firm",
    ],
    "action": [
        "hold_silent",
        "reassure_time_wait",
        "reassure_decision",
        "greet_close",
    ],
}


def get_allowed_responses(aida_stage: str) -> list[str]:
    return AIDA_ALLOWED_RESPONSES.get(aida_stage, AIDA_ALLOWED_RESPONSES["interest"])


def build_allowed_response_desc(allowed: list[str]) -> str:
    lines = []
    for rid in allowed:
        cost = RESPONSE_COSTS.get(rid, 0.0)
        desc = RESPONSE_DESCRIPTIONS.get(rid, rid)
        lines.append(f"- **{rid}**：{desc} action_cost={cost:.2f}")
    return "\n".join(lines)


# ── Prompt ────────────────────────────────────────────────────────────────────

EXPERT_PROMPT = """你是一个 BDI 认知建模 + 零售行为领域的专家标注员，对 AIDA 购买阶段理论和顾客心理状态迁移有深入理解。

# 背景
智能零售设备内置摄像头持续观察顾客，可主动选择 response 与顾客互动。
任务：针对当前顾客状态，从下方允许的 response 中选出 4 个候选，然后逐一预测 ActionOutcome。

# 当前 AIDA 阶段
{aida_stage}

# 当前阶段允许的 response_id
{allowed_response_desc}

候选选择规则：
- 必须输出且只输出 4 个候选 response_id
- `hold_silent` 必须包含（无介入基线，用于对比）
- 候选不能重复
- 候选必须来自“当前阶段允许的 response_id”，不能使用其他 response
- LLM 只预测 outcome，不输出 best_action、不输出 action_cost、不输出 preference_score

# 推理方法（每个候选走完整链路，先推理再填字段）
1. **BDI 因果链**：该 response 的具体行为→更新顾客哪个 belief？激活/抑制哪个 desire？intention 更靠近购买还是后退/放弃？
2. **AIDA 迁移**：基于 BDI 变化推断 next_aida_stage（推进一格≈+0.33，倒退为负，不变≈0）
3. **风险评估**：当前阶段时机是否合适？顾客感到被打扰/被推销，还是被理解？给出 risk / benefit
4. **量化**：
   - delta_stage：AIDA 推进量（范围 -1 ~ +1）
   - delta_mental：兴趣升降 + 犹豫降低 + 信任升降综合量（范围 -1 ~ +1，正=改善）
5. **rationale**：把整条推理链压缩为一句话因果解释

# action 选择边界
- `greet_open` 只在顾客刚进入交互范围、尚未真正开始浏览或比较，但已经适合被轻量唤起时给高分；如果顾客已经主动观察设备，则不要把普通开场问候当成最佳动作。
- 如果 manifest 显示顾客“还没明确需求/不知道该看哪类/在找关注方向”，`elicit_need_focus_open` 通常应比直接展示属性或对比更合适；不要假设已有明确商品。
- `inform_comparison_brief` 只在顾客已经面对两个或多个清楚候选、视线/BDI 明确体现“比较差异”时给高分。
- `inform_attributes_brief` 只在顾客已经锁定某个商品、需要确认参数/功能/适用性时给高分。
- `recommend_soft` 只在顾客已偏向某个选项且需要轻柔确认时给高分；不要在模糊需求阶段直接推荐。
- `recommend_firm` 只在顾客已经基本选定、身体/视线呈现准备操作、只差明确确认时给高分；此时它可以高于低成本的 price/reassure。
- `inform_demo_brief` 只在顾客困惑于使用方式、功能展示或新颖商品如何工作时给高分。
- `greet_close` 只在支付/选择已经完成、正在等待出货、取货、致谢或准备离开时给高分；如果顾客还在付款前确认、担心时间或等待同伴意见，不要用 `greet_close` 抢先结束。
- 如果顾客已经按自己的节奏顺畅浏览、比较或操作，且任何主动介入都可能打断当前状态，`hold_silent` 或 `hold_ambient` 可以高于其他动作；不要为了“显得有帮助”而强行介入。
- 不要在 belief/desire/intention 里写 `target_act`、response_id 或 dialogue-act 标签；BDI 必须是自然心理状态描述。

# 一致性约束（输出必须满足）
- next_bdi.intention 必须与 next_aida_stage 语义一致（action 阶段 intention 应为准备操作/购买）
- risk=high 时 delta_mental 通常为负（顾客反感）
- benefit=high 时 delta_mental 不应明显为负
- hold_silent 的 delta_stage 应在 [-0.1, 0.3]

# 顾客 Manifest
{manifest_json}

# 输出格式（只输出 JSON，不附加解释或 Markdown）
{{
  "candidate_actions": ["hold_silent", "response_id_2", "response_id_3", "response_id_4"],
  "outcomes": {{
    "hold_silent": {{
      "next_aida_stage": "...",
      "next_bdi": {{"belief": "...", "desire": "...", "intention": "..."}},
      "risk": "low",
      "benefit": "low",
      "delta_stage": 0.0,
      "delta_mental": 0.0,
      "rationale": "..."
    }},
    "response_id_2": {{"...": "..."}},
    "response_id_3": {{"...": "..."}},
    "response_id_4": {{"...": "..."}}
  }}
}}"""

RETRY_PROMPT = """上一轮输出存在以下一致性问题，请逐条修正后重新输出完整 JSON：

{errors}

只输出修正后的 JSON，不附加解释。"""


# ── Validation ────────────────────────────────────────────────────────────────

def validate_outcomes(current_aida: str, candidates: list[str], outcomes: dict) -> list[str]:
    errors = []
    current_idx = STAGE_ORDER.get(current_aida, -1)
    allowed = set(get_allowed_responses(current_aida))
    required_outcome_keys = {
        "next_aida_stage",
        "next_bdi",
        "risk",
        "benefit",
        "delta_stage",
        "delta_mental",
        "rationale",
    }
    required_bdi_keys = {"belief", "desire", "intention"}

    if len(candidates) != 4:
        errors.append(f"候选数量应为 4 个，当前为 {len(candidates)} 个")

    if len(candidates) != len(set(candidates)):
        errors.append("候选 response_id 不能重复")

    if BASELINE not in candidates:
        errors.append(f"缺少基线候选 {BASELINE}")

    for rid in candidates:
        if rid not in allowed:
            errors.append(f"[{rid}] 不属于 {current_aida} 阶段允许的 response")

    for rid in candidates:
        if rid not in outcomes:
            errors.append(f"缺少候选的 outcome：{rid}")

    for rid, oc in outcomes.items():
        missing = sorted(required_outcome_keys - set(oc))
        if missing:
            errors.append(f"[{rid}] outcome 缺少字段：{', '.join(missing)}")
            continue

        next_bdi = oc.get("next_bdi", {})
        if not isinstance(next_bdi, dict):
            errors.append(f"[{rid}] next_bdi 必须是对象")
            continue

        missing_bdi = sorted(required_bdi_keys - set(next_bdi))
        if missing_bdi:
            errors.append(f"[{rid}] next_bdi 缺少字段：{', '.join(missing_bdi)}")

        misplaced = sorted((required_outcome_keys - {"next_bdi"}) & set(next_bdi))
        if misplaced:
            errors.append(f"[{rid}] 字段被错误放入 next_bdi：{', '.join(misplaced)}")

        next_stage = oc.get("next_aida_stage", "")
        next_idx = STAGE_ORDER.get(next_stage, -1)
        ds = float(oc.get("delta_stage", 0))
        dm = float(oc.get("delta_mental", 0))
        risk = oc.get("risk", "")
        benefit = oc.get("benefit", "")
        intention = next_bdi.get("intention", "")

        if next_stage not in STAGE_ORDER:
            errors.append(f"[{rid}] next_aida_stage={next_stage} 不在允许阶段 {list(STAGE_ORDER)}")

        if not -1.0 <= ds <= 1.0:
            errors.append(f"[{rid}] delta_stage={ds:.2f} 超出 [-1, 1]")

        if not -1.0 <= dm <= 1.0:
            errors.append(f"[{rid}] delta_mental={dm:.2f} 超出 [-1, 1]")

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

        label_leaks = ["target_act", "response_id", "Recommend:", "Inform:", "Elicit:", "Reassure:", "Hold:"]
        bdi_text = " ".join(str(next_bdi.get(k, "")) for k in ("belief", "desire", "intention"))
        for marker in label_leaks:
            if marker in bdi_text:
                errors.append(f"[{rid}] next_bdi 泄漏 action 标签或内部字段：{marker}")

        if rid == BASELINE and abs(ds) > 0.4:
            errors.append(f"[{BASELINE}] delta_stage={ds:.2f} 过大，沉默基线不应大幅改变顾客阶段")

    return errors


# ── Core ──────────────────────────────────────────────────────────────────────

def attach_costs_and_scores(candidates: list[str], outcomes: dict,
                            alpha: float, beta: float, gamma: float) -> None:
    for rid in candidates:
        if rid not in outcomes:
            continue
        oc = outcomes[rid]
        cost = RESPONSE_COSTS.get(rid, 0.0)
        oc.pop("reward", None)
        oc["action_cost"] = cost
        oc["preference_score"] = compute_preference_score(
            float(oc.get("delta_stage", 0)),
            float(oc.get("delta_mental", 0)),
            cost,
            {"alpha": alpha, "beta": beta, "gamma": gamma},
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
    current_aida = manifest.get("aida_stage", "interest")
    allowed = get_allowed_responses(current_aida)

    prompt = EXPERT_PROMPT.format(
        aida_stage=current_aida,
        allowed_response_desc=build_allowed_response_desc(allowed),
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

        attach_costs_and_scores(candidates, outcomes, alpha, beta, gamma)
        errors = validate_outcomes(current_aida, candidates, outcomes)
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
            error_text = "\n".join(f"- {e}" for e in errors)
            raise ValueError(
                f"validation still failing after {MAX_RETRIES} retries:\n{error_text}"
            )

    best_action = max(
        (rid for rid in last_candidates if rid in last_outcomes),
        key=lambda rid: last_outcomes[rid].get("preference_score", -999),
    )
    best_payload = enrich_action_payload(best_action)

    return {
        "candidate_actions": last_candidates,
        "outcomes": last_outcomes,
        "best_action": best_action,
        "response_id": best_payload["response_id"],
        "realization": best_payload["terminal_realization"],
        "score_weights": {"alpha": alpha, "beta": beta, "gamma": gamma},
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def find_missing_labeled() -> list[Path]:
    return [
        f for f in sorted(MANIFEST_DIR.glob("piwm_*.json"))
        if not (LABELED_DIR / f.name).exists()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Deliberation: predict outcomes, compute preference_score, pick best_action. "
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
            aida_stage=manifest.get("aida_stage", "interest"),
            allowed_response_desc=build_allowed_response_desc(get_allowed_responses(manifest.get("aida_stage", "interest"))),
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
