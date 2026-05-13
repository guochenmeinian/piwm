#!/usr/bin/env python3
"""Generate videos from pre-rendered prompt files via Kling API."""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = REPO_ROOT / "data" / "prompts"
VIDEO_DIR = REPO_ROOT / "data" / "video"


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


def find_missing_videos() -> list[Path]:
    """Prompt files that do not yet have a generated video."""
    return [
        path
        for path in sorted(PROMPT_DIR.glob("piwm_*.md"))
        if not (VIDEO_DIR / f"{path.stem}.mp4").exists()
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Generate videos from saved prompt files via Kling API. "
                    "Run without arguments to batch-process prompts without videos."
    )
    parser.add_argument(
        "prompt", nargs="?",
        help="Prompt markdown path (use - for stdin). Omit to batch-process data/prompts/*.md."
    )
    parser.add_argument("--video-dir", default=str(VIDEO_DIR))
    parser.add_argument("--kling-model", default="kling-v2")
    parser.add_argument("--dry-run", action="store_true",
                        help="Batch: list prompt files that would be sent. Single: print prompt metadata only.")
    args = parser.parse_args()

    # ── batch mode ──
    if args.prompt is None:
        pending = find_missing_videos()
        if not pending:
            print("All prompts already have videos.", file=sys.stderr)
            return
        print(f"{'[dry-run] would process' if args.dry_run else 'Processing'} "
              f"{len(pending)} file(s):", file=sys.stderr)
        for f in pending:
            print(f"  {f.name}", file=sys.stderr)
        if args.dry_run:
            return
        for f in pending:
            prompt = f.read_text(encoding="utf-8")
            video_path = call_kling(prompt, f.stem, args.video_dir, args.kling_model)
            print(f"  saved {video_path}", file=sys.stderr)
        return

    # ── single-file mode ──
    if args.prompt == "-":
        prompt = sys.stdin.read()
        session_id = "stdin_prompt"
    else:
        prompt_path = Path(args.prompt)
        prompt = prompt_path.read_text(encoding="utf-8")
        session_id = prompt_path.stem

    if args.dry_run:
        print(f"Would generate video for {session_id} using {args.kling_model}")
        return

    video_path = call_kling(prompt, session_id, args.video_dir, args.kling_model)
    print(f"Video saved to {video_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
