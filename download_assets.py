#!/usr/bin/env python3
"""Download exact USGS-original MP4 files with SHA256; never generate or scrape media."""
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HOST = "usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com"
MAX_BYTES = 1024 * 1024 * 1024  # avoid infinite/unexpected media downloads
assets = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))["assets"]
out_dir = ROOT / "assets"
out_dir.mkdir(exist_ok=True)

failures = 0
for item in assets:
    dst = out_dir / item["filename"]
    if dst.name != item["filename"] or dst.suffix.lower() != ".mp4":
        raise SystemExit("Unsafe manifest filename")
    if urlparse(item["download_url"]).hostname != HOST or item["type"] != "real_video":
        raise SystemExit("Non-USGS or generated asset rejected: " + item["id"])
    if item["license_as_stated_on_source"] != "Public Domain":
        raise SystemExit("Rights are not declared for: " + item["id"])
    if dst.exists() and dst.stat().st_size > 2048:
        print("Already downloaded:", dst.name)
        continue
    partial = dst.with_suffix(".partial")
    h = hashlib.sha256()
    size = 0
    try:
        req = urllib.request.Request(item["download_url"], headers={"User-Agent": "GE1013-real-footage-study/1.0"})
        with urllib.request.urlopen(req, timeout=45) as response:
            if urlparse(response.geturl()).hostname != HOST:
                raise RuntimeError("Unexpected redirect away from approved source")
            with partial.open("wb") as target:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise RuntimeError("Unexpected file larger than 1 GiB")
                    h.update(chunk)
                    target.write(chunk)
        if size < 2048:
            raise RuntimeError("Downloaded file too small to be a video")
        partial.replace(dst)
        dst.with_suffix(".sha256").write_text(h.hexdigest() + "  " + dst.name + "\n", encoding="utf-8")
        print("Saved:", dst.name, size, "bytes", "sha256=" + h.hexdigest())
        if shutil.which("ffprobe"):
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1", str(dst)]
            status = subprocess.run(cmd, capture_output=True, text=True)
            if status.returncode:
                print("WARNING: ffprobe failed:", status.stderr, file=sys.stderr)
    except Exception as exc:
        failures += 1
        partial.unlink(missing_ok=True)
        print("FAILED:", item["id"], str(exc), "\nManual backup source page:", item["source_page"], file=sys.stderr)
print("NOTE: download/hash is not proof of licensing; review.json requires a real human reviewer.")

if failures:
    raise SystemExit(f"{failures} original USGS video download(s) failed. Use source_page for manual download, then retry.")
