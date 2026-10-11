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
        final = self.render(fast=False)  # production encoder settings, burned-in TTS-timed subtitles
        srt = (self.root / "output/captions.srt").read_text(encoding="utf-8")
        self.assertIn("00:00:10,000 --> ", srt)  # scene 1 cue starts exactly at the scene start
        self.assertIn("Scene 1 narration text", srt)
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
        import review_gate
        timings = _rd(self.root, "assets/audio/02.timings.json")  # consistent (but silent) TTS output
        timings["audio_sha256"] = review_gate.sha256_file(self.root / "assets/audio/02.mp3")
        _w(self.root, "assets/audio/02.timings.json", timings)
        write_review(self.root)  # a human re-approved the (silent) audio; QA must still catch it
        self.render(no_subtitles=True)
        errors = self.qa()
        self.assertTrue(any(e.startswith("scene 2: narration not audible") for e in errors), errors)

    def test_release_check_requires_signed_human_approval_of_this_exact_mp4(self):
        import release_check
        from fixture_project import WHEN, sign_file
        make_renderable_project(self.root, mode="tts")
        final = self.render(no_subtitles=True)

        def problems():
            with contextlib.redirect_stdout(io.StringIO()):
                return release_check.release_problems(self.root)
        self.assertTrue(any("Missing or invalid output/final_review.json" in e for e in problems()))
        approval = {"video_sha256": __import__("review_gate").sha256_file(final), "approved": True,
                    "watched_full_video": True, "listened_full_audio": True,
                    "checked_captions_and_credits": True, "reviewed_by": "Tester A", "reviewed_at": WHEN}
        _w(self.root, "output/final_review.json", approval)
        self.assertTrue(any("Missing output/final_review.sigs/tester-0.sig" in e for e in problems()))
        sign_file(self.root, "tester-0", "output/final_review.json", "output/final_review.sigs")
        self.assertEqual(problems(), [])
        _w(self.root, "output/final_review.json", dict(approval, listened_full_audio=False))
        sign_file(self.root, "tester-0", "output/final_review.json", "output/final_review.sigs")
        self.assertTrue(any("listened_full_audio must be boolean true" in e for e in problems()))
        _w(self.root, "output/final_review.json", approval)
        sign_file(self.root, "tester-0", "output/final_review.json", "output/final_review.sigs")
        self.render(no_subtitles=False)  # re-render: a different MP4 nobody has watched
        self.assertTrue(any("approves a different MP4" in e for e in problems()))


if __name__ == "__main__":
    unittest.main()
