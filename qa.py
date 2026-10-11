#!/usr/bin/env python3
"""Technical MP4 + build input-integrity checks. Human scientific QA remains mandatory.

Fail-closed: missing tools or unmeasurable audio are errors, not warnings.
Checks: build receipt, 1080x1920 @30 fps, length = timeline, per-scene narration
audibility, digital clipping, and black/frozen frames inside each footage area
(USGS title cards, slates and padding show up here).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from build_provenance import verify_build_receipt
from validate import validate

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
OUTPUT = ROOT / "output/GE1013_Kilauea_2018_DRAFT.mp4"
# build.py normalises the mix to -16 LUFS. A narrated scene measures close to that (EBU R128
# integrated, silence gated out); a -30 LUFS field-audio bed alone, or silence, falls far below.
SPEECH_MIN_LUFS = -24.0
CLIPPED_SAMPLES = 10
BLACK = "blackdetect=d=0.5:pic_th=0.98:pix_th=0.10"
FREEZE = "freezedetect=n=0.001:d=1.5"


def _ffmpeg(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", *map(str, args)],
                          capture_output=True, text=True)


def volume(output, start=None, duration=None):
    window = (["-ss", start, "-t", duration] if start is not None else [])
    result = _ffmpeg([*window, "-i", output, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    mean = re.findall(r"mean_volume:\s*(-?(?:inf|\d+(?:\.\d+)?)) dB", result.stderr)
    peak = re.findall(r"max_volume:\s*(-?(?:inf|\d+(?:\.\d+)?)) dB", result.stderr)
    if result.returncode or not mean or not peak:
        return None
    clipped = re.findall(r"histogram_0db:\s*(\d+)", result.stderr)
    return {"mean": float(mean[-1]), "max": float(peak[-1]), "clipped": int(clipped[-1]) if clipped else 0}


def scene_loudness(output, start, duration):
    """EBU R128 integrated loudness (LUFS) of one window of the rendered file, or None."""
    result = _ffmpeg(["-ss", start, "-t", duration, "-i", output, "-vn", "-af", "ebur128", "-f", "null", "-"])
    level = re.findall(r"I:\s+(-?(?:inf|\d+(?:\.\d+)?)) LUFS", result.stderr)
    if result.returncode or not level:
        return None
    return float(level[-1])


def _probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                             str(path)], capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else None


def footage_rect(source_probe, seg):
    """Where build.py placed the footage inside the 1080x1920 frame (scale-to-fit + pad)."""
    video = [s for s in (source_probe or {}).get("streams", []) if s.get("codec_type") == "video"]
    if not video:
        return None
    width, height = int(video[0]["width"]), int(video[0]["height"])
    if seg.get("crop"):
        width, height = int(seg["crop"]["w"]), int(seg["crop"]["h"])
    scale = min(W / width, H / height)
    w, h = int(width * scale) // 2 * 2, int(height * scale) // 2 * 2
    return w, h, (W - w) // 2, (H - h) // 2


def speech_windows(root, timeline, narration):
    segments = timeline["segments"]
    starts = [sum(float(s["duration"]) for s in segments[:i]) for i in range(len(segments))]
    indices = [int(s["index"]) for s in narration.get("segments", [])]
    if indices and all((root / "assets/audio" / f"{i:02d}.mp3").is_file() for i in indices):
        return [(f"scene {i}", starts[i], float(segments[i]["duration"])) for i in indices]
    intro = float(segments[0]["duration"])
    return [("recorded narration", intro, sum(float(s["duration"]) for s in segments) - intro)]


def run_qa(root=ROOT, output=None):
    """Approval gate + build receipt + technical checks (used before any release)."""
    root = Path(root)
    output = Path(output) if output else root / "output" / OUTPUT.name
    errors = validate(strict=True, root=root)
    errors.extend(verify_build_receipt(root, output))
    return errors + technical_problems(root, output)


def technical_problems(root, output):
    """Media checks only: format, length, audibility, clipping, black/frozen footage, clean decode."""
    root, output = Path(root), Path(output)
    errors = []
    missing = [tool for tool in ("ffprobe", "ffmpeg") if not shutil.which(tool)]
    if missing:
        return errors + [f"{' and '.join(missing)} not installed; audio/video QA cannot run"]
    if not output.is_file():
        return errors + ["Rendered MP4 not found"]
    data = _probe(output)
    if data is None:
        return errors + ["ffprobe cannot open rendered MP4"]
    try:
        timeline = json.loads((root / "timeline.json").read_text(encoding="utf-8"))
        narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))
        assets = {a["id"]: a for a in json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]}
    except (OSError, ValueError, KeyError) as exc:
        return errors + [f"Cannot read project files for QA: {type(exc).__name__}"]
    total = sum(float(s["duration"]) for s in timeline["segments"])
    duration = float(data["format"].get("duration", 0))
    video = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if not 108 <= duration <= 132:
        errors.append(f"Length outside 108–132 seconds: {duration}")
    if abs(duration - total) > 1 / FPS + 0.05:
        errors.append(f"Length {duration:.3f}s differs from timeline {total:.3f}s (truncation or padding)")
    if not video or (video[0].get("width"), video[0].get("height")) != (W, H):
        errors.append("Expected 1080x1920 video")
    elif video[0].get("r_frame_rate") != f"{FPS}/1":
        errors.append(f"Expected {FPS} fps, got {video[0].get('r_frame_rate')}")
    if not audio:
        return errors + ["No audio stream"]
    if int(audio[0].get("sample_rate", 0)) < 16000:
        errors.append("Audio sample rate too low")
    if float(audio[0].get("duration", 0) or 0) < total - 0.05:
        errors.append("Audio stream shorter than the timeline (narration truncated?)")
    print(f"Media probe: {duration:.2f}s; video={len(video)}; audio={len(audio)}")
    decode = _ffmpeg(["-v", "error", "-i", output, "-f", "null", "-"])
    if decode.returncode or decode.stderr.strip():
        errors.append("Rendered MP4 does not decode cleanly: " + decode.stderr.strip()[:200])

    whole = volume(output)
    if whole is None:
        errors.append("Audio level could not be measured; QA cannot pass without a measurement")
    elif whole["clipped"] >= CLIPPED_SAMPLES:
        errors.append(f"Digital clipping: {whole['clipped']} samples at 0 dBFS; lower the narration gain")
    for label, start, length in speech_windows(root, timeline, narration):
        level = scene_loudness(output, start, length)
        if level is None:
            errors.append(f"Could not measure audio for {label}")
        elif level < SPEECH_MIN_LUFS:
            errors.append(f"{label}: narration not audible ({level} LUFS < {SPEECH_MIN_LUFS} LUFS)")
        else:
            print(f"Audio {label}: {level} LUFS")

    start = 0.0
    for index, seg in enumerate(timeline["segments"]):
        length = float(seg["duration"])
        if seg.get("kind") == "video" and seg.get("asset_id") in assets:
            rect = footage_rect(_probe(root / "assets" / assets[seg["asset_id"]]["filename"]), seg)
            if rect is None:
                errors.append(f"Scene {index}: cannot locate footage area for black/freeze QA")
            else:
                w, h, x, y = rect
                result = _ffmpeg(["-ss", start, "-t", length, "-i", output, "-an",
                                  "-vf", f"crop={w}:{h}:{x}:{y},{BLACK},{FREEZE}", "-f", "null", "-"])
                if result.returncode:
                    errors.append(f"Scene {index}: black/freeze detection failed to run")
                for t in re.findall(r"black_start:\s*([\d.]+)", result.stderr):
                    errors.append(f"Scene {index}: black footage from {start + float(t):.2f}s "
                                  "(USGS slate/card? choose another start_seconds)")
                for t in re.findall(r"freeze_start:\s*([\d.]+)", result.stderr):
                    errors.append(f"Scene {index}: frozen footage from {start + float(t):.2f}s "
                                  "(title card or padding? choose another start_seconds)")
        start += length
    return errors


if __name__ == "__main__":
    problems = run_qa()
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print("TECHNICAL AND BUILD-INTEGRITY QA PASS. HUMAN must still check science, footage context and quality.")
