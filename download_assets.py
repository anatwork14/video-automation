#!/usr/bin/env python3
"""Fail-closed downloader for official original USGS footage.

Only create SHA256 sidecars when THIS script downloads the original HTTPS URL.
Never endorse a pre-existing arbitrary local MP4 by hashing it implicitly.
No network traffic occurs when imported as a Python module.
"""
import argparse
import hashlib
import http.client
import json
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
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


def _rate(value):
    try:
        num, den = str(value).split("/")
        return round(float(num) / float(den), 3) if float(den) else None
    except ValueError:
        return None


def probe_media(file):
    """Summarise a source and prove it is a complete, decodable video BEFORE any provenance is written."""
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg and ffprobe are required to inspect downloaded sources")
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file)],
        capture_output=True, text=True, check=True,
    )
    details = json.loads(p.stdout)
    video = [s for s in details.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in details.get("streams", []) if s.get("codec_type") == "audio"]
    if not video:
        raise RuntimeError("Downloaded source has no video stream")
    container = float(details.get("format", {}).get("duration", 0) or 0)
    stream = float(video[0].get("duration", 0) or 0)
    if container <= 0 or stream <= 0:
        raise RuntimeError("Downloaded source has invalid duration")
    if abs(container - stream) > 1.0:
        raise RuntimeError(f"Container {container:.2f}s vs video stream {stream:.2f}s: truncated or damaged file")
    decode = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-i", str(file),
         "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    if decode.returncode or decode.stderr.strip():
        raise RuntimeError("Video stream does not decode cleanly: " + decode.stderr.strip()[:300])
    return {
        "duration_seconds": round(min(container, stream), 3),
        "width": video[0].get("width"), "height": video[0].get("height"),
        "fps": _rate(video[0].get("avg_frame_rate")), "video_codec": video[0].get("codec_name"),
        "audio_codec": audio[0].get("codec_name") if audio else None,
    }


def provenance_path(media):
    return Path(media).with_suffix(".provenance.json")


def check_provenance(item, dest):
    """The provenance record must describe THIS file from THIS manifest URL."""
    record = provenance_path(dest)
    if not record.is_file():
        raise RuntimeError(f"{dest.name} has no provenance record; move it aside and re-download")
    data = json.loads(record.read_text(encoding="utf-8"))
    if data.get("download_url") != item["download_url"] or data.get("source_page") != item["source_page"]:
        raise RuntimeError(f"{dest.name} was downloaded from a different URL than assets.json now lists")
    if data.get("sha256") != compute_hash(dest) or data.get("bytes") != dest.stat().st_size:
        raise RuntimeError(f"{dest.name} differs from its provenance record")
    return data


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
        check_provenance(item, dest)
        probe_media(dest)
        print("Existing downloaded original verified:", dest.name)
        return dest
    if sidecar.exists() or provenance_path(dest).exists():
        raise RuntimeError(f"Orphan SHA256/provenance record for {dest.name}; investigate source before proceeding")
    partial = directory / (item["filename"] + ".partial")
    partial.unlink(missing_ok=True)
    count = 0
    sha = hashlib.sha256()
    try:
        request = urllib.request.Request(item["download_url"], headers={
            "User-Agent": "GE1013-source-documentary/1.0"
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            final_url = response.geturl()
            if urlparse(final_url).hostname != HOST:
                raise RuntimeError("Download redirected outside approved official media host")
            headers = getattr(response, "headers", None) or {}
            declared = headers.get("Content-Length")
            with partial.open("wb") as output:
                while True:
                    try:
                        chunk = response.read(256 * 1024)
                    except http.client.IncompleteRead as exc:
                        raise RuntimeError(f"Truncated download after {count} bytes") from exc
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > MAX_BYTES:
                        raise RuntimeError("Excessively large MP4; stop downloading")
                    sha.update(chunk)
                    output.write(chunk)
        if declared is not None and str(declared).isdigit() and int(declared) != count:
            raise RuntimeError(f"Truncated download: received {count} of {declared} declared bytes")
        if count < 2048:
            raise RuntimeError("Downloaded file too small to be genuine video")
        media = probe_media(partial)  # complete + decodable BEFORE any provenance is written
        record = {
            "id": item["id"], "source_page": item["source_page"],
            "download_url": item["download_url"], "final_url": final_url,
            "etag": headers.get("ETag"), "last_modified": headers.get("Last-Modified"),
            "content_length": int(declared) if declared is not None and str(declared).isdigit() else None,
            "bytes": count, "sha256": sha.hexdigest(),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "media": media,
            "note": "Transport/technical provenance only; NOT a licence or scientific approval.",
        }
        partial.rename(dest)
        provenance_path(dest).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
