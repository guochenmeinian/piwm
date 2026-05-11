# Pipeline

```text
data/seed/piwm_NNN.txt
  -> gen_manifest.py      -> data/manifest/piwm_NNN.json
  -> gen_deliberation.py  -> data/labeled/piwm_NNN.json
  -> gen_video.py         -> data/kling/piwm_NNN.md
  -> Kling API            -> data/video/piwm_NNN.mp4
```

## Step 1: Manifest

`gen_manifest.py` 生成当前顾客状态：

- persona / persona_visual
- AIDA stage
- BDI: belief / desire / intention
- observable behavior
- facial expression
- body posture
- 10 秒 timeline

Manifest 不包含机器动作，不包含终端响应。

## Step 2: Deliberation

`gen_deliberation.py` 对当前 AIDA 阶段取 4 个候选 T-state，逐一预测 outcome、计算 reward，并选择 `best_action`。

T-state 是兼容标签；脚本会自动补齐 v2 字段：

- `dialogue_act`
- `act_params`
- `co_acts`
- `terminal_realization`

输出结构：

```json
{
  "candidate_actions": ["T1_SILENT_OBSERVE", "T2_VALUE_COMPARE", "T4_OPEN_QUESTION", "T5_DEMO"],
  "outcomes": {
    "T2_VALUE_COMPARE": {
      "next_aida_stage": "desire",
      "next_bdi": {"belief": "...", "desire": "...", "intention": "..."},
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.33,
      "delta_mental": 1.5,
      "action_cost": 0.3,
      "reward": 0.852,
      "rationale": "...",
      "dialogue_act": "Inform",
      "act_params": {"content_type": "comparison", "depth": "brief"},
      "co_acts": [],
      "terminal_realization": {"surface_text": "...", "screen": {"action": "show_comparison_or_details"}}
    }
  },
  "best_action": "T2_VALUE_COMPARE",
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": [],
  "realization": {"surface_text": "..."}
}
```

## Step 3: Kling Prompt

`gen_video.py` 将 manifest/labeled 中的顾客观察字段填入 Kling prompt。这个视频是 intervention 前的顾客状态片段，因此不强制写 terminal realization。

## Backfill Existing Samples

已有 22 条 labeled 样例来自旧动态 A-action。运行：

```bash
python script/upgrade_labeled_v2.py
```

脚本会保留旧动作名，同时补齐 v2 policy 和 terminal realization 字段。
