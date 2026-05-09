# PIWM 数据设计

## 一、问题定义

智能零售设备（售货机/智能冰箱）内置摄像头持续观察顾客，但现有系统只被动等待操作输入。PIWM 训练一个 **Proactive Intent Agent**：从视觉信号推断顾客购买意图，决定设备应切换到哪个状态——或保持沉默。

两个核心难题：意图是内隐的（只有外显行为可观测）；干预效果没有直接可观测的结果标签。

解法：**全合成数据管线** — LLM 同时生成行为信号 + 意图标签 + 干预结果，视频生成模型将行为描述转为视频。

---

## 二、理论框架

**AIDA**（宏观购买阶段）和 **BDI**（微观认知结构）双层状态建模：

| AIDA | 顾客状态 | 典型可见行为 |
|---|---|---|
| Attention | 注意到设备，无明确兴趣 | 目光扫过，步伐放缓 |
| Interest | 主动观察，开始比较 | 停步，目光来回扫视，轻微前倾 |
| Desire | 有购买意愿，进入权衡 | 目光锁定，身体前倾，手部靠近 |
| Action | 决定购买，进入操作 | 手臂伸出，动作直接坚定 |

BDI = Belief（当前认知判断）/ Desire（想达成的目标）/ Intention（接下来的行为倾向）

**关系**：AIDA 是结果，BDI 是原因。推理时先走 BDI 因果链，再映射到 AIDA 迁移。干预动作改变的是 Belief（提供新信息）或 Desire（激活需求），进而影响 Intention，反映到 AIDA 变化。

---

## 三、设备动作空间（T-state）

设备可主动切换到 8 个状态（T0 为待机默认态，不参与决策）：

| T-state | 含义 | action_cost |
|---|---|---|
| **T1_SILENT_OBSERVE** | 静默观察，不打扰（**no-intervention 基线**） | 0.00 |
| T2_VALUE_COMPARE | 屏幕弹双卡对比（价格/规格/场景） | 0.30 |
| T3_STRONG_RECOMMEND | 单品全屏 + "立即购买" CTA | 0.65 |
| T4_OPEN_QUESTION | 三选一气泡题 + 数字人提问 | 0.20 |
| T5_DEMO | 关键功能 3D 演示（≤10s）+ 数字人解说 | 0.40 |
| T6_ACK_WAIT | 轻确认 + "您慢慢看"退至背景 | 0.10 |
| T7_DISENGAGE | 主动退出互动，回到 attract loop | 0.05 |
| T_TRANSACT | 收银/出货（顾客已决定） | 0.00 |

`action_cost` 固定，不由模型生成。`best_action = argmax(reward)`，若 T1 最高则不介入。

**Reward 函数**（clip to [-1, 1]）：

```
reward = α · Δstage + β · Δmental − γ · action_cost
默认：α=0.4, β=0.5, γ=0.1
```

- `Δstage`：AIDA 阶段推进量（推进一格 ≈ +0.33，倒退为负）
- `Δmental`：兴趣 + 信任 + 犹豫缓解的综合量（-3 ~ +3）
- `β > α`：顾客体验优先于即时转化

---

## 四、数据 Schema

训练用：`data/labeled/piwm_NNN.json`（新旧数据统一格式）

```json
{
  "session_id": "piwm_700",
  "persona": "双休日无聊出来逛逛街的普通消费者",
  "aida_stage": "interest",
  "bdi": {
    "belief": "售货机里可能有感兴趣的商品，但信息不够，没把握购买",
    "desire": "想进一步了解商品是否符合需求，确认再决定",
    "intention": "继续停留浏览，在做决定前保持谨慎"
  },
  "observable_behavior": "在机器前停留，身体轻微前倾，视线在前方多个位置之间切换",
  "facial_expression": "表情自然克制，带轻微思考和犹豫",
  "body_posture": "正面朝向机器，站姿稳定，双手自然放置",
  "candidate_actions": ["T1_SILENT_OBSERVE", "T2_VALUE_COMPARE", "T4_OPEN_QUESTION", "T5_DEMO"],
  "outcomes": {
    "T1_SILENT_OBSERVE": {
      "next_aida_stage": "interest",
      "next_bdi": {"belief": "缺乏新信息，仍不确定", "desire": "继续谨慎观察", "intention": "继续停留，若无法确认可能放弃"},
      "risk": "low", "benefit": "low",
      "delta_stage": 0.02, "delta_mental": -0.1, "action_cost": 0.00, "reward": -0.04,
      "rationale": "沉默不打扰但无法改善信息不足，顾客状态停滞"
    },
    "T2_VALUE_COMPARE": {
      "next_aida_stage": "desire",
      "next_bdi": {"belief": "能看到商品差异，选择成本降低", "desire": "想在对比卡中锁定候选", "intention": "围绕少数候选进行最后比较"},
      "risk": "low", "benefit": "high",
      "delta_stage": 0.33, "delta_mental": 1.5, "action_cost": 0.30, "reward": 0.84,
      "rationale": "比较卡降低决策负担，belief 从模糊变清晰，interest 推进为 desire"
    },
    "T4_OPEN_QUESTION": {
      "next_aida_stage": "interest",
      "next_bdi": {"belief": "可以告知偏好以获得定向建议", "desire": "想回答后得到更匹配的选项", "intention": "从被动浏览转为主动交互"},
      "risk": "low", "benefit": "medium",
      "delta_stage": 0.10, "delta_mental": 0.7, "action_cost": 0.20, "reward": 0.39,
      "rationale": "提问激活参与感，但无法直接给信息，转化效率低于比较卡"
    },
    "T5_DEMO": {
      "next_aida_stage": "desire",
      "next_bdi": {"belief": "对某款商品特性有直观认知", "desire": "想确认演示商品是否符合需求", "intention": "重点关注演示商品，考虑进一步操作"},
      "risk": "medium", "benefit": "high",
      "delta_stage": 0.25, "delta_mental": 1.2, "action_cost": 0.40, "reward": 0.70,
      "rationale": "演示增强具体商品吸引力，但若商品不契合需求可能反效果"
    }
  },
  "best_action": "T2_VALUE_COMPARE",
  "reward_weights": {"alpha": 0.4, "beta": 0.5, "gamma": 0.1}
}
```

视频生成专用字段（仅新数据，存于 `data/manifest/`，不进训练）：

```json
{
  "persona_visual": "一名 25–35 岁的普通亚洲女性，穿着简洁日常休闲服饰",
  "timeline": {
    "t_0_2": "顾客从前方走近，脚步逐渐放慢，在机器前停下",
    "t_2_5": "身体轻微前倾，目光稳定看向前方，随后短暂下移",
    "t_5_8": "目光在前方不同位置自然切换，节奏缓慢",
    "t_8_10": "继续停留，再次短暂下移视线，保持思考状态"
  }
}
```

---

## 五、数据生成管线（新数据）

单条样本内各步骤顺序依赖，跨样本可并行批处理：

```
data/seed/piwm_NNN.txt
  └─[依赖]─ gen_manifest.py  → data/manifest/piwm_NNN.json
                              ├─[依赖]─ gen_deliberation.py → data/labeled/piwm_NNN.json
                              └─[依赖]─ gen_video.py        → data/kling/piwm_NNN.md
                                                              └─ Kling API → data/video/piwm_NNN.mp4
```

gen_deliberation 和 gen_video 均依赖 manifest，两者之间无依赖，可在 Step 1 完成后并行执行。

### Seed 设计

Seed 是一段自然语言约束，注入 gen_manifest.py prompt 底部，控制样本分布而不固定具体内容（LLM 仍自由填充细节，避免样本重复）。

**Seed 格式**：`AIDA 阶段 × 犹豫度 × persona 类型 [+ 特殊约束]`

典型 seed 示例：

```
# data/seed/piwm_722.txt
interest 阶段，高犹豫，中年家庭主妇，对价格敏感，反复确认后仍拿不定主意

# data/seed/piwm_723.txt
desire 阶段，低犹豫，年轻上班族下班路过，已经有目标商品，正在最后确认

# data/seed/piwm_724.txt
attention 阶段，路过时被吸引，大学生，背着书包，停留时间短

# data/seed/piwm_725.txt
action 阶段，中年男性出差途中，决策快，直接准备操作购买
```

**批量生成时的目标分布**（通过 seed 控制）：

| | attention | interest | desire | action |
|---|---|---|---|---|
| 低犹豫 | 5 | 10 | 15 | 15 |
| 中犹豫 | 5 | 20 | 20 | 5 |
| 高犹豫 | 5 | 20 | 10 | 5 |
| 小计 | 15 | 50 | 45 | 25 |

共 135 条，实际按需调整，保证各阶段和犹豫度有足够覆盖。

---

## 六、三个训练任务

`export_to_jsonl.py` 从 `data/labeled/` 导出，新旧数据统一格式：

### Task 1 — State Inference（感知）
视频 → 顾客状态。每条 labeled JSON 产生 **1 条**。

```jsonl
{"id": "piwm_700_si", "task": "state_inference",
 "video_path": "data/video/piwm_700.mp4",
 "persona": "双休日无聊出来逛逛街的普通消费者",
 "target": {"aida_stage": "interest", "bdi": {"belief": "...", "desire": "...", "intention": "..."},
            "observable_behavior": "...", "facial_expression": "...", "body_posture": "..."}}
```

### Task 2 — World Model（预测）
当前状态 + 机器动作 → 下一状态。每条 labeled JSON 产生 **N 条**（N = `candidate_actions` 的数量，当前设计为 4）。

```jsonl
{"id": "piwm_700_wm_T2", "task": "world_model",
 "input": {"aida_stage": "interest", "bdi": {"belief": "...", "desire": "...", "intention": "..."},
           "machine_state": "T2_VALUE_COMPARE"},
 "target": {"next_aida_stage": "desire", "next_bdi": {"belief": "...", "desire": "...", "intention": "..."},
            "reward": 0.84, "rationale": "..."}}
```

### Task 3 — Policy（决策）
当前状态 → 最优机器动作。每条 labeled JSON 产生 **1 条**。

```jsonl
{"id": "piwm_700_policy", "task": "policy",
 "input": {"aida_stage": "interest", "bdi": {"belief": "...", "desire": "...", "intention": "..."},
           "observable_behavior": "...",
           "candidate_actions": ["T1_SILENT_OBSERVE", "T2_VALUE_COMPARE", "T4_OPEN_QUESTION", "T5_DEMO"]},
 "target": {"best_action": "T2_VALUE_COMPARE", "rationale": "..."}}
```

### Task 4 — DPO（偏好，待做）
每条 labeled JSON 最多产生 **N-1 对**（best_action vs 其余每个）。

```jsonl
{"id": "piwm_700_dpo_T2vsT1", "task": "dpo",
 "context": {"aida_stage": "interest", "bdi": {"belief": "...", "desire": "...", "intention": "..."}},
 "chosen":  {"machine_state": "T2_VALUE_COMPARE", "reward": 0.84},
 "rejected": {"machine_state": "T1_SILENT_OBSERVE", "reward": -0.04}}
```

---

## 七、数据规模与划分

**总视频数**：旧数据 ~250 条 + 新生成 ~150 条 = **~400 条**

每条视频导出：Task 1 × 1 + Task 2 × 4 + Task 3 × 1 = **6 条训练记录**，共 **~2400 条**（不含 DPO）

**数据划分**：

| 用途 | 视频数 | 训练记录数 |
|---|---|---|
| SFT 训练 | ~300（旧 200 + 新 100） | ~1800 |
| 评测（hold-out） | ~60 | ~360（仅用于评测，不训练） |
| DPO / 待定 | ~40 | 按需从 labeled JSON 直接生成 DPO 对，无需额外视频 |

**视角说明**：旧数据和新数据 schema 完全一致，训练时不区分视角，统一为零售场景。

**旧数据迁移**：GPT-4V 描述已有视频 → 生成 AIDA/BDI/observable fields → 跑 gen_deliberation.py → 输出统一格式 labeled JSON。

---

## 八、评测

**数据划分**：~60 条 hold-out 测试集，按 AIDA 阶段均匀抽取（各 ~15 条），不参与训练。

**三个任务的评测指标**：

| 任务 | 指标 | baseline |
|---|---|---|
| State Inference | AIDA top-1 accuracy | 随机猜 25% |
| World Model | reward MAE + next_aida_stage accuracy | — |
| Policy | best_action top-1 accuracy | 始终选 T1（永不介入） |

**端到端对比**：policy baseline = 始终 T1_SILENT_OBSERVE。比较模型策略与 baseline 在测试集上的平均 reward，量化主动介入的实际收益。

**Proactive rate**：测试集上 best_action ≠ T1 的比例，应与训练集分布吻合（~85% 情况下应介入）。

**局限性**：测试标签由专家模型（GPT）生成，与训练标签同源，度量的是对专家模型的拟合程度，非真实部署效果。真实效果需 A/B 实验验证。

---

## 九、待讨论

1. **候选数量**：当前固定 4 个（AIDA 查表），可选方案是将全部 8 个 T-state 都给专家模型（更 BDI-aware，但 N=8 → 总记录 400×10=4000，API 成本翻倍）
2. **DPO 时机**：SFT 之后，用现有 labeled JSON 直接生成 DPO 对即可（best vs worst），不需要额外生成数据
