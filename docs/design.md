# PIWM Data Design

本文记录轻量 `piwm` 仓库的当前设计。它保持小仓库定位：快速生成 seed、manifest、labeled、视频 prompt 和少量视频样例。

## 1. Problem

智能零售设备持续观察顾客，但不能只等待顾客主动操作。PIWM 要学习：

1. 从视频可见行为推断 AIDA + BDI 状态。
2. 预测不同机器响应会如何改变顾客状态。
3. 在低打扰前提下选择最合适的 proactive response。

核心难点：

- 顾客意图是内隐变量，只能通过目光、停留、姿态、手部动作等外显信号间接推断。
- 干预后的真实反应难以低成本采集，因此轻量仓库使用 LLM 生成 action-conditioned outcome，再用 Kling 生成可视样例。

## 2. State Model

宏观状态使用 AIDA：

| AIDA | 顾客状态 | 典型可见行为 |
|---|---|---|
| `attention` | 注意到设备，无明确兴趣 | 目光扫过，步伐放慢 |
| `interest` | 主动观察，开始比较 | 停步，目光来回扫视，轻微前倾 |
| `desire` | 有购买意愿，进入权衡 | 目光锁定，身体前倾，手部靠近 |
| `action` | 决定购买，进入操作 | 手臂伸出，动作直接坚定 |

微观状态使用 BDI：

- `belief`: 顾客对商品、价格、场景或设备的认知判断。
- `desire`: 顾客当前想解决的问题。
- `intention`: 顾客接下来最可能采取的行为。

## 3. Action Space

当前语义中心是 6 个 `DialogueAct`：

| Act | 作用 |
|---|---|
| `Greet` | 开场或收尾礼节 |
| `Elicit` | 提问探询顾客需求 |
| `Inform` | 提供比较、演示、参数或价格信息 |
| `Recommend` | 给出温和或明确的推荐 |
| `Reassure` | 安抚、降压、降低决策压力 |
| `Hold` | 静默观察或背景退出 |

候选动作通过 `response_id` 索引，例如：

| response_id | act |
|---|---|
| `hold_silent` | `Hold(mode=silent)` |
| `inform_comparison_brief` | `Inform(content_type=comparison, depth=brief)` |
| `recommend_firm` | `Recommend(pressure=firm)` |
| `elicit_need_focus_open` | `Elicit(openness=open, slot=need_focus)` |
| `inform_demo_brief` | `Inform(content_type=demo, depth=brief)` |
| `reassure_time_wait` | `Reassure(focus=time)` + `Hold(mode=ambient)` |
| `hold_ambient` | `Hold(mode=ambient)` |
| `greet_close` | `Greet(phase=close)` |

更完整契约见 [action_space.md](action_space.md)。

## 4. Realization

Policy layer 输出：

```json
{
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": []
}
```

Realization layer 确定终端响应：

```json
{
  "surface_text": "我把这几款的差别列在屏幕上，您可以先比较价格、功能和适合场景。",
  "screen": {"action": "show_comparison_or_details", "target": "{candidate_items}", "cta": null},
  "voice_style": "neutral",
  "light": "soft_focus_on_comparison_cards",
  "cabinet_motion": null,
  "duration_ms": 4000
}
```

这样可以避免把“策略选择”“屏幕 UI”“数字人台词”混成一个不可维护字段。

## 5. Data Generation

```text
seed -> manifest -> labeled -> prompts -> video
```

### Manifest

由 seed 约束生成顾客当前状态：

- persona / persona_visual
- AIDA + BDI
- observable behavior
- facial expression
- body posture
- timeline

### Labeled

对候选动作逐一预测 outcome：

- next AIDA + next BDI
- risk / benefit
- delta_stage / delta_mental
- action_cost / reward
- rationale
- response_id / dialogue_act / act_params / terminal_realization

### Prompts

将 manifest/labeled 中的顾客观察字段渲染成视频 prompt。视频只描述 intervention 前的顾客状态，不包含终端响应。

## 6. Reward

```text
reward = alpha * delta_stage + beta * delta_mental - gamma * action_cost
default: alpha=0.4, beta=0.5, gamma=0.1
clip to [-1, 1]
```

`delta_mental` 权重高于 `delta_stage`，表示顾客体验和决策压力优先于短期转化。

## 7. Compatibility

本仓库早期 22 条 labeled 样例使用旧动作键。运行：

```bash
python script/upgrade_labeled.py
```

即可统一归一到 `response_id` 格式。新生成数据直接使用 canonical action 格式。
