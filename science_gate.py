"""Structural evidence registry verification, NOT proof scientific claims are true."""
import json
from pathlib import Path
from urllib.parse import urlparse


def check_claims(root):
    issues = []
    root = Path(root)
    try:
        rows = json.loads((root / "claims.json").read_text(encoding="utf-8"))["claims"]
        scenes = json.loads((root / "timeline.json").read_text(encoding="utf-8"))["segments"]
    except (OSError, ValueError, KeyError) as exc:
        return ["Science evidence registry unavailable: " + str(exc)]
    ids, covered = set(), set()
    for row in rows:
        key = row.get("id")
        if not key or key in ids:
            issues.append("Missing or repeated science claim ID")
        ids.add(key)
        index = row.get("scene")
        if not isinstance(index, int) or not 0 <= index < len(scenes) or scenes[index].get("kind") not in ("intro", "video", "outro"):
            issues.append(f"{key}: invalid video scene index")
        else:
            covered.add(index)
        if len(str(row.get("claim", "")).strip()) < 20:
            issues.append(f"{key}: scientific claim is missing")
        for field in ("reference", "media_reference"):
            if field not in row:
                continue
            parsed = urlparse(row[field])
            if parsed.scheme != "https" or parsed.hostname not in ("www.usgs.gov", "data.usgs.gov"):
                issues.append(f"{key}: evidence link must be HTTPS on an official USGS domain")
        if not row.get("reference") or not row.get("evidence_note"):
            issues.append(f"{key}: source/evidence excerpt missing")
    try:
        narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]
        narrated = {seg.get("index") for seg in narration if str(seg.get("text", "")).strip()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        narrated = set()  # validate.py reports missing/invalid narration itself
    for index, scene in enumerate(scenes):
        if (scene.get("kind") == "video" or index in narrated) and index not in covered:
            issues.append(f"Scene {index} has no scientific evidence")
    return issues
