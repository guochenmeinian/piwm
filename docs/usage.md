# Usage

数据流：`seed → manifest → labeled → kling → video`

---

## gen_manifest.py

生成 Perception 标注（persona + persona_visual + AIDA + BDI + 外显行为 + timeline）。

**批量模式**（无参数）：扫描 `data/seed/`，对没有对应 manifest 的 seed 文件逐一生成。

```bash
python script/gen_manifest.py                                      # 批量：seed/ → manifest/
python script/gen_manifest.py --dry-run                           # 批量：列出待处理 seed
python script/gen_manifest.py "action 阶段，不犹豫，正在伸手"      # 单条：自然语言约束
python script/gen_manifest.py "..." --id piwm_750                 # 单条：指定 ID
python script/gen_manifest.py "..." --dry-run                     # 单条：预览 prompt
python script/gen_manifest.py "..." -o -                          # 单条：输出到 stdout
```

---

## gen_deliberation.py

Expert model：推理每个候选动作的 BDI 因果链 → 预测 ActionOutcome → 计算 reward → 选 best_action。

BDI 一致性校验失败时自动 retry（最多 2 次）。

**批量模式**（无参数）：对 `data/manifest/` 中没有对应 labeled 文件的 manifest 逐一处理。

```bash
python script/gen_deliberation.py                                  # 批量：manifest/ → labeled/
python script/gen_deliberation.py --dry-run                       # 批量：列出待处理文件
python script/gen_deliberation.py data/manifest/piwm_700.json    # 单条
python script/gen_deliberation.py data/manifest/piwm_700.json \
  --alpha 0.5 --beta 0.4 --gamma 0.2 -o data/labeled/custom.json
```

reward = α·Δstage + β·Δmental − γ·cost，clip [-1,1]，默认 α=0.4 β=0.5 γ=0.1

---

## gen_video.py

填充 Kling prompt 模板（`data/kling/`），可选调 Kling API 生成 mp4。

**批量模式**（无参数）：对 `data/manifest/` 中没有对应 kling 文件的条目逐一处理，优先使用 labeled 版本。

```bash
python script/gen_video.py                                         # 批量：manifest/ → kling/
python script/gen_video.py --dry-run                              # 批量：列出待处理文件
python script/gen_video.py data/labeled/piwm_700.json            # 单条（用 labeled）
python script/gen_video.py data/manifest/piwm_700.json           # 单条（用 manifest）
KLING_API_KEY=... python script/gen_video.py data/labeled/piwm_700.json --call-kling
```

---

## 常见用法

```bash
# 单条完整跑
python script/gen_manifest.py "desire 阶段，中等犹豫" --id piwm_750
python script/gen_deliberation.py data/manifest/piwm_750.json
python script/gen_video.py data/labeled/piwm_750.json --call-kling

# 管道串（单条）
python script/gen_manifest.py "..." -o - \
  | python script/gen_deliberation.py - -o - \
  | python script/gen_video.py -

# 全量批量（三步）
python script/gen_manifest.py
python script/gen_deliberation.py
python script/gen_video.py
```
