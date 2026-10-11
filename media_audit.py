#!/usr/bin/env python3
"""Verify original footage hash, codec and available length for each scene.

These are deterministic properties. Only a human can verify footage meaning,
licensing and correct source attribution.
"""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def hash_video(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sha256(path):
    sidecar = path.with_suffix(".sha256")
    if not sidecar.is_file():
        raise ValueError(f"Missing {sidecar.name}; run download_assets.py")
    values = sidecar.read_text(encoding="utf-8").strip().split()
    if len(values) != 2 or not re.fullmatch("[0-9a-f]{64}", values[0]) or values[1] != path.name:
        raise ValueError(f"Invalid sha256 sidecar for {path.name}")
    return values[0]


def audit(root=ROOT):
    root = Path(root)
    errors = []
    if not shutil.which("ffprobe"):
        return ["ffprobe binary is unavailable"]
    assets = json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]
    scenes = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    by_id = {a["id"]: a for a in assets}
    windows = []
    for scene in scenes:
        if scene.get("kind") == "video":
            windows.append(scene)
        elif isinstance(scene.get("background"), dict):  # real footage behind an intro/outro card
            windows.append(dict(scene["background"], duration=scene.get("duration")))
    for scene in windows:
        item = by_id.get(scene.get("asset_id"))
        if not item:
            errors.append(f"Unknown scene source {scene.get('asset_id')}")
            continue
        path = root / "assets" / item["filename"]
        if not path.is_file():
            errors.append(f"Source media missing: {path.name}")
            continue
        try:
            if read_sha256(path) != hash_video(path):
                errors.append(f"Source media changed since SHA256 record: {path.name}")
            record = path.with_suffix(".provenance.json")
            if not record.is_file():
                errors.append(f"No provenance record for {path.name}; re-download with download_assets.py")
            else:
                prov = json.loads(record.read_text(encoding="utf-8"))
                if (prov.get("download_url") != item.get("download_url")
                        or prov.get("source_page") != item.get("source_page")):
                    errors.append(f"{path.name}: provenance URL differs from assets.json")
                if prov.get("sha256") != read_sha256(path) or prov.get("bytes") != path.stat().st_size:
                    errors.append(f"{path.name}: provenance record does not match the file")
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                capture_output=True, text=True, check=True,
            )
            metadata = json.loads(r.stdout)
            streams = [x for x in metadata.get("streams", []) if x.get("codec_type") == "video"]
            if not streams:
                errors.append(f"No video stream in source: {path.name}")
                continue
            # Use the shorter of container and video-stream length: never count missing frames.
            duration = min(float(metadata.get("format", {}).get("duration", 0) or 0),
                           float(streams[0].get("duration", 0) or 1e9))
            start = float(scene.get("start_seconds", 0))
            required = float(scene["duration"])
            if start < 0 or duration <= 0:
                errors.append(f"Bad original footage duration/trim: {path.name}")
            elif start + required > duration + .05:
                errors.append(
                    f"FOOTAGE TOO SHORT: {path.name} available={duration-start:.1f}s, "
                    f"required={required:.1f}s. Add VERIFIED sources or shorten scene; do not freeze/loop."
                )
            print(f"VERIFIED FILE: {path.name} {duration:.2f}s "
                  f"{streams[0].get('width')}x{streams[0].get('height')}")
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f"Media could not be validated ({path.name}): {type(exc).__name__}")
    return errors


if __name__ == "__main__":
    found = audit()
    for item in found:
        print("BLOCKED:", item)
    if found:
        raise SystemExit(1)
    print("MEDIA HASH/TECHNICAL GATE PASS; HUMAN SOURCE VERIFICATION STILL REQUIRED.")
