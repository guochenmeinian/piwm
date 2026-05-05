#!/usr/bin/env python3
"""Step 3: Fill Kling prompt template from a manifest, optionally call Kling API."""

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifest"
LABELED_DIR = REPO_ROOT / "data" / "labeled"
PROMPT_DIR = REPO_ROOT / "data" / "prompt"
VIDEO_DIR = REPO_ROOT / "data" / "video"

KLING_TEMPLATE = """# Task
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
"""


def render_prompt(manifest: dict) -> str:
    timeline = manifest.get("timeline", {})
    return KLING_TEMPLATE.format(
        aida_stage=manifest.get("aida_stage", ""),
        interest_level=manifest.get("interest_level", ""),
        hesitation_level=manifest.get("hesitation_level", ""),
        observable_behavior=manifest.get("observable_behavior", ""),
        facial_expression=manifest.get("facial_expression", ""),
        body_posture=manifest.get("body_posture", ""),
        t_0_2=timeline.get("t_0_2", ""),
        t_2_5=timeline.get("t_2_5", ""),
        t_5_8=timeline.get("t_5_8", ""),
        t_8_10=timeline.get("t_8_10", ""),
    )


def call_kling(prompt: str, session_id: str, output_dir: str, model: str = "kling-v2") -> str:
    """Call Kling API to generate video. Stub - fill in with actual SDK / HTTP calls.

    Returns the local path or remote URL of the generated video.
    """
    import requests

    api_key = os.environ.get("KLING_API_KEY")
    if not api_key:
        raise RuntimeError("KLING_API_KEY not set")

    endpoint = os.environ.get("KLING_ENDPOINT", "https://api.klingai.com/v1/videos/text2video")
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": 10,
        "aspect_ratio": "16:9",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    video_url = data.get("video_url") or data.get("data", {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"No video_url in response: {data}")

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{session_id}.mp4")
    with requests.get(video_url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    return out_path


def find_missing_prompts() -> list[Path]:
    """All piwm_* files that don't have a prompt yet. Prefers labeled/ over manifest/."""
    all_ids = {f.stem for f in MANIFEST_DIR.glob("piwm_*.json")}
    result = []
    for stem in sorted(all_ids):
        if (PROMPT_DIR / f"{stem}.md").exists():
            continue
        labeled = LABELED_DIR / f"{stem}.json"
        result.append(labeled if labeled.exists() else MANIFEST_DIR / f"{stem}.json")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Render Kling prompt from manifest and optionally generate video. "
                    "Run without arguments to batch-process all un-prompted labeled files."
    )
    parser.add_argument(
        "manifest", nargs="?",
        help="Manifest/labeled JSON path (use - for stdin). Omit to batch all data/labeled/ → data/prompt/."
    )
    parser.add_argument("-o", "--output",
                        help=f"Output path (single-file mode). Default: {PROMPT_DIR}/<id>.md. Use '-' for stdout.")
    parser.add_argument("--call-kling", action="store_true",
                        help="Call Kling API to generate video (requires KLING_API_KEY)")
    parser.add_argument("--video-dir", default=str(VIDEO_DIR))
    parser.add_argument("--kling-model", default="kling-v2")
    parser.add_argument("--dry-run", action="store_true",
                        help="Batch: list files that would be processed. Single: print prompt to stdout.")
    args = parser.parse_args()

    # ── batch mode ──
    if args.manifest is None:
        pending = find_missing_prompts()
        if not pending:
            print("All labeled files already have prompts.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} file(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        for f in pending:
            manifest = json.loads(f.read_text(encoding="utf-8"))
            session_id = manifest.get("session_id", f.stem)
            prompt = render_prompt(manifest)
            out_path = PROMPT_DIR / f"{session_id}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(prompt, encoding="utf-8")
            print(f"  ✓ {out_path.name}", file=sys.stderr)
            if args.call_kling:
                video_path = call_kling(prompt, session_id, args.video_dir, args.kling_model)
                print(f"    → {video_path}", file=sys.stderr)
        return

    # ── single-file mode ──
    if args.manifest == "-":
        manifest = json.load(sys.stdin)
    else:
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    prompt = render_prompt(manifest)
    session_id = manifest.get("session_id", "unknown")

    if args.output == "-" or args.dry_run:
        print(prompt)
    else:
        out_path = Path(args.output) if args.output else PROMPT_DIR / f"{session_id}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt, encoding="utf-8")
        print(f"Prompt saved to {out_path}", file=sys.stderr)

    if args.call_kling and not args.dry_run:
        video_path = call_kling(prompt, session_id, args.video_dir, args.kling_model)
        print(f"Video saved to {video_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
