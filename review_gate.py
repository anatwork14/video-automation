"""Bind every human approval to exact source bytes, scientific text and edit decisions.

Automated validation cannot certify a human actually visited a source page.
It rejects stale approvals, string booleans, unnamed/AI reviewers, future
timestamps, approvals for removed claims and missing evidence excerpts.
Signatures over review.json are verified separately (review_signatures.py).
All review.json files must stay local.
"""
import hashlib
import json
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

DEFAULT_VOICE = "assets/voiceover.wav"
VOICE_SUFFIXES = (".wav", ".mp3", ".m4a", ".flac")
AI_NAMES = {"ai", "chatgpt", "claude", "bot", "automation"}
CLOCK_SKEW = timedelta(minutes=10)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _nfc(value):
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(v) for v in value]
    if isinstance(value, dict):
        return {_nfc(k): _nfc(v) for k, v in value.items()}
    return value


def sha256_object(value):
    """Canonical JSON digest: key order, whitespace, line endings and NFC/NFD do not matter."""
    canonical = json.dumps(_nfc(value), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def text_sha256(text):
    """Digest of narration text as spoken (NFC, surrounding whitespace ignored).

    voiceover.py, subtitles.py and this gate MUST share this function.
    """
    return hashlib.sha256(unicodedata.normalize("NFC", str(text)).strip().encode("utf-8")).hexdigest()


def load_optional_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def recorded_voice_path(root, group=None):
    """Resolve group.json narration_audio_file. One rule for gate, build, receipt and QA."""
    raw = (group if isinstance(group, dict) else {}).get("narration_audio_file", DEFAULT_VOICE)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("narration_audio_file must be a relative path under assets/")
    rel = PurePosixPath(raw.strip().replace("\\", "/"))
    if (rel.is_absolute() or ".." in rel.parts or len(rel.parts) < 2 or rel.parts[0] != "assets"
            or rel.suffix.lower() not in VOICE_SUFFIXES):
        raise ValueError(f"narration_audio_file {raw!r} must be assets/<name> with one of "
                         + ", ".join(VOICE_SUFFIXES))
    root = Path(root)
    path = root.joinpath(*rel.parts)
    if path.exists() and (root / "assets").resolve() not in path.resolve().parents:
        raise ValueError(f"narration_audio_file {raw!r} resolves outside assets/")
    return path


def reviewer_problems(entry, valid_names, require_rights=False, require_source=False, now=None):
    if not isinstance(entry, dict):
        return ["review entry must be a JSON object"]
    problems = []
    if entry.get("approved") is not True:
        problems.append("approved must be boolean true")
    if require_rights and entry.get("rights_checked") is not True:
        problems.append("rights_checked must be boolean true")
    if require_source and entry.get("source_read") is not True:
        problems.append("source_read must be boolean true")
    name = entry.get("reviewed_by")
    if (not isinstance(name, str) or not name.strip() or name not in valid_names
            or name.lower().strip() in AI_NAMES):
        problems.append("reviewed_by must exactly match a real registered member name")
    date = entry.get("reviewed_at")
    try:
        if not isinstance(date, str):
            raise ValueError("not a string")
        parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("requires ISO8601 timezone")
        if parsed > (now or datetime.now(timezone.utc)) + CLOCK_SKEW:
            problems.append("reviewed_at is in the future")
    except ValueError:
        problems.append("reviewed_at must be timezone-aware ISO8601")
    return problems


def audio_evidence(root, narration, group=None):
    """Return content digest + errors for scene TTS/manual scene/recorded voice."""
    root = Path(root)
    if group is None:
        group = load_optional_json(root / "group.json", {})
    errors = []
    scripts = narration.get("segments", [])
    files = [root / "assets" / "audio" / f"{int(seg['index']):02d}.mp3" for seg in scripts]
    timing_files = [p.with_suffix(".timings.json") for p in files]
    script_hash = sha256_object(narration)
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
                    if metadata.get("text_sha256") != text_sha256(scene["text"]):
                        errors.append(f"STALE AUDIO: scene {scene['index']} TTS generated from different narration")
                    if metadata.get("provider") != "edge-tts":
                        errors.append(f"Unknown audio timing provider: scene {scene['index']}")
                    if not metadata.get("boundaries"):
                        errors.append(f"Missing voice timestamp boundaries in scene {scene['index']}")
                    digests.append({"file": timing.name, "sha256": sha256_file(timing)})
                except (OSError, ValueError, KeyError, AttributeError) as exc:
                    errors.append(f"Bad TTS metadata for scene {scene['index']}: {type(exc).__name__}")
        return {"mode": mode, "sha256": sha256_object({
            "script_sha256": script_hash, "mode": mode, "files": digests
        })}, errors
    if any(p.exists() for p in files) or any(p.exists() for p in timing_files):
        errors.append("Incomplete/ambiguous scene audio; regenerate ALL scenes or remove stale files")
        return None, errors
    try:
        recorded = recorded_voice_path(root, group)
    except ValueError as exc:
        return None, [str(exc)]
    rel = recorded.relative_to(root).as_posix()
    if recorded.is_file():
        return {"mode": "recorded_voice", "path": rel, "sha256": sha256_object({
            "script_sha256": script_hash, "mode": "recorded_voice",
            "files": [{"file": rel, "sha256": sha256_file(recorded)}]
        })}, errors
    return None, [f"Missing complete scene audio or recorded voice {rel}"]


def claim_set_sha256(claims):
    return sha256_object(sorted([str(c.get("id")), c.get("scene")] for c in claims))


def evidence_hashes(root, assets, claims, narration, group=None, timeline=None):
    root = Path(root)
    if timeline is None:
        timeline = load_optional_json(root / "timeline.json")
    result = {
        "narration_sha256": sha256_object(narration),
        "claim_set_sha256": claim_set_sha256(claims),
        "timeline_sha256": sha256_object(timeline) if timeline is not None else None,
        "assets": {}, "claims": {},
    }
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
    result["audio"], result["audio_errors"] = audio_evidence(root, narration, group)
    return result


def _section(review, key, errors):
    value = review.get(key, {})
    if not isinstance(value, dict):
        errors.append(f"review.json '{key}' must be a JSON object")
        return {}
    return value


def check_reviews(root, group, review, assets, claims, narration, timeline=None, now=None):
    root = Path(root)
    if not isinstance(review, dict):
        return ["review.json must be a JSON object"]
    members = group.get("team_members", []) if isinstance(group, dict) else []
    valid_names = {m["name"] for m in members if isinstance(m, dict)
                   and isinstance(m.get("name"), str) and m["name"].strip()}
    errors = []
    values = evidence_hashes(root, assets, claims, narration, group, timeline)
    asset_rows = _section(review, "assets", errors)
    claim_rows = _section(review, "claims", errors)
    for a in assets:
        aid = a["id"]
        row = asset_rows.get(aid, {})
        errors.extend(f"Asset {aid}: {p}" for p in reviewer_problems(
            row, valid_names, require_rights=True, now=now
        ))
        row = row if isinstance(row, dict) else {}
        for field, expected in values["assets"][aid].items():
            if expected is None or row.get(field) != expected:
                errors.append(f"Asset {aid}: missing/stale {field}")
        if a.get("manual_source_review_required") is not True:
            errors.append(f"Asset {aid}: manual source review flag missing or not boolean true")
        if not isinstance(row.get("rights_evidence_excerpt"), str) or len(row["rights_evidence_excerpt"].strip()) < 20:
            errors.append(f"Asset {aid}: add the precise rights evidence from its source page")
    for aid in sorted(set(asset_rows) - {a["id"] for a in assets}):
        errors.append(f"Asset approval {aid} has no matching asset in assets.json; remove or re-review")
    for c in claims:
        cid = c["id"]
        row = claim_rows.get(cid, {})
        errors.extend(f"Claim {cid}: {p}" for p in reviewer_problems(
            row, valid_names, require_source=True, now=now
        ))
        row = row if isinstance(row, dict) else {}
        if row.get("approved_claim_sha256") != values["claims"][cid]["approved_claim_sha256"]:
            errors.append(f"Claim {cid}: text/source has changed since approval")
        if not isinstance(row.get("source_excerpt"), str) or len(row["source_excerpt"].strip()) < 20:
            errors.append(f"Claim {cid}: requires precise primary source excerpt (human checked)")
    for cid in sorted(set(claim_rows) - {c["id"] for c in claims}):
        errors.append(f"Claim approval {cid} has no matching claim in claims.json (removed?); re-review the claim set")
    script = _section(review, "script", errors)
    errors.extend("Script: " + p for p in reviewer_problems(script, valid_names, now=now))
    if script.get("approved_narration_sha256") != values["narration_sha256"]:
        errors.append("Script text changed since approval")
    if script.get("approved_claim_set_sha256") != values["claim_set_sha256"]:
        errors.append("Claim set (IDs/scenes) changed since script approval")
    if review.get("script_reviewed") is not True:
        errors.append("script_reviewed must be boolean true")
    edit = _section(review, "timeline", errors)
    errors.extend("Timeline: " + p for p in reviewer_problems(edit, valid_names, now=now))
    if not values["timeline_sha256"] or edit.get("approved_timeline_sha256") != values["timeline_sha256"]:
        errors.append("Timeline (clip order, start_seconds, crop, on-screen text) changed since approval")
    logos = _section(review, "logos", errors)
    errors.extend("Logos: " + p for p in reviewer_problems(logos, valid_names, now=now))
    if logos.get("approved_sha256") != values["logo_sha256"] or not values["logo_sha256"]:
        errors.append("Logo bytes changed or missing since approval")
    if review.get("course_logos_reviewed") is not True:
        errors.append("course_logos_reviewed must be boolean true")
    if isinstance(group, dict) and group.get("language") == "en" and review.get("english_language_reviewed") is not True:
        errors.append("english_language_reviewed must be boolean true")
    errors.extend(values["audio_errors"])
    audio = _section(review, "audio", errors)
    errors.extend("Audio: " + p for p in reviewer_problems(audio, valid_names, now=now))
    if not values["audio"] or audio.get("approved_audio_digest") != values["audio"]["sha256"]:
        errors.append("Audio bytes and/or narration changed since approval")
    if values["audio"] and audio.get("mode") != values["audio"]["mode"]:
        errors.append("Audio mode must match actual input (edge_tts/manual_scene/recorded_voice)")
    if not isinstance(audio.get("synthetic_voice"), bool):
        errors.append("Audio: synthetic_voice must be boolean true/false (declared by the reviewer)")
    elif values["audio"] and values["audio"]["mode"] == "edge_tts" and audio["synthetic_voice"] is not True:
        errors.append("Audio: Edge TTS narration is synthetic; synthetic_voice must be true")
    return errors
