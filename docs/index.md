# PIWM Data Index

当前仓库维护两条数据流：

```text
seed -> manifest -> prompt -> video
seed -> manifest -> labeled
```

`seed / manifest / labeled / prompts / video` 已覆盖 `piwm_700` 到 `piwm_805` 共 106 条。

---

## 文档导航

- [design.md](design.md)：任务设定、状态模型、动作模型、preference score 设计。
- [pipeline.md](pipeline.md)：从 `seed` 到 `manifest / prompt / labeled / video` 的生成流程与校验流程。
- [schema.md](schema.md)：`manifest / labeled / prompt` 的字段契约与示例结构。
- [action_space.md](action_space.md)：动作空间、参数设计、`response_id` 与 terminal realization 契约。
- [usage.md](usage.md)：脚本运行方式、环境变量、常用命令。
- [reference.md](reference.md)：外部参考资料。

---

## 当前状态

| Stage | Count |
|---|---:|
| seed | 106 |
| manifest | 106 |
| labeled | 106 |
| prompts | 106 |
| video | 106 |

`labeled` 字段约束：

- 每条记录都有 4 个 candidate actions
- 每条都包含 `hold_silent` 作为 baseline
- 每个 outcome 都有完整的 `delta_stage / delta_mental / action_cost / preference_score`
- `best_action` 与最高 `preference_score` 一致
- 顶层 `response_id` 与 `best_action` 一致
- `response_id` 是唯一动作键，不再额外展开 `dialogue_act / act_params / co_acts`

---

## 流程说明

这套数据的核心流程很简单：

- `seed`：定义场景初始条件与样本设定。
- `manifest`：把场景整理成结构化状态，包含阶段、用户意图、注意力、行为线索等。
- `labeled`：基于同一个状态生成 4 个候选动作，并为每个动作写 outcome 与 `preference_score`，最终确定 `best_action`。
- `prompt`：把 `manifest` 转成视频生成提示词，用于生成交互前 10 秒视频。
- `video`：根据 prompt 生成对应视频片段。

因此，训练上主要对应两件事：

- 从图像或视频状态中恢复结构化状态信息。
- 在给定状态下，对候选 action 做偏好判断，并选出 `best_action`。

---

## Stage 配比

当前 stage 分布为 `15 / 37 / 39 / 15`（attention / interest / desire / action）。

| Stage | Count |
|---|---:|
| attention | 15 |
| interest | 37 |
| desire | 39 |
| action | 15 |

结论：整体阶段分布是均衡的，中段 `interest / desire` 略多，但仍然符合零售交互数据的自然形态。

---

## Best Action 分布

| Best Action | Count |
|---|---:|
| Elicit:need_focus | 20 |
| Inform:comparison | 20 |
| Inform:demo | 13 |
| Greet:close | 11 |
| Reassure:time | 11 |
| Inform:price | 10 |
| Recommend:firm | 7 |
| Reassure:decision | 6 |
| Inform:attributes | 4 |
| Recommend:soft | 4 |

结论：动作分布 `总体合理，但不均匀`。

- `attention`：以 `Elicit:need_focus` 和 `Inform:demo` 为主，符合“先聚焦 / 先激发兴趣”的阶段语义。
- `interest`：以 `Inform:comparison`、`Elicit:need_focus`、`Inform:demo` 为主，符合“比较 / 聚焦 / 理解功能”的中段语义。
- `desire`：`Recommend:firm / Reassure:time / Inform:price / Inform:comparison / Reassure:decision` 相对均衡，符合“推进决策但不过早收尾”的语义。
- `action`：以 `Greet:close` 为主、`Reassure:time` 为辅，基本符合“等待出货 / 礼貌收尾 / 时间确认”的收尾语义。

---

## Stage 内部分布

### attention

| Best Action | Count |
|---|---:|
| Elicit:need_focus | 9 |
| Inform:demo | 6 |

### interest

| Best Action | Count |
|---|---:|
| Inform:comparison | 14 |
| Elicit:need_focus | 11 |
| Inform:demo | 7 |
| Inform:attributes | 4 |
| Inform:price | 1 |

### desire

| Best Action | Count |
|---|---:|
| Recommend:firm | 7 |
| Reassure:time | 7 |
| Inform:price | 9 |
| Inform:comparison | 6 |
| Reassure:decision | 6 |
| Recommend:soft | 4 |

### action

| Best Action | Count |
|---|---:|
| Greet:close | 11 |
| Reassure:time | 4 |

---

## Index -> Best Action

下表按 `labeled/*.json` 顶层 `best_action` 统计，可直接当作每个样本的主动作索引表。

| Index | Best Action |
|---|---|
| piwm_700 | elicit_need_focus_open |
| piwm_701 | elicit_need_focus_open |
| piwm_702 | inform_comparison_brief |
| piwm_703 | elicit_need_focus_open |
| piwm_704 | elicit_need_focus_open |
| piwm_705 | elicit_need_focus_open |
| piwm_706 | elicit_need_focus_open |
| piwm_707 | inform_comparison_brief |
| piwm_708 | inform_comparison_brief |
| piwm_709 | elicit_need_focus_open |
| piwm_710 | elicit_need_focus_open |
| piwm_711 | elicit_need_focus_open |
| piwm_712 | inform_price_brief |
| piwm_713 | inform_price_brief |
| piwm_714 | inform_comparison_brief |
| piwm_715 | inform_price_brief |
| piwm_716 | inform_price_brief |
| piwm_717 | reassure_decision |
| piwm_718 | greet_close |
| piwm_719 | greet_close |
| piwm_720 | greet_close |
| piwm_721 | greet_close |
| piwm_722 | inform_demo_brief |
| piwm_723 | inform_demo_brief |
| piwm_724 | elicit_need_focus_open |
| piwm_725 | elicit_need_focus_open |
| piwm_726 | inform_demo_brief |
| piwm_727 | elicit_need_focus_open |
| piwm_728 | inform_demo_brief |
| piwm_729 | inform_demo_brief |
| piwm_730 | elicit_need_focus_open |
| piwm_731 | elicit_need_focus_open |
| piwm_732 | elicit_need_focus_open |
| piwm_733 | inform_demo_brief |
| piwm_734 | inform_comparison_brief |
| piwm_735 | inform_price_brief |
| piwm_736 | inform_comparison_brief |
| piwm_737 | inform_comparison_brief |
| piwm_738 | inform_comparison_brief |
| piwm_739 | inform_comparison_brief |
| piwm_740 | inform_comparison_brief |
| piwm_741 | inform_comparison_brief |
| piwm_742 | inform_comparison_brief |
| piwm_743 | inform_demo_brief |
| piwm_744 | inform_demo_brief |
| piwm_745 | inform_demo_brief |
| piwm_746 | inform_demo_brief |
| piwm_747 | inform_demo_brief |
| piwm_748 | inform_demo_brief |
| piwm_749 | inform_demo_brief |
| piwm_750 | inform_comparison_brief |
| piwm_751 | inform_attributes_brief |
| piwm_752 | inform_attributes_brief |
| piwm_753 | inform_comparison_brief |
| piwm_754 | inform_comparison_brief |
| piwm_755 | elicit_need_focus_open |
| piwm_756 | elicit_need_focus_open |
| piwm_757 | elicit_need_focus_open |
| piwm_758 | elicit_need_focus_open |
| piwm_759 | elicit_need_focus_open |
| piwm_760 | recommend_soft |
| piwm_761 | inform_price_brief |
| piwm_762 | recommend_soft |
| piwm_763 | recommend_firm |
| piwm_764 | recommend_firm |
| piwm_765 | recommend_firm |
| piwm_766 | recommend_soft |
| piwm_767 | recommend_firm |
| piwm_768 | recommend_firm |
| piwm_769 | recommend_firm |
| piwm_770 | recommend_firm |
| piwm_771 | reassure_time_wait |
| piwm_772 | reassure_time_wait |
| piwm_773 | reassure_time_wait |
| piwm_774 | reassure_time_wait |
| piwm_775 | reassure_time_wait |
| piwm_776 | reassure_time_wait |
| piwm_777 | inform_comparison_brief |
| piwm_778 | inform_price_brief |
| piwm_779 | reassure_decision |
| piwm_780 | reassure_decision |
| piwm_781 | reassure_decision |
| piwm_782 | reassure_decision |
| piwm_783 | reassure_decision |
| piwm_784 | reassure_time_wait |
| piwm_785 | inform_comparison_brief |
| piwm_786 | inform_comparison_brief |
| piwm_787 | inform_comparison_brief |
| piwm_788 | inform_comparison_brief |
| piwm_789 | greet_close |
| piwm_790 | greet_close |
| piwm_791 | greet_close |
| piwm_792 | greet_close |
| piwm_793 | greet_close |
| piwm_794 | reassure_time_wait |
| piwm_795 | reassure_time_wait |
| piwm_796 | greet_close |
| piwm_797 | greet_close |
| piwm_798 | reassure_time_wait |
| piwm_799 | reassure_time_wait |
| piwm_800 | inform_price_brief |
| piwm_801 | inform_price_brief |
| piwm_802 | inform_price_brief |
| piwm_803 | inform_attributes_brief |
| piwm_804 | inform_attributes_brief |
| piwm_805 | recommend_soft |

---

## 质量结论

当前数据可以直接作为正式版本使用，结构完整、索引清晰、视频与标注一一对应。

可以直接把这份文档理解为：

- 数据覆盖范围说明
- 数据流与训练任务说明
- 动作与阶段分布概览
- 每个 index 对应的主动作索引表
