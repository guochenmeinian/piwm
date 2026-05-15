# Proactive Intent World Model (PIWM)

轻量版 PIWM 数据合成仓库。它保留 `seed -> manifest -> labeled -> kling -> video` 的小型生产线，用来快速生成和审阅智能售货机/智能冰箱前置摄像头视角下的顾客行为样本。

当前同步主项目的 v2.2 口径，但仍保持轻量仓库定位：

- policy 语义中心是 6 个 `DialogueAct`：`Greet / Elicit / Inform / Recommend / Reassure / Hold`。
- `T-state` 和旧 `A*` 动作只作为兼容标签保留。
- labeled JSON 同时包含旧字段 `candidate_actions / best_action` 和新字段 `candidate_action_specs / best_action_spec / action_key / schema_version / dialogue_act / act_params / realization`。
- `co_acts` 不再是 canonical 字段；新数据使用 `act_params.supporting_acts`，需要回溯旧格式时使用 `legacy_co_acts`。
- 每个 outcome 会补齐 `terminal_realization`，描述屏幕、语音、灯效、柜体动作和持续时间。
- 每个 outcome 同时保留旧 action label key，并新增 canonical `action_key`；如果多个旧动作映射到同一个 `(act, params)`，再用 `action_instance_key` 区分具体候选，避免覆盖 outcome。
- 这个仓库是 terminal/prototype 数据生产线，不替代主项目 `PIWM-Train-Synth-v1` 的真人导购训练集。

## Pipeline

```text
data/seed/piwm_NNN.txt
  -> script/gen_manifest.py     -> data/manifest/piwm_NNN.json
  -> script/gen_deliberation.py -> data/labeled/piwm_NNN.json
  -> script/gen_video.py        -> data/kling/piwm_NNN.md
  -> Kling API                  -> data/video/piwm_NNN.mp4
```

## Directory

```text
data/
  seed/       natural-language constraints
  manifest/   customer state and observable behavior
  labeled/    v2-compatible action/outcome labels
  kling/      rendered Kling prompts
  video/      generated videos
docs/
  action_space_v2.md
  schema.md
  pipeline.md
  usage.md
script/
  action_space_v2.py
  gen_manifest.py
  gen_deliberation.py
  gen_video.py
  upgrade_labeled_v2.py
  audit_action_space_v2.py
```

## Quick Start

```bash
pip install openai requests

python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_750
python script/gen_deliberation.py data/manifest/piwm_750.json
python script/gen_video.py data/labeled/piwm_750.json
```

Backfill existing labeled files to v2.2 fields:

```bash
python script/upgrade_labeled_v2.py
python script/audit_action_space_v2.py
```

Docs: [docs/action_space_v2.md](docs/action_space_v2.md) · [docs/schema.md](docs/schema.md) · [docs/pipeline.md](docs/pipeline.md) · [docs/usage.md](docs/usage.md)
