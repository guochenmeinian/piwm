# Pipeline

PIWM 当前维护两条独立数据流：

```text
seed -> manifest -> prompt -> video
seed -> manifest -> labeled
```

设计原则：

- 视频只建模 `intervention 前 10s` 的顾客状态
- 动作决策只建模 `当前 state -> 候选动作 -> synthetic preference`
- `prompt` 不依赖 `labeled`
- `best_action` 不是 LLM 直接输出，而是系统按 score 计算

---

## Step 1: Seed -> Manifest

输入：`data/seed/piwm_NNN.txt`

`gen_manifest.py` 把 seed 渲染成当前顾客状态，输出到 `data/manifest/piwm_NNN.json`：

- `persona / persona_visual`
- `aida_stage`
- `bdi.belief / desire / intention`
- `observable_behavior`
- `facial_expression`
- `body_posture`
- `timeline.t_0_2 / t_2_5 / t_5_8 / t_8_10`

Manifest 只描述顾客当前状态，不写机器动作，不写终端响应，不写未来 intervention。

---

## Step 2A: Manifest -> Prompt

输入：`data/manifest/piwm_NNN.json`

`gen_prompt.py` 只读取顾客观察字段，生成 `data/prompts/piwm_NNN.md`。

这一层的目标是给视频模型一个更稳定的 pre-interaction 状态脚本，所以：

- 只描述顾客、环境、镜头和 10s 时间线
- 不引入 `best_action`
- 不引入 `terminal_realization`
- 不让视频 prompt 暗示“后面机器会怎么干预”

也就是说，视频 prompt 负责“把 state 拍清楚”，不负责“把 policy 演出来”。

---

## Step 2B: Manifest -> Labeled

输入：`data/manifest/piwm_NNN.json`

`gen_deliberation.py` 生成 `data/labeled/piwm_NNN.json`。它分成两段：

### 2B.1 LLM 负责的部分

LLM 只做受约束的 outcome prediction：

1. 根据当前 `aida_stage` 读取允许动作池
2. 选择 4 个候选 `response_id`
3. 必须包含 `hold_silent`
4. 为每个候选预测：
   - `next_aida_stage`
   - `next_bdi`
   - `risk / benefit`
   - `delta_stage / delta_mental`
   - `rationale`

LLM 不负责输出：

- `action_cost`
- `preference_score`
- `best_action`

### 2B.2 系统负责的部分

系统根据 `response_id` 自动补齐动作契约和分数：

- `response_id`
- `dialogue_act`
- `act_params`
- `co_acts`
- `terminal_realization`
- `action_cost`
- `preference_score`

公式：

```text
preference_score = alpha * delta_stage + beta * delta_mental - gamma * action_cost
default: alpha=0.4, beta=0.5, gamma=0.2
clip to [-1, 1]
```

然后系统执行：

```text
best_action = argmax(preference_score)
```

所以 `best_action` 是系统计算结果，不是 LLM 偏好声明。

---

## 审计与重跑

`gen_deliberation.py` 在保存前会做严格校验。

当前会检查：

- 候选数量必须为 4
- `hold_silent` 必须出现
- 候选不能重复
- 候选必须属于当前 `aida_stage` 的允许池
- `next_aida_stage` 必须合法
- `next_bdi` 字段必须完整
- outcome 必须包含完整的 `risk / benefit / delta_* / rationale`
- `delta_stage / delta_mental` 范围必须合理
- `next_bdi` 里不能泄漏 `target_act / Recommend:firm` 这类内部标签
- `action` 阶段不能乱跳到 schema 外阶段

若校验失败：

1. 脚本把错误反馈给 LLM
2. 自动 retry
3. 若多次 retry 后仍失败，脚本直接报错，不落盘

这意味着当前数据不会再出现“validation 失败但照样保存 best attempt”的旧问题。

---

## 人工审计与少量校正

自动校验只能保证结构一致，不能完全保证语义自然。

因此实际流程里还保留了一层人工审计：

- 看 `best_action` 是否真的符合 manifest 的直觉
- 看 score 排序是否和场景语义一致
- 看是否出现“过早 close”“模糊需求却直接 comparison”“推荐语义漂移”这类问题

如果问题来自 LLM 输出不稳，优先重跑。  
如果问题来自少量边界样本的 score 排序仍不理想，允许极少量人工校正，但必须保证：

- 改后的 `preference_score` 仍符合公式
- `best_action` 仍等于最高 score
- 修改理由可追溯

---

## 输出结构示意

```json
{
  "candidate_actions": ["hold_silent", "inform_comparison_brief", "elicit_need_focus_open", "inform_demo_brief"],
  "outcomes": {
    "inform_comparison_brief": {
      "next_aida_stage": "desire",
      "next_bdi": {"belief": "...", "desire": "...", "intention": "..."},
      "risk": "low",
      "benefit": "high",
      "delta_stage": 0.33,
      "delta_mental": 0.8,
      "action_cost": 0.3,
      "preference_score": 0.592,
      "rationale": "...",
      "response_id": "inform_comparison_brief",
      "dialogue_act": "Inform",
      "act_params": {"content_type": "comparison", "depth": "brief"},
      "co_acts": [],
      "terminal_realization": {"surface_text": "...", "screen": {"action": "show_comparison_or_details"}}
    }
  },
  "best_action": "inform_comparison_brief",
  "response_id": "inform_comparison_brief",
  "dialogue_act": "Inform",
  "act_params": {"content_type": "comparison", "depth": "brief"},
  "co_acts": [],
  "realization": {"surface_text": "..."}
}
```

---

## Step 3: Prompt -> Video

`gen_video.py` 读取 `data/prompts/*.md` 并调用 Kling API 生成 `data/video/*.mp4`。

这一步当前不是主线，但保留接口不变，方便在 state / labeled 稳定后再批量补视频。

---

## Normalize Existing Labeled Files

运行：

```bash
python script/upgrade_labeled.py
```

脚本会统一 labeled 文件中的 `response_id`、动作语义字段和 realization 字段。  
当前 `piwm_700–799` 已经全部按统一 schema 和统一 scoring 规则校验过，不再区分旧版批次。
