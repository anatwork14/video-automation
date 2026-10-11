#!/usr/bin/env python3
"""Structural / submission-readiness gate. No web calls, no AI self-approval."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from science_gate import check_claims

ROOT = Path(__file__).resolve().parent
MEDIA_HOST = "usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com"


def read_json(filename, root=ROOT):
    return json.loads((root / filename).read_text(encoding="utf-8"))


def validate(strict=False, root=ROOT):
    errors = []
    try:
        data = read_json("assets.json", root)
        timeline = read_json("timeline.json", root)
        narration = read_json("narration.json", root)
    except (OSError, ValueError) as exc:
        return [f"Invalid/missing JSON: {exc}"]
    items = data.get("assets", [])
    ids = [i.get("id") for i in items]
    if len(items) < 1 or len(set(ids)) != len(ids):
        errors.append("Asset IDs missing or duplicated")
    for item in items:
        try:
            host = urlparse(item["download_url"]).hostname
            source = urlparse(item["source_page"])
            filename = item["filename"]
            if host != MEDIA_HOST or source.hostname != "www.usgs.gov":
                errors.append(f"{item['id']}: URL is outside approved USGS hosts")
            if Path(filename).name != filename or not filename.endswith(".mp4"):
                errors.append(f"{item['id']}: unsafe filename")
            if item["type"] != "real_video" or item["license_as_stated_on_source"] != "Public Domain":
                errors.append(f"{item['id']}: source/rights not approved for this starter")
            for field in ("captured_date", "location", "agency_credit", "description"):
                if not item.get(field):
                    errors.append(f"{item['id']}: missing {field}")
        except KeyError as exc:
            errors.append(f"Asset missing key: {exc}")
    segments = timeline.get("segments", [])
    if not segments or segments[0].get("kind") != "intro" or segments[-1].get("kind") != "outro":
        errors.append("Timeline must begin with intro and end with outro")
    try:
        duration = sum(float(s["duration"]) for s in segments)
        if abs(duration - float(timeline["duration_seconds"])) > 0.1 or not 108 <= duration <= 132:
            errors.append("Timeline must add up to 108–132 seconds")
    except (KeyError, TypeError, ValueError):
        errors.append("Invalid timeline duration")
    for seg in segments:
        if seg.get("kind") == "video" and seg.get("asset_id") not in ids:
            errors.append(f"Timeline references unknown footage: {seg.get('asset_id')}")
    scripts = {s.get("index"): s.get("text") for s in narration.get("segments", [])}
    for index, seg in enumerate(segments):
        if index and not scripts.get(index):
            errors.append(f"Missing narration for segment {index}")
    errors.extend(check_claims(root))
    if not strict:
        return errors

    try:
        group = read_json("group.json", root)
    except (OSError, ValueError):
        return errors + ["Create local group.json from group.example.json; do not commit personal data."]
    members = group.get("team_members", [])
    if not (3 <= len(members) <= 5):
        errors.append("Group requires 3–5 members")
    if not str(group.get("group_number", "")).strip() or group["group_number"] == "CHUA_DIEN":
        errors.append("Missing registered group number")
    if any(not x.get("name") or "HO TEN" in x["name"] or not x.get("student_id") or x["student_id"].startswith("MSSV ") for x in members):
        errors.append("Real group member names/MSSVs required")
    if group.get("language") not in {"vi", "en"}:
        errors.append("Group language must be vi or en")
    if group.get("english_program_member") and group.get("language") != "en":
        errors.append("English-program member requires English narration/video")
    if narration.get("language") != group.get("language"):
        errors.append("Narration language does not match group language")
    try:
        review = read_json("review.json", root)
    except (OSError, ValueError):
        return errors + ["Create review.json from review.example.json; human must approve sources."]
    for item in items:
        entry = review.get("assets", {}).get(item["id"], {})
        if not (entry.get("approved") and entry.get("rights_checked") and entry.get("reviewed_by") and entry.get("reviewed_at")):
            errors.append(f"Human provenance/rights approval missing: {item['id']}")
        file = root / "assets" / item["filename"]
        if not file.exists() or file.stat().st_size < 2048:
            errors.append(f"Missing downloaded original: {file.name}")
    for claim in read_json("claims.json", root)["claims"]:
        entry = review.get("claims", {}).get(claim["id"], {})
        if not (entry.get("approved") and entry.get("source_read")
                and entry.get("reviewed_by") and entry.get("reviewed_at")):
            errors.append("Scientific claim lacks HUMAN approval: " + claim["id"])
    from media_audit import audit as audit_media
    errors.extend(audit_media(root))
    if not review.get("script_reviewed"):
        errors.append("Script still requires human scientific review")
    if not review.get("course_logos_reviewed"):
        errors.append("Course/sponsor logos still require human review")
    if group.get("language") == "en" and not review.get("english_language_reviewed"):
        errors.append("English audio/captions not reviewed")
    if not (root / "assets" / "logos_from_assignment.png").exists():
        errors.append("Missing assets/logos_from_assignment.png (run extract_logos.py)")
    scene_audio = all((root / "assets" / "audio" / f"{n:02d}.mp3").exists() for n in scripts)
    old_voice = root / group.get("narration_audio_file", "assets/voiceover.wav")
    if not scene_audio and not old_voice.exists():
        errors.append("Missing scene audio clips or complete legacy voiceover")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Require real footage, team, audio and human approvals")
    opts = parser.parse_args()
    problems = validate(strict=opts.strict)
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        raise SystemExit(1)
    print("PASS:", "submission-readiness gate" if opts.strict else "manifest and timeline structure")
