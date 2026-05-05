# Data Schema

## Manifest

`data/manifest/piwm_<id>.json`

```json
{
  "session_id": "piwm_700",
  "persona": "一名下班后路过便利区的年轻上班族",
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


| 字段                          | 类型     | 说明                                       |
| --------------------------- | ------ | ---------------------------------------- |
| `session_id`                | string | `piwm_<N>` 格式，N 从 700 起                  |
| `persona`                   | string | 一句话顾客画像（身份 + 情境）                         |
| `persona_visual`            | string | 外观视觉描述（年龄段、性别、发型、服装、随身物品），直接用于 Kling 生成  |
| `aida_stage`                | enum   | `attention / interest / desire / action` |
| `bdi`                       | object | belief / desire / intention 各一句话         |
| `observable_behavior`       | string | 镜头中可见的行为特征                               |
| `facial_expression`         | string | 表情状态                                     |
| `body_posture`              | string | 身体姿态                                     |
| `timeline.t_0_2` ~ `t_8_10` | string | 10 秒视频分段脚本，各一句                           |


---

## Labeled

`data/labeled/piwm_<id>.json`

包含 Manifest 全部字段，额外新增：

```json
{
  "candidate_actions": ["A0_silence", "A1_offer_recommendation", "A2_show_comparison", "A3_handoff"],
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
      "rationale": "顾客已下决心，沉默不干扰，reward 基线偏低但稳"
    },
    "A1_offer_recommendation": {
      "next_aida_stage": "action",
      "next_bdi": { "..." },
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.0,
      "delta_mental": 1.5,
      "action_cost": 0.4,
      "reward": 0.71,
      "rationale": "..."
    }
  },
  "best_action": "A1_offer_recommendation",
  "reward_weights": { "alpha": 0.4, "beta": 0.5, "gamma": 0.1 }
}
```


| 字段                            | 类型           | 说明                                      |
| ----------------------------- | ------------ | --------------------------------------- |
| `candidate_actions`           | list[string] | 4 个候选，第一个固定 `A0_silence`                |
| `outcomes`                    | dict         | key = action name，value = ActionOutcome |
| `outcomes[*].next_aida_stage` | enum         | 该动作后顾客预测进入的 AIDA 阶段                     |
| `outcomes[*].next_bdi`        | object       | 该动作后的 belief / desire / intention       |
| `outcomes[*].risk`            | enum         | `low / medium / high`，动作引发反感的概率         |
| `outcomes[*].benefit`         | enum         | `low / medium / high`，动作推进决策的程度         |
| `outcomes[*].delta_stage`     | float [-1,1] | AIDA 阶段变化量（推进一格 ≈ 0.33）                 |
| `outcomes[*].delta_mental`    | float [-3,3] | 心理状态综合变化量                               |
| `outcomes[*].action_cost`     | float [0,1]  | 介入成本（`A0_silence` 强制 0）                 |
| `outcomes[*].reward`          | float [-1,1] | `α·Δstage + β·Δmental − γ·cost`，脚本计算    |
| `outcomes[*].rationale`       | string       | 一句话解释                                   |
| `best_action`                 | string       | `argmax(reward)` 推出，与 outcomes 内部一致     |
| `reward_weights`              | object       | 生成该批数据时的 α/β/γ 值，方便复盘                   |


### Reward 公式

```
reward = α · Δstage + β · Δmental − γ · action_cost    clip to [-1, 1]

默认：α=0.4, β=0.5, γ=0.1
```

---

## Kling Prompt

`data/kling/piwm_<id>.md` — 纯文本，填充自 labeled JSON 的行为字段 + timeline，直接传 Kling API。