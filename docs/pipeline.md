# Pipeline

```text
data/seed/piwm_NNN.txt
  -> gen_manifest.py      -> data/manifest/piwm_NNN.json
  -> gen_deliberation.py  -> data/labeled/piwm_NNN.json
  -> gen_prompt.py        -> data/prompts/piwm_NNN.md
  -> gen_video.py         -> data/video/piwm_NNN.mp4
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

`gen_deliberation.py` 对当前 AIDA 阶段取 4 个候选 `response_id`，逐一预测 outcome、计算 reward，并选择 `best_action`。

脚本会自动补齐这些动作字段：

- `response_id`
- `dialogue_act`
- `act_params`
- `co_acts`
- `terminal_realization`

输出结构：

```json
{
  "candidate_actions": ["hold_silent", "inform_comparison_brief", "elicit_need_focus_open", "inform_demo_brief"],
  "outcomes": {
    "inform_comparison_brief": {
      "next_aida_stage": "desire",
      "next_bdi": {"belief": "...", "desire": "...", "intention": "..."},
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.33,
      "delta_mental": 1.5,
      "action_cost": 0.3,
      "reward": 0.852,
      "rationale": "...",
      "response_id": "inform_comparison_brief",
      "dialogue_act": "Inform",
      "act_params": {"content_type": "comparison", "depth": "brief"},
      "co_acts": [],
      "terminal_realization": {"surface_text": "...", "screen": {"action": "show_comparison_or_details"}}
    }
  },
  "best_action": "inform_comparison_brief",
  "response_id": "inform_comparison_brief",
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": [],
  "realization": {"surface_text": "..."}
}
```

## Step 3: Prompt

`gen_prompt.py` 将 manifest/labeled 中的顾客观察字段填入 pre-interaction 视频 prompt。这个 prompt 只描述 intervention 前的顾客状态片段，不写 terminal realization。

## Step 4: Video

`gen_video.py` 读取 `data/prompts/*.md` 并调用 Kling API 生成视频。

## Normalize Labeled Files

运行：

```bash
python script/upgrade_labeled.py
```

脚本会统一 labeled 文件中的 `response_id`、action 语义字段与 terminal realization 字段。
