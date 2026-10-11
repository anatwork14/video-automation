"""Tests for deterministic, source-text-bound free TTS captions (no external TTS request)."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import hashlib
from subtitles import group_boundaries, stamp, generate
from voiceover import select_voice, text_digest


class SpeechTests(unittest.TestCase):
    def test_vi_default_voice(self):
        self.assertEqual(select_voice("vi", None), "vi-VN-NamMinhNeural")
        with self.assertRaises(ValueError):
            select_voice("vi", "en-US-GuyNeural")

    def test_boundary_grouping(self):
        words = [
            {"start_seconds": 0, "duration_seconds": .3, "text": "Núi"},
            {"start_seconds": .31, "duration_seconds": .3, "text": "lửa"},
            {"start_seconds": 2.1, "duration_seconds": .4, "text": "Kīlauea"},
        ]
        self.assertEqual([x[2] for x in group_boundaries(words)], ["Núi lửa", "Kīlauea"])
        self.assertEqual(stamp(70.2), "00:01:10,200")

    def test_subtitles_reject_stale_script(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets" / "audio").mkdir(parents=True)
            (root / "timeline.json").write_text(json.dumps({
                "segments": [{"kind": "intro", "duration": 5}, {"kind": "video", "duration": 10}]
            }))
            (root / "narration.json").write_text(json.dumps({
                "segments": [{"index": 1, "text": "Bản đã sửa."}]
            }))
            (root / "assets" / "audio" / "01.timings.json").write_text(json.dumps({
                "text_sha256": text_digest("Nội dung cũ"),
                "duration_seconds": 4,
                "boundaries": [{"start_seconds": 0, "duration_seconds": 1, "text": "cũ"}],
            }))
            with self.assertRaisesRegex(ValueError, "script differs"):
                generate(root)

    def test_subtitles_absolute_timestamps(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets" / "audio").mkdir(parents=True)
            (root / "timeline.json").write_text(json.dumps({
                "segments": [{"kind": "intro", "duration": 10}, {"kind": "video", "duration": 22}]
            }))
            (root / "narration.json").write_text(json.dumps({
                "segments": [{"index": 1, "text": "Lửa nóng"}]
            }))
            (root / "assets" / "audio" / "01.timings.json").write_text(json.dumps({
                "text_sha256": text_digest("Lửa nóng"),
                "duration_seconds": 4,
                "boundaries": [
                    {"start_seconds": 1., "duration_seconds": .5, "text": "Lửa"},
                    {"start_seconds": 1.6, "duration_seconds": .5, "text": "nóng"}
                ]
            }))
            s = generate(root).read_text()
            self.assertIn("00:00:11,000 --> 00:00:12,100", s)
            self.assertIn("Lửa nóng", s)


if __name__ == "__main__":
    unittest.main()
