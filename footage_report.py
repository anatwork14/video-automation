#!/usr/bin/env python3
"""Measurements + previews to support HUMAN editing decisions. Read-only towards the project.

For each footage scene in timeline.json: source size/duration, black/frozen spans
(typically USGS title cards, logos and slates), detected pillar/letter-box bars,
the earliest start_seconds whose window avoids those spans, and a contact sheet
of that window under output/previews/. It NEVER edits timeline.json and NEVER
approves anything: a reviewer must watch the clip, decide, edit the timeline and
re-approve it (timeline.approved_timeline_sha256).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLACK = "blackdetect=d=0.5:pic_th=0.98:pix_th=0.10"
FREEZE = "freezedetect=n=0.001:d=1.5"
GUARD = 0.25  # seconds kept clear after a detected card/slate


def _ffmpeg(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", *map(str, args)],
                          capture_output=True, text=True)


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,duration:format=duration", "-of", "json", str(src)],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    duration = min(float(data["format"]["duration"]), float(stream.get("duration") or 1e9))
    return int(stream["width"]), int(stream["height"]), duration


def bad_spans(src, duration):
    """Black and frozen spans over the whole source: [(start, end, kind)]."""
    log = _ffmpeg(["-i", src, "-an", "-vf", f"{BLACK},{FREEZE}", "-f", "null", "-"]).stderr
    spans = [(float(a), float(b), "black") for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", log)]
    for k, start in enumerate(starts):
        spans.append((start, ends[k] if k < len(ends) else duration, "frozen"))
    return sorted(spans)


def detect_bars(src, width, height, duration):
    """Pillar-box bars only (constant black side columns over the WHOLE clip).

    cropdetect with reset=0 accumulates the union of non-black content. Vertical
    cropping is never suggested: dark night sky reads as "black" and is genuine content.
    """
    log = _ffmpeg(["-i", src, "-an", "-vf", "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"]).stderr
    found = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", log)
    if not found:
        return None
    w, _, x, _ = map(int, found[-1])
    if w >= 0.9 * width:
        return None
    return {"w": w, "h": height, "x": x, "y": 0}


def suggest_start(spans, duration, length, current=0.0):
    """Earliest start >= current whose [start, start+length] window avoids every span."""
    candidates = sorted({current, *[end + GUARD for _, end, _ in spans if end + GUARD >= current]})
    for start in candidates:
        if start + length > duration:
            continue
        if all(end <= start or begin >= start + length for begin, end, _ in spans):
            return round(start, 2)
    return None


def contact_sheet(src, start, length, target):
    """One frame per second of the proposed window (max 30), so short titles/logos are visible."""
    target.parent.mkdir(parents=True, exist_ok=True)
    result = _ffmpeg(["-ss", start, "-t", min(length, 30), "-i", src, "-an", "-vf",
                      "fps=1,scale=320:-2,tile=6x5", "-frames:v", 1, "-y", target])
    return target if result.returncode == 0 and target.is_file() else None


def report(root=ROOT, previews=True):
    root = Path(root)
    timeline = json.loads((root / "timeline.json").read_text(encoding="utf-8"))
    assets = {a["id"]: a for a in json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]}
    rows = []
    for index, seg in enumerate(timeline["segments"]):
        if seg.get("kind") != "video":
            continue
        item = assets[seg["asset_id"]]
        src = root / "assets" / item["filename"]
        row = {"scene": index, "asset_id": item["id"], "required_seconds": float(seg["duration"]),
               "current_start_seconds": float(seg.get("start_seconds", 0))}
        if not src.is_file():
            row["status"] = "SOURCE NOT DOWNLOADED"
            rows.append(row)
            continue
        width, height, duration = probe(src)
        spans = bad_spans(src, duration)
        length, current = row["required_seconds"], row["current_start_seconds"]
        clean_now = all(end <= current or begin >= current + length for begin, end, _ in spans)
        suggestion = suggest_start(spans, duration, length)
        row.update({
            "source": f"{width}x{height}", "source_seconds": round(duration, 2),
            "black_or_frozen_spans": [{"start": round(a, 2), "end": round(b, 2), "kind": k} for a, b, k in spans],
            "current_window_clean": clean_now,
            "suggested_start_seconds": suggestion,
            "suggested_crop_of_bars": detect_bars(src, width, height, duration),
            "status": "RECOMMENDATION ONLY - a reviewer must watch the window and decide",
            "detector_limits": ("Detects black and frozen frames only. Titles, logos or lower-thirds "
                                "burned onto MOVING footage are invisible to it: check the preview."),
        })
        if previews and suggestion is not None:
            sheet = contact_sheet(src, suggestion, length, root / "output/previews" / f"scene{index:02d}_{item['id']}.png")
            row["preview"] = sheet.relative_to(root).as_posix() if sheet else None
        rows.append(row)
    target = root / "output/previews/footage_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


if __name__ == "__main__":
    for row in report():
        print(json.dumps(row, ensure_ascii=False))
    print("Written output/previews/. These are measurements, NOT decisions: timeline.json was not changed.",
          file=sys.stderr)
