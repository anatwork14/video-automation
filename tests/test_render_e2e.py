"""End-to-end: strict validation -> REAL FFmpeg render -> qa.py, on a synthetic signed fixture.

The 'footage' is lavfi test patterns and the 'voice' is sine tones (fixture only).
This proves the pipeline mechanics, never the scientific content of a real video.
"""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
import qa
from fixture_project import _rd, _w, make_renderable_project


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_streams", "-show_format",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


class EndToEndRender(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patcher = patch.object(build, "FONT_PATH", next(f for f in build.FONTS if Path(f).is_file()))
        patcher.start()
        self.addCleanup(patcher.stop)

    def render(self, fast=True, **kwargs):
        args = [x if x != "medium" else "ultrafast" for x in build.VIDEO_ARGS] if fast else build.VIDEO_ARGS
        with patch.object(build, "VIDEO_ARGS", args), contextlib.redirect_stdout(io.StringIO()):
            return build.build_draft(self.root, **kwargs)

    def qa(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return qa.run_qa(self.root)

    def test_production_settings_render_passes_qa_and_detects_staleness(self):
        make_renderable_project(self.root, mode="tts")
        final = self.render(fast=False, no_subtitles=True)
        info = probe(final)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        self.assertEqual((video["width"], video["height"], video["r_frame_rate"]), (1080, 1920, "30/1"))
        self.assertEqual(int(video["nb_read_packets"]), 120 * 30)
        self.assertEqual((audio["codec_name"], audio["sample_rate"]), ("aac", "48000"))
        self.assertAlmostEqual(float(info["format"]["duration"]), 120.0, delta=0.05)
        self.assertEqual(self.qa(), [])
        receipt = _rd(self.root, "output/build_manifest.json")
        self.assertTrue(receipt["tools"]["ffmpeg"].startswith("ffmpeg version"))
        self.assertIn("validate.py", receipt["inputs"])
        timeline = _rd(self.root, "timeline.json")
        timeline["segments"][1]["caption"] = "edited after render"
        _w(self.root, "timeline.json", timeline)
        errors = self.qa()
        self.assertTrue(any("Stale build: input changed or missing: timeline.json" in e for e in errors), errors)
        self.assertTrue(any("Timeline (clip order" in e for e in errors), errors)

    def test_black_and_frozen_footage_are_reported_with_times(self):
        # a1 is used from start_seconds=1: black at 5-7 s and frozen grey at 20-23 s of the source.
        make_renderable_project(self.root, mode="tts", source_filters={
            "a1": "drawbox=c=black:t=fill:enable='between(t,5,7)',"
                  "drawbox=c=gray:t=fill:enable='between(t,20,23)'"})
        self.render(no_subtitles=True)
        errors = self.qa()
        self.assertTrue(any(e.startswith("Scene 1: black footage from 14.") for e in errors), errors)
        self.assertTrue(any(e.startswith("Scene 1: frozen footage from 29.") for e in errors), errors)
        self.assertFalse(any(e.startswith("Scene 2") for e in errors), errors)

    def test_silent_scene_narration_is_reported(self):
        make_renderable_project(self.root, mode="tts")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "anullsrc=r=48000:cl=stereo", "-t", "8", str(self.root / "assets/audio/02.mp3")], check=True)
        from fixture_project import write_review
        write_review(self.root)  # a human re-approved the (silent) audio; QA must still catch it
        self.render(no_subtitles=True)
        errors = self.qa()
        self.assertTrue(any(e.startswith("scene 2: narration not audible") for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
