#!/usr/bin/env python3
"""Basic deterministic technical checks. DOES NOT replace human scientific/visual review."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from validate import validate

ROOT = Path(__file__).resolve().parent
output = ROOT / "output" / "GE1013_Kilauea_2018_DRAFT.mp4"
errors = validate(strict=True)
if not shutil.which("ffprobe"):
    errors.append("ffprobe not installed")
elif not output.exists():
    errors.append("Rendered MP4 not found")
else:
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", str(output)], capture_output=True, text=True)
    if probe.returncode:
        errors.append("ffprobe could not open rendered MP4: " + probe.stderr)
    else:
        meta = json.loads(probe.stdout)
        duration = float(meta["format"].get("duration", 0))
        video = [s for s in meta.get("streams", []) if s.get("codec_type") == "video"]
        audio = [s for s in meta.get("streams", []) if s.get("codec_type") == "audio"]
        if not 108 <= duration <= 132:
            errors.append(f"Duration out of range: {duration}")
        if not video or (video[0].get("width"), video[0].get("height")) != (1080, 1920):
            errors.append("Expected 1080x1920 video")
        if not audio:
            errors.append("No audio stream")
        else:
            if int(audio[0].get("sample_rate", 0)) < 16000:
                errors.append("Audio sample rate too low")
        print(f"Probe: duration={duration:.2f}s video={len(video)} audio={len(audio)}")
for problem in errors:
    print("FAIL:", problem, file=sys.stderr)
if errors:
    raise SystemExit(1)
print("TECHNICAL QA PASS. STILL REQUIRED: watch/listen entire MP4, verify claims, logos, credits, captions, and event match.")
