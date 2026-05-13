# PIWM Data Index

每条记录对应一个顾客场景：seed → manifest → labeled → prompt → video。

**Pipeline 列说明**：S=seed · M=manifest · L=labeled · P=prompt · V=video

---

## 现有数据（piwm_700–721）

| ID | Stage | Persona（摘要） | Best Action | S | M | L | P | V | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| piwm_700 | interest | 双休日无聊逛街的普通消费者 | Inform:comparison | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_701 | interest | 下班路过便利区的年轻白领女性 | Recommend:soft | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_702 | interest | 午休后路过便利区、想买饮品 | Inform:comparison | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ seed 写 attention，实际生成 interest |
| piwm_703 | attention | 课间路过校园便利区被设备外观吸引的学生 | Elicit:need_focus | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_704 | attention | 下班途中被智能售货机吸引的年轻女性 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_705 | attention | 午休后路过便利区的中年办公室职员 | Recommend:soft | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ attention 阶段出现 Recommend:soft 偏激进 |
| piwm_706 | interest | 课间路过校园便利区的男大学生 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_707 | interest | 午后课间路过自助零售区、想买饮品的女生 | Inform:comparison | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_708 | interest | 加班后路过便利区的年轻上班族 | Recommend:soft | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_709 | interest | 午休后路过便利区的中年男职员 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_710 | interest | 午休间隙路过便利区、担心不合适的顾客 | Inform:comparison | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_711 | interest | 课间经过校园便利区的大学生 | Inform:demo | ✓ | ✓ | ✓ | ✓ | ✗ | |
| piwm_712 | desire | 下班途中准备快速购买的上班族 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Recommend/Reassure |
| piwm_713 | desire | 午休后路过便利区的年轻女白领 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Recommend/Reassure |
| piwm_714 | desire | 午休结束前路过便利区、比较两个选择 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Recommend/Reassure |
| piwm_715 | desire | 课间路过校园便利区的大学生 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Recommend/Reassure |
| piwm_716 | desire | 午休后路过便利区、有顾虑的中年女性 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Reassure:decision |
| piwm_717 | desire | 下班后路过便利区、反复权衡的年轻上班族 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ desire 阶段应为 Reassure/Recommend |
| piwm_718 | action | 课间已决定购买、表情轻松的学生 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ action 阶段不应是 Inform:attributes |
| piwm_719 | action | 午休后快速完成确认的中年男性 | Recommend:soft | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ action 阶段 Recommend:soft 语义存疑 |
| piwm_720 | action | 下班途中略微迟疑的年轻上班族 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ action 阶段不应是 Inform:attributes |
| piwm_721 | action | 晚自习前快速购买的学生 | Inform:attributes | ✓ | ✓ | ✓ | ✓ | ✗ | ⚠ action 阶段不应是 Inform:attributes |

---

## 现有数据分布分析

### Stage 分布

| Stage | 数量 | 占比 | 目标占比 |
|---|---|---|---|
| attention | 3 | 14% | 15% |
| interest | 9 | 41% | 35% |
| desire | 6 | 27% | 35% |
| action | 4 | 18% | 15% |

### Best Action 分布（⚠ 严重失衡）

| Best Action | 现有 | 目标（100条总量） |
|---|---|---|
| Inform:attributes | 12 | 12 |
| Inform:comparison | 4 | 15 |
| Inform:demo | 1 | 8 |
| Recommend:soft | 4 | 12 |
| Recommend:firm | 0 | 8 |
| Elicit:need_focus | 1 | 10 |
| Elicit:companion_opinion | 0 | 5 |
| Reassure:time | 0 | 8 |
| Reassure:decision | 0 | 7 |
| Hold:silent | 0 | 10 |
| Hold:ambient | 0 | 5 |
| Greet:close | 0 | 5 |

---

## 待生成数据规划（piwm_722–821，目标 100 条总量含现有 22 条）

还需生成 **78 条**，seed 需覆盖以下缺口：

| 优先级 | 缺口 | 需补条数 | seed 设计方向 |
|---|---|---|---|
| 🔴 高 | Recommend:firm | 8 | desire-low-hesitation，顾客信息充足、只差临门一脚 |
| 🔴 高 | Reassure:time | 8 | desire，外部时间压力明显（赶班车/午休要结束） |
| 🔴 高 | Reassure:decision | 7 | desire-high-hesitation，决策焦虑、反复拿起放下 |
| 🔴 高 | Hold:silent | 10 | attention/interest，顾客在思考、不需要打扰 |
| 🔴 高 | Greet:close | 5 | action，已完成扫码/操作，进入结尾 |
| 🟡 中 | Hold:ambient | 5 | attention，顾客明显不感兴趣、即将离开 |
| 🟡 中 | Elicit:companion_opinion | 5 | 带伴场景，需要询问同行者意见 |
| 🟡 中 | Inform:comparison（补） | 11 | interest，正在多款之间比较 |
| 🟡 中 | Elicit:need_focus（补） | 9 | attention，顾客信息需求不明确 |
| 🟢 低 | desire 全段修复 | 6 | 重新生成 712–717，候选集加入 Recommend/Reassure |
| 🟢 低 | action 全段修复 | 4 | 重新生成 718–721，加入 Greet:close / Reassure:time |

---

## Persona 配比目标（78条新增）

| Persona 类型 | 目标条数 | 特征 |
|---|---|---|
| 年轻白领 | 16 | 时间有限、目标明确 |
| 学生 | 16 | 预算敏感、对商品陌生 |
| 中年消费者 | 16 | 谨慎、高品质需求 |
| 老年顾客 | 15 | 不熟悉设备、需要引导 |
| 带伴购物者 | 15 | 有同行者参与决策 |
