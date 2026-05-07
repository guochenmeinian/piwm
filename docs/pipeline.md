# Pipeline

```
data/seed/piwm_NNN.txt
  └─ gen_manifest.py  →  data/manifest/piwm_NNN.json
       └─ gen_deliberation.py  →  data/labeled/piwm_NNN.json
            └─ gen_video.py  →  data/kling/piwm_NNN.md
                 └─ Kling API  →  data/video/piwm_NNN.mp4
```

---

## Step 1 — Manifest（Perception 标注）

`gen_manifest.py` 调用 GPT，按人物层 → 认知层 → 外显层 → 时间线层的顺序生成结构化样本。

### Schema

```json
{
  "session_id": "piwm_700",
  "persona": "下班路过便利区的年轻上班族",
  "persona_visual": "25 岁左右的女性，扎马尾，穿深蓝色西装外套和白衬衫，单肩背一个黑色小包",
  "aida_stage": "action",
  "bdi": {
    "belief": "眼前设备有自己想要的饮品",
    "desire": "尽快买到一瓶能马上喝的饮料",
    "intention": "短暂确认后直接完成购买"
  },
  "observable_behavior": "目光集中，扫视范围小，一手抬起靠近操作区",
  "facial_expression": "表情平静明确，已做出决定",
  "body_posture": "身体正面朝向镜头，微微前倾，肩膀放松",
  "timeline": {
    "t_0_2": "顾客走近停在画面中央，目光落向前方偏下",
    "t_2_5": "短暂扫视后目光固定，头部轻微点一下",
    "t_5_8": "身体前倾，一手从身侧抬起，动作干净直接",
    "t_8_10": "手继续向前准备操作，表情自然坚定"
  }
}
```

### 生成 Prompt

```
你是一个有 10 年产业经验的数据合成专家，熟悉零售行为、消费者心理、AIDA 购买阶段、BDI 建模，以及面向视频生成的数据设计。

# 生成流程
1. 人物层：persona（一句话画像）+ persona_visual（外观描述：年龄段、性别、发型、服装、随身物品）
2. 认知层：aida_stage + bdi（belief / desire / intention）
3. 外显层：observable_behavior + facial_expression + body_posture
4. 时间线层：timeline（t_0_2 / t_2_5 / t_5_8 / t_8_10，各一句）

# 场景约束（默认成立，无需在字段中重复）
- 10 秒，单镜头，固定机位，写实自然
- 智能售货机正面上方前置摄像头，轻微俯视
- 顾客始终正面朝向镜头，面部无遮挡，双手在画面内
- 不出现机器本体、商品、货架、价格标签、屏幕 UI
- 无人互动，无对白，无夸张表情或动作

# 输出
只输出 JSON，不要解释、注释、Markdown 或任务复述

当前的session_id是{session_id}
[如有 seed 约束附加在此处]
```

---

## Step 2 — Labeled（Deliberation 标注）

`gen_deliberation.py` 调用专家模型，对 4 个候选动作逐一推理 BDI 因果链 → 预测 ActionOutcome → 计算 reward → 选 best_action。BDI 一致性校验失败时自动 retry（最多 2 次）。

### 新增字段（在 Manifest 基础上追加）

```json
{
  "candidate_actions": ["A0_silence", "A1_xxx", "A2_xxx", "A3_xxx"],
  "outcomes": {
    "A0_silence": {
      "next_aida_stage": "action",
      "next_bdi": { "belief": "...", "desire": "...", "intention": "..." },
      "risk": "low",
      "benefit": "low",
      "delta_stage": 0.0,
      "delta_mental": 0.1,
      "action_cost": 0.0,
      "reward": 0.05,
      "rationale": "顾客已下决心，沉默不干扰"
    },
    "A1_xxx": { "...": "..." }
  },
  "best_action": "A1_xxx",
  "reward_weights": { "alpha": 0.4, "beta": 0.5, "gamma": 0.1 }
}
```

reward = α·Δstage + β·Δmental − γ·action_cost，clip [-1, 1]

---

## Step 3 — Kling Prompt（视频脚本）

`gen_video.py` 将 labeled JSON 填入模板，输出 `data/kling/piwm_NNN.md`，直接传 Kling API。

### 模板结构

```
# Task
生成一段 10 秒、单镜头、固定机位、写实自然风格的视频，模拟智能售货机前置摄像头记录到的顾客行为片段。

# Camera
镜头来自智能售货机正面上方的前置摄像头。第一人称视角，轻微俯视，固定机位，不晃动，不变焦。摄像头朝外拍摄顾客，视野完全不受遮挡。画面中清晰可见顾客的面部、目光方向、细微表情、上半身和双手。顾客始终位于画面中央附近，正面朝向镜头，面部无遮挡，双手始终在画面内。你能不受视野遮挡地看到顾客周身，画面中**禁止出现**机器本体、商品、货架、价格标签或任何商品。

# Character
{persona_visual}
背景：{persona}

# State
- 购买阶段：{aida_stage}
- Belief：{belief}
- Desire：{desire}
- Intention：{intention}

# Behavior
- 可见行为：{observable_behavior}
- 表情：{facial_expression}
- 姿态：{body_posture}

# Timeline
- 0–2 秒：{t_0_2}
- 2–5 秒：{t_2_5}
- 5–8 秒：{t_5_8}
- 8–10 秒：{t_8_10}

# Constraints
- 顾客外观必须与 Character 描述完全一致，全程不变
- 禁止出现：售货机本体、机器边框、商品、货架
- 无夸张表情、无夸张动作、无表演感，无其他人介入交互
- 整体效果像真实零售设备前置摄像头记录到的顾客浏览片段
```
