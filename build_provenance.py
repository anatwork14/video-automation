"""Deterministic build receipt binds rendered MP4 to exact reviewed inputs.

The receipt contains SHA256 fingerprints only, not private student information.
Technical integrity is NOT scientific or licensing approval.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from review_gate import sha256_file


def inputs_for(root):
    root = Path(root)
    assets = json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]
    files = [
        "assets.json", "claims.json", "narration.json", "timeline.json",
        "group.json", "review.json", "assets/logos_from_assignment.png",
        "build.py", "subtitles.py", "voiceover.py", "review_gate.py",
        "build_provenance.py", "media_audit.py", "science_gate.py", "pipeline.py",
    ]
    files += ["assets/" + item["filename"] for item in assets]
    scene_paths = ["assets/audio/" + f"{int(scene['index']):02d}.mp3" for scene in narration]
    if scene_paths and all((root / p).is_file() for p in scene_paths):
        files += scene_paths
        files += ["assets/audio/" + f"{int(scene['index']):02d}.timings.json"
                  for scene in narration if (root / "assets/audio" / f"{int(scene['index']):02d}.timings.json").is_file()]
    else:
        files.append("assets/voiceover.wav")
    if (root / "output/captions.srt").is_file():
        files.append("output/captions.srt")
    return sorted(set(files))


def snapshot(root):
    root = Path(root)
    return {p: sha256_file(root / p) for p in inputs_for(root)}


def write_build_receipt(root, output):
    root, output = Path(root), Path(output)
    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "video_file": output.name,
        "video_sha256": sha256_file(output),
        "inputs": snapshot(root),
        "status": "DRAFT_NOT_HUMAN_APPROVED",
    }
    target = root / "output/build_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def verify_build_receipt(root, output):
    root, output = Path(root), Path(output)
    record = root / "output/build_manifest.json"
    if not record.is_file():
        return ["No build_manifest.json; output may be stale/untraceable"]
    try:
        saved = json.loads(record.read_text(encoding="utf-8"))
        current = snapshot(root)
        errors = []
        if saved.get("inputs") != current:
            for file in sorted(set(saved.get("inputs", {})) | set(current)):
                if saved.get("inputs", {}).get(file) != current.get(file):
                    errors.append(f"Stale build: input changed or missing: {file}")
        if not output.is_file() or saved.get("video_file") != output.name:
            errors.append("Build receipt points to wrong or missing output")
        elif saved.get("video_sha256") != sha256_file(output):
            errors.append("Rendered MP4 differs from build receipt")
        return errors
    except (OSError, ValueError, KeyError) as error:
        return ["Could not verify build receipt: " + str(error)]
