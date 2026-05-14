# Data Schema

当前 schema 已同步 PIWM v2.1：旧 `candidate_actions / best_action` 继续保留，新增 `schema_version / dialogue_act / act_params / realization` 和 outcome 级 `terminal_realization`。

字段边界：

- `co_acts` 只作为 legacy input alias，不再作为新数据的 canonical 字段。
- 辅助动作写入 `act_params.supporting_acts`。
- 需要旧格式回溯时使用 `legacy_co_acts`。
- 本仓库是 terminal/prototype 数据线；主项目 `PIWM-Train-Synth-v1` 的真人导购训练数据不在这里维护。

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

Labeled 在 manifest 基础上追加动作、预测 outcome、reward 和 v2 terminal realization。

```json
{
  "schema_version": "dialogue_act_terminal_realization_v2.1",
  "candidate_actions": ["T1_SILENT_OBSERVE", "T2_VALUE_COMPARE", "T4_OPEN_QUESTION", "T5_DEMO"],
  "outcomes": {
    "T2_VALUE_COMPARE": {
      "next_aida_stage": "desire",
      "next_bdi": {
        "belief": "能看到商品差异，选择成本降低",
        "desire": "想在对比卡中锁定候选",
        "intention": "围绕少数候选进行最后比较"
      },
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.33,
      "delta_mental": 1.5,
      "action_cost": 0.3,
      "reward": 0.852,
      "rationale": "比较卡降低决策负担，belief 从模糊变清晰",
      "dialogue_act": "Inform",
      "act_params": {"content_type": "comparison", "depth": "brief"},
      "terminal_realization": {
        "surface_text": "我把这几款的差别列在屏幕上，您可以先比较价格、功能和适合场景。",
        "screen": {"action": "show_comparison_or_details", "target": "{candidate_items}", "cta": null},
        "voice_style": "neutral",
        "light": "soft_focus_on_comparison_cards",
        "cabinet_motion": null,
        "duration_ms": 4000,
        "dialogue_act": "Inform",
        "act_params": {"content_type": "comparison", "depth": "brief"},
        "legacy_action": "T2_VALUE_COMPARE"
      }
    }
  },
  "best_action": "T2_VALUE_COMPARE",
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "realization": {"...": "..."},
  "reward_weights": {"alpha": 0.4, "beta": 0.5, "gamma": 0.1}
}
```

字段规则：

| Field | Required | Meaning |
|---|---|---|
| `schema_version` | yes | 当前为 `dialogue_act_terminal_realization_v2.1` |
| `candidate_actions` | yes | 兼容动作标签；新数据推荐使用 T-state |
| `outcomes[*].dialogue_act` | yes | 6-act policy label |
| `outcomes[*].act_params` | yes | act 参数 |
| `outcomes[*].terminal_realization` | yes | 终端响应包 |
| `best_action` | yes | `argmax(reward)` |
| `dialogue_act / act_params` | yes | best action 的 v2.1 policy 字段 |
| `act_params.supporting_acts` | conditional | 辅助动作，例如 `Reassure + Hold` |
| `legacy_co_acts` | optional | 仅用于旧 `co_acts` 回溯 |
| `realization` | yes | best action 的 terminal realization |

Reward:

```text
reward = alpha * delta_stage + beta * delta_mental - gamma * action_cost
clip to [-1, 1]
default: alpha=0.4, beta=0.5, gamma=0.1
```

## Existing Dynamic A-actions

早期样例中存在 `A0_silence`、`A2_compare_best_value_options` 这类动态 action 名。它们现在作为 `legacy_action` 保留，不再作为语义中心。运行以下命令可回填 v2 字段：

```bash
python script/upgrade_labeled_v2.py
```

## Kling Prompt

`data/kling/piwm_<id>.md` 仍是视频生成 prompt。它描述 intervention 前的顾客观察片段，不要求包含 terminal realization。
