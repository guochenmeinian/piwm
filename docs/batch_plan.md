# Batch Generation Plan

每行是一条可直接运行的命令，按需挑选。

```bash
# 用法
python script/gen_manifest.py "<note>"
```

---

## Attention — 顾客刚注意到设备，尚未产生明确兴趣

### 低犹豫
```bash
python script/gen_manifest.py "attention 阶段，犹豫程度低，下班路过的年轻上班族随意扫了一眼机器，步伐放缓但未停下，目光短暂停留"
python script/gen_manifest.py "attention 阶段，犹豫程度低，学生路过时被机器外观吸引，快速打量一眼后继续走，没有驻足意图"
python script/gen_manifest.py "attention 阶段，犹豫程度低，中年男性经过便利区时眼神扫过机器，面部表情中性，身体没有明显转向"
```

### 中犹豫
```bash
python script/gen_manifest.py "attention 阶段，犹豫程度中等，年轻女性被机器吸引后停下脚步，头部微转向机器但身体尚未正面朝向，表情带轻微疑问"
python script/gen_manifest.py "attention 阶段，犹豫程度中等，学生背着书包停在机器前方约一米处，目光在机器上扫视但不确定要不要靠近"
python script/gen_manifest.py "attention 阶段，犹豫程度中等，上班族在机器前短暂停留，目光游移，不确定机器里有没有自己想要的东西"
```

### 高犹豫
```bash
python script/gen_manifest.py "attention 阶段，犹豫程度高，顾客靠近机器后快速扫视，表情略显困惑，身体已经开始转身准备离开"
python script/gen_manifest.py "attention 阶段，犹豫程度高，中年女性站在机器旁边，目光不聚焦，似乎在等人同时随意打量，兴趣低"
```

---

## Interest — 顾客产生兴趣，开始主动观察

### 低犹豫
```bash
python script/gen_manifest.py "interest 阶段，犹豫程度低，男大学生停在机器前，目光积极地在不同区域扫视，身体前倾，表情明显带有兴趣"
python script/gen_manifest.py "interest 阶段，犹豫程度低，年轻上班族站在机器前方，眼神专注，快速浏览选项，动作轻松自然，没有明显迟疑"
python script/gen_manifest.py "interest 阶段，犹豫程度低，女大学生对机器里的饮品明显感兴趣，目光来回停留，嘴角轻微上扬，身体微微前倾"
```

### 中犹豫
```bash
python script/gen_manifest.py "interest 阶段，犹豫程度中等，上班族站在机器前比较两个区域，目光在左右之间来回移动，表情淡漠，似乎精力全都已经被工作耗尽，还没决定看哪个"
python script/gen_manifest.py "interest 阶段，犹豫程度中等，中年男性对机器有兴趣但动作缓慢，目光停留在某处后又移开，像是在思考是否需要"
python script/gen_manifest.py "interest 阶段，犹豫程度中等，学生有购买意愿但反复扫视，表情带思考感，手放在身侧但偶尔轻微抬起"
python script/gen_manifest.py "interest 阶段，犹豫程度中等，年轻女性在机器前驻留较长时间，兴趣明显但动作犹豫，目光不断切换，像在权衡"
```

### 高犹豫
```bash
python script/gen_manifest.py "interest 阶段，犹豫程度高，顾客站在机器前表现出兴趣但频繁转移目光，似乎有顾虑，身体姿态偏向后退"
python script/gen_manifest.py "interest 阶段，犹豫程度高，中年女性对机器感兴趣但面部表情带有担忧，目光在机器和周围环境之间来回，迟迟不靠近"
python script/gen_manifest.py "interest 阶段，犹豫程度高，学生对某个方向有明显兴趣，但身体语言显示不确定，重心轻微后移，后退了一步，表情犹豫"
```

---

## Desire — 顾客已产生购买意愿，进入权衡阶段

### 低犹豫
```bash
python script/gen_manifest.py "desire 阶段，犹豫程度低，上班族已明确想要某款饮料，目光锁定在固定位置，身体前倾，表情平静专注，即将做出决定"
python script/gen_manifest.py "desire 阶段，犹豫程度低，年轻女性想要机器里的某款产品，表情从思考转为确定，目光不再扫视，从口袋拿出了手机"
python script/gen_manifest.py "desire 阶段，犹豫程度低，学生对特定产品有强烈欲望，眼神明确，身体准备好操作，只是还差最后一步确认"
```

### 中犹豫
```bash
python script/gen_manifest.py "desire 阶段，犹豫程度中等，顾客想买但还在比较两个选择，目光在两个方向之间切换，偶尔点头又摇头，手指轻微动作"
python script/gen_manifest.py "desire 阶段，犹豫程度中等，中年男性有明确购买意愿但在做最后确认，目光重复扫同一区域，面部表情显示权衡"
python script/gen_manifest.py "desire 阶段，犹豫程度中等，女性顾客想要某产品但略显犹豫，身体已经靠近但手没有动，目光游移在目标和周边之间"
python script/gen_manifest.py "desire 阶段，犹豫程度中等，学生对选择很感兴趣但面露思考，像是在考虑价格是否合适，手轻微摩挲，迟迟不操作"
```

### 高犹豫
```bash
python script/gen_manifest.py "desire 阶段，犹豫程度高，顾客非常想要但迟迟不行动，表情带有明显纠结，重心反复前后移动，目光在目标上停留后又移开"
python script/gen_manifest.py "desire 阶段，犹豫程度高，中年女性明显想购买但有顾虑，眉头轻微皱起，嘴唇轻抿，手抬起后又放下，像在做艰难决定"
python script/gen_manifest.py "desire 阶段，犹豫程度高，学生对某产品强烈想要但犹豫不决，目光多次回到同一位置，面部表情复杂，动作迟缓"
python script/gen_manifest.py "desire 阶段，犹豫程度高，年轻上班族在机器前反复权衡，身体语言显示挣扎，一只手微微抬起后放下，表情纠结"
```

---

## Action — 顾客已决定，进入购买操作阶段

### 低犹豫
```bash
python script/gen_manifest.py "action 阶段，犹豫程度极低，下班路过的年轻上班族已确认目标，目光锁定，一手自然抬起直接向前，动作干净无来回"
python script/gen_manifest.py "action 阶段，犹豫程度极低，学生已下决心，表情轻松坚定，身体前倾，手臂伸出准备操作，全程无犹豫迹象"
python script/gen_manifest.py "action 阶段，犹豫程度极低，年轻女性表情平静，目光专注在操作区，身体微前倾，手部动作流畅自然，明显是熟悉流程的常客"
python script/gen_manifest.py "action 阶段，犹豫程度极低，中年男性快速完成确认，动作直接，面部表情中性放松，完全没有犹豫或回头确认的迹象"
```

### 中犹豫
```bash
python script/gen_manifest.py "action 阶段，犹豫程度中等，顾客开始操作但中途停顿了一下，目光从操作区短暂移回确认位置，表情略显不确定后继续"
python script/gen_manifest.py "action 阶段，犹豫程度中等，年轻上班族伸手操作时略微迟疑，动作中断了一下，像是临时再看了一眼确认才继续"
python script/gen_manifest.py "action 阶段，犹豫程度中等，学生在最后确认环节停顿，目光在操作区和其他位置之间短暂移动，手部动作稍有犹豫"
```
