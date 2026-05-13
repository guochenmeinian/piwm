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
    response_id: str | None = None,
) -> dict[str, Any]:
    template = deepcopy(REALIZATION_TEMPLATES.get(_template_key(dialogue_act, act_params), REALIZATION_TEMPLATES["Hold:ambient"]))
    template.update(
        {
            "dialogue_act": dialogue_act,
            "act_params": deepcopy(act_params),
            "co_acts": deepcopy(co_acts or []),
            "response_id": response_id,
        }
    )
    return template


def enrich_action_payload(response_id: str) -> dict[str, Any]:
    normalized = normalize_response_id(response_id)
    act = response_to_act(normalized)
    return {
        "response_id": normalized,
        "dialogue_act": act["act"],
        "act_params": deepcopy(act["params"]),
        "co_acts": deepcopy(act.get("co_acts", [])),
        "terminal_realization": derive_terminal_realization(
            act["act"],
            act["params"],
            act.get("co_acts", []),
            response_id=normalized,
        ),
    }


def enrich_labeled_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize response ids and enrich action/realization fields in-place."""
    outcomes = record.get("outcomes", {})
    normalized_outcomes: dict[str, Any] = {}
    for response_id, outcome in outcomes.items():
        normalized = normalize_response_id(response_id)
        outcome.update(enrich_action_payload(normalized))
        normalized_outcomes[normalized] = outcome
    if normalized_outcomes:
        record["outcomes"] = normalized_outcomes

    candidate_actions = record.get("candidate_actions", [])
    if candidate_actions:
        record["candidate_actions"] = [normalize_response_id(action) for action in candidate_actions]

    best_action = record.get("best_action")
    if best_action:
        normalized_best = normalize_response_id(best_action)
        record["best_action"] = normalized_best
        best = enrich_action_payload(normalized_best)
        record["response_id"] = best["response_id"]
        record["dialogue_act"] = best["dialogue_act"]
        record["act_params"] = best["act_params"]
        record["co_acts"] = best["co_acts"]
        record["realization"] = best["terminal_realization"]
    return record
