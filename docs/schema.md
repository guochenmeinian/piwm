# Data Schema

当前 schema 使用统一 action 格式：`candidate_actions / best_action` 直接使用 `response_id` 作为动作键。

## Manifest

`data/manifest/piwm_<id>.json`

Manifest 只描述当前顾客状态和 10 秒视频脚本，不写动作决策。

```json
{
  "session_id": "piwm_700",
  "persona": "一名下班后路过便利区的年轻上班族",
  "persona_visual": "25 岁左右的女性，扎马尾，穿深蓝色西装外套和白衬衫，单肩背一个黑色小包",
  "aida_stage": "interest",
  "bdi": {
    "belief": "设备里可能有合适商品，但还需要比较信息",
    "desire": "想确认哪一款最符合当前需求",
    "intention": "继续停留浏览，在决定前保持谨慎"
  },
  "observable_behavior": "目光在多个位置之间切换，身体轻微前倾",
  "facial_expression": "表情自然克制，带轻微思考",
  "body_posture": "正面朝向镜头，站姿稳定，双手在画面内",
  "timeline": {
    "t_0_2": "顾客走近并停下",
    "t_2_5": "目光稳定看向前方并短暂下移",
    "t_5_8": "视线在不同位置自然切换",
    "t_8_10": "继续停留，保持思考状态"
  }
}
```

## Labeled

`data/labeled/piwm_<id>.json`

Labeled 在 manifest 基础上追加候选动作、预测 outcome、synthetic preference score 和 terminal realization。

```json
{
  "candidate_actions": ["hold_silent", "inform_comparison_brief", "elicit_need_focus_open", "inform_demo_brief"],
  "outcomes": {
    "inform_comparison_brief": {
      "next_aida_stage": "desire",
      "next_bdi": {
        "belief": "能看到商品差异，选择成本降低",
        "desire": "想在对比卡中锁定候选",
        "intention": "围绕少数候选进行最后比较"
      },
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.33,
      "delta_mental": 0.8,
      "action_cost": 0.3,
      "preference_score": 0.592,
      "rationale": "比较卡降低决策负担，belief 从模糊变清晰",
      "response_id": "inform_comparison_brief",
      "terminal_realization": {
        "surface_text": "我把这几款的差别列在屏幕上，您可以先比较价格、功能和适合场景。",
        "screen": {"action": "show_comparison_or_details", "target": "{candidate_items}", "cta": null},
        "voice_style": "neutral",
        "light": "soft_focus_on_comparison_cards",
        "cabinet_motion": null,
        "duration_ms": 4000
      }
    }
  },
  "best_action": "inform_comparison_brief",
  "response_id": "inform_comparison_brief",
  "realization": {"...": "..."},
  "score_weights": {"alpha": 0.4, "beta": 0.5, "gamma": 0.2}
}
```

字段规则：

| Field | Required | Meaning |
|---|---|---|
| `candidate_actions` | yes | 当前候选 `response_id` 列表 |
| `outcomes[*].response_id` | yes | outcome 对应的稳定动作键 |
| `outcomes[*].terminal_realization` | yes | 终端响应包 |
| `outcomes[*].preference_score` | yes | 系统计算的 synthetic preference score |
| `best_action` | yes | `argmax(preference_score)` |
| `response_id` | yes | `best_action` 的显式镜像字段 |
| `realization` | yes | best action 的 terminal realization |

Preference score:

```text
preference_score = alpha * delta_stage + beta * delta_mental - gamma * action_cost
clip to [-1, 1]
default: alpha=0.4, beta=0.5, gamma=0.2
```

`preference_score` 是用于合成标注的专家偏好代理分数，不是真实用户反馈 reward。LLM 只预测 outcome；`action_cost / preference_score / best_action` 由系统确定。

## Prompt

`data/prompts/piwm_<id>.md` 是视频生成 prompt，由 manifest 渲染。它描述 intervention 前的顾客观察片段，不要求包含 terminal realization。
