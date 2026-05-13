#!/usr/bin/env python3
"""Render pre-interaction 10s video prompts from manifests or labeled records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"
PROMPT_DIR = REPO_ROOT / "data" / "prompts"

PROMPT_TEMPLATE = """# Goal
生成一段 10 秒、写实自然、单镜头的视频。视频内容是交互发生前的顾客状态片段，用于模拟智能零售设备前置摄像头捕捉到的真实观察画面。

# Camera And Framing
- 视角：设备正面上方前置摄像头，朝外拍摄顾客
- 镜头：固定机位，轻微俯视，不平移，不旋转，不推拉，不变焦
- 构图：顾客位于画面中央附近，头部、面部、上半身、双手持续清晰可见
- 画面：真实商用摄像头质感，光线稳定，无遮挡，无镜头漂移
- 禁止出现机器本体、机器边框、商品、货架、屏幕 UI、价格标签、文字叠层

# Subject Continuity
- 顾客外观在 10 秒内完全一致，不换脸、不换衣、不增减配饰
- 只有一名顾客，无其他人进入画面
- 动作幅度克制，表情自然，不做戏剧化表演

# Character
{persona_visual}
人物背景：{persona}

# Internal State Reference
这些状态只用于约束行为气质，不应直接以文字、符号或 UI 出现在画面里。
- 购买阶段：{aida_stage}
- Belief：{belief}
- Desire：{desire}
- Intention：{intention}

# Observable Performance
- 主要可见行为：{observable_behavior}
- 面部状态：{facial_expression}
- 身体姿态：{body_posture}

# 10-Second Timeline
- 0–2 秒：{t_0_2}
- 2–5 秒：{t_2_5}
- 5–8 秒：{t_5_8}
- 8–10 秒：{t_8_10}

# Motion Quality
- 所有头部、视线、停顿、前倾、手部变化都应缓慢、连续、符合真实顾客行为
- 视线变化要自然，可短暂停留后再移动，不能高频乱跳
- 手部不触碰画面外不存在的具体商品或按钮，不做扫码、付款、取货等已交互动作
- 保持“正在观察和判断”的交互前状态，不展示机器主动响应

# Negative Constraints
- 不出现售货机本体、柜门、商品、货架、二维码、付款界面、促销字幕
- 不出现镜头抖动、剪辑、转场、景别变化、夸张景深变化
- 不出现畸形手部、多余手指、面部扭曲、身体比例突变
- 不出现突然转身离开、突然贴近镜头、夸张点头或明显舞台化动作
"""


def render_prompt(record: dict) -> str:
    timeline = record.get("timeline", {})
    bdi = record.get("bdi", {})
    return PROMPT_TEMPLATE.format(
        persona_visual=record.get("persona_visual", ""),
        persona=record.get("persona", ""),
        aida_stage=record.get("aida_stage", ""),
        belief=bdi.get("belief", ""),
        desire=bdi.get("desire", ""),
        intention=bdi.get("intention", ""),
        observable_behavior=record.get("observable_behavior", ""),
        facial_expression=record.get("facial_expression", ""),
        body_posture=record.get("body_posture", ""),
        t_0_2=timeline.get("t_0_2", ""),
        t_2_5=timeline.get("t_2_5", ""),
        t_5_8=timeline.get("t_5_8", ""),
        t_8_10=timeline.get("t_8_10", ""),
    )


def find_prompt_sources(overwrite: bool = False) -> list[Path]:
    all_ids = {f.stem for f in MANIFEST_DIR.glob("piwm_*.json")}
    result = []
    for stem in sorted(all_ids):
        if not overwrite and (PROMPT_DIR / f"{stem}.md").exists():
            continue
        labeled = LABELED_DIR / f"{stem}.json"
        result.append(labeled if labeled.exists() else MANIFEST_DIR / f"{stem}.json")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render pre-interaction video prompts from manifest/labeled JSON files."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        help="Manifest/labeled JSON path (use - for stdin). Omit to batch-process data/manifest/.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Output path in single-file mode. Default: {PROMPT_DIR}/<id>.md. Use '-' for stdout.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing prompt files in batch mode.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Batch: list files that would be processed. Single: print prompt to stdout.",
    )
    args = parser.parse_args()

    if args.manifest is None:
        pending = find_prompt_sources(overwrite=args.overwrite)
        if not pending:
            print("All manifests already have prompts.", file=sys.stderr)
            return
        print(
            f"{'[dry-run] would process' if args.dry_run else 'Processing'} {len(pending)} file(s):",
            file=sys.stderr,
        )
        for path in pending:
            print(f"  {path.name}", file=sys.stderr)
        if args.dry_run:
            return
        for path in pending:
            record = json.loads(path.read_text(encoding="utf-8"))
            session_id = record.get("session_id", path.stem)
            prompt = render_prompt(record)
            out_path = PROMPT_DIR / f"{session_id}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(prompt, encoding="utf-8")
            print(f"  saved {out_path.name}", file=sys.stderr)
        return

    if args.manifest == "-":
        record = json.load(sys.stdin)
    else:
        with open(args.manifest, "r", encoding="utf-8") as f:
            record = json.load(f)

    prompt = render_prompt(record)
    session_id = record.get("session_id", "unknown")
    if args.output == "-" or args.dry_run:
        print(prompt)
        return

    out_path = Path(args.output) if args.output else PROMPT_DIR / f"{session_id}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt, encoding="utf-8")
    print(f"Prompt saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
