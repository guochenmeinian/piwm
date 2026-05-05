# PIWM 设计理念

## 一、问题定义

智能售货机和智能冰箱的前置摄像头能持续拍摄顾客，但现有系统只被动等待操作输入。PIWM 的目标是训练一个 **主动意图感知代理（Proactive Intent Agent）**：在顾客还没有做出明确动作之前，通过观察其行为信号推断购买意图，并在合适的时机主动介入——或选择沉默。

核心难题有两个：

1. **感知难**：顾客的意图是内隐的，摄像头只能看到面部、姿态、目光方向等外显信号，需要从这些信号中推断其心理状态。
2. **数据难**：真实视频中无法直接获取意图标签，人工标注代价高且涉及隐私；更难的是，干预动作的"好不好"没有直接可观测的结果标签。

PIWM 通过 **全合成数据管线** 绕过这两个问题：用 LLM 同时生成行为信号和意图标签，用专家模型模拟推理结果，再用视频生成模型将行为描述转化为视频。

---

## 二、理论框架

### 2.1 AIDA 购买阶段

AIDA（Attention → Interest → Desire → Action）是营销学中对消费者决策过程的经典分层描述。PIWM 将其作为 **宏观状态空间**：

| 阶段 | 顾客状态 | 典型行为 |
|------|----------|----------|
| Attention | 注意到设备，尚无明确兴趣 | 目光扫过，步伐放缓 |
| Interest | 产生兴趣，主动观察 | 停下脚步，目光来回扫视 |
| Desire | 有购买意愿，进入权衡 | 目光锁定，身体前倾，手部动作 |
| Action | 决定购买，进入操作 | 手臂伸出，动作直接坚定 |

AIDA 阶段是粗粒度的、可解释的，适合用来衡量干预的宏观效果（`delta_stage`）。

### 2.2 BDI 认知建模

BDI（Belief / Desire / Intention）来自 AI 规划领域的 Agent 理论，描述行为背后的认知结构：

- **Belief**：顾客对当前情境的判断（"这台机器里可能有我想要的"）
- **Desire**：顾客想达成的目标（"找到一款解渴的饮品"）
- **Intention**：顾客接下来倾向采取的行动（"再看几秒，没有合适的就离开"）

BDI 是比 AIDA 更细粒度的微观状态，捕捉行为背后的 **因果结构**。干预动作改变的是 Belief（提供新信息）或 Desire（激活新需求），进而影响 Intention，最终反映到 AIDA 阶段的变化。

两层状态的关系：**AIDA 是结果，BDI 是原因**。推理时先走 BDI 因果链，再映射到 AIDA 迁移，保证标签的语义一致性。

---

## 三、数据管线设计

```
Seed (自然语言约束)
  │
  ▼
Manifest (感知层标签)      ← gen_manifest.py   →  data/manifest/
  │  persona, persona_visual
  │  aida_stage, bdi
  │  observable_behavior, facial_expression, body_posture
  │  timeline (10s 脚本)
  │
  ▼
Labeled (推理层标签)       ← gen_deliberation.py →  data/labeled/
  │  candidate_actions × 4
  │  outcomes: next_bdi, delta_stage, delta_mental, action_cost, reward
  │  best_action
  │
  ▼
Kling Prompt (视频脚本)    ← gen_video.py       →  data/kling/
  │  Character + State + Behavior + Timeline
  │
  ▼
Video                      ← Kling API          →  data/video/
```

### 3.1 Seed 控制分布

直接让 LLM 自由生成样本会产生分布偏斜（LLM 偏好生成"有趣"的场景）。Seed 是一段自然语言约束，注入到 Manifest 生成提示词的底部，将生成结果限定在目标（AIDA 阶段 × 犹豫程度 × 人物类型）的格子里。

这是 **软约束**：Seed 不改变 JSON 结构，只引导字段的语义取值方向，LLM 仍有空间填充具体细节，避免样本之间过度重复。

### 3.2 感知层与视觉层分离

Manifest 包含两类人物描述：
- `persona`：叙事性画像，说明顾客的身份和情境，驱动 BDI 和行为的合理性
- `persona_visual`：外观视觉描述（年龄、性别、发型、服装、随身物品），直接注入 Kling 提示词

分离的原因：Kling 等视频生成模型需要具体的外观描述才能在多次生成中保持角色一致；而叙事性 persona 是行为逻辑的锚点，不适合直接作为视觉指令。

---

## 四、推理层设计（Deliberation）

### 4.1 候选动作空间

每条样本有 4 个候选动作：

- **A0_silence**：系统不介入，强制 `action_cost = 0`，作为基线
- **A1–A3**：由专家模型根据当前 AIDA × BDI 状态自主命名，覆盖不同策略方向（信息补充 / 比较引导 / 行动催化 / 降低风险 / 转交人工等）

A0_silence 的引入是设计上的关键决策：它迫使模型在选择干预时必须超过"不干预"的基准 reward，从而避免过度激进的干预策略。

### 4.2 Reward 函数

```
reward = α · Δstage + β · Δmental − γ · action_cost    clip to [−1, 1]

默认：α = 0.4,  β = 0.5,  γ = 0.1
```

三个分量的设计意图：

| 分量 | 含义 | 权重设定理由 |
|------|------|-------------|
| `α · Δstage` | AIDA 阶段推进量 | 购买转化是最终目标，但不应是唯一目标 |
| `β · Δmental` | 心理状态综合改善量（兴趣↑、犹豫↓、信任↑） | 权重最高，避免以负面体验换取短期转化 |
| `−γ · action_cost` | 干预的打扰成本 | 权重最低，作为轻惩罚抑制不必要的主动介入 |

`β > α` 的设计选择体现了一个核心理念：**顾客体验优先于即时转化**。一个让顾客反感但完成了购买的干预（高 Δstage、低 Δmental）应该得到比一个改善了顾客体验但未直接推进转化的干预更低的 reward。

### 4.3 BDI 一致性验证

专家模型生成的标签需经过规则验证，不通过时以多轮对话方式要求修正（最多 2 次重试）。验证规则：

- `delta_stage` 方向必须与 `next_aida_stage` 的迁移方向一致
- `risk = high` 时 `delta_mental` 不应为正
- `next_aida_stage = action` 时 `intention` 不应含犹豫语义
- A0_silence 的 `delta_stage` 幅度不超过 ±0.4
- 4 个候选的 reward 差距不小于 0.25（保证区分度）

这一步是数据质量的关键门控，确保标签内部的因果逻辑自洽，而不只是形式上符合 JSON 结构。

---

## 五、设计取舍

| 决策 | 选择 | 放弃的方案 | 原因 |
|------|------|-----------|------|
| 状态表示 | AIDA + BDI 双层 | 单一连续向量 | 可解释性更强，适合小数据规模 |
| 数据来源 | 全合成 | 真实视频标注 | 隐私、成本、标签获取难度 |
| 候选动作数量 | 固定 4 个 | 动态数量 | 训练时 action space 一致，便于对比学习 |
| 干预基线 | A0_silence 强制 cost=0 | 无基线 | 防止模型学到"总是干预"的捷径 |
| 人物描述分离 | persona + persona_visual | 单一 persona | Kling 视觉一致性要求具体外观描述 |
| 样本分布控制 | Seed 软约束 | 纯随机生成 | 避免 LLM 分布偏斜，保证阶段覆盖均衡 |
