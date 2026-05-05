# Usage

数据流：`gen_manifest` → `gen_deliberation` → `gen_video`（后两步无强制先后）

---

## gen_manifest.py

生成 Perception 标注（persona + AIDA + BDI + 外显行为 + 10 秒 timeline）。

```bash
python script/gen_manifest.py [note] [--id ID] [--dry-run] [-o PATH]
```

```bash
python script/gen_manifest.py                                    # 自动编号 piwm_700+
python script/gen_manifest.py "action 阶段，不犹豫，正在伸手"    # 自然语言约束
python script/gen_manifest.py "..." --id piwm_750               # 指定 ID
python script/gen_manifest.py "..." --dry-run                   # 预览 prompt，不调 API
python script/gen_manifest.py "..." -o -                        # stdout（管道用）
```

---

## gen_deliberation.py

Expert model：推理每个候选动作的 BDI 因果链 → 预测 ActionOutcome → 计算 reward → 选 best_action。

BDI 一致性校验失败时自动 retry（最多 2 次）。

```bash
python script/gen_deliberation.py <manifest> [--alpha A] [--beta B] [--gamma G]
                                  [--action-space PATH] [--no-merge] [--dry-run] [-o PATH]
```

```bash
python script/gen_deliberation.py data/manifest/piwm_700.json
python script/gen_deliberation.py data/manifest/piwm_700.json --dry-run
python script/gen_deliberation.py data/manifest/piwm_700.json \
  --alpha 0.5 --beta 0.4 --gamma 0.2 -o data/labeled/piwm_700_abl.json
```

reward = α·Δstage + β·Δmental − γ·cost，clip [-1,1]，默认 α=0.4 β=0.5 γ=0.1

---

## gen_video.py

填充 Kling prompt 模板，可选调 Kling API 生成 mp4。

```bash
python script/gen_video.py <manifest> [--call-kling] [--kling-model MODEL] [-o PATH]
```

```bash
python script/gen_video.py data/labeled/piwm_700.json
KLING_API_KEY=... python script/gen_video.py data/labeled/piwm_700.json --call-kling
```

---

## 常见用法

```bash
# 单条完整跑
python script/gen_manifest.py "desire 阶段，中等犹豫"
python script/gen_deliberation.py data/manifest/piwm_700.json
python script/gen_video.py data/labeled/piwm_700.json --call-kling

# 管道串
python script/gen_manifest.py "..." -o - | python script/gen_deliberation.py - -o - | python script/gen_video.py -

# 批量生成 manifest
for i in $(seq 1 20); do
  python script/gen_manifest.py "action 阶段，不犹豫"
done

# 批量 deliberation
for f in data/manifest/piwm_*.json; do python script/gen_deliberation.py "$f"; done
```
