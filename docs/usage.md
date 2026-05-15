# Usage

数据流：`seed -> manifest -> labeled -> kling -> video`

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

生成 v2.2-compatible labeled JSON。输出保留 `candidate_actions / best_action / outcomes`，同时新增 `candidate_action_specs / best_action_spec / action_key / action_instance_key / outcomes_by_action_key / outcomes_by_action_instance_key / schema_version / dialogue_act / act_params / realization`。辅助动作写入 `act_params.supporting_acts`，旧格式回溯字段为 `legacy_co_acts`。

```bash
python script/gen_deliberation.py
python script/gen_deliberation.py --dry-run
python script/gen_deliberation.py data/manifest/piwm_700.json
python script/gen_deliberation.py data/manifest/piwm_700.json --dry-run
python script/gen_deliberation.py data/manifest/piwm_700.json \
  --alpha 0.5 --beta 0.4 --gamma 0.2 \
  -o data/labeled/custom.json
```

## upgrade_labeled_v2.py

给已有 labeled JSON 回填 v2.2 字段。不会改 manifest/kling/video。

```bash
python script/upgrade_labeled_v2.py --dry-run
python script/upgrade_labeled_v2.py
python script/upgrade_labeled_v2.py data/labeled/piwm_700.json
```

## audit_action_space_v2.py

检查 labeled JSON 是否仍有旧顶层 `co_acts` 或 schema 版本不一致。

```bash
python script/audit_action_space_v2.py
```

## gen_video.py

填充 Kling prompt，可选调用 Kling API。

```bash
python script/gen_video.py
python script/gen_video.py --dry-run
python script/gen_video.py data/labeled/piwm_700.json
python script/gen_video.py data/manifest/piwm_700.json
KLING_API_KEY=... python script/gen_video.py data/labeled/piwm_700.json --call-kling
```

## Common Flow

```bash
python script/gen_manifest.py "desire 阶段，中等犹豫" --id piwm_750
python script/gen_deliberation.py data/manifest/piwm_750.json
python script/gen_video.py data/labeled/piwm_750.json
```

## Validation

```bash
python3 -m py_compile script/action_space_v2.py script/gen_manifest.py script/gen_deliberation.py script/gen_video.py script/upgrade_labeled_v2.py
python script/upgrade_labeled_v2.py --dry-run
python script/audit_action_space_v2.py
```

`upgrade_labeled_v2.py --dry-run` 返回 `0 file(s) would change` 时，说明已有 labeled JSON 已补齐 v2 字段。
