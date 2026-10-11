"""Synthetic project fixture shared by tests (not itself a test module).

Everything lives in a TemporaryDirectory: synthetic JSON, placeholder media bytes,
a throwaway git repository and an ephemeral SSH key that signs ONLY the fixture's
review.json. Names/IDs are placeholders ("Tester A", "TEST-A"). Nothing here
approves real content; it demonstrates that any automated actor holding a key can
sign, which is why real reviewers must keep their private keys to themselves.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import review_gate  # noqa: E402
from review_signatures import ALLOWED_SIGNERS, NAMESPACE, SIGNATURE_DIR  # noqa: E402

USGS_MEDIA = "https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/"
WHEN = "2026-10-11T13:30:00+07:00"
KEY_DIR = ".fixture-keys"  # inside the temp dir only

DEFAULT_TIMELINE = {"duration_seconds": 120, "segments": [
    {"kind": "intro", "duration": 10, "heading": "H0", "caption": "C0"},
    {"kind": "video", "asset_id": "a1", "duration": 50, "heading": "H1", "caption": "C1"},
    {"kind": "video", "asset_id": "a2", "duration": 50, "heading": "H2", "caption": "C2"},
    {"kind": "outro", "duration": 10, "heading": "H3", "caption": "C3"},
]}


def _w(root, name, obj):
    (Path(root) / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _rd(root, name):
    return json.loads((Path(root) / name).read_text(encoding="utf-8"))


def _asset(i):
    return {
        "id": f"a{i}", "filename": f"a{i}.mp4", "type": "real_video",
        "captured_date": f"2018-05-1{i}", "location": "Synthetic location",
        "description": "synthetic", "source_page": f"https://www.usgs.gov/x{i}",
        "download_url": USGS_MEDIA + f"a{i}.mp4",
        "license_as_stated_on_source": "Public Domain",
        "agency_credit": "USGS test credit", "manual_source_review_required": True,
    }


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True, text=True)


def setup_signing(root, principals):
    """Throwaway git repo + one ephemeral ed25519 key per principal; commit allowed_signers."""
    root = Path(root)
    keys = root / KEY_DIR
    keys.mkdir(exist_ok=True)
    lines = []
    for principal in principals:
        key = keys / principal
        if not key.exists():
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", principal, "-f", str(key)],
                           check=True, capture_output=True)
        pub = (keys / (principal + ".pub")).read_text().split()
        lines.append(f'{principal} namespaces="{NAMESPACE}" {pub[0]} {pub[1]}')
    (root / ALLOWED_SIGNERS).write_text("\n".join(lines) + "\n")
    if not (root / ".git").exists():
        _git(root, "init", "-q")
    _git(root, "add", ALLOWED_SIGNERS)
    if subprocess.run(["git", "-C", str(root), "diff", "--cached", "--quiet"]).returncode:
        _git(root, "commit", "-q", "-m", "fixture reviewer keys")


def sign_review(root, principal):
    root = Path(root)
    key = root / KEY_DIR / principal
    sig_dir = root / SIGNATURE_DIR
    sig_dir.mkdir(exist_ok=True)
    produced = root / "review.json.sig"
    produced.unlink(missing_ok=True)
    subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", str(key), "-n", NAMESPACE, str(root / "review.json")],
                   check=True, capture_output=True)
    shutil.move(str(produced), str(sig_dir / f"{principal}.sig"))


def make_project(root, language="vi", timeline=None, members=None):
    root = Path(root)
    (root / "assets/audio").mkdir(parents=True, exist_ok=True)
    _w(root, "assets.json", {"assets": [_asset(1), _asset(2)]})
    _w(root, "timeline.json", timeline or DEFAULT_TIMELINE)
    _w(root, "narration.json", {"language": language, "segments": [
        {"index": i, "text": f"Scene {i} narration text"} for i in (1, 2, 3)]})
    _w(root, "claims.json", {"claims": [
        {"id": f"c{i}", "scene": i, "claim": f"Synthetic scientific claim number {i} here",
         "reference": "https://www.usgs.gov/ref", "evidence_note": "synthetic note"}
        for i in (1, 2, 3)]})
    members = members or [{"name": f"Tester {c}", "student_id": f"TEST-{c}"} for c in "ABC"]
    for number, member in enumerate(members):
        if isinstance(member, dict):
            member.setdefault("reviewer_id", f"tester-{number}")
    _w(root, "group.json", {
        "group_number": "T1", "course": "Course", "language": language,
        "english_program_member": False, "team_members": members,
    })
    for i in (1, 2):
        (root / f"assets/a{i}.mp4").write_bytes(bytes([i]) * 4096)
    (root / "assets/logos_from_assignment.png").write_bytes(b"logo-bytes")
    (root / "assets/voiceover.wav").write_bytes(b"voice-bytes")
    setup_signing(root, [m["reviewer_id"] for m in members if isinstance(m, dict)])
    write_review(root)


def write_review(root, mutate=None, sign=True):
    """Synthetic review whose digests match the fixture (test-only), signed by member 0."""
    root = Path(root)
    assets = _rd(root, "assets.json")["assets"]
    claims = _rd(root, "claims.json")["claims"]
    narration = _rd(root, "narration.json")
    group = _rd(root, "group.json")
    h = review_gate.evidence_hashes(root, assets, claims, narration, group)
    first = group["team_members"][0] if group["team_members"] else None
    who = first.get("name") if isinstance(first, dict) else "x"

    def base(**extra):
        return {"approved": True, "reviewed_by": who, "reviewed_at": WHEN, **extra}
    mode = (h["audio"] or {}).get("mode")
    review = {
        "assets": {a["id"]: base(rights_checked=True,
                                 rights_evidence_excerpt="synthetic rights excerpt 123",
                                 **h["assets"][a["id"]]) for a in assets},
        "claims": {c["id"]: base(source_read=True, source_excerpt="synthetic source excerpt 12345",
                                 **h["claims"][c["id"]]) for c in claims},
        "script": base(approved_narration_sha256=h["narration_sha256"],
                       approved_claim_set_sha256=h["claim_set_sha256"]),
        "timeline": base(approved_timeline_sha256=h["timeline_sha256"]),
        "logos": base(approved_sha256=h["logo_sha256"]),
        "audio": base(mode=mode, synthetic_voice=(mode == "edge_tts"),
                      approved_audio_digest=(h["audio"] or {}).get("sha256")),
        "script_reviewed": True, "course_logos_reviewed": True,
        "english_language_reviewed": True,
    }
    if mutate:
        mutate(review)
    _w(root, "review.json", review)
    if sign and isinstance(first, dict) and isinstance(first.get("reviewer_id"), str) \
            and (root / KEY_DIR / first["reviewer_id"]).exists():
        sign_review(root, first["reviewer_id"])
    return review


def add_tts_audio(root, stale_scene=None):
    root = Path(root)
    narration = _rd(root, "narration.json")
    for seg in narration["segments"]:
        i = seg["index"]
        text = "old text" if i == stale_scene else seg["text"]
        (root / f"assets/audio/{i:02d}.mp3").write_bytes(b"mp3" + bytes([i]) * 100)
        _w(root, f"assets/audio/{i:02d}.timings.json", {
            "provider": "edge-tts", "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "boundaries": [{"text": "w", "start_seconds": 0, "duration_seconds": 0.1}]})
