"""PIWM v2 action-space helpers for the lightweight pipeline.

This module mirrors the canonical action/realization contract maintained in
ProactiveIntentWorldModel while keeping this repository self-contained.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any


ACTION_SCHEMA_VERSION = "dialogue_act_terminal_realization_v2.2"
SUPPORTING_ACTS_PARAM = "supporting_acts"

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


def _normalize_supporting_act(supporting_act: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy co_acts and v2.2 supporting_acts into one shape."""
    act = supporting_act.get("type") or supporting_act.get("act")
    params = supporting_act.get("params", {})
    if not act:
        raise ValueError(f"supporting act missing type/act: {supporting_act}")
    return {"type": act, "params": deepcopy(params)}


def normalize_supporting_acts(supporting_acts: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    normalized = []
    seen = set()
    for supporting_act in supporting_acts or []:
        item = _normalize_supporting_act(supporting_act)
        key = (item["type"], tuple(sorted(item["params"].items())))
        if key not in seen:
            normalized.append(item)
            seen.add(key)
    return normalized


def supporting_acts_from_params(params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return normalize_supporting_acts((params or {}).get(SUPPORTING_ACTS_PARAM, []))


def legacy_co_acts_from_params(params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        {"act": supporting_act["type"], "params": deepcopy(supporting_act.get("params", {}))}
        for supporting_act in supporting_acts_from_params(params)
    ]


def merge_supporting_acts(
    params: dict[str, Any] | None = None,
    co_acts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    merged = deepcopy(params or {})
    supporting_acts = normalize_supporting_acts(
        list(merged.get(SUPPORTING_ACTS_PARAM, [])) + list(co_acts or [])
    )
    if supporting_acts:
        merged[SUPPORTING_ACTS_PARAM] = supporting_acts
    else:
        merged.pop(SUPPORTING_ACTS_PARAM, None)
    return merged


def validate_dialogue_act(act: str, params: dict[str, Any] | None = None) -> None:
    if act not in DIALOGUE_ACTS:
        raise ValueError(f"unknown DialogueAct: {act}")
    params = params or {}
    allowed = DIALOGUE_ACT_PARAM_VALUES[act]
    for key, value in params.items():
        if key == SUPPORTING_ACTS_PARAM:
            continue
        if key not in allowed:
            raise ValueError(f"invalid param for {act}: {key}")
        if value not in allowed[key]:
            raise ValueError(f"invalid value for {act}.{key}: {value}")
    for supporting_act in supporting_acts_from_params(params):
        validate_dialogue_act(supporting_act["type"], supporting_act.get("params", {}))


def _normalize_act_spec(spec: dict[str, Any]) -> dict[str, Any]:
    params = merge_supporting_acts(spec.get("params", {}), spec.get("co_acts", []))
    validate_dialogue_act(spec["act"], params)
    return {
        "act": spec["act"],
        "params": params,
        "co_acts": legacy_co_acts_from_params(params),
    }


def t_state_to_act(t_state: str) -> dict[str, Any]:
    if t_state not in T_STATE_TO_DIALOGUE_ACT:
        raise ValueError(f"unknown T-state: {t_state}")
    return _normalize_act_spec(T_STATE_TO_DIALOGUE_ACT[t_state])


def legacy_action_to_act(action: str) -> dict[str, Any]:
    """Map either canonical A1-A8 labels or older dynamic A* aliases to v2 acts."""
    if action in LEGACY_ACTION_TO_DIALOGUE_ACT:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT[action])

    lowered = action.lower()
    if "silence" in lowered or "silent" in lowered:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT["A1_silent_observe"])
    if "compare" in lowered:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT["A2_offer_value_comparison"])
    if "demo" in lowered or "trial" in lowered:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT["A5_provide_demonstration"])
    if "question" in lowered or "ask" in lowered or "invite" in lowered:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT["A4_open_with_question"])
    if "risk" in lowered or "reassur" in lowered or "wait" in lowered:
        return _normalize_act_spec(LEGACY_ACTION_TO_DIALOGUE_ACT["A6_acknowledge_and_wait"])
    if "recommend" in lowered or "nudge" in lowered or "pick" in lowered or "match" in lowered:
        return _normalize_act_spec({"act": "Recommend", "params": {"target": "item", "pressure": "soft"}, "co_acts": []})
    if "price" in lowered:
        return _normalize_act_spec({"act": "Inform", "params": {"content_type": "price", "depth": "brief"}, "co_acts": []})
    if "info" in lowered or "tag" in lowered or "hint" in lowered or "popular" in lowered:
        return _normalize_act_spec({"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}, "co_acts": []})
    return _normalize_act_spec({"act": "Inform", "params": {"content_type": "attributes", "depth": "brief"}, "co_acts": []})


def action_to_act(action: str) -> dict[str, Any]:
    if action.startswith("T"):
        return t_state_to_act(action)
    return legacy_action_to_act(action)


def canonical_action_spec(action: str) -> dict[str, Any]:
    """Return the canonical v2.2 action object for a legacy/T-state label."""

    spec = action_to_act(action)
    return {"act": spec["act"], "params": deepcopy(spec["params"])}


def action_spec_key(act: str, params: dict[str, Any] | None = None) -> str:
    """Return a stable JSON-safe key for a canonical ``(act, params)`` spec."""

    normalized = merge_supporting_acts(params or {})
    params_json = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(params_json.encode("utf-8")).hexdigest()[:12]
    return f"{act}_{digest}"


def action_instance_key(action: str, action_key: str, *, disambiguate: bool = False) -> str:
    """Return a unique key for one legacy/T-state candidate occurrence."""

    if not disambiguate:
        return action_key
    digest = hashlib.sha1(action.encode("utf-8")).hexdigest()[:8]
    return f"{action_key}__{digest}"


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
    act_params = merge_supporting_acts(act_params, co_acts)
    validate_dialogue_act(dialogue_act, act_params)
    template = deepcopy(REALIZATION_TEMPLATES.get(_template_key(dialogue_act, act_params), REALIZATION_TEMPLATES["Hold:ambient"]))
    template.update(
        {
            "dialogue_act": dialogue_act,
            "act_params": deepcopy(act_params),
            "legacy_action": legacy_action,
        }
    )
    legacy_co_acts = legacy_co_acts_from_params(act_params)
    if legacy_co_acts:
        template["legacy_co_acts"] = legacy_co_acts
    return template


def enrich_action_payload(action: str) -> dict[str, Any]:
    act = action_to_act(action)
    action_spec = {"act": act["act"], "params": deepcopy(act["params"])}
    payload = {
        "action_key": action_spec_key(act["act"], act["params"]),
        "action_spec": action_spec,
        "dialogue_act": act["act"],
        "act_params": deepcopy(act["params"]),
        "terminal_realization": derive_terminal_realization(
            act["act"],
            act["params"],
            act.get("co_acts", []),
            legacy_action=T_STATE_LEGACY_ACTION.get(action, action),
        ),
    }
    legacy_co_acts = legacy_co_acts_from_params(act["params"])
    if legacy_co_acts:
        payload["legacy_co_acts"] = legacy_co_acts
    return payload


def enrich_labeled_record(record: dict[str, Any]) -> dict[str, Any]:
    """Add v2.2 action/realization fields to a labeled record in-place and return it."""

    record["schema_version"] = ACTION_SCHEMA_VERSION
    outcomes = record.get("outcomes", {})
    candidate_actions = list(record.get("candidate_actions") or outcomes.keys())
    candidate_specs = [canonical_action_spec(action) for action in candidate_actions]
    candidate_keys = [action_spec_key(spec["act"], spec["params"]) for spec in candidate_specs]
    duplicate_keys = {key for key in candidate_keys if candidate_keys.count(key) > 1}
    candidate_instance_keys = [
        action_instance_key(action, key, disambiguate=key in duplicate_keys)
        for action, key in zip(candidate_actions, candidate_keys)
    ]
    action_to_instance_key = dict(zip(candidate_actions, candidate_instance_keys))
    if candidate_actions:
        record["candidate_action_specs"] = candidate_specs
        record["candidate_action_keys"] = candidate_keys
        record["candidate_action_instance_keys"] = candidate_instance_keys

    outcomes_by_action_key: dict[str, list[Any]] = {}
    outcomes_by_action_instance_key: dict[str, Any] = {}
    for action, outcome in outcomes.items():
        outcome.update(enrich_action_payload(action))
        outcome.pop("co_acts", None)
        instance_key = action_to_instance_key.get(action) or action_instance_key(action, outcome["action_key"])
        outcome["action_instance_key"] = instance_key
        outcomes_by_action_key.setdefault(outcome["action_key"], []).append(outcome)
        outcomes_by_action_instance_key[instance_key] = outcome
    if outcomes_by_action_key:
        record["outcomes_by_action_key"] = outcomes_by_action_key
        record["outcomes_by_action_instance_key"] = outcomes_by_action_instance_key

    best_action = record.get("best_action")
    if best_action:
        best = enrich_action_payload(best_action)
        record["best_action_spec"] = best["action_spec"]
        record["best_action_key"] = best["action_key"]
        record["best_action_instance_key"] = action_to_instance_key.get(best_action, best["action_key"])
        record["dialogue_act"] = best["dialogue_act"]
        record["act_params"] = best["act_params"]
        record.pop("co_acts", None)
        if best.get("legacy_co_acts"):
            record["legacy_co_acts"] = best["legacy_co_acts"]
        else:
            record.pop("legacy_co_acts", None)
        record["realization"] = best["terminal_realization"]
    return record
