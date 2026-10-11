#!/usr/bin/env python3
"""One-command preparation and guarded rendering. No automatic approval or publishing."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def step(*args):
    print("\n==>", " ".join(map(str, args)), flush=True)
    subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser(description="Real-footage-only GE1013 video automation")
    ap.add_argument("stage", choices=["prepare", "render", "all"])
    ap.add_argument("--assignment-pdf", type=Path, help="Local course PDF for extracting logos (never committed)")
    ap.add_argument("--tts", action="store_true", help="Optional paid OpenAI speech; no AI imagery/video")
    ap.add_argument("--no-subtitles", action="store_true", help="Do not burn rough-timed SRT")
    args = ap.parse_args()

    if args.stage in {"prepare", "all"}:
        step("validate.py")
        step("download_assets.py")
        if args.assignment_pdf:
            step("extract_logos.py", args.assignment_pdf.resolve())
        if args.tts:
            step("voiceover.py")
        step("subtitles.py")
        print("\nPREPARE COMPLETE (or missing downloads reported above).")
        print("NEXT: group.json and review.json must be filled/approved by real humans.")
    if args.stage in {"render", "all"}:
        step("validate.py", "--strict")  # deliberately BLOCKS when approvals are absent
        cmd = ["build.py"]
        if args.no_subtitles:
            cmd.append("--no-subtitles")
        step(*cmd)
        step("qa.py")
        print("\nDRAFT GENERATED AND TECHNICALLY CHECKED. Publication is MANUAL after watching it.")


if __name__ == "__main__":
    main()
