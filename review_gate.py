"""Bind every human approval to exact source bytes and scientific text.

Automated validation cannot certify a human actually visited a source page.
It rejects stale approvals, string booleans, unnamed/AI reviewers, and
missing evidence excerpts. All review.json files must stay local.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_object(value):
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def reviewer_problems(entry, valid_names, require_rights=False, require_source=False):
    problems = []
    if type(entry.get("approved")) is not bool or entry["approved"] is not True:
        problems.append("approved must be boolean true")
    if require_rights and entry.get("rights_checked") is not True:
        problems.append("rights_checked must be boolean true")
    if require_source and entry.get("source_read") is not True:
        problems.append("source_read must be boolean true")
    name = entry.get("reviewed_by")
    if not isinstance(name, str) or name not in valid_names or name.lower().strip() in {
        "ai", "chatgpt", "claude", "bot", "automation"
    }:
        problems.append("reviewed_by must exactly match a real registered member name")
    date = entry.get("reviewed_at")
    try:
        if not isinstance(date, str):
            raise ValueError("not a string")
        parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("requires ISO8601 timezone")
    except ValueError:
        problems.append("reviewed_at must be timezone-aware ISO8601")
    return problems


def audio_evidence(root, narration):
    """Return content digest + errors for scene TTS/manual scene/recorded voice."""
    root = Path(root)
    errors = []
    scripts = narration.get("segments", [])
    files = [root / "assets" / "audio" / f"{int(seg['index']):02d}.mp3" for seg in scripts]
    timing_files = [p.with_suffix(".timings.json") for p in files]
    recorded = root / "assets" / "voiceover.wav"
    script_hash = sha256_file(root / "narration.json")
    if scripts and all(p.is_file() for p in files):
        found = [p.is_file() for p in timing_files]
        if any(found) and not all(found):
            errors.append("Some scene voice tracks have TTS timings but others do not")
        mode = "edge_tts" if all(found) else "manual_scene"
        digests = []
        for scene, media, timing in zip(scripts, files, timing_files):
            digests.append({"file": media.name, "sha256": sha256_file(media)})
            if timing.exists():
                try:
                    metadata = json.loads(timing.read_text(encoding="utf-8"))
                    expected = hashlib.sha256(scene["text"].encode("utf-8")).hexdigest()
                    if metadata.get("text_sha256") != expected:
                        errors.append(f"STALE AUDIO: scene {scene['index']} TTS generated from different narration")
                    if metadata.get("provider") != "edge-tts":
                        errors.append(f"Unknown audio timing provider: scene {scene['index']}")
                    if not metadata.get("boundaries"):
                        errors.append(f"Missing voice timestamp boundaries in scene {scene['index']}")
                    digests.append({"file": timing.name, "sha256": sha256_file(timing)})
                except (OSError, ValueError, KeyError) as exc:
                    errors.append(f"Bad TTS metadata for scene {scene['index']}: {exc}")
        return {"mode": mode, "sha256": sha256_object({
            "script_sha256": script_hash, "mode": mode, "files": digests
        })}, errors
    if any(p.exists() for p in files) or any(p.exists() for p in timing_files):
        errors.append("Incomplete/ambiguous scene audio; regenerate ALL scenes or remove stale files")
        return None, errors
    if recorded.is_file():
        return {"mode": "recorded_voice", "sha256": sha256_object({
            "script_sha256": script_hash, "mode": "recorded_voice",
            "files": [{"file": recorded.name, "sha256": sha256_file(recorded)}]
        })}, errors
    return None, ["Missing original voice recording or complete scene audio"]


def evidence_hashes(root, assets, claims, narration):
    root = Path(root)
    result = {"narration_sha256": sha256_file(root / "narration.json"), "assets": {}, "claims": {}}
    for a in assets:
        media = root / "assets" / a["filename"]
        result["assets"][a["id"]] = {
            "approved_manifest_sha256": sha256_object(a),
            "approved_media_sha256": sha256_file(media) if media.is_file() else None,
        }
    for claim in claims:
        result["claims"][claim["id"]] = {"approved_claim_sha256": sha256_object(claim)}
    logo = root / "assets" / "logos_from_assignment.png"
    result["logo_sha256"] = sha256_file(logo) if logo.is_file() else None
    result["audio"], result["audio_errors"] = audio_evidence(root, narration)
    return result


def check_reviews(root, group, review, assets, claims, narration):
    root = Path(root)
    valid_names = {m.get("name") for m in group.get("team_members", [])
                   if isinstance(m, dict) and isinstance(m.get("name"), str)}
    errors = []
    values = evidence_hashes(root, assets, claims, narration)
    for a in assets:
        aid = a["id"]
        row = review.get("assets", {}).get(aid, {})
        errors.extend(f"Asset {aid}: {p}" for p in reviewer_problems(
            row, valid_names, require_rights=True
        ))
        for field, expected in values["assets"][aid].items():
            if expected is None or row.get(field) != expected:
                errors.append(f"Asset {aid}: missing/stale {field}")
        if a.get("manual_source_review_required") is not True:
            errors.append(f"Asset {aid}: manual source review flag missing or not boolean true")
        if not isinstance(row.get("rights_evidence_excerpt"), str) or len(row["rights_evidence_excerpt"].strip()) < 20:
            errors.append(f"Asset {aid}: add the precise rights evidence from its source page")
    for c in claims:
        cid = c["id"]
        row = review.get("claims", {}).get(cid, {})
        errors.extend(f"Claim {cid}: {p}" for p in reviewer_problems(
            row, valid_names, require_source=True
        ))
        if row.get("approved_claim_sha256") != values["claims"][cid]["approved_claim_sha256"]:
            errors.append(f"Claim {cid}: text/source has changed since approval")
        if not isinstance(row.get("source_excerpt"), str) or len(row["source_excerpt"].strip()) < 20:
            errors.append(f"Claim {cid}: requires precise primary source excerpt (human checked)")
    script = review.get("script", {})
    errors.extend("Script: " + p for p in reviewer_problems(script, valid_names))
    if script.get("approved_narration_sha256") != values["narration_sha256"]:
        errors.append("Script text changed since approval")
    if review.get("script_reviewed") is not True:
        errors.append("script_reviewed must be boolean true")
    logos = review.get("logos", {})
    errors.extend("Logos: " + p for p in reviewer_problems(logos, valid_names))
    if logos.get("approved_sha256") != values["logo_sha256"] or not values["logo_sha256"]:
        errors.append("Logo bytes changed or missing since approval")
    if review.get("course_logos_reviewed") is not True:
        errors.append("course_logos_reviewed must be boolean true")
    if group.get("language") == "en" and review.get("english_language_reviewed") is not True:
        errors.append("english_language_reviewed must be boolean true")
    errors.extend(values["audio_errors"])
    audio = review.get("audio", {})
    errors.extend("Audio: " + p for p in reviewer_problems(audio, valid_names))
    if not values["audio"] or audio.get("approved_audio_digest") != values["audio"]["sha256"]:
        errors.append("Audio bytes and/or narration changed since approval")
    if values["audio"] and audio.get("mode") != values["audio"]["mode"]:
        errors.append("Audio mode must match actual input (edge_tts/manual_scene/recorded_voice)")
    return errors
