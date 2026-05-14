# Proactive Intent World Model (PIWM)

轻量版 PIWM 数据合成仓库。它保留一条交互前视频生成线和一条 action deliberation 标注线，用来快速生成和审阅智能售货机/智能冰箱前置摄像头视角下的顾客行为样本。

当前动作与数据口径：

- policy 语义中心是 6 个 `DialogueAct`：`Greet / Elicit / Inform / Recommend / Reassure / Hold`。
- `response_id` 作为稳定动作键；语义中心仍是 `dialogue_act / act_params / co_acts`。
- labeled JSON 使用 `candidate_actions / best_action / outcomes`，并在 outcome 与顶层补齐 action 语义字段。
- 每个 outcome 会补齐 `terminal_realization`，描述屏幕、语音、灯效、柜体动作和持续时间。

## Pipeline

```text
data/seed/piwm_NNN.txt
  -> script/gen_manifest.py     -> data/manifest/piwm_NNN.json
  -> script/gen_prompt.py       -> data/prompts/piwm_NNN.md
  -> script/gen_video.py        -> data/video/piwm_NNN.mp4

data/manifest/piwm_NNN.json
  -> script/gen_deliberation.py -> data/labeled/piwm_NNN.json
```

## Directory

```text
data/
  seed/       natural-language constraints
  manifest/   customer state and observable behavior
  labeled/    action/outcome labels
  prompts/    rendered pre-interaction video prompts
  video/      generated videos
docs/
  action_space.md
  schema.md
  pipeline.md
  usage.md
script/
  action_space.py
  gen_manifest.py
  gen_deliberation.py
  gen_prompt.py
  gen_video.py
  upgrade_labeled.py
```

## Quick Start

```bash
pip install openai requests

python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_750
python script/gen_prompt.py data/manifest/piwm_750.json
KLING_API_KEY=... python script/gen_video.py data/prompts/piwm_750.md
python script/gen_deliberation.py data/manifest/piwm_750.json
```

Normalize labeled files to the current action format:

```bash
python script/upgrade_labeled.py
```

Docs: [docs/action_space.md](docs/action_space.md) · [docs/schema.md](docs/schema.md) · [docs/pipeline.md](docs/pipeline.md) · [docs/usage.md](docs/usage.md)
