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


def sign_file(root, principal, document, signature_dir):
    """Sign <root>/<document> with the fixture key; store as <signature_dir>/<principal>.sig."""
    root = Path(root)
    key = root / KEY_DIR / principal
    sig_dir = root / signature_dir
    sig_dir.mkdir(parents=True, exist_ok=True)
    produced = root / (document + ".sig")
    produced.unlink(missing_ok=True)
    subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", str(key), "-n", NAMESPACE, str(root / document)],
                   check=True, capture_output=True)
    shutil.move(str(produced), str(sig_dir / f"{principal}.sig"))


def sign_review(root, principal):
    sign_file(root, principal, "review.json", SIGNATURE_DIR)


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
            "audio_sha256": review_gate.sha256_file(root / f"assets/audio/{i:02d}.mp3"),
            "boundaries": [{"text": "w", "start_seconds": 0, "duration_seconds": 0.1}]})


# --------------------------------------------------------------------------
# Renderable fixture: REAL FFmpeg test patterns + tones (never real footage, never in assets/)
# --------------------------------------------------------------------------
RENDER_TIMELINE = {"duration_seconds": 120, "segments": [
    {"kind": "intro", "duration": 10, "heading": "TEST PATTERN", "caption": "Synthetic fixture"},
    {"kind": "video", "asset_id": "a1", "duration": 50, "heading": "TEST 1", "caption": "testsrc2", "start_seconds": 1},
    {"kind": "video", "asset_id": "a2", "duration": 50, "heading": "TEST 2", "caption": "mandelbrot"},
    {"kind": "outro", "duration": 10, "heading": "TEST", "caption": "Synthetic fixture"},
]}
PATTERNS = {"a1": "testsrc2=size=640x360:rate=30", "a2": "mandelbrot=size=640x360:rate=30"}


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", *map(str, args)],
                   check=True, capture_output=True)


def tone(path, seconds, freq=220, volume=4.0):
    """Sine test tone. lavfi sine defaults to amplitude 1/8 (-18 dBFS); volume=4 gives ~-6 dBFS peak."""
    ffmpeg("-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=48000:duration={seconds}",
           "-af", f"volume={volume}", path)


def _source_provenance(root, item):
    from download_assets import probe_media
    path = Path(root) / "assets" / item["filename"]
    digest = review_gate.sha256_file(path)
    path.with_suffix(".sha256").write_text(f"{digest}  {path.name}\n")
    path.with_suffix(".provenance.json").write_text(json.dumps({
        "id": item["id"], "source_page": item["source_page"], "download_url": item["download_url"],
        "final_url": item["download_url"], "etag": None, "last_modified": None, "content_length": None,
        "bytes": path.stat().st_size, "sha256": digest, "downloaded_at_utc": WHEN,
        "media": probe_media(path), "note": "TEST FIXTURE: synthetic lavfi pattern, not footage",
    }))


def make_renderable_project(root, mode="tts", speech=(8.0, 8.0, 6.0), source_filters=None):
    """Full strict-valid project whose media are real FFmpeg test signals.

    source_filters: optional {asset_id: ffmpeg -vf} to inject defects (black/frozen spans).
    """
    from PIL import Image
    root = Path(root)
    make_project(root, timeline=RENDER_TIMELINE)
    for item in _rd(root, "assets.json")["assets"]:
        vf = (source_filters or {}).get(item["id"])
        ffmpeg("-f", "lavfi", "-i", PATTERNS[item["id"]], "-t", 55, *(["-vf", vf] if vf else []),
               "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
               root / "assets" / item["filename"])
        _source_provenance(root, item)
    Image.new("RGB", (600, 120), "#ffffff").save(root / "assets/logos_from_assignment.png")
    (root / "assets/voiceover.wav").unlink()
    if mode == "tts":
        narration = _rd(root, "narration.json")
        for seg, seconds in zip(narration["segments"], speech):
            i = seg["index"]
            tone(root / f"assets/audio/{i:02d}.mp3", seconds, freq=200 + 40 * i)
            words = seg["text"].split()
            step = min(seconds / len(words), 0.4)  # realistic speech pace (~2.5 words/s)
            _w(root, f"assets/audio/{i:02d}.timings.json", {
                "provider": "edge-tts", "synthetic_voice": True, "voice": "test", "rate": "+0%",
                "text_sha256": review_gate.text_sha256(seg["text"]), "duration_seconds": seconds,
                "audio_sha256": review_gate.sha256_file(root / f"assets/audio/{i:02d}.mp3"),
                "boundaries": [{"start_seconds": round(k * step, 3), "duration_seconds": round(step * 0.8, 3),
                                "text": w} for k, w in enumerate(words)]})
    else:
        tone(root / "assets/voiceover.wav", speech[0])
    write_review(root)
    return root
