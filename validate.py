#!/usr/bin/env python3
"""Structural / submission-readiness gate. No web calls, no AI self-approval."""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
from science_gate import check_claims
from review_gate import check_reviews, recorded_voice_path
from sources import MEDIA_TYPES, filename_ok, media_host_ok, source_host_ok
from review_signatures import verify_review_signatures

ROOT = Path(__file__).resolve().parent
VIETNAMESE_PROSE = re.compile(
    r"[àáạảãăằắặẳẵâầấậẩẫèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđ]", re.IGNORECASE
)

def contains_vietnamese_prose(text):
    # NFC first: decomposed (NFD) Vietnamese pasted from macOS must not bypass the gate.
    return bool(VIETNAMESE_PROSE.search(unicodedata.normalize("NFC", str(text))))


def english_problems(segments, narration, group):
    """Everything that reaches the screen or the voice must be English for an English group."""
    errors = []
    for index, scene in enumerate(segments):
        content = " ".join(str(x) for x in [
            scene.get("heading", ""), scene.get("caption", ""), scene.get("kicker", ""),
            *scene.get("hook_lines", []), *scene.get("credits", []),
            *(shot.get("label", "") for shot in scene.get("shots", []) if isinstance(shot, dict)),
            *(x for shot in scene.get("shots", []) if isinstance(shot, dict)
              for x in [*shot.get("hook_lines", []), *(shot.get("fact_card") or {}).get("lines", []),
                        (shot.get("fact_card") or {}).get("source", "")])])
        if contains_vietnamese_prose(content):
            errors.append(f"English group: video scene {index} still has Vietnamese on-screen prose")
    if contains_vietnamese_prose(group.get("course", "")):
        errors.append("English group: translate course text in group.json")
    for speech in narration.get("segments", []):
        if contains_vietnamese_prose(speech.get("text", "")):
            errors.append(f"English group: voiceover scene {speech.get('index')} is still Vietnamese")
    return errors


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
            kind = item["type"]
            if item.get("origin") == "team_made":
                # Only plain explanatory diagrams drawn by diagrams.py; never footage, never an event depiction.
                if (kind != "diagram" or item.get("generator") != "diagrams.py"
                        or item.get("license_as_stated_on_source") != "Original work (team-made)"
                        or not item["filename"].endswith(".png")):
                    errors.append(f"{item['id']}: team-made assets must be diagrams.py PNG diagrams")
            else:
                if not media_host_ok(item["download_url"], kind) or not source_host_ok(item["source_page"], kind):
                    errors.append(f"{item['id']}: URL is outside the approved official hosts (sources.py)")
                if kind not in MEDIA_TYPES or item["license_as_stated_on_source"] != "Public Domain":
                    errors.append(f"{item['id']}: media type/rights not approved for this project")
            if not filename_ok(item["filename"]):
                errors.append(f"{item['id']}: unsafe filename")
            for field in ("captured_date", "location", "agency_credit", "description"):
                if not item.get(field):
                    errors.append(f"{item['id']}: missing {field}")
        except KeyError as exc:
            errors.append(f"Asset missing key: {exc}")
    segments = timeline.get("segments", [])
    if not segments or segments[0].get("kind") != "intro" or segments[-1].get("kind") != "outro":
        errors.append("Timeline must begin with intro and end with outro")
    music = timeline.get("music")
    if music is not None:
        if (not isinstance(music, dict) or music.get("file") != "assets/music/score.wav"
                or isinstance(music.get("lufs"), bool) or not isinstance(music.get("lufs"), (int, float))
                or not -36 <= music["lufs"] <= -20):
            errors.append("music must be {file: assets/music/score.wav (made by music.py), lufs: -36..-20}")
    if not any(s.get("kind") == "video" for s in segments):
        errors.append("Timeline needs at least one genuine footage (kind=video) scene")
    for index, seg in enumerate(segments):
        if seg.get("kind") not in ("intro", "video", "outro"):
            errors.append(f"Scene {index}: unknown kind {seg.get('kind')!r}")
        refs = [seg] if seg.get("kind") == "video" and not seg.get("shots") else []
        if "shots" in seg:
            shots = seg["shots"]
            if not isinstance(shots, list) or not shots or not all(isinstance(x, dict) for x in shots):
                errors.append(f"Scene {index}: shots must be a non-empty list of objects")
                shots = []
            for k, shot in enumerate(shots):
                card = shot.get("fact_card")
                if card is not None:
                    if (not isinstance(card, dict) or not card.get("lines") or not str(card.get("source", "")).startswith("Source:")
                            or not card.get("tag")):
                        errors.append(f"Scene {index} shot {k}: fact_card needs tag, lines and a 'Source: ...' line")
                elif shot.get("asset_id") not in ids:
                    errors.append(f"Scene {index} shot {k}: unknown footage {shot.get('asset_id')!r}")
                if card is None and (not isinstance(shot.get("label"), str) or len(shot["label"].strip()) < 6):
                    errors.append(f"Scene {index} shot {k}: label must identify place and date")
                length = shot.get("duration")
                if isinstance(length, bool) or not isinstance(length, (int, float)) or length <= 0:
                    errors.append(f"Scene {index} shot {k}: duration must be positive")
            if shots and abs(sum(float(x.get("duration", 0) or 0) for x in shots) - float(seg.get("duration", 0))) > 0.02:
                errors.append(f"Scene {index}: shot durations must add up to the scene duration")
            refs.extend(x for x in shots if not x.get("fact_card"))
        hooks = [seg] + [x for x in seg.get("shots", []) if isinstance(x, dict)]
        if any(h.get("layout") == "hook" and not (isinstance(h.get("hook_lines"), list) and h["hook_lines"]) for h in hooks):
            errors.append(f"Scene {index}: hook layout needs hook_lines")
        if "background" in seg:
            if seg.get("kind") not in ("intro", "outro") or not isinstance(seg["background"], dict):
                errors.append(f"Scene {index}: background is only allowed on intro/outro as an object")
            else:
                refs.append(seg["background"])
                if seg["background"].get("asset_id") not in ids:
                    errors.append(f"Scene {index}: background references unknown footage")
        for ref in refs or [seg]:
            start = ref.get("start_seconds", 0)
            if isinstance(start, bool) or not isinstance(start, (int, float)) or start < 0:
                errors.append(f"Scene {index}: start_seconds must be a non-negative number")
            crop = ref.get("crop")
            if crop is not None and (not isinstance(crop, dict) or set(crop) != {"w", "h", "x", "y"} or any(
                    isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in crop.values())):
                errors.append(f"Scene {index}: crop must be {{w,h,x,y}} non-negative integers")
            if ref.get("fill", "black") not in ("black", "blur"):
                errors.append(f"Scene {index}: fill must be 'black' or 'blur'")
            lufs = ref.get("field_audio_lufs")
            if lufs is not None and (isinstance(lufs, bool) or not isinstance(lufs, (int, float)) or not -40 <= lufs <= -20):
                errors.append(f"Scene {index}: field_audio_lufs must be between -40 and -20 (background bed)")
    try:
        duration = sum(float(s["duration"]) for s in segments)
        if abs(duration - float(timeline["duration_seconds"])) > 0.1 or not 108 <= duration <= 132:
            errors.append("Timeline must add up to 108–132 seconds")
    except (KeyError, TypeError, ValueError):
        errors.append("Invalid timeline duration")
    for seg in segments:
        if seg.get("kind") == "video" and not seg.get("shots") and seg.get("asset_id") not in ids:
            errors.append(f"Timeline references unknown footage: {seg.get('asset_id')}")
    scripts = {s.get("index"): s.get("text") for s in narration.get("segments", [])}
    for index, seg in enumerate(segments):
        if index and not scripts.get(index) and seg.get("layout") != "credits":  # credits roll may be silent
            errors.append(f"Missing narration for segment {index}")
    errors.extend(check_claims(root))
    if not strict:
        return errors

    try:
        group = read_json("group.json", root)
    except (OSError, ValueError):
        return errors + ["Create local group.json from group.example.json; do not commit personal data."]
    if not isinstance(group, dict):
        return errors + ["group.json must be a JSON object"]
    members = group.get("team_members", [])
    if not isinstance(members, list) or not (3 <= len(members) <= 5):
        errors.append("Group requires 3–5 members")
        members = members if isinstance(members, list) else []
    if not str(group.get("group_number", "")).strip() or group.get("group_number") == "CHUA_DIEN":
        errors.append("Missing registered group number")

    def placeholder(member):
        if not isinstance(member, dict):
            return True
        name, sid = member.get("name"), member.get("student_id")
        return (not isinstance(name, str) or not name.strip() or "HO TEN" in name
                or not isinstance(sid, str) or not sid.strip() or sid.startswith("MSSV "))
    if any(placeholder(x) for x in members):
        errors.append("Real group member names/MSSVs required")
    names = [x.get("name").strip() for x in members if not placeholder(x)]
    if len(set(names)) != len(names):
        errors.append("Group member names must be unique (approvals are matched by name)")
    if group.get("language") not in {"vi", "en"}:
        errors.append("Group language must be vi or en")
    if group.get("english_program_member") and group.get("language") != "en":
        errors.append("English-program member requires English narration/video")
    if narration.get("language") != group.get("language"):
        errors.append("Narration language does not match group language")
    if group.get("language") == "en":
        errors.extend(english_problems(segments, narration, group))
    try:
        review_bytes = (root / "review.json").read_bytes()
        review = json.loads(review_bytes.decode("utf-8"))
    except (OSError, ValueError):
        return errors + ["Create review.json from review.example.json; human must approve sources."]
    if not isinstance(review, dict):
        return errors + ["review.json must be a JSON object"]

    def rows(key):
        value = review.get(key)
        return value if isinstance(value, dict) else {}

    def entry_ok(entry, flag):
        return isinstance(entry, dict) and entry.get("approved") is True and entry.get(flag) is True
    for item in items:
        if not entry_ok(rows("assets").get(item["id"]), "rights_checked"):
            errors.append(f"Human provenance/rights approval missing: {item['id']}")
        file = root / "assets" / item["filename"]
        if not file.exists() or file.stat().st_size < 2048:
            errors.append(f"Missing downloaded original: {file.name}")
    claims = read_json("claims.json", root)["claims"]
    for claim in claims:
        if not entry_ok(rows("claims").get(claim["id"]), "source_read"):
            errors.append("Scientific claim lacks HUMAN approval: " + claim["id"])
    from media_audit import audit as audit_media
    errors.extend(audit_media(root))
    if review.get("script_reviewed") is not True:
        errors.append("Script still requires human scientific review")
    if review.get("course_logos_reviewed") is not True:
        errors.append("Course/sponsor logos still require human review")
    if group.get("language") == "en" and review.get("english_language_reviewed") is not True:
        errors.append("English audio/captions not reviewed")
    if not (root / "assets" / "logos_from_assignment.png").exists():
        errors.append("Missing assets/logos_from_assignment.png (run extract_logos.py)")
    errors.extend(check_reviews(root, group, review, items, claims, narration, timeline))
    errors.extend(verify_review_signatures(root, group, review_bytes, review))
    scene_audio = all((root / "assets" / "audio" / f"{n:02d}.mp3").exists() for n in scripts)
    try:
        recorded = recorded_voice_path(root, group)
    except ValueError as exc:
        errors.append(str(exc))
        recorded = None
    if not scene_audio and not (recorded and recorded.is_file()):
        errors.append("Missing scene audio clips or complete recorded voiceover")
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
