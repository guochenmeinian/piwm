# PIWM Data Index

当前仓库维护两条数据流：

```text
seed -> manifest -> prompt -> video
seed -> manifest -> labeled
```

`seed / manifest / labeled / prompts` 已覆盖 `piwm_700` 到 `piwm_805` 共 106 条。  
`video` 当前已有 3 条样例（`piwm_700`–`piwm_702`）。

---

## 当前状态

| Stage | Count |
|---|---:|
| seed | 106 |
| manifest | 106 |
| labeled | 106 |
| prompts | 106 |
| video | 3 |

当前 `labeled` 数据已经过统一重跑和校验：

- 每条记录都有 4 个 candidate actions
- 每条都包含 `hold_silent` 作为 baseline
- 每个 outcome 都有完整的 `delta_stage / delta_mental / action_cost / preference_score`
- `best_action` 与最高 `preference_score` 一致
- 顶层 `response_id` 与 `best_action` 一致

---

## Stage 配比

原始 100 条目标分布是 `15 / 35 / 35 / 15`（attention / interest / desire / action）。
当前新增 6 条长尾动作补样本后，分布变为 `15 / 37 / 39 / 15`。

| Stage | Current | Target |
|---|---:|---:|
| attention | 15 | 15 |
| interest | 37 | 35 |
| desire | 39 | 35 |
| action | 15 | 15 |

结论：原始 `700–799` 版本的 stage 配比是精确对齐的。  
当前 `700–805` 扩展版为了补长尾动作，轻微增加了 `interest / desire`，但没有破坏整体阶段语义。

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
- `desire`：`Recommend:firm / Reassure:time / Inform:price / Inform:comparison / Reassure:decision` 相对均衡，说明后决策阶段已经比早期版本健康很多。
- `action`：以 `Greet:close` 为主、`Reassure:time` 为辅，基本符合“等待出货 / 礼貌收尾 / 时间确认”的收尾语义。

这轮补样本后，原本最稀缺的两类已经被拉起来：

- `Inform:attributes`：`2 -> 4`
- `Recommend:soft`：`3 -> 4`

它们仍然比头部动作少，但已经不再是“明显缺失”的状态。

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

## 质量结论

当前这版数据可以作为单一正式版本继续往下走，不需要再区分旧版 / v2 / 迁移版。

可以认为已经解决的问题：

- `piwm_700–799` 已全部按同一 schema、同一 scoring 规则统一生成和校验
- `piwm_800–805` 已作为长尾动作补样本接入同一流程，新增 `Inform:price * 3 / Inform:attributes * 2 / Recommend:soft * 1`
- 旧的候选重复、candidate 数量不足、best_action 与 score 不一致问题已清掉
- `gen_deliberation.py` 已收紧 validator，不再允许 validation 失败后直接落盘
- prompt 已补充更明确的 action 边界，减少了“模糊需求却直接 comparison / 过早 close / 推荐语义漂移”这类错误

当前剩余工作：

- 补更多 `video` 样例
- 如果继续追求动作均衡，可进一步补 `Reassure:decision`、`Recommend:soft`、`Inform:attributes`
- 如需论文或实验记录，可把当前分布和 scoring 规则固化到设计文档中
