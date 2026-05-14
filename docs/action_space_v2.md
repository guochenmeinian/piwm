# PIWM Action Space v2.1

本文同步自主项目 `ProactiveIntentWorldModel` 的动作空间口径。轻量仓库只保留必要实现，不复制训练、评测和远端数据盘体系。

当前边界：

- 轻量仓库仍是 `seed -> manifest -> deliberation -> kling` terminal/prototype 生产线。
- 主项目 `PIWM-Train-Synth-v1` 保留真人导购逻辑；本仓库不替代那批训练集。
- 两边共享 6 个 `DialogueAct`，但 realization 主体不同：本仓库生成 terminal response，主训练集保留 human-salesperson behavior。

## 1. Three Layers

```text
Policy layer      DialogueAct + params
Realization layer deterministic template translation
Terminal layer    screen / voice / light / cabinet motion
```

policy 只决定“做什么”，terminal realization 决定“终端怎么表现”。旧 `A*` 和 `T-state` 标签仍可读，但不再是语义中心。

## 2. Dialogue Acts

| Act | Params | Meaning |
|---|---|---|
| `Greet` | `phase=open|close` | 开场或收尾礼节 |
| `Elicit` | `openness=open|closed`, `slot=need_focus|budget|usage|companion_opinion` | 获取顾客偏好或需求 |
| `Inform` | `content_type=comparison|demo|attributes|price`, `depth=brief|detailed` | 提供比较、演示、参数或价格信息 |
| `Recommend` | `target=item|action`, `pressure=soft|firm` | 推荐商品或下一步 |
| `Reassure` | `focus=time|decision|alternatives` | 安抚、降压、降低决策压力 |
| `Hold` | `mode=silent|ambient` | 静默观察或背景退出 |

共现规则：

- `Elicit / Inform / Recommend` 每轮最多一个。
- `Greet / Reassure / Hold` 可以和 task act 共现。
- 新能力优先加到 `params` 或 realization 模板，不直接新增 act。
- v2.1 不再把辅助动作写成顶层 `co_acts`；新格式写入 `act_params.supporting_acts`，旧格式回溯字段为 `legacy_co_acts`。

示例：

```json
{
  "dialogue_act": "Reassure",
  "act_params": {
    "focus": "time",
    "supporting_acts": [
      {"type": "Hold", "params": {"mode": "ambient"}}
    ]
  },
  "legacy_co_acts": [
    {"act": "Hold", "params": {"mode": "ambient"}}
  ]
}
```

## 3. T-state Compatibility

| T-state | DialogueAct |
|---|---|
| `T1_SILENT_OBSERVE` | `Hold(mode=silent)` |
| `T2_VALUE_COMPARE` | `Inform(content_type=comparison, depth=brief)` |
| `T3_STRONG_RECOMMEND` | `Recommend(target=item, pressure=firm)` |
| `T4_OPEN_QUESTION` | `Elicit(openness=open, slot=need_focus)` |
| `T5_DEMO` | `Inform(content_type=demo, depth=brief)` |
| `T6_ACK_WAIT` | `Reassure(focus=time, supporting_acts=[Hold(mode=ambient)])` |
| `T7_DISENGAGE` | `Hold(mode=ambient)` |
| `T_TRANSACT` | `Greet(phase=close)` |

当前 `gen_deliberation.py` 仍按 AIDA 阶段生成 4 个 T-state 候选，脚本自动补齐 v2 act 字段。

## 4. Terminal Realization

每个最佳动作和每个 outcome 都应带终端响应包：

```json
{
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
```

实现入口：

- `script/action_space_v2.py`: act enum、兼容映射、supporting_acts 规范化、realization 模板。
- `script/gen_deliberation.py`: 新生成 labeled JSON 时自动写入 v2 字段。
- `script/upgrade_labeled_v2.py`: 给已有 labeled JSON 回填 v2 字段。
- `script/audit_action_space_v2.py`: 检查 labeled JSON 是否仍残留顶层 `co_acts` 或 schema mismatch。
