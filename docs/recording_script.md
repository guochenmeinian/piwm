# 真人测试集录制脚本建议

## 1. 目标

真人测试集建议用于评估两件事：

1. 模型能否从真实视频前 10 秒恢复出合理的 `state`。
2. 在给定候选动作后，模型选出的 `best_action` 是否与预设 ground truth 一致，并且该动作是否能引出预期的真实顾客反应。

这里的关键不是让演员“演一个标签”，而是让他们在一个自然的小情境中，先表现出指定的前置状态，再在收到设备动作后给出可观察的后续反应。

---

## 2. 推荐时间轴

每条视频建议 `25s` 左右，统一切成 4 段：

| 时间 | 内容 | 用途 |
|---|---|---|
| `t_0_10` | 顾客自然进入并表现前置状态 | state 识别输入 |
| `t_10_15` | 设备“处理中”，顾客继续自然等待 | 模拟模型推理延迟 |
| `t_15_20` | 设备执行预设 action | intervention |
| `t_20_25/30` | 顾客对 action 做出真实反应 | outcome ground truth |

建议：

- `t_0_10` 必须能单独成立，哪怕把后面剪掉，也能据此判断 AIDA + BDI。
- `t_10_15` 不要让演员突然静止，应该延续原有状态，只做轻微自然变化。
- `t_15_20` 由设备屏幕、语音或导演口令触发，但演员不要提前看脚本中的动作名。
- `t_20_25/30` 要出现清楚的可观察变化，例如继续浏览、靠近比较、点头后操作、放松等待、直接下单、准备离开等。

---

## 3. Ground Truth 设计

每条样本建议提前固定以下字段：

```json
{
  "sample_id": "real_001",
  "pre_state": {
    "aida_stage": "desire",
    "bdi": {
      "belief": "...",
      "desire": "...",
      "intention": "..."
    }
  },
  "candidate_actions": [
    "hold_silent",
    "reassure_decision",
    "reassure_time_wait",
    "recommend_soft"
  ],
  "best_action": "recommend_soft",
  "expected_post_reaction": {
    "next_aida_stage": "action",
    "observable_reaction": "顾客听到温和推荐后，目光重新锁定目标商品，轻微点头，随后伸手操作。",
    "next_bdi": {
      "belief": "...",
      "desire": "...",
      "intention": "..."
    }
  }
}
```

### 为什么要提前固定

- 这样每条视频都有明确评测标签，不会拍完后再倒推答案。
- 你可以控制 10 个 `best_action` 的覆盖率，避免测试集只集中在头部动作。
- 后续评测时可以同时看：
  - 前 10 秒 state 是否识别正确
  - 选出的 `best_action` 是否正确
  - 真实反应是否与预设 outcome 一致

---

## 4. 对演员的说明方式

不要直接把 `best_action` 或标签名告诉演员。建议拆成两张卡：

### A. 演员卡

只给：

- 你是谁
- 你现在想买什么 / 还没想清楚什么
- 你此刻在犹豫什么
- 前 10 秒应该自然表现出什么
- 听到设备之后，你“真实会怎么反应”

### B. 导演卡

额外给：

- `pre_state`
- `candidate_actions`
- `best_action`
- action 的设备表现形式
- 需要捕捉的 post-reaction

这样演员演的是“人”，导演控制的是“标签”。

---

## 5. 录制统一要求

### 机位

- 固定正面机位为主，尽量模拟设备前置摄像头。
- 顾客全程至少露出上半身、双手和主要视线方向。
- 背景保持一致，避免测试集里混入太多无关域差异。

### 表演

- 不要夸张，不要舞台化。
- 每段只做 2 到 4 个清楚动作，留足停顿。
- 不要一上来就把标签演得过满，例如 `action` 也应允许“将要操作但仍短暂停顿”。
- 同一个脚本可拍 2 到 3 位演员版本，保留自然差异。

### 设备 action

- 尽量真的给出屏幕/语音刺激，不要完全靠演员脑补。
- 如果暂时没有真机，可用：
  - 屏幕卡片
  - 旁白音频
  - 导演在 `t_15` 统一播报固定台词

### 文件组织

```text
real_test/
  scripts/
    real_001.json
  videos/
    real_001_actor01_take01.mp4
  annotations/
    real_001_actor01_take01.json
```

---

## 6. 建议样本配比

当前 10 个常见 `best_action` 建议至少各拍 `2` 条，形成一个 `20` 条左右的核心测试集：

| best_action | 建议条数 |
|---|---:|
| `elicit_need_focus_open` | 2 |
| `inform_comparison_brief` | 2 |
| `inform_demo_brief` | 2 |
| `inform_price_brief` | 2 |
| `inform_attributes_brief` | 2 |
| `recommend_soft` | 2 |
| `recommend_firm` | 2 |
| `reassure_time_wait` | 2 |
| `reassure_decision` | 2 |
| `greet_close` | 2 |

如果预算允许，再给长尾或容易混淆的动作各补 1 条：

- `recommend_soft` vs `recommend_firm`
- `reassure_time_wait` vs `reassure_decision`
- `inform_comparison_brief` vs `inform_attributes_brief`

这样总量会落在 `24-30` 条，比较适合作为第一版真人测试集。

---

## 7. 单条样本脚本模板

```markdown
# Sample ID
real_001

# Ground Truth
- pre_aida_stage: desire
- best_action: recommend_soft
- expected_next_aida_stage: action

# Actor Card
你是一名下班后的年轻上班族，已经偏向某一款饮品，但还想得到一个不强迫的确认。

## t_0_10
- 站在设备前，目光多次回到同一目标位置
- 偶尔扫一眼旁边选项，但很快回来
- 手部动作克制，不要直接操作

## t_10_15
- 继续保持原状态
- 可轻微摩挲手指或短暂停顿

## t_15_20
设备会给出一句温和推荐。

## t_20_25
- 听到后轻微点头
- 神情放松
- 随后伸手准备操作

# Director Card
- candidate_actions:
  - hold_silent
  - reassure_decision
  - reassure_time_wait
  - recommend_soft
- intervention:
  - surface_text: 如果您想省时间，可以先从这款开始看，它比较符合您现在关注的点。
- expected_post_reaction:
  - next_aida_stage: action
  - observable_reaction: 轻微点头，目光锁定目标，随后伸手操作
```

---

正式脚本样例不放在说明文档里，统一维护在 `data/real_scripts/` 下，便于后续直接扩成拍摄清单和标注文件。

---

## 8. 建议的标注产物

真人视频拍完后，每条样本建议至少保留三层标签：

1. `pre_state_gt`
   - 前 10 秒人工确认后的 AIDA + BDI
2. `best_action_gt`
   - 预设动作标签
3. `post_reaction_gt`
   - 动作后的真实可观察反应
   - 可再派生 `next_aida_stage / next_bdi`

这样你后面可以分别评测：

- 视觉 state 模型
- action 选择模型
- action 后 outcome 预测模型

而且三者不会混成一个很难解释的总分。
