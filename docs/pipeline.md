
## Pipeline
1. GPT5.5 生成 Manifest（依次生成 BDI、用户行为信息、具体Timeline表现）
2. 专家模型打ground truth（candidate_actions + expected_action）
3. 填充kling prompt模版 生成视频

### Manifest

生成的template
```json
{
  // # turn 1 GPT 5.5
  
  "session_id": "xxx",
  // 1. 背景
  "persona": "",               // [...]
  "aida_stage": "interest",    // [...]
  "bdi": {
    "belief": "",              // A companion's approval may influence whether the choice feels safe
    "desire": "",              //"see how the product works"
    "intention": "",           // ask for a demonstration"
  },
  
  // 2. manifest
  "interest_level": "",        // 较高，愿意停留继续观察
  "hesitation_level": "",      // interest / desire 之间，已产生明显兴趣但尚未决定购买
  "observable_behavior": "",   // 中等偏高，正在比较和确认信息
  "facial_expression": "",     // 走近后停留，身体轻微前倾，目光在机器前方不同区域之间切换
  "body_posture": "",          // 轻微思考、权衡、犹豫，没有夸张表情
  
  // 3. 视频生成
  "timeline": {
    "t_0_2": "",
    "t_2_5": "",
    "t_5_8": "",
    "t_8_10": ""
  },
  
  
  
  // # turn 2 专家模型
  
  // 4. action space / prediction
  "candidate_actions": [
      "Ax_xxx",
      "Ax_xxx",
      "Ax_xxx",
      "Ax_xxx"
  ],
  "best_action": "Ax_xxx"
}
```

生成出来的sample
```json
{
    "session_id": "piwm_00000001",
    "persona": "一名下班后路过便利区的年轻上班族，想快速买一瓶常喝的饮料解渴。",
    "aida_stage": "action",
    "bdi": {
        "belief": "顾客已经确认眼前设备里有自己熟悉且合适的饮品，认为这次购买风险低、决策成本低。",
        "desire": "尽快买到一瓶能马上喝的饮料，减少停留时间。",
        "intention": "短暂确认后直接完成选择，并准备伸手操作购买。"
    },
    "interest_level": "高",
    "hesitation_level": "低",
    "observable_behavior": "顾客目光集中在固定位置，扫视范围很小，很快点头确认，双手从放松状态转为准备操作。",
    "facial_expression": "表情平静但明确，眉眼放松，嘴角轻微收起，呈现已做出决定的状态。",
    "body_posture": "身体正面朝向镜头，微微前倾，肩膀放松，一只手自然抬起靠近操作区域。",
    "timeline": {
        "t_0_2": "顾客走近后停在画面中央，目光迅速落向前方偏下位置，表情平静专注。",
        "t_2_5": "顾客只做短暂扫视，眼神很快固定在同一方向，头部轻微点一下，像是确认了目标。",
        "t_5_8": "顾客身体微微前倾，一只手从身侧抬起，动作干净直接，没有明显来回比较。",
        "t_8_10": "顾客保持目光稳定，手继续向前准备操作，表情自然坚定，呈现即将购买的状态。"
    }
}
```

生成用的提示词
```md
你是一个有 10 年产业经验的数据合成专家，熟悉零售行为、消费者心理、AIDA 购买阶段、BDI（belief / desire / intention）建模，以及面向视频生成的数据设计。

你的任务是：
为“智能售货机 / 智能冰箱前置摄像头视角下的顾客行为视频生成”构造一条高质量、结构一致、可直接填入视频生成 Prompt Template 的结构化数据。

# 总目标
请围绕一个顾客在零售设备前停留、观察、比较、犹豫的短时片段，生成一条完整样本。
该样本将被用于后续视频生成，因此你输出的字段必须：
- 内部语义一致
- 符合零售场景常识
- 符合 AIDA 阶段定义
- 能通过外显行为、表情和姿态体现出来
- 能自然映射为一个 10 秒视频片段

# 生成流程
请按以下顺序思考并生成：

1. 先生成“背景层”：
- persona：顾客画像，简洁但具体
- aida_stage：当前处于 attention / interest / desire / action 之一
- bdi：
  - belief：顾客当前对商品/购买情境的认知或判断
  - desire：顾客当前想达成的目标
  - intention：顾客接下来倾向采取的行为

2. 再生成“外显层（manifest）”：
这些字段必须是上面心理状态在镜头中可被观察到的体现：
- interest_level：购买兴趣强度
- hesitation_level：犹豫程度
- observable_behavior：可见行为特征
- facial_expression：表情状态
- body_posture：身体姿态

3. 再生成“时间线层（timeline）”：
生成一个 10 秒视频分段脚本：
- 0–2 秒
- 2–5 秒
- 5–8 秒
- 8–10 秒

# 场景约束
以下约束默认成立，不需要在生成字段中重复解释，但生成内容必须兼容这些约束：
- 视频时长 10 秒
- 单镜头、固定机位、无剪辑、写实自然风格
- 镜头来自智能售货机或智能冰箱正面上方的前置摄像头
- 第一人称视角，轻微俯视，固定机位，不晃动，不变焦
- 摄像头朝外拍摄顾客，视野完全不受遮挡
- 画面中清晰可见顾客的面部、目光方向、细微表情、上半身和双手
- 顾客始终位于画面中央附近，正面朝向镜头，面部无遮挡
- 画面中不需要出现机器本体、屏幕内容、商品、货架、价格标签或任何商品信息
- 室内零售环境，明亮自然照明，背景干净、安静、日常
- 无人与顾客互动，无对白，无字幕，无杂音
- 无夸张表情、无夸张动作、无表演感

# 字段说明
请严格输出以下 JSON 字段：
- session_id：唯一字符串，格式类似 "piwm_xxxxxxxx"
- persona：一句话顾客画像
- aida_stage：只能是 "attention" / "interest" / "desire" / "action"
- bdi：
  - belief：顾客当前对商品或购买情境的认知
  - desire：顾客当前想达成的目标
  - intention：顾客接下来倾向采取的行为
- interest_level：购买兴趣强度
- hesitation_level：犹豫程度
- observable_behavior：镜头中可见的行为特征
- facial_expression：表情状态
- body_posture：身体姿态
- timeline：10 秒视频分段脚本，每段 1 句

# 输出格式
只输出 JSON，对象结构如下：

{
  "session_id": "",
  "persona": "",
  "aida_stage": "",
  "bdi": {
    "belief": "",
    "desire": "",
    "intention": ""
  },
  "interest_level": "",
  "hesitation_level": "",
  "observable_behavior": "",
  "facial_expression": "",
  "body_posture": "",
  "timeline": {
    "t_0_2": "",
    "t_2_5": "",
    "t_5_8": "",
    "t_8_10": ""
  }
}

# 输出要求
- 只输出 JSON
- 不要输出解释
- 不要输出注释
- 不要输出 Markdown
- 不要复述任务


当前的session_id是{session_id}

```



### Kling

生成提示词
```
# Task
请生成一段 10 秒、单镜头、固定机位、无剪辑、写实自然风格的视频。

# Camera
镜头来自智能售货机或智能冰箱正面上方的前置摄像头。第一人称视角，轻微俯视，固定机位，不晃动，不变焦。摄像头朝外拍摄顾客，视野完全不受遮挡。画面中清晰可见顾客的面部、目光方向、细微表情、上半身和双手。顾客始终位于画面中央附近，正面朝向镜头，面部无遮挡，双手始终在画面内。画面中不需要出现机器本体、屏幕内容、商品、货架、价格标签或任何商品信息。

# Scene
室内零售环境，明亮自然的展示照明，背景干净、安静、日常。无人与顾客互动，无对白，无字幕，无杂音。

# Behavior State
- 当前购买阶段：{aida_stage}
- 购买兴趣强度：{interest_level}
- 犹豫程度：{hesitation_level}
- 主要可见行为：{observable_behavior}
- 表情状态：{facial_expression}
- 身体姿态：{body_posture}

# Timeline
- 0–2 秒：{t_0_2}
- 2–5 秒：{t_2_5}
- 5–8 秒：{t_5_8}
- 8–10 秒：{t_8_10}

# Constraints
- 顾客必须始终正面可见
- 面部无遮挡，五官清晰
- 不能出现任何商品、货架、价格标签、机器本体或屏幕 UI
- 无其他人介入交互
- 无夸张表情、无夸张动作、无表演感
- 整体效果像真实零售设备前置摄像头记录到的顾客浏览片段
```

