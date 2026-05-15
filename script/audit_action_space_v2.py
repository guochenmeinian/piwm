#!/usr/bin/env python3
"""Audit lightweight PIWM labeled JSON files for v2.2 action-space fields."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from action_space_v2 import ACTION_SCHEMA_VERSION, merge_supporting_acts, supporting_acts_from_params


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LABELED_DIR = REPO_ROOT / "data" / "labeled"


def audit_labeled_dir(labeled_dir: Path) -> dict[str, Any]:
    best_dialogue_acts = Counter()
    candidate_dialogue_acts = Counter()
    supporting_acts = Counter()
    diagnostics = Counter()
    n_outcomes = 0

    for path in sorted(labeled_dir.glob("piwm_*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("schema_version") != ACTION_SCHEMA_VERSION:
            diagnostics["schema_version_mismatch"] += 1
        if "co_acts" in row:
            diagnostics["top_level_co_acts_present"] += 1
        if len(row.get("candidate_actions", [])) != len(row.get("candidate_action_specs", [])):
            diagnostics["candidate_action_specs_count_mismatch"] += 1
        if len(row.get("candidate_actions", [])) != len(row.get("candidate_action_instance_keys", [])):
            diagnostics["candidate_action_instance_keys_count_mismatch"] += 1
        if len(set(row.get("candidate_action_instance_keys", []))) != len(row.get("candidate_action_instance_keys", [])):
            diagnostics["candidate_action_instance_key_duplicate"] += 1
        if row.get("best_action") and not row.get("best_action_spec"):
            diagnostics["best_action_spec_missing"] += 1
        if row.get("outcomes") and not row.get("outcomes_by_action_key"):
            diagnostics["outcomes_by_action_key_missing"] += 1
        if row.get("outcomes") and not row.get("outcomes_by_action_instance_key"):
            diagnostics["outcomes_by_action_instance_key_missing"] += 1
        best_dialogue_acts[row.get("dialogue_act", "<missing>")] += 1
        for support in supporting_acts_from_params(row.get("act_params", {})):
            supporting_acts[support["type"]] += 1

        for outcome in row.get("outcomes", {}).values():
            n_outcomes += 1
            if "co_acts" in outcome:
                diagnostics["outcome_co_acts_present"] += 1
            terminal = outcome.get("terminal_realization", {})
            if "co_acts" in terminal:
                diagnostics["terminal_co_acts_present"] += 1
            if "action_key" not in outcome:
                diagnostics["outcome_action_key_missing"] += 1
            if "action_spec" not in outcome:
                diagnostics["outcome_action_spec_missing"] += 1
            if "action_instance_key" not in outcome:
                diagnostics["outcome_action_instance_key_missing"] += 1
            params = merge_supporting_acts(outcome.get("act_params", {}), outcome.get("co_acts", []))
            candidate_dialogue_acts[outcome.get("dialogue_act", "<missing>")] += 1
            for support in supporting_acts_from_params(params):
                supporting_acts[support["type"]] += 1

    n_records = sum(best_dialogue_acts.values())
    return {
        "artifact": "piwm_lightweight_action_space_v2_2_audit",
        "schema_version": ACTION_SCHEMA_VERSION,
        "labeled_dir": labeled_dir.as_posix(),
        "n_records": n_records,
        "n_outcomes": n_outcomes,
        "best_dialogue_act_counts": dict(sorted(best_dialogue_acts.items())),
        "candidate_dialogue_act_counts": dict(sorted(candidate_dialogue_acts.items())),
        "supporting_act_counts": dict(sorted(supporting_acts.items())),
        "diagnostics": dict(sorted(diagnostics.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labeled-dir", type=Path, default=DEFAULT_LABELED_DIR)
    args = parser.parse_args()
    print(json.dumps(audit_labeled_dir(args.labeled_dir), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
