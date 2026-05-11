"""PIWM v2 action-space helpers for the lightweight pipeline.

This module mirrors the canonical action/realization contract maintained in
ProactiveIntentWorldModel while keeping this repository self-contained.
"""

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
    "Recommend": {"target": ["item", "action"], "pressure": ["soft", "firm"]},
    "Reassure": {"focus": ["time", "decision", "alternatives"]},
    "Hold": {"mode": ["silent", "ambient"]},
}

LEGACY_ACTION_TO_DIALOGUE_ACT: dict[str, dict[str, Any]] = {
    "A1_silent_observe": {"act": "Hold", "params": {"mode": "silent"}, "co_acts": []},
    "A2_offer_value_comparison": {
        "act": "Inform",
        "params": {"content_type": "comparison", "depth": "brief"},
        "co_acts": [],
    },
    "A3_strong_recommend": {"act": "Recommend", "params": {"target": "item", "pressure": "firm"}, "co_acts": []},
    "A4_open_with_question": {"act": "Elicit", "params": {"openness": "open", "slot": "need_focus"}, "co_acts": []},
    "A5_provide_demonstration": {
        "act": "Inform",
        "params": {"content_type": "demo", "depth": "brief"},
        "co_acts": [],
    },
    "A6_acknowledge_and_wait": {
        "act": "Reassure",
        "params": {"focus": "time"},
        "co_acts": [{"act": "Hold", "params": {"mode": "ambient"}}],
    },
    "A7_disengage": {"act": "Hold", "params": {"mode": "ambient"}, "co_acts": []},
    "A8_offer_companion_invite": {
        "act": "Elicit",
        "params": {"openness": "open", "slot": "companion_opinion"},
        "co_acts": [],
    },
}

T_STATE_TO_DIALOGUE_ACT: dict[str, dict[str, Any]] = {
    "T1_SILENT_OBSERVE": LEGACY_ACTION_TO_DIALOGUE_ACT["A1_silent_observe"],
    "T2_VALUE_COMPARE": LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"],
    "T3_STRONG_RECOMMEND": LEGACY_ACTION_TO_DIALOGUE_ACT["A3_strong_recommend"],
    "T4_OPEN_QUESTION": LEGACY_ACTION_TO_DIALOGUE_ACT["A4_open_with_question"],
    "T5_DEMO": LEGACY_ACTION_TO_DIALOGUE_ACT["A5_provide_demonstration"],
    "T6_ACK_WAIT": LEGACY_ACTION_TO_DIALOGUE_ACT["A6_acknowledge_and_wait"],
    "T7_DISENGAGE": LEGACY_ACTION_TO_DIALOGUE_ACT["A7_disengage"],
    "T_TRANSACT": {"act": "Greet", "params": {"phase": "close"}, "co_acts": []},
}

T_STATE_LEGACY_ACTION: dict[str, str | None] = {
    "T1_SILENT_OBSERVE": "A1_silent_observe",
    "T2_VALUE_COMPARE": "A2_offer_value_comparison",
    "T3_STRONG_RECOMMEND": "A3_strong_recommend",
    "T4_OPEN_QUESTION": "A4_open_with_question",
    "T5_DEMO": "A5_provide_demonstration",
    "T6_ACK_WAIT": "A6_acknowledge_and_wait",
    "T7_DISENGAGE": "A7_disengage",
    "T_TRANSACT": None,
}

REALIZATION_TEMPLATES: dict[str, dict[str, Any]] = {
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


def t_state_to_act(t_state: str) -> dict[str, Any]:
    if t_state not in T_STATE_TO_DIALOGUE_ACT:
        raise ValueError(f"unknown T-state: {t_state}")
    return deepcopy(T_STATE_TO_DIALOGUE_ACT[t_state])


def legacy_action_to_act(action: str) -> dict[str, Any]:
    """Map either canonical A1-A8 labels or older dynamic A* aliases to v2 acts."""
    if action in LEGACY_ACTION_TO_DIALOGUE_ACT:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT[action])

    lowered = action.lower()
    if "silence" in lowered or "silent" in lowered:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT["A1_silent_observe"])
    if "compare" in lowered:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"])
    if "demo" in lowered or "trial" in lowered:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT["A5_provide_demonstration"])
    if "question" in lowered or "ask" in lowered or "invite" in lowered:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT["A4_open_with_question"])
    if "risk" in lowered or "reassur" in lowered or "wait" in lowered:
        return deepcopy(LEGACY_ACTION_TO_DIALOGUE_ACT["A6_acknowledge_and_wait"])
    if "recommend" in lowered or "nudge" in lowered or "pick" in lowered or "match" in lowered:
        return {"act": "Recommend", "params": {"target": "item", "pressure": "soft"}, "co_acts": []}
    if "price" in lowered:
        return {"act": "Inform", "params": {"content_type": "price", "depth": "brief"}, "co_acts": []}
    if "info" in lowered or "tag" in lowered or "hint" in lowered or "popular" in lowered:
        return {"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}, "co_acts": []}
    return {"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}, "co_acts": []}


def action_to_act(action: str) -> dict[str, Any]:
    if action.startswith("T"):
        return t_state_to_act(action)
    return legacy_action_to_act(action)


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
    legacy_action: str | None = None,
) -> dict[str, Any]:
    template = deepcopy(REALIZATION_TEMPLATES.get(_template_key(dialogue_act, act_params), REALIZATION_TEMPLATES["Hold:ambient"]))
    template.update(
        {
            "dialogue_act": dialogue_act,
            "act_params": deepcopy(act_params),
            "co_acts": deepcopy(co_acts or []),
            "legacy_action": legacy_action,
        }
    )
    return template


def enrich_action_payload(action: str) -> dict[str, Any]:
    act = action_to_act(action)
    return {
        "dialogue_act": act["act"],
        "act_params": deepcopy(act["params"]),
        "co_acts": deepcopy(act.get("co_acts", [])),
        "terminal_realization": derive_terminal_realization(
            act["act"],
            act["params"],
            act.get("co_acts", []),
            legacy_action=T_STATE_LEGACY_ACTION.get(action, action),
        ),
    }


def enrich_labeled_record(record: dict[str, Any]) -> dict[str, Any]:
    """Add v2 action/realization fields to a labeled record in-place and return it."""
    outcomes = record.get("outcomes", {})
    for action, outcome in outcomes.items():
        outcome.update(enrich_action_payload(action))

    best_action = record.get("best_action")
    if best_action:
        best = enrich_action_payload(best_action)
        record["dialogue_act"] = best["dialogue_act"]
        record["act_params"] = best["act_params"]
        record["co_acts"] = best["co_acts"]
        record["realization"] = best["terminal_realization"]
    return record
