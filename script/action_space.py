"""PIWM action-space helpers for the lightweight pipeline."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DIALOGUE_ACTS = [
    "Greet",
    "Elicit",
    "Inform",
    "Recommend",
    "Reassure",
    "Hold",
]

DIALOGUE_ACT_PARAM_VALUES: dict[str, dict[str, list[str]]] = {
    "Greet": {"phase": ["open", "close"]},
    "Elicit": {"openness": ["open", "closed"], "slot": ["need_focus", "budget", "usage", "companion_opinion"]},
    "Inform": {"content_type": ["comparison", "demo", "attributes", "price"], "depth": ["brief", "detailed"]},
    "Recommend": {"pressure": ["soft", "firm"]},
    "Reassure": {"focus": ["time", "decision", "alternatives"]},
    "Hold": {"mode": ["silent", "ambient"]},
}

RESPONSE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "hold_silent": {"act": "Hold", "params": {"mode": "silent"}, "co_acts": []},
    "inform_comparison_brief": {
        "act": "Inform",
        "params": {"content_type": "comparison", "depth": "brief"},
        "co_acts": [],
    },
    "recommend_firm": {"act": "Recommend", "params": {"pressure": "firm"}, "co_acts": []},
    "elicit_need_focus_open": {"act": "Elicit", "params": {"openness": "open", "slot": "need_focus"}, "co_acts": []},
    "inform_demo_brief": {
        "act": "Inform",
        "params": {"content_type": "demo", "depth": "brief"},
        "co_acts": [],
    },
    "reassure_time_wait": {
        "act": "Reassure",
        "params": {"focus": "time"},
        "co_acts": [{"act": "Hold", "params": {"mode": "ambient"}}],
    },
    "hold_ambient": {"act": "Hold", "params": {"mode": "ambient"}, "co_acts": []},
    "elicit_companion_opinion_open": {
        "act": "Elicit",
        "params": {"openness": "open", "slot": "companion_opinion"},
        "co_acts": [],
    },
    "greet_close": {"act": "Greet", "params": {"phase": "close"}, "co_acts": []},
    "reassure_decision": {"act": "Reassure", "params": {"focus": "decision"}, "co_acts": []},
    "reassure_alternatives": {"act": "Reassure", "params": {"focus": "alternatives"}, "co_acts": []},
    "elicit_budget": {"act": "Elicit", "params": {"openness": "open", "slot": "budget"}, "co_acts": []},
}

LEGACY_RESPONSE_IDS: dict[str, str] = {
    "T1_SILENT_OBSERVE": "hold_silent",
    "T2_VALUE_COMPARE": "inform_comparison_brief",
    "T3_STRONG_RECOMMEND": "recommend_firm",
    "T4_OPEN_QUESTION": "elicit_need_focus_open",
    "T5_DEMO": "inform_demo_brief",
    "T6_ACK_WAIT": "reassure_time_wait",
    "T7_DISENGAGE": "hold_ambient",
    "T_TRANSACT": "greet_close",
    "A1_silent_observe": "hold_silent",
    "A2_offer_value_comparison": "inform_comparison_brief",
    "A3_strong_recommend": "recommend_firm",
    "A4_open_with_question": "elicit_need_focus_open",
    "A5_provide_demonstration": "inform_demo_brief",
    "A6_acknowledge_and_wait": "reassure_time_wait",
    "A7_disengage": "hold_ambient",
    "A8_offer_companion_invite": "elicit_companion_opinion_open",
}

REALIZATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "Reassure:decision": {
        "surface_text": "您可以先保留几个候选，不用马上决定。",
        "screen": {"action": "show_shortlist_hint", "cta": None},
        "voice_style": "soft",
        "light": "low_pressure_idle",
        "cabinet_motion": None,
        "duration_ms": 3500,
    },
    "Reassure:alternatives": {
        "surface_text": "还有其他选择，您不用现在就定，可以先看看别的。",
        "screen": {"action": "show_alternatives_hint", "cta": None},
        "voice_style": "soft",
        "light": "low_pressure_idle",
        "cabinet_motion": None,
        "duration_ms": 3000,
    },
    "Elicit:budget": {
        "surface_text": "您大概想花多少？我帮您筛选合适的选项。",
        "screen": {"action": "show_budget_input", "cta": None},
        "voice_style": "curious",
        "light": "soft_invitation",
        "cabinet_motion": None,
        "duration_ms": 4000,
    },
    "Hold:silent": {
        "surface_text": "",
        "screen": {"action": "idle_minimal", "cta": None},
        "voice_style": "silent",
        "light": "maintain_current_soft_breathing",
        "cabinet_motion": None,
        "duration_ms": 0,
    },
    "Hold:ambient": {
        "surface_text": "您慢慢看，需要时我再帮您。",
        "screen": {"action": "return_to_attract_loop", "cta": None},
        "voice_style": "soft",
        "light": "ambient_low_attention",
        "cabinet_motion": None,
        "duration_ms": 2500,
    },
    "Inform:comparison": {
        "surface_text": "我把这几款的差别列在屏幕上，您可以先比较价格、功能和适合场景。",
        "screen": {"action": "show_comparison_or_details", "target": "{candidate_items}", "cta": None},
        "voice_style": "neutral",
        "light": "soft_focus_on_comparison_cards",
        "cabinet_motion": None,
        "duration_ms": 4000,
    },
    "Inform:demo": {
        "surface_text": "我用一个简短演示帮您看清楚这个功能。",
        "screen": {"action": "play_short_demo", "target": "{selected_item}", "cta": None},
        "voice_style": "neutral",
        "light": "focus_on_demo_area",
        "cabinet_motion": None,
        "duration_ms": 8000,
    },
    "Inform:attributes": {
        "surface_text": "屏幕上列出了主要参数、价格和适合人群，您可以先快速看一眼。",
        "screen": {"action": "show_attribute_table", "target": "{selected_item}", "cta": None},
        "voice_style": "neutral",
        "light": "soft_focus_on_attribute_table",
        "cabinet_motion": None,
        "duration_ms": 5000,
    },
    "Inform:price": {
        "surface_text": "我先把价格和优惠信息放在屏幕上，方便您判断。",
        "screen": {"action": "show_price_or_discount", "target": "{selected_item}", "cta": None},
        "voice_style": "neutral",
        "light": "soft_focus_on_price",
        "cabinet_motion": None,
        "duration_ms": 3500,
    },
    "Recommend:soft": {
        "surface_text": "如果您想省时间，可以先从这款开始看，它比较符合您现在关注的点。",
        "screen": {"action": "highlight_recommended_item", "target": "{recommended_item}", "cta": None},
        "voice_style": "soft",
        "light": "gentle_highlight",
        "cabinet_motion": None,
        "duration_ms": 4500,
    },
    "Recommend:firm": {
        "surface_text": "这款最适合您，建议直接选这款。",
        "screen": {"action": "highlight_single_item_with_cta", "target": "{recommended_item}", "cta": "buy_now"},
        "voice_style": "assertive",
        "light": "strong_highlight",
        "cabinet_motion": None,
        "duration_ms": 5000,
    },
    "Elicit:need_focus": {
        "surface_text": "您今天想先看价格、功能，还是适合什么场景？",
        "screen": {"action": "show_choice_bubbles", "choices": ["价格", "功能", "场景"], "cta": None},
        "voice_style": "curious",
        "light": "soft_invitation",
        "cabinet_motion": None,
        "duration_ms": 5000,
    },
    "Elicit:companion_opinion": {
        "surface_text": "如果是送人或和同伴一起选，也可以按使用场景来比较。",
        "screen": {"action": "show_companion_or_gift_prompt", "cta": None},
        "voice_style": "curious",
        "light": "soft_invitation",
        "cabinet_motion": None,
        "duration_ms": 4500,
    },
    "Reassure:time": {
        "surface_text": "不着急，您可以慢慢看，需要我时我再出现。",
        "screen": {"action": "show_low_pressure_wait_message", "cta": None},
        "voice_style": "soft",
        "light": "low_pressure_idle",
        "cabinet_motion": None,
        "duration_ms": 3000,
    },
    "Reassure:decision": {
        "surface_text": "您可以先保留几个候选，不用马上决定。",
        "screen": {"action": "show_shortlist_hint", "cta": None},
        "voice_style": "soft",
        "light": "low_pressure_idle",
        "cabinet_motion": None,
        "duration_ms": 3500,
    },
    "Greet:close": {
        "surface_text": "感谢惠顾，祝您使用愉快。",
        "screen": {"action": "show_thank_you", "cta": None},
        "voice_style": "warm",
        "light": "transaction_complete",
        "cabinet_motion": "dispense_or_unlock_if_applicable",
        "duration_ms": 3000,
    },
}


def normalize_response_id(response_id: str) -> str:
    if response_id in RESPONSE_DEFINITIONS:
        return response_id
    if response_id in LEGACY_RESPONSE_IDS:
        return LEGACY_RESPONSE_IDS[response_id]

    lowered = response_id.lower()
    if "silence" in lowered or "silent" in lowered:
        return "hold_silent"
    if "compare" in lowered:
        return "inform_comparison_brief"
    if "demo" in lowered or "trial" in lowered:
        return "inform_demo_brief"
    if "question" in lowered or "ask" in lowered or "invite" in lowered:
        return "elicit_need_focus_open"
    if "risk" in lowered or "reassur" in lowered or "wait" in lowered:
        return "reassure_time_wait"
    if "recommend" in lowered or "nudge" in lowered or "pick" in lowered or "match" in lowered:
        return "recommend_soft"
    if "price" in lowered:
        return "inform_price_brief"
    if "info" in lowered or "tag" in lowered or "hint" in lowered or "popular" in lowered:
        return "inform_attributes_brief"
    return "inform_attributes_brief"


RESPONSE_DEFINITIONS.update(
    {
        "recommend_soft": {"act": "Recommend", "params": {"pressure": "soft"}, "co_acts": []},
        "inform_price_brief": {
            "act": "Inform",
            "params": {"content_type": "price", "depth": "brief"},
            "co_acts": [],
        },
        "inform_attributes_brief": {
            "act": "Inform",
            "params": {"content_type": "attributes", "depth": "brief"},
            "co_acts": [],
        },
    }
)

RESPONSE_COSTS: dict[str, float] = {
    "hold_silent": 0.00,
    "hold_ambient": 0.05,
    "reassure_time_wait": 0.10,
    "reassure_decision": 0.10,
    "reassure_alternatives": 0.10,
    "elicit_need_focus_open": 0.20,
    "elicit_budget": 0.20,
    "elicit_companion_opinion_open": 0.20,
    "inform_attributes_brief": 0.25,
    "inform_price_brief": 0.25,
    "inform_comparison_brief": 0.30,
    "inform_demo_brief": 0.40,
    "recommend_soft": 0.45,
    "recommend_firm": 0.65,
    "greet_close": 0.00,
}

RESPONSE_DESCRIPTIONS: dict[str, str] = {
    "hold_silent": "静默观察——屏幕保持极简 attract，不做任何主动介入。顾客感受：完全自主空间，零压力。",
    "hold_ambient": "主动退出互动——回到 attract loop，数字人「不打扰您了」后静默。顾客感受：被放手，无追销感。",
    "reassure_time_wait": "消除时间焦虑——屏幕显示「为您保留中」小窗，数字人「您慢慢看」后退到背景。顾客感受：时间压力消除。",
    "reassure_decision": "降低决策压力——数字人「不用马上决定，可以先保留候选」。顾客感受：后悔风险降低。",
    "reassure_alternatives": "提示备选——数字人「还有其他选择，不用现在定」。顾客感受：不被锁定。",
    "elicit_need_focus_open": "开放式引导——三选一气泡（功能/价格/场景），数字人「您今天想先看哪一点？」",
    "elicit_budget": "询问预算——数字人「您大概想花多少？」帮助缩小候选范围。",
    "elicit_companion_opinion_open": "邀请同伴发言——数字人「这位朋友觉得哪款更合适？」引入同伴参与决策。",
    "inform_attributes_brief": "展示商品参数——屏幕列出主要规格、价格和适合人群。低打扰。",
    "inform_price_brief": "展示价格优惠——屏幕显示当前价格和优惠信息，直接解决价格疑虑。",
    "inform_comparison_brief": "弹出对比卡——双卡对比价格/规格/场景，无强 CTA。选择成本降低。",
    "inform_demo_brief": "短演示——关键功能 3D 动画（≤10s），数字人简短解说。直观了解功能亮点。",
    "recommend_soft": "软推荐——高亮某款商品，数字人「这款比较符合您关注的点」，无强 CTA。",
    "recommend_firm": "强推荐——单品全屏 + 「立即购买」CTA，数字人「这款最适合您，建议直接选」。推销感较强。",
    "greet_close": "收尾致谢——订单确认页，数字人致谢，出货口出货。顾客感受：顺畅完成购买。",
}

DEFAULT_SCORE_WEIGHTS = {"alpha": 0.4, "beta": 0.5, "gamma": 0.2}


def compute_preference_score(delta_stage: float, delta_mental: float, action_cost: float, weights: dict[str, float] | None = None) -> float:
    w = weights or DEFAULT_SCORE_WEIGHTS
    score = (
        float(w.get("alpha", DEFAULT_SCORE_WEIGHTS["alpha"])) * delta_stage
        + float(w.get("beta", DEFAULT_SCORE_WEIGHTS["beta"])) * delta_mental
        - float(w.get("gamma", DEFAULT_SCORE_WEIGHTS["gamma"])) * action_cost
    )
    return max(-1.0, min(1.0, score))


def response_to_act(response_id: str) -> dict[str, Any]:
    normalized = normalize_response_id(response_id)
    if normalized not in RESPONSE_DEFINITIONS:
        raise ValueError(f"unknown response_id: {response_id}")
    return deepcopy(RESPONSE_DEFINITIONS[normalized])


def _template_key(dialogue_act: str, act_params: dict[str, Any]) -> str:
    if dialogue_act == "Hold":
        return f"Hold:{act_params.get('mode', 'ambient')}"
    if dialogue_act == "Inform":
        return f"Inform:{act_params.get('content_type', 'attributes')}"
    if dialogue_act == "Recommend":
        return f"Recommend:{act_params.get('pressure', 'soft')}"
    if dialogue_act == "Elicit":
        return f"Elicit:{act_params.get('slot', 'need_focus')}"
    if dialogue_act == "Reassure":
        return f"Reassure:{act_params.get('focus', 'time')}"
    if dialogue_act == "Greet":
        return f"Greet:{act_params.get('phase', 'close')}"
    return "Hold:ambient"


def derive_terminal_realization(
    dialogue_act: str,
    act_params: dict[str, Any],
    co_acts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    template = deepcopy(REALIZATION_TEMPLATES.get(_template_key(dialogue_act, act_params), REALIZATION_TEMPLATES["Hold:ambient"]))
    return template


def enrich_action_payload(response_id: str) -> dict[str, Any]:
    normalized = normalize_response_id(response_id)
    act = response_to_act(normalized)
    return {
        "response_id": normalized,
        "terminal_realization": derive_terminal_realization(
            act["act"],
            act["params"],
            act.get("co_acts", []),
        ),
    }


def enrich_labeled_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize response ids and enrich action/realization fields in-place."""
    outcomes = record.get("outcomes", {})
    normalized_outcomes: dict[str, Any] = {}
    weights = DEFAULT_SCORE_WEIGHTS
    for response_id, outcome in outcomes.items():
        normalized = normalize_response_id(response_id)
        if "reward" in outcome and "preference_score" not in outcome:
            outcome["preference_score"] = outcome.pop("reward")
        # Older labeled files used delta_mental in roughly [-3, 3]. Current
        # schema uses [-1, 1], so normalize obvious old-scale values.
        delta_mental = float(outcome.get("delta_mental", 0.0))
        if abs(delta_mental) > 1.0:
            delta_mental = max(-1.0, min(1.0, delta_mental / 3.0))
            outcome["delta_mental"] = delta_mental
        outcome.pop("dialogue_act", None)
        outcome.pop("act_params", None)
        outcome.pop("co_acts", None)
        outcome.update(enrich_action_payload(normalized))
        cost = RESPONSE_COSTS.get(normalized, 0.0)
        outcome["action_cost"] = cost
        outcome["preference_score"] = compute_preference_score(
            float(outcome.get("delta_stage", 0.0)),
            float(outcome.get("delta_mental", 0.0)),
            cost,
            weights,
        )
        normalized_outcomes[normalized] = outcome
    if normalized_outcomes:
        record["outcomes"] = normalized_outcomes

    candidate_actions = record.get("candidate_actions", [])
    if candidate_actions:
        if normalized_outcomes:
            record["candidate_actions"] = list(normalized_outcomes.keys())
        else:
            record["candidate_actions"] = list(dict.fromkeys(normalize_response_id(action) for action in candidate_actions))

    if normalized_outcomes:
        normalized_best = max(
            normalized_outcomes,
            key=lambda rid: normalized_outcomes[rid].get("preference_score", -999),
        )
        record["best_action"] = normalized_best
        best = enrich_action_payload(normalized_best)
        record["response_id"] = best["response_id"]
        record["realization"] = best["terminal_realization"]
    record.pop("dialogue_act", None)
    record.pop("act_params", None)
    record.pop("co_acts", None)
    record.pop("reward_weights", None)
    record["score_weights"] = deepcopy(DEFAULT_SCORE_WEIGHTS)
    return record
