#!/usr/bin/env python3
"""Cut each shot exactly where the narration changes subject (prevents misleading juxtapositions).

A shot inside a multi-shot scene may carry `"cue": "<word or phrase>"`: the shot then
starts at the first TTS word boundary matching that cue (after the previous shot's
start). The first shot starts at 0 and the last one ends at the scene end. Durations
are snapped to whole frames and written back into the timeline file, so a reviewer
approves the exact cut points (the timeline hash changes whenever they change).

Usage: python sync_shots.py --root variants/volcano_hazards [timeline file]
"""
import json
import re
import unicodedata

from project import take_root

FPS = 30


def norm(word):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFC", str(word)).lower())


def cue_time(boundaries, cue, after):
    """Start time of the first boundary where the cue begins (TTS may merge tokens, e.g. 'In 2004')."""
    target = norm(cue)
    for k, b in enumerate(boundaries):
        if float(b["start_seconds"]) < after:
            continue
        joined = ""
        for x in boundaries[k:k + 6]:
            joined += norm(x["text"])
            if joined.startswith(target):
                return float(b["start_seconds"])
            if not target.startswith(joined):
                break
    raise ValueError(f"cue {cue!r} not found in the narration word timings after {after:.2f}s")


def sync(root, timeline_name="timeline.json"):
    path = root / timeline_name
    timeline = json.loads(path.read_text(encoding="utf-8"))
    changed = []
    for index, seg in enumerate(timeline["segments"]):
        shots = seg.get("shots") or []
        if not any("cue" in s for s in shots):
            continue
        timings = json.loads((root / "assets/audio" / f"{index:02d}.timings.json").read_text(encoding="utf-8"))
        boundaries = timings["boundaries"]
        starts, after = [0.0], 0.0
        for shot in shots[1:]:
            if "cue" not in shot:
                raise ValueError(f"Scene {index}: once cues are used, every shot after the first needs one")
            after = cue_time(boundaries, shot["cue"], after + 0.01)
            starts.append(after)
        total = round(float(seg["duration"]) * FPS)
        frames = [round(t * FPS) for t in starts] + [total]
        for k, shot in enumerate(shots):
            length = (frames[k + 1] - frames[k]) / FPS
            if length < 1.0:
                raise ValueError(f"Scene {index} shot {k}: only {length:.2f}s; move the cue")
            shot["duration"] = round(length, 4)
        changed.append(index)
    path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv=None):
    root, rest = take_root(argv)
    print("Synced scenes:", sync(root, rest[0] if rest else "timeline.json"))


if __name__ == "__main__":
    main()
