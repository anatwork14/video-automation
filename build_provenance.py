"""Deterministic build receipt binds rendered MP4 to exact reviewed inputs and tools.

The receipt contains SHA256 fingerprints and tool versions only, not private
student information. It proves integrity (what went in, what came out), not
authenticity: anyone who can run build.py can write a receipt. Technical
integrity is NOT scientific or licensing approval.
"""
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from review_gate import load_optional_json, recorded_voice_path, sha256_file

RECEIPT = "output/build_manifest.json"
CONFIG = ["assets.json", "claims.json", "narration.json", "timeline.json", "group.json",
          "review.json", "requirements.txt", "reviewers.allowed_signers",
          "assets/logos_from_assignment.png"]
CODE = ["build.py", "build_provenance.py", "download_assets.py", "media_audit.py", "pipeline.py",
        "qa.py", "review_gate.py", "review_hashes.py", "review_signatures.py", "science_gate.py",
        "subtitles.py", "validate.py", "voiceover.py"]


def _optional(root, rel):
    return [rel] if (root / rel).is_file() else []


def inputs_for(root):
    root = Path(root)
    assets = load_optional_json(root / "assets.json", {}).get("assets", [])
    narration = load_optional_json(root / "narration.json", {}).get("segments", [])
    files = list(CONFIG) + list(CODE)  # listed even if absent, so deleting gate code stales the receipt
    files += sorted(p.name for p in root.glob("*.py"))  # plus any other pipeline module
    files += sorted(p.relative_to(root).as_posix() for p in (root / "review.sigs").glob("*.sig"))
    for item in assets:
        base = "assets/" + item["filename"]
        files += [base] + _optional(root, base[:-4] + ".sha256") + _optional(root, base[:-4] + ".provenance.json")
    scene_paths = ["assets/audio/" + f"{int(scene['index']):02d}.mp3" for scene in narration]
    if scene_paths and all((root / p).is_file() for p in scene_paths):
        files += scene_paths
        files += [p[:-4] + ".timings.json" for p in scene_paths if (root / (p[:-4] + ".timings.json")).is_file()]
    else:
        try:
            files.append(recorded_voice_path(root, load_optional_json(root / "group.json", {})).relative_to(root).as_posix())
        except ValueError:
            files.append("group.json")  # invalid path: validate.py blocks the build
    return sorted(set(files))


def snapshot(root):
    root = Path(root)
    return {p: (sha256_file(root / p) if (root / p).is_file() else None) for p in inputs_for(root)}


def _version(cmd):
    if not shutil.which(cmd):
        return None
    out = subprocess.run([cmd, "-version"], capture_output=True, text=True).stdout
    return out.splitlines()[0] if out else None


def tool_versions(font_path=None):
    try:
        from PIL import __version__ as pillow
    except ImportError:
        pillow = None
    return {
        "ffmpeg": _version("ffmpeg"), "ffprobe": _version("ffprobe"),
        "python": platform.python_version(), "pillow": pillow,
        "font_file": Path(font_path).name if font_path else None,
        "font_sha256": sha256_file(font_path) if font_path and Path(font_path).is_file() else None,
    }


def write_build_receipt(root, output, before=None, font_path=None):
    root, output = Path(root), Path(output)
    current = snapshot(root)
    if before is not None and before != current:
        changed = sorted(f for f in set(before) | set(current) if before.get(f) != current.get(f))
        raise ValueError("Inputs changed DURING the render; re-run: " + ", ".join(changed))
    if font_path is None:
        import build
        font_path = build.FONT_PATH
    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "video_file": output.name,
        "video_sha256": sha256_file(output),
        "inputs": current,
        "tools": tool_versions(font_path),
        "status": "DRAFT_NOT_HUMAN_APPROVED",
    }
    target = root / RECEIPT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def verify_build_receipt(root, output):
    root, output = Path(root), Path(output)
    record = root / RECEIPT
    if not record.is_file():
        return ["No build_manifest.json; output may be stale/untraceable"]
    try:
        saved = json.loads(record.read_text(encoding="utf-8"))
        if not isinstance(saved, dict) or not isinstance(saved.get("inputs"), dict):
            return ["build_manifest.json is malformed; re-render"]
        current = snapshot(root)
        errors = []
        for file in sorted(set(saved["inputs"]) | set(current)):
            if saved["inputs"].get(file) != current.get(file):
                errors.append(f"Stale build: input changed or missing: {file}")
        tools = saved.get("tools") if isinstance(saved.get("tools"), dict) else {}
        for name in ("ffmpeg", "ffprobe"):
            if tools.get(name) != _version(name):
                errors.append(f"Stale build: {name} version changed since render")
        if not output.is_file() or saved.get("video_file") != output.name:
            errors.append("Build receipt points to wrong or missing output")
        elif saved.get("video_sha256") != sha256_file(output):
            errors.append("Rendered MP4 differs from build receipt")
        return errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        return ["Could not verify build receipt: " + type(error).__name__]
