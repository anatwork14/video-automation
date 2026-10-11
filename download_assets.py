#!/usr/bin/env python3
"""Fail-closed downloader for official original USGS footage.

Only create SHA256 sidecars when THIS script downloads the original HTTPS URL.
Never endorse a pre-existing arbitrary local MP4 by hashing it implicitly.
No network traffic occurs when imported as a Python module.
"""
import argparse
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
MAX_BYTES = 1024 * 1024 * 1024


def allowed_original(item):
    remote = urlparse(item.get("download_url", ""))
    source = urlparse(item.get("source_page", ""))
    if remote.scheme != "https" or remote.hostname != HOST:
        raise ValueError(f"Only the approved USGS original host is allowed for {item.get('id')}")
    if source.scheme != "https" or source.hostname != "www.usgs.gov":
        raise ValueError(f"Missing official USGS source page for {item.get('id')}")
    filename = item.get("filename", "")
    if Path(filename).name != filename or not filename.endswith(".mp4"):
        raise ValueError(f"Unsafe original filename: {filename}")
    if item.get("type") != "real_video" or item.get("manual_source_review_required") is not True:
        raise ValueError("Only genuine video requiring manual review may be downloaded")


def compute_hash(file):
    sha = hashlib.sha256()
    with Path(file).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def probe_media(file):
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is required to inspect downloaded sources")
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file)],
        capture_output=True, text=True, check=True,
    )
    details = json.loads(p.stdout)
    if not any(s.get("codec_type") == "video" for s in details.get("streams", [])):
        raise RuntimeError("Downloaded source has no video stream")
    if float(details.get("format", {}).get("duration", 0)) <= 0:
        raise RuntimeError("Downloaded source has invalid duration")


def get_one(item, root=ROOT):
    allowed_original(item)
    directory = Path(root) / "assets"
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / item["filename"]
    sidecar = dest.with_suffix(".sha256")
    if dest.is_file():
        if not sidecar.is_file():
            raise RuntimeError(
                f"{dest.name} already exists WITHOUT provenance hash. "
                "Inspect the official USGS source; move this file aside, then run downloader again. "
                "Never auto-trust manually substituted footage."
            )
        expected = sidecar.read_text(encoding="utf-8").strip()
        actual = compute_hash(dest) + "  " + dest.name
        if expected != actual:
            raise RuntimeError(f"{dest.name} differs from recorded SHA256; investigate, do NOT overwrite")
        probe_media(dest)
        print("Existing downloaded original verified:", dest.name)
        return dest
    if sidecar.exists():
        raise RuntimeError(f"Orphan SHA256 sidecar: {sidecar.name}; investigate source before proceeding")
    partial = directory / (item["filename"] + ".partial")
    partial.unlink(missing_ok=True)
    count = 0
    sha = hashlib.sha256()
    try:
        request = urllib.request.Request(item["download_url"], headers={
            "User-Agent": "GE1013-source-documentary/1.0"
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            if urlparse(response.geturl()).hostname != HOST:
                raise RuntimeError("Download redirected outside approved official media host")
            with partial.open("wb") as output:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > MAX_BYTES:
                        raise RuntimeError("Excessively large MP4; stop downloading")
                    sha.update(chunk)
                    output.write(chunk)
        if count < 2048:
            raise RuntimeError("Downloaded file too small to be genuine video")
        probe_media(partial)
        partial.rename(dest)
        sidecar.write_text(sha.hexdigest() + "  " + dest.name + "\n", encoding="utf-8")
        print("Downloaded official source:", dest.name, count, "bytes")
        return dest
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()
    assets = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))["assets"]
    failures = []
    for item in assets:
        try:
            get_one(item)
        except Exception as exc:
            failures.append(f"{item.get('id')}: {exc}; source page: {item.get('source_page')}")
    if failures:
        for issue in failures:
            print("BLOCKED:", issue, file=sys.stderr)
        raise SystemExit(f"{len(failures)} source downloads/validations failed")
    print("All ORIGINALS passed transport/hash/media checks. This DOES NOT certify licensing or scientific context.")


if __name__ == "__main__":
    main()
