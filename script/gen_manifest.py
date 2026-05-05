#!/usr/bin/env python3
"""Step 1: Generate Manifest JSON via GPT."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
SESSION_PREFIX = "piwm_"
SESSION_START = 700  # piwm_70x range

PROMPT_TEMPLATE = """你是一个有 10 年产业经验的数据合成专家，熟悉零售行为、消费者心理、AIDA 购买阶段、BDI（belief / desire / intention）建模，以及面向视频生成的数据设计。

你的任务是：
为"智能售货机 / 智能冰箱前置摄像头视角下的顾客行为视频生成"构造一条高质量、结构一致、可直接填入视频生成 Prompt Template 的结构化数据。

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

1. 先生成"背景层"：
- persona：顾客画像，简洁但具体
- aida_stage：当前处于 attention / interest / desire / action 之一
- bdi：
  - belief：顾客当前对商品/购买情境的认知或判断
  - desire：顾客当前想达成的目标
  - intention：顾客接下来倾向采取的行为

2. 再生成"外显层（manifest）"：
这些字段必须是上面心理状态在镜头中可被观察到的体现：
- interest_level：购买兴趣强度
- hesitation_level：犹豫程度
- observable_behavior：可见行为特征
- facial_expression：表情状态
- body_posture：身体姿态

3. 再生成"时间线层（timeline）"：
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

{{
  "session_id": "",
  "persona": "",
  "aida_stage": "",
  "bdi": {{
    "belief": "",
    "desire": "",
    "intention": ""
  }},
  "interest_level": "",
  "hesitation_level": "",
  "observable_behavior": "",
  "facial_expression": "",
  "body_posture": "",
  "timeline": {{
    "t_0_2": "",
    "t_2_5": "",
    "t_5_8": "",
    "t_8_10": ""
  }}
}}

# 输出要求
- 只输出 JSON
- 不要输出解释
- 不要输出注释
- 不要输出 Markdown
- 不要复述任务

当前的session_id是{session_id}{extra_note}"""


def render_extra_note(note: str) -> str:
    if not note:
        return ""
    return (
        "\n\n# 额外说明（用户提供的自然语言约束，请严格遵守）\n"
        f"{note}\n"
    )


def generate_manifest(
    session_id: str,
    note: str = None,
    model: str = "gpt-5.5",
) -> dict:
    client = OpenAI()

    prompt = PROMPT_TEMPLATE.format(
        session_id=session_id,
        extra_note=render_extra_note(note),
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    result["session_id"] = session_id
    return result


def next_session_id(start: int = SESSION_START) -> str:
    """Pick next session_id by scanning MANIFEST_DIR for piwm_<N>.json with N >= start."""
    pattern = re.compile(rf"^{re.escape(SESSION_PREFIX)}(\d+)$")
    used = set()
    if MANIFEST_DIR.exists():
        for p in MANIFEST_DIR.glob(f"{SESSION_PREFIX}*.json"):
            m = pattern.match(p.stem)
            if m:
                used.add(int(m.group(1)))
    n = start
    while n in used:
        n += 1
    return f"{SESSION_PREFIX}{n}"


def main():
    parser = argparse.ArgumentParser(description="Step 1: generate manifest JSON via GPT")
    parser.add_argument(
        "note", nargs="?",
        help='自然语言约束，会附在 prompt 底部 (例如: "action 阶段，不犹豫，正在伸手购买")'
    )
    parser.add_argument(
        "--id", dest="session_id",
        help=f"session_id (e.g. piwm_750). 缺省时自动从 {SESSION_PREFIX}{SESSION_START} 起编号"
    )
    parser.add_argument("--model", default="gpt-5.5", help="OpenAI model name")
    parser.add_argument("--dry-run", action="store_true", help="打印最终 prompt，不调用 API")
    parser.add_argument(
        "--output", "-o",
        help=f"输出路径，缺省 {MANIFEST_DIR}/<session_id>.json，'-' 写 stdout"
    )
    args = parser.parse_args()

    session_id = args.session_id or next_session_id()

    if args.dry_run:
        print(PROMPT_TEMPLATE.format(
            session_id=session_id,
            extra_note=render_extra_note(args.note),
        ))
        return

    result = generate_manifest(session_id, args.note, args.model)

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(out)
        return

    out_path = Path(args.output) if args.output else MANIFEST_DIR / f"{session_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
