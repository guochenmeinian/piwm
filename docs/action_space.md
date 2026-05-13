# PIWM Action Space

## 1. Three Layers

```text
Policy layer      DialogueAct + params
Realization layer deterministic template translation
Terminal layer    screen / voice / light / cabinet motion
```

Policy 只决定"做什么"，Terminal Realization 决定"终端怎么表现"。

## 2. Dialogue Acts

| Act | Params | 用途 |
|---|---|---|
| `Greet` | `phase=open\|close` | 开场或收尾 |
| `Elicit` | `openness=open\|closed`, `slot=need_focus\|budget\|usage\|companion_opinion` | 获取顾客偏好或需求 |
| `Inform` | `content_type=comparison\|demo\|attributes\|price`, `depth=brief\|detailed` | 提供信息 |
| `Recommend` | `pressure=soft\|firm` | 给出温和或明确的推荐 |
| `Reassure` | `focus=time\|decision\|alternatives` | 安抚、降低决策压力 |
| `Hold` | `mode=silent\|ambient` | 静默观察或退到背景 |

共现规则：

- `Elicit / Inform / Recommend` 每轮最多一个。
- `Greet / Reassure / Hold` 可与 task act 共现。
- 新能力优先加到 `params` 或 realization 模板，不直接新增 act。

## 3. Terminal Realization

每个动作输出一个终端响应包：

```json
{
  "response_id": "inform_comparison_brief",
  "surface_text": "...",
  "screen": {"action": "...", "target": "...", "cta": null},
  "voice_style": "neutral | soft | assertive | curious | warm | silent",
  "light": "...",
  "cabinet_motion": null,
  "duration_ms": 0,
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": []
}
```

`response_id` 是某个 `dialogue_act + act_params + co_acts` 组合的稳定键，用于 `candidate_actions / best_action / outcomes` 做索引；它不是新的语义层。

实现入口：`script/action_space.py`
