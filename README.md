# Proactive Intent World Model (PIWM)

PIWM 数据生成仓库，用来生成零售设备前置摄像头视角下的顾客状态、动作偏好标注和交互前视频样本。

当前数据包含两条主线：

- `seed -> manifest -> prompt -> video`
- `seed -> manifest -> labeled`

当前 `piwm_700` 到 `piwm_817` 共 118 条，`seed / manifest / labeled / prompts / video` 已一一对应。

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
python script/gen_deliberation.py data/manifest/piwm_750.json
python script/gen_video.py data/prompts/piwm_750.md
```

Kling 相关环境变量：

```bash
export KLING_ACCESS_KEY=...
export KLING_SECRET_KEY=...
export KLING_BASE_URL=https://api-beijing.klingai.com
```

Docs: [docs/index.md](docs/index.md) · [docs/schema.md](docs/schema.md) · [docs/pipeline.md](docs/pipeline.md) · [docs/usage.md](docs/usage.md)