"""QA review findings: regression tests for fixed defects plus expectedFailure
tests that pin CURRENT bugs (each docstring names the finding ID from
reports/qa.md). Remove @unittest.expectedFailure when the bug is fixed.

Hermetic: TemporaryDirectory + synthetic JSON + unittest.mock. No network, no
ffmpeg, no real or fake footage, no edge_tts install needed. All names and IDs
below are synthetic placeholders ("Tester A", "TEST-A"); nothing here approves
real content. Fixture "approvals" only exist inside temp dirs, and they are
generated programmatically, which also demonstrates finding N19: every gate
input is a plain file whose digests anyone (including an AI) can compute.
"""
import argparse
import asyncio
import contextlib
import hashlib
import importlib
import io
import json
import re
import subprocess
import sys
import tempfile
import types
import unicodedata
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build  # noqa: E402
import build_provenance  # noqa: E402
import download_assets  # noqa: E402
import media_audit  # noqa: E402
import pipeline  # noqa: E402
import qa  # noqa: E402
import review_gate  # noqa: E402
import validate as validate_mod  # noqa: E402
import voiceover  # noqa: E402

from fixture_project import (  # noqa: E402  shared synthetic, signed fixture
    DEFAULT_TIMELINE, _asset, _rd, _w, add_tts_audio, ffmpeg, make_project, make_renderable_project, tone,
    write_review,
)


def strict_errors(root):
    with patch("media_audit.audit", return_value=[]):
        return validate_mod.validate(strict=True, root=Path(root))


def gate_errors(root):
    root = Path(root)
    return review_gate.check_reviews(
        root, _rd(root, "group.json"), _rd(root, "review.json"),
        _rd(root, "assets.json")["assets"], _rd(root, "claims.json")["claims"],
        _rd(root, "narration.json"))


class TempProject(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)


# --------------------------------------------------------------------------
# F5 / F6 review gate: regression coverage + positive control
# --------------------------------------------------------------------------
class ReviewGateRegression(TempProject):
    def test_positive_control_synthetic_project_passes(self):
        make_project(self.root)
        self.assertEqual(strict_errors(self.root), [])

    def test_independent_digest_computation(self):
        make_project(self.root)
        h = review_gate.evidence_hashes(
            self.root, _rd(self.root, "assets.json")["assets"],
            _rd(self.root, "claims.json")["claims"], _rd(self.root, "narration.json"))
        canon_n = json.dumps(_rd(self.root, "narration.json"), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        self.assertEqual(h["narration_sha256"], hashlib.sha256(canon_n).hexdigest())
        self.assertEqual(h["assets"]["a1"]["approved_media_sha256"],
                         hashlib.sha256(bytes([1]) * 4096).hexdigest())
        canon = json.dumps(_asset(1), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
        self.assertEqual(h["assets"]["a1"]["approved_manifest_sha256"],
                         hashlib.sha256(canon).hexdigest())

    def _assert_blocked(self, mutate, needle):
        make_project(self.root)
        write_review(self.root, mutate)
        errors = gate_errors(self.root)
        self.assertTrue(any(needle in e for e in errors), (needle, errors))

    def test_string_booleans_rejected_everywhere(self):
        self._assert_blocked(lambda r: r["assets"]["a1"].update(approved="true"), "approved must be boolean")
        self._assert_blocked(lambda r: r["assets"]["a1"].update(rights_checked="true"), "rights_checked")
        self._assert_blocked(lambda r: r["claims"]["c1"].update(source_read="true"), "source_read")
        self._assert_blocked(lambda r: r.update(script_reviewed="true"), "script_reviewed")
        self._assert_blocked(lambda r: r.update(course_logos_reviewed=1), "course_logos_reviewed")
        self._assert_blocked(lambda r: r["script"].update(approved=1), "Script: approved must be boolean")

    def test_blank_unknown_or_ai_reviewer_rejected(self):
        for who in ("", "Mallory", "AI", "claude", None, 7):
            self._assert_blocked(lambda r, who=who: r["claims"]["c1"].update(reviewed_by=who),
                                 "registered member")

    def test_reviewer_name_is_exact_match_not_unicode_folded(self):
        # Fail-closed: NFD spelling of a member name is NOT accepted (usability only).
        make_project(self.root, members=[{"name": "Nguyễn A", "student_id": "T1"},
                                         {"name": "B", "student_id": "T2"},
                                         {"name": "C", "student_id": "T3"}])
        nfd = unicodedata.normalize("NFD", "Nguyễn A")
        self.assertNotEqual(nfd, "Nguyễn A")
        write_review(self.root, lambda r: r["claims"]["c1"].update(reviewed_by=nfd))
        self.assertTrue(any("registered member" in e for e in gate_errors(self.root)))

    def test_naive_or_malformed_dates_rejected(self):
        for bad in ("2026-10-11", "2026-10-11T13:30:00", "yesterday", "", None, 20261011):
            self._assert_blocked(lambda r, bad=bad: r["assets"]["a2"].update(reviewed_at=bad), "ISO8601")

    def test_changed_media_manifest_claim_script_logo_audio_invalidate_approval(self):
        make_project(self.root)
        self.assertEqual(gate_errors(self.root), [])
        (self.root / "assets/a1.mp4").write_bytes(b"substituted footage" * 300)
        self.assertTrue(any("a1" in e and "approved_media_sha256" in e for e in gate_errors(self.root)))
        (self.root / "assets/a1.mp4").write_bytes(bytes([1]) * 4096)
        self.assertEqual(gate_errors(self.root), [])

        a = _rd(self.root, "assets.json")
        a["assets"][1]["location"] = "Another place"
        _w(self.root, "assets.json", a)
        self.assertTrue(any("a2" in e and "approved_manifest_sha256" in e for e in gate_errors(self.root)))
        make_project(self.root)

        c = _rd(self.root, "claims.json")
        c["claims"][0]["claim"] = "A different and now unreviewed scientific claim"
        _w(self.root, "claims.json", c)
        self.assertTrue(any("c1" in e and "has changed" in e for e in gate_errors(self.root)))
        make_project(self.root)

        n = _rd(self.root, "narration.json")
        n["segments"][0]["text"] += " edited"
        _w(self.root, "narration.json", n)
        errors = gate_errors(self.root)
        self.assertTrue(any("Script text changed" in e for e in errors), errors)
        self.assertTrue(any("Audio bytes" in e for e in errors), errors)
        make_project(self.root)

        (self.root / "assets/logos_from_assignment.png").write_bytes(b"other logo")
        self.assertTrue(any("Logo bytes" in e for e in gate_errors(self.root)))
        make_project(self.root)

        (self.root / "assets/voiceover.wav").write_bytes(b"other voice")
        self.assertTrue(any("Audio bytes" in e for e in gate_errors(self.root)))

    def test_short_evidence_excerpts_rejected(self):
        self._assert_blocked(lambda r: r["assets"]["a1"].update(rights_evidence_excerpt="too short"),
                             "rights evidence")
        self._assert_blocked(lambda r: r["claims"]["c1"].update(source_excerpt="   "), "source excerpt")

    def test_asset_needs_manual_review_flag_in_manifest(self):
        make_project(self.root)
        a = _rd(self.root, "assets.json")
        a["assets"][0]["manual_source_review_required"] = "true"
        _w(self.root, "assets.json", a)
        self.assertTrue(any("manual source review flag" in e for e in gate_errors(self.root)))

    def test_audio_mode_must_match(self):
        self._assert_blocked(lambda r: r["audio"].update(mode="edge_tts"), "Audio mode")

    def test_english_group_needs_english_review_flag(self):
        make_project(self.root, language="en")
        write_review(self.root, lambda r: r.update(english_language_reviewed=False))
        self.assertTrue(any("english_language_reviewed" in e for e in gate_errors(self.root)))

    def test_key_order_and_whitespace_do_not_change_object_digest(self):
        self.assertEqual(review_gate.sha256_object({"a": 1, "b": [1, 2]}),
                         review_gate.sha256_object(json.loads('{ "b": [1, 2],\n "a": 1 }')))


# --------------------------------------------------------------------------
# F4 / F8 audio evidence
# --------------------------------------------------------------------------
class AudioEvidenceRegression(TempProject):
    def test_stale_tts_blocks_strict_validation(self):
        make_project(self.root)
        add_tts_audio(self.root, stale_scene=2)
        write_review(self.root)
        errors = strict_errors(self.root)
        self.assertTrue(any("STALE AUDIO: scene 2" in e for e in errors), errors)

    def test_tts_mode_digest_changes_when_mp3_changes(self):
        make_project(self.root)
        add_tts_audio(self.root)
        write_review(self.root)
        self.assertEqual(strict_errors(self.root), [])
        (self.root / "assets/audio/02.mp3").write_bytes(b"swapped")
        self.assertTrue(any("Audio bytes" in e for e in strict_errors(self.root)))

    def test_partial_scene_audio_is_ambiguous(self):
        make_project(self.root)
        add_tts_audio(self.root)
        (self.root / "assets/audio/03.mp3").unlink()
        (self.root / "assets/audio/03.timings.json").unlink()
        _, errors = review_gate.audio_evidence(self.root, _rd(self.root, "narration.json"))
        self.assertTrue(any("Incomplete/ambiguous" in e for e in errors))

    def test_mixed_timings_and_unknown_provider_and_empty_boundaries(self):
        make_project(self.root)
        add_tts_audio(self.root)
        (self.root / "assets/audio/01.timings.json").unlink()
        _, errors = review_gate.audio_evidence(self.root, _rd(self.root, "narration.json"))
        self.assertTrue(any("others do not" in e for e in errors), errors)
        add_tts_audio(self.root)
        t = _rd(self.root, "assets/audio/02.timings.json")
        t["provider"] = "other"
        t["boundaries"] = []
        _w(self.root, "assets/audio/02.timings.json", t)
        _, errors = review_gate.audio_evidence(self.root, _rd(self.root, "narration.json"))
        self.assertTrue(any("Unknown audio timing provider" in e for e in errors))
        self.assertTrue(any("Missing voice timestamp" in e for e in errors))

    def test_no_audio_at_all_fails_closed(self):
        make_project(self.root)
        (self.root / "assets/voiceover.wav").unlink()
        digest, errors = review_gate.audio_evidence(self.root, _rd(self.root, "narration.json"))
        self.assertIsNone(digest)
        self.assertTrue(errors)

    def test_scene_audio_wins_over_recorded_wav(self):
        make_project(self.root)
        add_tts_audio(self.root)
        digest, _ = review_gate.audio_evidence(self.root, _rd(self.root, "narration.json"))
        self.assertEqual(digest["mode"], "edge_tts")  # wav present but ignored, as in build.py


# --------------------------------------------------------------------------
# F1 / F6 voiceover + downloader regression
# --------------------------------------------------------------------------
def _fake_edge(chunks, captured=None):
    class FakeCommunicate:
        def __init__(self, **kwargs):
            if captured is not None:
                captured.update(kwargs)

        async def stream(self):
            for c in chunks:
                yield c
    return types.SimpleNamespace(Communicate=FakeCommunicate)


AUDIO = {"type": "audio", "data": b"x" * 2048}


class VoiceoverRegression(TempProject):
    def _synth(self, chunks, text="Núi lửa", force=False, rate="+0%", duration=10.0, captured=None):
        with patch.dict(sys.modules, {"edge_tts": _fake_edge(chunks, captured)}), \
             patch.object(voiceover, "ROOT", self.root), \
             patch.object(voiceover, "probe_duration", return_value=2.0), \
             contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(voiceover.synthesize_segment(1, text, duration, "vi-VN-NamMinhNeural", rate, force))

    def test_sentence_boundary_only_service_output_is_rejected_and_cleaned(self):
        """F1 FIXED: if the service only returns SentenceBoundary, fail closed, leave nothing behind."""
        sentence = {"type": "SentenceBoundary", "offset": 0, "duration": 5, "text": "Núi lửa"}
        with self.assertRaisesRegex(RuntimeError, "no WordBoundary"):
            self._synth([AUDIO, sentence])
        self.assertEqual(list((self.root / "assets/audio").glob("*")), [])

    def test_boundary_tick_conversion_and_explicit_kwarg(self):
        seen = {}
        self._synth([AUDIO, {"type": "WordBoundary", "offset": 12_500_000, "duration": 3_000_000, "text": "Núi"}],
                    captured=seen)
        meta = _rd(self.root, "assets/audio/01.timings.json")
        self.assertEqual(seen["boundary"], "WordBoundary")
        self.assertEqual(meta["boundaries"][0]["start_seconds"], 1.25)
        self.assertEqual(meta["boundaries"][0]["duration_seconds"], 0.3)
        self.assertIs(meta["synthetic_voice"], True)

    def test_too_short_audio_payload_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "no usable audio"):
            self._synth([{"type": "audio", "data": b"x" * 10},
                         {"type": "WordBoundary", "offset": 0, "duration": 1, "text": "a"}])

    def test_overlong_narration_rejected_without_trimming(self):
        with patch.object(voiceover, "probe_duration", return_value=9.9):
            with patch.dict(sys.modules, {"edge_tts": _fake_edge(
                    [AUDIO, {"type": "WordBoundary", "offset": 0, "duration": 1, "text": "a"}])}), \
                 patch.object(voiceover, "ROOT", self.root):
                with self.assertRaisesRegex(ValueError, "too long"):
                    asyncio.run(voiceover.synthesize_segment(1, "t", 10.0, "vi-VN-NamMinhNeural", "+0%"))
        self.assertFalse((self.root / "assets/audio/01.mp3").exists())

    def test_reuse_requires_same_text_voice_and_rate_and_manual_audio_never_overwritten(self):
        wb = {"type": "WordBoundary", "offset": 0, "duration": 1000000, "text": "a"}
        self._synth([AUDIO, wb])
        self._synth([AUDIO, wb])  # identical text/voice/rate -> reuse, no error
        with self.assertRaisesRegex(ValueError, "stale"):
            self._synth([AUDIO, wb], rate="+10%")
        with self.assertRaisesRegex(ValueError, "stale"):
            self._synth([AUDIO, wb], text="khác")
        (self.root / "assets/audio/01.timings.json").unlink()
        before = (self.root / "assets/audio/01.mp3").read_bytes()
        with self.assertRaisesRegex(ValueError, "manual audio"):
            self._synth([AUDIO, wb])
        self.assertEqual((self.root / "assets/audio/01.mp3").read_bytes(), before)

    def test_N15_stale_check_does_not_need_edge_tts_installed(self):
        """N15 (test hermeticity): synthesize_segment imports edge_tts BEFORE the purely local
        reuse/stale checks, so tests/test_tts_contract.py::test_wrong_script_fails_before_reuse
        errors with ModuleNotFoundError when requirements are not installed."""
        audio = self.root / "assets/audio"
        audio.mkdir(parents=True)
        (audio / "01.mp3").write_bytes(b"z" * 2048)
        _w(self.root, "assets/audio/01.timings.json", {
            "text_sha256": hashlib.sha256(b"old").hexdigest(), "voice": "v", "rate": "+0%"})
        with patch.dict(sys.modules, {"edge_tts": None}), patch.object(voiceover, "ROOT", self.root), \
             patch.object(voiceover, "probe_duration", return_value=1.0):
            with self.assertRaisesRegex(ValueError, "stale"):
                asyncio.run(voiceover.synthesize_segment(1, "new", 9.0, "v", "+0%"))

    def test_N12_requirements_lower_bound_supports_boundary_kwarg(self):
        """N12: voiceover.py passes boundary="WordBoundary" to edge_tts.Communicate. edge-tts
        7.0.0-7.0.2 do not accept that kwarg (TypeError; verified by inspecting the 7.0.2
        wheel); 7.1.0 accepts it via **kwargs. requirements.txt allows edge-tts>=7.0."""
        text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        m = re.search(r"edge-tts\s*(?:==|>=)\s*(\d+)\.(\d+)(?:\.(\d+))?", text)
        self.assertIsNotNone(m)
        lower = tuple(int(x or 0) for x in m.groups())
        self.assertGreaterEqual(lower, (7, 1, 0))

    def test_N10_voiceover_hashes_same_text_that_gate_and_subtitles_hash(self):
        """N10: voiceover.run() strips narration text before hashing; review_gate.audio_evidence
        and subtitles.generate hash the raw text, so any narration with leading/trailing
        whitespace/newline is permanently reported as STALE AUDIO."""
        _w(self.root, "timeline.json", {"segments": [{"kind": "intro", "duration": 10},
                                                     {"kind": "video", "duration": 20}]})
        narration = {"language": "vi", "segments": [{"index": 1, "text": "Xin chào\n"}]}
        _w(self.root, "narration.json", narration)
        wb = {"type": "WordBoundary", "offset": 0, "duration": 1000000, "text": "Xin"}
        args = argparse.Namespace(voice=None, rate="+0%", force=False)
        with patch.dict(sys.modules, {"edge_tts": _fake_edge([AUDIO, wb])}), \
             patch.object(voiceover, "ROOT", self.root), \
             patch.object(voiceover.shutil, "which", return_value="/bin/ffprobe"), \
             patch.object(voiceover, "probe_duration", return_value=2.0), \
             contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(voiceover.run(args))
        _, errors = review_gate.audio_evidence(self.root, narration)
        self.assertEqual([e for e in errors if "STALE" in e], [])


class DownloaderRegression(TempProject):
    class Resp:
        def __init__(self, body, url):
            self._b, self._url = body, url

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def geturl(self):
            return self._url

        def read(self, n=-1):
            out, self._b = self._b[:n], self._b[n:]
            return out

    def _get(self, body, final_url=None):
        item = _asset(1)
        final_url = final_url or item["download_url"]
        with patch.object(download_assets.urllib.request, "urlopen",
                          return_value=self.Resp(body, final_url)), \
             patch.object(download_assets, "probe_media", return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            return download_assets.get_one(item, self.root)

    def test_success_writes_sidecar_that_media_audit_accepts(self):
        body = b"M" * 5000
        dest = self._get(body)
        sidecar = dest.with_suffix(".sha256")
        self.assertEqual(sidecar.read_text(), hashlib.sha256(body).hexdigest() + "  a1.mp4\n")
        self.assertEqual(media_audit.read_sha256(dest), media_audit.hash_video(dest))
        self.assertFalse(list((self.root / "assets").glob("*.partial")))

    def test_redirect_outside_host_leaves_nothing(self):
        with self.assertRaisesRegex(RuntimeError, "redirected outside"):
            self._get(b"M" * 5000, final_url="https://evil.example/a1.mp4")
        self.assertEqual(list((self.root / "assets").glob("*")), [])

    def test_tiny_download_rejected_without_sidecar(self):
        with self.assertRaisesRegex(RuntimeError, "too small"):
            self._get(b"tiny")
        self.assertEqual(list((self.root / "assets").glob("*")), [])

    def test_existing_file_with_wrong_sidecar_or_orphan_sidecar_blocked(self):
        folder = self.root / "assets"
        folder.mkdir()
        (folder / "a1.mp4").write_bytes(b"A" * 3000)
        (folder / "a1.sha256").write_text("0" * 64 + "  a1.mp4\n")
        with self.assertRaisesRegex(RuntimeError, "differs from recorded SHA256"):
            download_assets.get_one(_asset(1), self.root)
        (folder / "a1.mp4").unlink()
        with self.assertRaisesRegex(RuntimeError, "Orphan"):
            download_assets.get_one(_asset(1), self.root)

    def test_import_and_reload_have_no_side_effects(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network at import")), \
             patch("subprocess.run", side_effect=AssertionError("subprocess at import")):
            importlib.reload(download_assets)
            importlib.reload(qa)


# --------------------------------------------------------------------------
# F9 / language gate
# --------------------------------------------------------------------------
class LanguageGate(TempProject):
    def test_english_group_with_vietnamese_screen_text_or_voice_is_blocked(self):
        tl = json.loads(json.dumps(DEFAULT_TIMELINE))
        tl["segments"][1]["caption"] = "Dung nham chảy ra biển"
        make_project(self.root, language="en", timeline=tl)
        n = _rd(self.root, "narration.json")
        n["segments"][1]["text"] = "Núi lửa phun trào"
        _w(self.root, "narration.json", n)
        g = _rd(self.root, "group.json")
        g["course"] = "Khoa học Trái Đất"
        _w(self.root, "group.json", g)
        write_review(self.root)
        errors = strict_errors(self.root)
        self.assertTrue(any("video scene 1" in e for e in errors), errors)
        self.assertTrue(any("voiceover scene 2" in e for e in errors), errors)
        self.assertTrue(any("course text" in e for e in errors), errors)

    def test_narration_language_must_match_group(self):
        make_project(self.root, language="vi")
        n = _rd(self.root, "narration.json")
        n["language"] = "en"
        _w(self.root, "narration.json", n)
        write_review(self.root)
        self.assertTrue(any("does not match group language" in e for e in strict_errors(self.root)))

    def test_english_member_flag_forces_english(self):
        make_project(self.root, language="vi")
        g = _rd(self.root, "group.json")
        g["english_program_member"] = True
        _w(self.root, "group.json", g)
        write_review(self.root)
        self.assertTrue(any("English-program member" in e for e in strict_errors(self.root)))

    def test_N4_decomposed_unicode_vietnamese_is_detected(self):
        """N4: contains_vietnamese_prose matches only precomposed (NFC) code points. The same
        Vietnamese text in NFD (what macOS/some IMEs paste) bypasses the English-group gate."""
        nfc = "Dung nham chảy ra biển"
        nfd = unicodedata.normalize("NFD", nfc)
        self.assertTrue(validate_mod.contains_vietnamese_prose(nfc))
        self.assertTrue(validate_mod.contains_vietnamese_prose(nfd))


# --------------------------------------------------------------------------
# NEW gate defects (strict validation)
# --------------------------------------------------------------------------
class NewGateDefects(TempProject):
    def test_N1_timeline_change_after_approval_invalidates_review(self):
        """N1 (High): review digests cover assets.json, claims.json, narration, audio and logo,
        but NOT timeline.json (clip order, start_seconds, on-screen dates/headings/captions) or
        group.json. Swapping clips and rewriting the date caption after approval still passes
        `validate --strict`, so the rendered video is not what the humans approved. AGENTS.md
        claims approvals are content-bound; the receipt only detects this after the fact."""
        make_project(self.root)
        self.assertEqual(strict_errors(self.root), [])
        t = _rd(self.root, "timeline.json")
        t["segments"][1]["heading"] = "04.06.2018 | UNREVIEWED HEADING"
        t["segments"][1]["start_seconds"] = 3
        t["segments"][1], t["segments"][2] = t["segments"][2], t["segments"][1]
        _w(self.root, "timeline.json", t)
        self.assertTrue(strict_errors(self.root))

    def test_N2_legacy_audio_path_from_group_must_be_the_approved_file(self):
        """N2 (High): review_gate.audio_evidence and build_provenance hash only
        assets/voiceover.wav, but validate.py (existence) and build.py (render) use
        group.json["narration_audio_file"]. Pointing it at a different, never-reviewed file
        passes strict validation while the approved wav is ignored. Absolute / ../ paths are
        also accepted."""
        make_project(self.root)
        (self.root / "assets/other.wav").write_bytes(b"UNREVIEWED different audio")
        g = _rd(self.root, "group.json")
        g["narration_audio_file"] = "assets/other.wav"
        _w(self.root, "group.json", g)
        self.assertTrue(strict_errors(self.root))

    def test_N3_timeline_without_real_footage_is_rejected(self):
        """N3 (Medium): a timeline of intro+outro only (no `video` scene) passes strict
        validation: unused assets still need approval but nothing requires them to be on the
        timeline, no claim/media audit applies, and no minimum real-footage share exists."""
        tl = {"duration_seconds": 120, "segments": [
            {"kind": "intro", "duration": 10, "heading": "a", "caption": "b"},
            {"kind": "outro", "duration": 110, "heading": "a", "caption": "b"}]}
        make_project(self.root, timeline=tl)
        _w(self.root, "claims.json", {"claims": []})
        _w(self.root, "narration.json", {"language": "vi", "segments": [{"index": 1, "text": "Only narration"}]})
        write_review(self.root)
        self.assertTrue(strict_errors(self.root))

    def test_N5_whitespace_only_member_names_and_ids_rejected(self):
        """N5: `not x.get("name")` is falsy only for "", so " " passes as a real registered
        member name/MSSV, and that same " " is then accepted as reviewed_by."""
        make_project(self.root, members=[{"name": " ", "student_id": " "},
                                         {"name": "  ", "student_id": "  "},
                                         {"name": "   ", "student_id": "   "}])
        self.assertTrue(strict_errors(self.root))

    def test_N14_future_review_timestamp_rejected(self):
        """N14 (Low): reviewed_at only has to be timezone-aware; year 2999 (or a time before
        the footage file existed) is accepted."""
        make_project(self.root)
        write_review(self.root, lambda r: r["claims"]["c1"].update(reviewed_at="2999-01-01T00:00:00+00:00"))
        self.assertTrue(gate_errors(self.root))

    def test_N6a_malformed_review_json_returns_errors_not_traceback(self):
        """N6 (Low): review.json that is valid JSON of the wrong shape ([] / assets as a list /
        entry as a string) raises AttributeError out of validate()/build.py instead of a FAIL
        line. Still fails closed (non-zero exit) but unreadable for the humans."""
        make_project(self.root)
        for bad in ([], {"assets": []}, {"assets": {"a1": "yes"}}):
            _w(self.root, "review.json", bad)
            errors = strict_errors(self.root)
            self.assertTrue(errors)

    def test_N6b_malformed_group_json_returns_errors_not_traceback(self):
        """N6: team_members as a list of strings raises AttributeError in validate()."""
        make_project(self.root)
        g = _rd(self.root, "group.json")
        g["team_members"] = ["A", "B", "C"]
        _w(self.root, "group.json", g)
        self.assertTrue(strict_errors(self.root))

    def test_N11_nfc_and_nfd_narration_hash_identically_for_audio(self):
        """N11 (Low, fail-closed): audio timing text_sha256 is computed over raw code points.
        Canonically-equivalent NFD narration (same speech) is reported as STALE AUDIO."""
        make_project(self.root)
        text_nfc = "Núi lửa Kīlauea"
        text_nfd = unicodedata.normalize("NFD", text_nfc)
        self.assertNotEqual(text_nfc, text_nfd)
        n = {"language": "vi", "segments": [{"index": 1, "text": text_nfd}]}
        _w(self.root, "narration.json", n)
        (self.root / "assets/audio/01.mp3").write_bytes(b"mp3")
        _w(self.root, "assets/audio/01.timings.json", {
            "provider": "edge-tts", "text_sha256": hashlib.sha256(text_nfc.encode()).hexdigest(),
            "boundaries": [{"text": "a", "start_seconds": 0, "duration_seconds": 1}]})
        _, errors = review_gate.audio_evidence(self.root, n)
        self.assertEqual([e for e in errors if "STALE" in e], [])

    def test_N16_narration_digest_independent_of_line_endings(self):
        """N16 (Low, fail-closed): narration approval hashes raw file bytes (not canonical JSON
        like assets/claims), so git autocrlf on Windows or an editor re-save invalidates every
        approval without any content change."""
        make_project(self.root)
        args = (_rd(self.root, "assets.json")["assets"], _rd(self.root, "claims.json")["claims"],
                _rd(self.root, "narration.json"))
        pretty = json.dumps(args[2], ensure_ascii=False, indent=2)
        (self.root / "narration.json").write_bytes(pretty.replace("\n", "\n").encode())
        lf = review_gate.evidence_hashes(self.root, *args)["narration_sha256"]
        (self.root / "narration.json").write_bytes(pretty.replace("\n", "\r\n").encode())
        crlf = review_gate.evidence_hashes(self.root, *args)["narration_sha256"]
        self.assertEqual(lf, crlf)


# --------------------------------------------------------------------------
# build_provenance
# --------------------------------------------------------------------------
class ProvenanceTests(TempProject):
    def _receipt_project(self):
        make_project(self.root)
        for name in ("build.py", "subtitles.py", "voiceover.py", "review_gate.py",
                     "build_provenance.py", "media_audit.py", "science_gate.py", "pipeline.py"):
            (self.root / name).write_text("# stub " + name)
        (self.root / "output").mkdir()
        mp4 = self.root / "output/GE1013_Kilauea_2018_DRAFT.mp4"
        mp4.write_bytes(b"synthetic mp4 bytes")
        build_provenance.write_build_receipt(self.root, mp4)
        return mp4

    def test_receipt_detects_changed_footage_review_and_group(self):
        mp4 = self._receipt_project()
        self.assertEqual(build_provenance.verify_build_receipt(self.root, mp4), [])
        (self.root / "assets/a2.mp4").write_bytes(b"swapped" * 900)
        self.assertTrue(any("a2.mp4" in e for e in build_provenance.verify_build_receipt(self.root, mp4)))
        (self.root / "assets/a2.mp4").write_bytes(bytes([2]) * 4096)
        g = _rd(self.root, "group.json")
        g["group_number"] = "T2"
        _w(self.root, "group.json", g)
        self.assertTrue(any("group.json" in e for e in build_provenance.verify_build_receipt(self.root, mp4)))
        make_project(self.root)
        write_review(self.root, lambda r: r["script"].update(reviewed_by="Tester B"))
        self.assertTrue(any("review.json" in e for e in build_provenance.verify_build_receipt(self.root, mp4)))

    def test_missing_receipt_and_wrong_output_name_rejected(self):
        mp4 = self._receipt_project()
        other = self.root / "output/other.mp4"
        other.write_bytes(mp4.read_bytes())
        self.assertTrue(any("wrong or missing" in e for e in build_provenance.verify_build_receipt(self.root, other)))
        (self.root / "output/build_manifest.json").unlink()
        self.assertTrue(any("No build_manifest" in e for e in build_provenance.verify_build_receipt(self.root, mp4)))

    def test_receipt_contains_no_member_names_or_ids(self):
        self._receipt_project()
        text = (self.root / "output/build_manifest.json").read_text(encoding="utf-8")
        for needle in ("Tester A", "TEST-A", "student_id"):
            self.assertNotIn(needle, text)

    def test_scene_audio_and_timings_enter_receipt_inputs(self):
        make_project(self.root)
        add_tts_audio(self.root)
        files = build_provenance.inputs_for(self.root)
        self.assertIn("assets/audio/01.mp3", files)
        self.assertIn("assets/audio/03.timings.json", files)
        self.assertNotIn("assets/voiceover.wav", files)

    def test_N8_receipt_covers_the_gate_code_itself(self):
        """N8 (Low-Med): inputs_for hashes build/review_gate/science_gate/media_audit... but
        NOT validate.py (the strict gate), qa.py, or review_hashes.py. Weakening validate.py
        after a render does not stale the receipt. (AGENTS.md says build code is bound.)"""
        make_project(self.root)
        self.assertIn("validate.py", build_provenance.inputs_for(self.root))

    def test_N6c_receipt_with_wrong_json_shape_returns_error_list(self):
        """N6: a build_manifest.json holding a JSON list raises AttributeError (only OSError,
        ValueError, KeyError are caught)."""
        mp4 = self._receipt_project()
        (self.root / "output/build_manifest.json").write_text("[]")
        self.assertTrue(build_provenance.verify_build_receipt(self.root, mp4))

    def test_N9_error_messages_do_not_leak_absolute_paths(self):
        """N9 (Low, PII): 'Could not verify build receipt: [Errno 2] ... <absolute path>' embeds
        the local home directory / OS username in console and CI logs."""
        mp4 = self._receipt_project()
        (self.root / "group.json").unlink()
        errors = build_provenance.verify_build_receipt(self.root, mp4)
        self.assertTrue(errors)
        self.assertNotIn(str(self.root), " ".join(errors))


# --------------------------------------------------------------------------
# qa.py
# --------------------------------------------------------------------------
class QaTests(unittest.TestCase):
    def _run(self, stderr, ffmpeg_present=True, duration=120.0):
        probe = json.dumps({"format": {"duration": str(duration)}, "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"},
            {"codec_type": "audio", "sample_rate": "48000", "duration": str(duration)}]})

        def fake_run(cmd, **kwargs):
            if cmd[0] == "ffprobe":
                return SimpleNamespace(returncode=0, stdout=probe, stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr=stderr)

        def which(name):
            return "/bin/" + name if (name == "ffprobe" or ffmpeg_present) else None
        with tempfile.TemporaryDirectory() as d:
            _w(d, "timeline.json", DEFAULT_TIMELINE)
            _w(d, "assets.json", {"assets": [_asset(1), _asset(2)]})
            _w(d, "narration.json", {"language": "vi", "segments": [{"index": 1, "text": "t"}]})
            out = Path(d) / "x.mp4"
            out.write_bytes(b"x")
            with patch.object(qa, "validate", return_value=[]), \
                 patch.object(qa, "verify_build_receipt", return_value=[]), \
                 patch.object(qa.shutil, "which", side_effect=which), \
                 patch.object(qa.subprocess, "run", side_effect=fake_run), \
                 contextlib.redirect_stdout(io.StringIO()):
                return qa.run_qa(Path(d), out)

    def test_silent_audio_rejected(self):
        # Exact volumedetect output for digital silence.
        silence = "mean_volume: -91.0 dB\nmax_volume: -91.0 dB"
        self.assertTrue(any("not audible" in e for e in self._run(silence)))

    def test_normal_audio_passes(self):
        self.assertEqual(self._run("mean_volume: -25.0 dB\nmax_volume: -6.2 dB"), [])

    def test_wrong_length_and_missing_audio_rejected(self):
        self.assertTrue(any("Length outside" in e for e in self._run("max_volume: -6 dB", duration=95)))

    def test_stale_receipt_errors_propagate(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.mp4"
            out.write_bytes(b"x")
            with patch.object(qa, "validate", return_value=[]), \
                 patch.object(qa, "verify_build_receipt", return_value=["Stale build: input changed or missing: x"]), \
                 patch.object(qa.shutil, "which", return_value=None):
                errors = qa.run_qa(Path(d), out)
        self.assertIn("Stale build: input changed or missing: x", errors)

    def test_N7a_missing_ffmpeg_must_not_silently_skip_audibility(self):
        """N7a (Medium, fail-open): when ffmpeg is absent (ffprobe present) the loudness check is
        skipped without any error or warning and QA can PASS with a silent video."""
        self.assertTrue(self._run("max_volume: -inf dB", ffmpeg_present=False))

    def test_N7b_unmeasurable_peak_must_not_pass(self):
        """N7b (Medium, fail-open): if volumedetect output cannot be parsed qa.py only prints a
        WARNING and returns no error."""
        self.assertTrue(self._run("garbled output without volumedetect lines"))

    def test_N7c_peak_of_minus_47_db_is_not_audible_narration(self):
        """N7c (F7 PARTIAL, Low-Med): audibility threshold is global peak > -48 dBFS, so a nearly
        inaudible track, or one loud click in an otherwise silent video, passes. No per-scene
        narration, mean-volume or silencedetect check exists."""
        self.assertTrue(self._run("mean_volume: -70.0 dB\nmax_volume: -47.0 dB"))


# --------------------------------------------------------------------------
# build.py with mocked FFmpeg
# --------------------------------------------------------------------------
class BuildMainTests(unittest.TestCase):
    """Real FFmpeg (no mocked renderer). Fixture media are lavfi test signals, never footage."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        # Encoder preset only; every guard and filter graph is the production one.
        fast = [x if x != "medium" else "ultrafast" for x in build.VIDEO_ARGS]
        for patcher in (patch.object(build, "VIDEO_ARGS", fast),
                        patch.object(build, "FONT_PATH", next(f for f in build.FONTS if Path(f).is_file()))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _build(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return build.build_draft(self.root, **kwargs)

    def test_F3_recorded_voice_flow_does_not_touch_subtitles(self):
        make_renderable_project(self.root, mode="recorded", speech=(60.0,))
        with patch.object(build, "generate_subtitles", side_effect=AssertionError("subtitles called")):
            final = self._build()  # README flow: plain `render`, no --no-subtitles
        self.assertTrue(final.is_file())
        self.assertFalse((self.root / "output/captions.srt").exists())

    def test_F8_legacy_voiceover_longer_than_available_time_is_refused(self):
        segments = DEFAULT_TIMELINE["segments"]  # 120 s total, 10 s intro -> 110 s available
        tone(self.root / "long.wav", 110.5)
        with self.assertRaisesRegex(ValueError, "NEVER trim"):
            build.build_audio(segments, {}, self.root / "long.wav", self.root / "a.m4a", cwd=self.root)
        self.assertFalse((self.root / "a.m4a").exists())
        tone(self.root / "fits.wav", 109.5)
        out = build.build_audio(segments, {}, self.root / "fits.wav", self.root / "b.m4a", cwd=self.root)
        self.assertAlmostEqual(build.probe_length(out), 120.0, delta=0.05)

    def test_F8_scene_narration_longer_than_scene_is_refused(self):
        segments = [{"duration": 2}, {"duration": 3}]
        tone(self.root / "s1.mp3", 3.5)
        with self.assertRaisesRegex(ValueError, "never silently trim"):
            build.build_audio(segments, {1: self.root / "s1.mp3"}, None, self.root / "a.m4a", cwd=self.root)
        self.assertFalse((self.root / "a.m4a").exists())

    def test_scene_audio_is_padded_never_trimmed_and_stays_in_sync(self):
        segments = [{"duration": 2}, {"duration": 3}, {"duration": 2.5}]
        tone(self.root / "s1.mp3", 2.0)
        tone(self.root / "s2.mp3", 1.0)
        out = build.build_audio(segments, {1: self.root / "s1.mp3", 2: self.root / "s2.mp3"},
                                None, self.root / "a.m4a", cwd=self.root)
        self.assertAlmostEqual(build.probe_length(out), 7.5, delta=0.05)
        for start, length, audible in ((0, 1.9, False), (2.05, 1.9, True), (4.1, 0.8, False), (5.05, 0.9, True)):
            level = qa.volume(out, start, length)
            self.assertEqual(level["max"] > -30, audible, (start, level))

    def test_tts_scene_mode_flags_synthetic_voice_for_outro_label(self):
        make_renderable_project(self.root, mode="tts")
        seen = []
        real = build.make_card
        with patch.object(build, "make_card", side_effect=lambda f, s, i, g, a: (seen.append(dict(g)), real(f, s, i, g, a))):
            self._build(no_subtitles=True)
        self.assertTrue(seen and all(g.get("_synthetic_voice") is True for g in seen))

    def test_N13_concat_list_uses_ffmpeg_quoting_even_with_apostrophe_in_path(self):
        """N13 FIXED: concat.txt quoting verified by REAL ffmpeg on a path containing an apostrophe."""
        folder = self.root / "o'brien seg"
        folder.mkdir()
        parts = []
        for k in range(2):
            ffmpeg("-f", "lavfi", "-i", "testsrc2=size=64x64:rate=30", "-frames:v", 15,
                   *build.VIDEO_ARGS, folder / f"{k}.mp4")
            parts.append(folder / f"{k}.mp4")
        listing = folder / "concat.txt"
        listing.write_text("".join(build.concat_line(x) for x in parts))
        for line in listing.read_text().splitlines():
            self.assertRegex(line, r"^file '")
        ffmpeg("-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", self.root / "joined.mp4")
        self.assertEqual(build.count_frames(self.root / "joined.mp4"), 30)


# --------------------------------------------------------------------------
# pipeline.py wiring
# --------------------------------------------------------------------------
class PipelineWiring(unittest.TestCase):
    def _steps(self, argv):
        seen = []
        with patch.object(pipeline, "step", side_effect=lambda *a: seen.append([str(x) for x in a])), \
             patch.object(sys, "argv", ["pipeline.py", *argv]), contextlib.redirect_stdout(io.StringIO()):
            pipeline.main()
        return seen

    def test_prepare_no_tts_no_subtitles_runs_only_validate_and_download(self):
        self.assertEqual(self._steps(["prepare", "--no-tts", "--no-subtitles"]),
                         [["validate.py"], ["download_assets.py"]])

    def test_prepare_default_runs_tts_then_subtitles(self):
        names = [s[0] for s in self._steps(["prepare"])]
        self.assertEqual(names, ["validate.py", "download_assets.py", "voiceover.py", "subtitles.py"])

    def test_render_always_strict_validates_builds_then_qa(self):
        self.assertEqual(self._steps(["render"]), [["validate.py", "--strict"], ["build.py"], ["qa.py"]])
        self.assertIn("--no-subtitles", self._steps(["render", "--no-subtitles"])[1])


# --------------------------------------------------------------------------
# Repository invariants (read-only)
# --------------------------------------------------------------------------
class RepoInvariants(unittest.TestCase):
    def test_review_example_covers_all_ids_and_approves_nothing(self):
        ex = _rd(ROOT, "review.example.json")
        asset_ids = {a["id"] for a in _rd(ROOT, "assets.json")["assets"]}
        claim_ids = {c["id"] for c in _rd(ROOT, "claims.json")["claims"]}
        self.assertEqual(set(ex["assets"]), asset_ids)
        self.assertEqual(set(ex["claims"]), claim_ids)
        flat = json.dumps(ex)
        self.assertNotIn("true", flat.replace("false", ""))  # no approved/*_checked true value
        for section in ("script", "logos", "audio", "timeline"):
            self.assertIs(ex[section]["approved"], False)
            self.assertEqual(ex[section]["reviewed_by"], "")

    def test_example_review_and_placeholder_group_cannot_pass_strict(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_project(root)
            _w(root, "group.json", _rd(ROOT, "group.example.json"))
            _w(root, "review.json", _rd(ROOT, "review.example.json"))
            errors = strict_errors(root)
        self.assertTrue(any("Real group member" in e for e in errors))
        self.assertTrue(any("Human provenance/rights approval missing" in e for e in errors))

    def test_no_pii_media_or_approvals_tracked_by_git(self):
        try:
            out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("not a git checkout")
        bad = [p for p in out.splitlines()
               if re.search(r"(^|/)(group|review)\.json$|\.(mp4|mov|mp3|wav|sha256|pdf)$|(^|/)\.env$", p)]
        self.assertEqual(bad, [])

    def test_ci_installs_and_requires_ffmpeg_with_least_privilege(self):
        """F2 FIXED: CI must fail when ffmpeg/ffprobe/fonts are missing."""
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("apt-get install -y ffmpeg fonts-dejavu-core", ci)
        self.assertIn("command -v ffmpeg", ci)
        self.assertIn("command -v ffprobe", ci)
        self.assertNotRegex(ci, r"ffmpeg -version[^\n]*\|\s*head")
        self.assertRegex(ci, r"permissions:\s*\n\s+contents: read")
        self.assertNotIn("pull_request_target", ci)
        self.assertNotRegex(ci, r"secrets\.")

    def test_build_font_path_hook_exists_for_smoke_test_patching(self):
        """F2 FIXED: tests patch build.FONT_PATH; it must exist or patch.multiple raises."""
        self.assertTrue(hasattr(build, "FONT_PATH"))


if __name__ == "__main__":
    unittest.main()
