"""Batch 4: CLI/rate parsing, import side effects, MP3<->timings binding (no network, no TTS service)."""
import asyncio
import contextlib
import importlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline
import review_gate
import voiceover
from fixture_project import _rd, _w, add_tts_audio, make_project


class RateParsing(unittest.TestCase):
    def test_negative_rate_reaches_voiceover_from_pipeline(self):
        seen = []
        with patch.object(pipeline, "step", side_effect=lambda *a: seen.append([str(x) for x in a])), \
             patch.object(sys, "argv", ["pipeline.py", "prepare", "--rate", "-5%"]), \
             contextlib.redirect_stdout(io.StringIO()):
            pipeline.main()
        self.assertIn(["voiceover.py", "--rate=-5%"], seen)

    def test_voiceover_cli_accepts_negative_and_positive_rates(self):
        for given, expected in ((["--rate", "-5%"], "-5%"), (["--rate=+8%"], "+8%"), ([], "+0%")):
            captured = {}

            async def fake_run(args):
                captured["rate"] = args.rate
            with patch.object(voiceover, "run", side_effect=fake_run):
                voiceover.main(given)
            self.assertEqual(captured["rate"], expected)

    def test_invalid_rate_rejected_before_any_tts(self):
        with tempfile.TemporaryDirectory() as d:
            _w(d, "timeline.json", {"segments": [{"duration": 5}, {"duration": 5}]})
            _w(d, "narration.json", {"language": "vi", "segments": [{"index": 1, "text": "a"}]})
            for bad in ("5%", "-5", "fast", "+1000%"):
                with patch.object(voiceover, "ROOT", Path(d)), patch.dict(sys.modules, {"edge_tts": None}):
                    with self.assertRaisesRegex(SystemExit, "signed percentage"):
                        asyncio.run(voiceover.run(types.SimpleNamespace(voice=None, rate=bad, force=False)))


class ImportSideEffects(unittest.TestCase):
    def test_scripts_do_nothing_when_imported(self):
        names = ["review_hashes", "voiceover_openai", "footage_report", "release_check", "pipeline", "qa",
                 "download_assets", "build", "media_audit"]
        try:
            importlib.import_module("fitz")
            names.append("extract_logos")
        except ImportError:
            pass
        with patch("subprocess.run", side_effect=AssertionError("subprocess at import")), \
             patch("urllib.request.urlopen", side_effect=AssertionError("network at import")), \
             patch.object(sys, "argv", ["x"]), contextlib.redirect_stdout(io.StringIO()) as out:
            for name in names:
                importlib.reload(importlib.import_module(name))
        self.assertEqual(out.getvalue(), "")


class TimingBinding(unittest.TestCase):
    def test_mp3_swapped_under_unchanged_timings_is_detected(self):
        """N22: a new MP3 next to an old timing file (half-written regeneration) must not pass."""
        with tempfile.TemporaryDirectory() as d:
            make_project(d)
            add_tts_audio(d)
            narration = _rd(d, "narration.json")
            self.assertEqual(review_gate.audio_evidence(d, narration)[1], [])
            (Path(d) / "assets/audio/02.mp3").write_bytes(b"regenerated audio")
            errors = review_gate.audio_evidence(d, narration)[1]
            self.assertTrue(any("Scene 2 MP3 does not match its timing file" in e for e in errors), errors)

    def test_voiceover_records_audio_digest(self):
        chunks = [{"type": "audio", "data": b"x" * 2048},
                  {"type": "WordBoundary", "offset": 0, "duration": 1_000_000, "text": "Núi"}]

        class Fake:
            def __init__(self, **kw):
                pass

            async def stream(self):
                for c in chunks:
                    yield c
        with tempfile.TemporaryDirectory() as d, \
                patch.dict(sys.modules, {"edge_tts": types.SimpleNamespace(Communicate=Fake)}), \
                patch.object(voiceover, "ROOT", Path(d)), patch.object(voiceover, "probe_duration", return_value=2.0), \
                contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(voiceover.synthesize_segment(1, "Núi", 10.0, "vi-VN-NamMinhNeural", "+0%"))
            meta = json.loads((Path(d) / "assets/audio/01.timings.json").read_text())
            self.assertEqual(meta["audio_sha256"], review_gate.sha256_file(Path(d) / "assets/audio/01.mp3"))


if __name__ == "__main__":
    unittest.main()
