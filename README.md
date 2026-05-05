# Proactive Intent World Model (PIWM)

智能售货机 前置摄像头视角下的顾客行为数据合成 pipeline，用于训练零售场景多模态主动代理。

## 架构

```
Perception   →  从视频帧推断 AIDA 阶段 + BDI（训练数据由 gen_manifest 合成）
Deliberation →  对每个候选动作预测 next BDI + reward（gen_deliberation 合成标注）
Action       →  argmax(reward) 选 best_action，含 A0_silence 沉默基线
```

## 目录

```
data/       manifest/  labeled/  prompt/  video/
docs/       usage.md  schema.md  pipeline.md  draft/
script/     gen_manifest.py  gen_deliberation.py  gen_video.py
```

## Quick Start

```bash
pip install openai python-dotenv requests
# .env 里写 OPENAI_API_KEY=sk-...  KLING_API_KEY=...

python script/gen_manifest.py "action 阶段，不犹豫，正在伸手购买"
python script/gen_deliberation.py data/manifest/piwm_700.json
python script/gen_video.py data/labeled/piwm_700.json
```

→ [docs/usage.md](docs/usage.md) · [docs/schema.md](docs/schema.md) · [docs/pipeline.md](docs/pipeline.md)