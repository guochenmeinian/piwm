# Usage

数据流：`seed -> manifest -> labeled -> prompts -> video`

## Environment

```bash
pip install openai requests
```

`python-dotenv` 是可选依赖；如果没有安装，脚本仍可 dry-run。需要真实调用 OpenAI 时设置环境变量：

```bash
export OPENAI_API_KEY=...
```

需要调用 Kling 时设置：

```bash
export KLING_API_KEY=...
```

## gen_manifest.py

生成 Perception 标注。

```bash
python script/gen_manifest.py
python script/gen_manifest.py --dry-run
python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_750
python script/gen_manifest.py "interest 阶段，高犹豫，价格敏感" --id piwm_750 --dry-run
python script/gen_manifest.py "..." -o -
```

## gen_deliberation.py

生成 labeled JSON。输出保留 `best_action`，同时补齐 `response_id / dialogue_act / act_params / co_acts / realization`。

```bash
python script/gen_deliberation.py
python script/gen_deliberation.py --dry-run
python script/gen_deliberation.py data/manifest/piwm_700.json
python script/gen_deliberation.py data/manifest/piwm_700.json --dry-run
python script/gen_deliberation.py data/manifest/piwm_700.json \
  --alpha 0.5 --beta 0.4 --gamma 0.2 \
  -o data/labeled/custom.json
```

## upgrade_labeled.py

统一刷新 labeled JSON 的 action 索引与 realization 字段。不会改 manifest/prompts/video。

```bash
python script/upgrade_labeled.py --dry-run
python script/upgrade_labeled.py
python script/upgrade_labeled.py data/labeled/piwm_700.json
```

## gen_prompt.py

填充交互前 10 秒视频 prompt。

```bash
python script/gen_prompt.py
python script/gen_prompt.py --dry-run
python script/gen_prompt.py --overwrite
python script/gen_prompt.py data/labeled/piwm_700.json
python script/gen_prompt.py data/manifest/piwm_700.json
```

## gen_video.py

读取已渲染 prompt，调用 Kling API 生成视频。

```bash
python script/gen_video.py --dry-run
KLING_API_KEY=... python script/gen_video.py
KLING_API_KEY=... python script/gen_video.py data/prompts/piwm_700.md
```

## Common Flow

```bash
python script/gen_manifest.py "desire 阶段，中等犹豫" --id piwm_750
python script/gen_deliberation.py data/manifest/piwm_750.json
python script/gen_prompt.py data/labeled/piwm_750.json
KLING_API_KEY=... python script/gen_video.py data/prompts/piwm_750.md
```

## Validation

```bash
python3 -m py_compile script/action_space.py script/gen_manifest.py script/gen_deliberation.py script/gen_prompt.py script/gen_video.py script/upgrade_labeled.py
python script/upgrade_labeled.py --dry-run
```

`upgrade_labeled.py --dry-run` 返回 `0 file(s) would change` 时，说明已有 labeled JSON 已归一。
