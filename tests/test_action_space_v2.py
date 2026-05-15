import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "script"))

from action_space_v2 import ACTION_SCHEMA_VERSION, action_spec_key, enrich_labeled_record  # noqa: E402


def test_enrich_labeled_record_adds_v2_2_action_specs_and_keys():
    record = {
        "candidate_actions": ["T1_SILENT_OBSERVE", "T6_ACK_WAIT"],
        "best_action": "T6_ACK_WAIT",
        "outcomes": {
            "T1_SILENT_OBSERVE": {"reward": 0.1, "risk": "low", "benefit": "low"},
            "T6_ACK_WAIT": {"reward": 0.4, "risk": "low", "benefit": "medium"},
        },
    }

    enriched = enrich_labeled_record(record)

    assert ACTION_SCHEMA_VERSION == "dialogue_act_terminal_realization_v2.2"
    assert enriched["candidate_action_specs"] == [
        {"act": "Hold", "params": {"mode": "silent"}},
        {
            "act": "Reassure",
            "params": {
                "focus": "time",
                "supporting_acts": [{"type": "Hold", "params": {"mode": "ambient"}}],
            },
        },
    ]
    assert enriched["best_action_spec"] == enriched["candidate_action_specs"][1]
    expected_key = action_spec_key("Reassure", enriched["best_action_spec"]["params"])
    assert expected_key in enriched["outcomes_by_action_key"]
    assert enriched["outcomes_by_action_key"][expected_key][0]["reward"] == 0.4


def test_action_spec_key_is_stable_for_param_order():
    assert action_spec_key("Recommend", {"target": "item", "pressure": "firm"}) == action_spec_key(
        "Recommend", {"pressure": "firm", "target": "item"}
    )


def test_enrich_labeled_record_preserves_duplicate_canonical_action_keys():
    record = {
        "candidate_actions": ["A1_surface_value_offer", "A3_highlight_confirm_with_edit_safety"],
        "best_action": "A1_surface_value_offer",
        "outcomes": {
            "A1_surface_value_offer": {"reward": 0.3, "risk": "low", "benefit": "medium"},
            "A3_highlight_confirm_with_edit_safety": {"reward": 0.5, "risk": "low", "benefit": "high"},
        },
    }

    enriched = enrich_labeled_record(record)

    canonical_key = action_spec_key("Inform", {"content_type": "attributes", "depth": "brief"})
    assert len(enriched["outcomes_by_action_key"][canonical_key]) == 2
    assert len(set(enriched["candidate_action_instance_keys"])) == 2
    assert set(enriched["outcomes_by_action_instance_key"]) == set(enriched["candidate_action_instance_keys"])
