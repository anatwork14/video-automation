"""Batch 1 regressions: approvals bound to timeline/claim set/voice path; signed, non-forgeable review.

Hermetic: TemporaryDirectory, throwaway git repo and ephemeral SSH keys (fixture_project.py).
"""
import importlib.metadata
import inspect
import json
import os
import re
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import review_gate
import science_gate
import validate as validate_mod
from fixture_project import KEY_DIR, ROOT, _rd, _w, add_tts_audio, make_project, sign_review, write_review
from review_signatures import ALLOWED_SIGNERS, NAMESPACE, SIGNATURE_DIR

IN_CI = os.environ.get("CI") == "true"


def strict(root):
    with patch("media_audit.audit", return_value=[]):
        return validate_mod.validate(strict=True, root=Path(root))


def has(errors, needle):
    return any(needle in e for e in errors)


class Project(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        make_project(self.root)

    def assertBlocked(self, needle):
        errors = strict(self.root)
        self.assertTrue(has(errors, needle), (needle, errors))


class SignatureTests(Project):
    def test_positive_control_signed_review_passes(self):
        self.assertEqual(strict(self.root), [])

    def test_unsigned_review_is_rejected(self):
        (self.root / SIGNATURE_DIR / "tester-0.sig").unlink()
        self.assertBlocked("Missing review.sigs/tester-0.sig")

    def test_edit_after_signing_is_rejected(self):
        review = _rd(self.root, "review.json")
        review["claims"]["c1"]["source_excerpt"] = "edited after the reviewer signed it"
        _w(self.root, "review.json", review)
        self.assertBlocked("does not verify")

    def test_signature_from_key_outside_allowed_signers_is_rejected(self):
        rogue = self.root / KEY_DIR / "rogue"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(rogue)], check=True)
        subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", str(rogue), "-n", NAMESPACE,
                        str(self.root / "review.json")], check=True)
        (self.root / "review.json.sig").replace(self.root / SIGNATURE_DIR / "tester-0.sig")
        self.assertBlocked("does not verify")

    def test_wrong_namespace_signature_is_rejected(self):
        key = self.root / KEY_DIR / "tester-0"
        subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", str(key), "-n", "file",
                        str(self.root / "review.json")], check=True)
        (self.root / "review.json.sig").replace(self.root / SIGNATURE_DIR / "tester-0.sig")
        self.assertBlocked("does not verify")

    def test_uncommitted_key_substitution_is_rejected(self):
        with (self.root / ALLOWED_SIGNERS).open("a") as f:
            f.write("intruder ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n")
        self.assertBlocked("uncommitted changes")

    def test_untracked_allowed_signers_is_rejected(self):
        subprocess.run(["git", "-C", str(self.root), "rm", "-q", "--cached", ALLOWED_SIGNERS], check=True)
        self.assertBlocked("must be committed")

    def test_member_without_reviewer_id_is_rejected(self):
        group = _rd(self.root, "group.json")
        group["team_members"][0]["reviewer_id"] = ""
        _w(self.root, "group.json", group)
        self.assertBlocked("team_members[1] needs a reviewer_id")

    def test_every_named_reviewer_must_sign(self):
        write_review(self.root, lambda r: r["timeline"].update(reviewed_by="Tester B"))
        self.assertBlocked("Missing review.sigs/tester-1.sig")
        sign_review(self.root, "tester-1")
        self.assertEqual(strict(self.root), [])


class ContentBindingTests(Project):
    def test_deleting_a_claim_after_approval_is_rejected(self):
        claims = _rd(self.root, "claims.json")
        claims["claims"].pop()  # c3 removed after approval
        _w(self.root, "claims.json", claims)
        errors = strict(self.root)
        self.assertTrue(has(errors, "Claim approval c3 has no matching claim"), errors)
        self.assertTrue(has(errors, "Claim set (IDs/scenes) changed"), errors)

    def test_moving_a_claim_to_another_scene_is_rejected(self):
        claims = _rd(self.root, "claims.json")
        claims["claims"][0]["scene"] = 2
        _w(self.root, "claims.json", claims)
        errors = strict(self.root)
        self.assertTrue(has(errors, "Claim c1: text/source has changed"), errors)
        self.assertTrue(has(errors, "Claim set (IDs/scenes) changed"), errors)

    def test_start_seconds_or_crop_change_requires_timeline_reapproval(self):
        for change in ({"start_seconds": 6}, {"crop": {"w": 729, "h": 1080, "x": 595, "y": 0}}):
            make_project(self.root)
            timeline = _rd(self.root, "timeline.json")
            timeline["segments"][1].update(change)
            _w(self.root, "timeline.json", timeline)
            self.assertBlocked("Timeline (clip order, start_seconds, crop, on-screen text) changed")

    def test_edge_tts_audio_must_be_declared_synthetic(self):
        add_tts_audio(self.root)
        write_review(self.root, lambda r: r["audio"].update(synthetic_voice=False))
        self.assertBlocked("synthetic_voice must be true")
        write_review(self.root, lambda r: r["audio"].update(synthetic_voice="yes"))
        self.assertBlocked("synthetic_voice must be boolean")

    def test_future_timestamp_rejected_but_skew_tolerated(self):
        now = datetime(2026, 10, 11, 6, 30, tzinfo=timezone.utc)
        row = {"approved": True, "reviewed_by": "A"}
        ok = dict(row, reviewed_at=(now + timedelta(minutes=5)).isoformat())
        late = dict(row, reviewed_at=(now + timedelta(hours=2)).isoformat())
        self.assertEqual(review_gate.reviewer_problems(ok, {"A"}, now=now), [])
        self.assertIn("reviewed_at is in the future", review_gate.reviewer_problems(late, {"A"}, now=now))


class VoicePathTests(unittest.TestCase):
    def test_unsafe_paths_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ("/etc/passwd.wav", "../voice.wav", "assets/../../voice.wav", "voice.wav",
                        "assets/voice.txt", "", None, 3):
                with self.assertRaises(ValueError, msg=bad):
                    review_gate.recorded_voice_path(d, {"narration_audio_file": bad})

    def test_symlink_escaping_assets_rejected(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            (Path(d) / "assets").mkdir()
            target = Path(outside) / "voice.wav"
            target.write_bytes(b"x")
            (Path(d) / "assets/voice.wav").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "outside assets"):
                review_gate.recorded_voice_path(d, {"narration_audio_file": "assets/voice.wav"})

    def test_default_and_custom_paths_resolve_inside_assets(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(review_gate.recorded_voice_path(d, {}), Path(d) / "assets/voiceover.wav")
            self.assertEqual(review_gate.recorded_voice_path(d, {"narration_audio_file": "assets/voice/take2.m4a"}),
                             Path(d) / "assets/voice/take2.m4a")


class ScienceCoverageTests(unittest.TestCase):
    def test_narrated_outro_needs_a_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _w(root, "timeline.json", {"segments": [
                {"kind": "intro", "duration": 5}, {"kind": "video", "duration": 5}, {"kind": "outro", "duration": 5}]})
            _w(root, "narration.json", {"segments": [{"index": 1, "text": "a"}, {"index": 2, "text": "b"}]})
            _w(root, "claims.json", {"claims": [
                {"id": "x", "scene": 1, "claim": "A sufficiently long synthetic claim",
                 "reference": "https://www.usgs.gov/x", "evidence_note": "note"}]})
            self.assertIn("Scene 2 has no scientific evidence", science_gate.check_claims(root))


class EdgeTTSContract(unittest.TestCase):
    """Runs against the INSTALLED library (no network). Mandatory in CI."""

    def setUp(self):
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            if IN_CI:
                self.fail("edge-tts must be installed in CI (requirements.txt)")
            self.skipTest("edge-tts not installed locally; CI runs this contract test")

    def test_installed_version_matches_pin(self):
        pinned = re.search(r"^edge-tts==([\d.]+)$", (ROOT / "requirements.txt").read_text(), re.M)
        self.assertIsNotNone(pinned, "requirements.txt must pin edge-tts exactly")
        self.assertEqual(importlib.metadata.version("edge-tts"), pinned.group(1))

    def test_communicate_accepts_word_boundary_and_records_it(self):
        import edge_tts
        params = inspect.signature(edge_tts.Communicate).parameters
        self.assertIn("boundary", params)
        client = edge_tts.Communicate(text="Núi lửa", voice="vi-VN-NamMinhNeural", boundary="WordBoundary")
        self.assertEqual(client.tts_config.boundary, "WordBoundary")


if __name__ == "__main__":
    unittest.main()
