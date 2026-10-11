"""Production features: watermarked review draft (no approvals), background-footage cards, fades,
field-audio beds, loudness normalisation, new timeline fields, intro narration. REAL FFmpeg."""
import asyncio
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageStat

import build
import draft
import science_gate
import validate as validate_mod
import voiceover
from fixture_project import _rd, _w, ffmpeg, make_renderable_project, tone

FONT = next(f for f in build.FONTS if Path(f).is_file())


def frame(path, t):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(t), "-i", str(path),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (build.W, build.H), raw)


class ReviewDraft(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        fast = [x if x != "medium" else "ultrafast" for x in build.VIDEO_ARGS]
        for patcher in (patch.object(build, "VIDEO_ARGS", fast), patch.object(build, "FONT_PATH", FONT)):
            patcher.start()
            self.addCleanup(patcher.stop)
        make_renderable_project(self.root, mode="tts")
        # A draft needs NO approvals, signatures or private group data.
        for name in ("review.json", "group.json"):
            (self.root / name).unlink()
        timeline = _rd(self.root, "timeline.json")
        timeline["segments"][0]["background"] = {"asset_id": "a2", "start_seconds": 52 - 10}
        timeline["segments"][1]["start_seconds"] = 2
        _w(self.root, "timeline.proposed.json", timeline)

    def run_draft(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return draft.render_review_draft(self.root)

    def test_watermarked_unapproved_draft_from_proposal(self):
        final, problems, placeholders = self.run_draft()
        self.assertEqual(problems, [])
        self.assertEqual(final, self.root / "output/GE1013_Kilauea_2018_DRAFT.mp4")
        manifest = _rd(self.root, "output/GE1013_Kilauea_2018_DRAFT.manifest.json")
        self.assertEqual(manifest["status"], "UNAPPROVED_REVIEW_DRAFT")
        self.assertEqual(manifest["timeline_file"], "timeline.proposed.json")
        self.assertEqual(len(placeholders), 1)  # group placeholder (fixture has a logo)
        self.assertFalse((self.root / "review.json").exists())
        self.assertFalse((self.root / "output/build_manifest.json").exists())
        self.assertEqual(build.count_frames(final), 3600)
        for t in (1.0, 30.0, 115.0):  # red watermark pill on intro, footage and outro
            pill = frame(final, t).crop((400, build.WATERMARK_Y - 10, 680, build.WATERMARK_Y + 10))
            r, g, b = ImageStat.Stat(pill).mean
            self.assertGreater(r, g + 40, t)
        intro = ImageStat.Stat(frame(final, 5.0).convert("L").crop((0, 1300, 1080, 1360))).stddev[0]
        self.assertGreater(intro, 5)  # moving real-footage background, not a flat card
        first, settled = (ImageStat.Stat(frame(final, t).convert("L")).mean[0] for t in (0.0, 1.0))
        self.assertLess(first, settled)  # fade-in transition
        self.assertTrue((self.root / "output/GE1013_Kilauea_2018_DRAFT.srt").is_file())

    def test_stale_audio_stops_the_draft(self):
        narration = _rd(self.root, "narration.json")
        narration["segments"][0]["text"] += " Edited."
        _w(self.root, "narration.json", narration)
        with self.assertRaises(SystemExit):
            self.run_draft()
        self.assertFalse((self.root / "output/GE1013_Kilauea_2018_DRAFT.mp4").exists())


class AudioMix(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_field_audio_bed_and_loudness_normalisation(self):
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=320x180:r=30", "-f", "lavfi",
               "-i", "anoisesrc=color=pink:amplitude=0.3:sample_rate=48000", "-t", 12,
               "-c:v", "libx264", "-c:a", "aac", "-shortest", self.dir / "field.mp4")
        tone(self.dir / "voice.mp3", 3.0)
        segments = [{"duration": 4}, {"duration": 5}]
        out = build.build_audio(segments, {1: self.dir / "voice.mp3"}, None, self.dir / "mix.m4a", cwd=self.dir,
                                beds={0: (self.dir / "field.mp4", 2.0, -30.0), 1: (self.dir / "field.mp4", 6.0, -30.0)})
        level, peak = build.loudness(["-i", out], self.dir)
        self.assertAlmostEqual(level, build.TARGET_LUFS, delta=1.0)
        self.assertLessEqual(peak, -1.0)
        bed_only, _ = build.loudness(["-t", 3.5, "-i", out], self.dir)
        voiced, _ = build.loudness(["-ss", 4.2, "-t", 2.8, "-i", out], self.dir)
        self.assertGreater(voiced - bed_only, 8)  # the bed sits well under the narration

    def test_silent_field_audio_is_refused(self):
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=320x180:r=30", "-f", "lavfi", "-i", "anullsrc=r=48000",
               "-t", 6, "-c:v", "libx264", "-c:a", "aac", self.dir / "quiet.mp4")
        with self.assertRaisesRegex(ValueError, "source window is silent"):
            build.build_audio([{"duration": 4}], {}, None, self.dir / "m.m4a", cwd=self.dir,
                              beds={0: (self.dir / "quiet.mp4", 0.0, -30.0)})


class TimelineFields(unittest.TestCase):
    def check(self, mutate):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("assets.json", "claims.json", "narration.json", "timeline.json"):
                (root / name).write_bytes((build.ROOT / name).read_bytes())
            timeline = _rd(root, "timeline.json")
            mutate(timeline["segments"])
            _w(root, "timeline.json", timeline)
            return validate_mod.validate(strict=False, root=root)

    def test_valid_proposal_fields_pass(self):
        def ok(segs):
            segs[0]["background"] = {"asset_id": "may22_fissure22", "start_seconds": 60, "field_audio_lufs": -30}
            segs[1].update(start_seconds=6.9, crop={"w": 728, "h": 1080, "x": 598, "y": 0}, field_audio_lufs=-28)
        self.assertEqual(self.check(ok), [])

    def test_invalid_fields_rejected(self):
        cases = [
            (lambda s: s[1].update(field_audio_lufs=-6), "field_audio_lufs"),
            (lambda s: s[1].update(crop={"w": 728, "h": 1080, "x": 598}), "crop must be"),
            (lambda s: s[1].update(background={"asset_id": "may22_fissure22"}), "background is only allowed"),
            (lambda s: s[0].update(background={"asset_id": "nope"}), "unknown footage"),
            (lambda s: s[0].update(background={"asset_id": "may22_fissure22", "start_seconds": -1}), "start_seconds"),
        ]
        for mutate, needle in cases:
            errors = self.check(mutate)
            self.assertTrue(any(needle in e for e in errors), (needle, errors))


class IntroNarration(unittest.TestCase):
    def test_voiceover_accepts_the_intro_scene(self):
        class Fake:
            def __init__(self, **kw):
                pass

            async def stream(self):
                yield {"type": "audio", "data": b"x" * 2048}
                yield {"type": "WordBoundary", "offset": 0, "duration": 1_000_000, "text": "Hook"}
        with tempfile.TemporaryDirectory() as d:
            _w(d, "timeline.json", {"segments": [{"kind": "intro", "duration": 10}, {"kind": "video", "duration": 10}]})
            _w(d, "narration.json", {"language": "en", "segments": [{"index": 0, "text": "Hook."}]})
            with patch.dict(sys.modules, {"edge_tts": types.SimpleNamespace(Communicate=Fake)}), \
                 patch.object(voiceover, "ROOT", Path(d)), patch.object(voiceover, "probe_duration", return_value=2.0), \
                 patch.object(voiceover.shutil, "which", return_value="/bin/ffprobe"), \
                 contextlib.redirect_stdout(io.StringIO()):
                asyncio.run(voiceover.run(types.SimpleNamespace(voice=None, rate="+0%", force=False)))
            self.assertTrue((Path(d) / "assets/audio/00.timings.json").is_file())

    def test_narrated_intro_needs_a_claim(self):
        with tempfile.TemporaryDirectory() as d:
            _w(d, "timeline.json", {"segments": [{"kind": "intro", "duration": 5}, {"kind": "video", "duration": 5},
                                                  {"kind": "outro", "duration": 5}]})
            _w(d, "narration.json", {"segments": [{"index": 0, "text": "hook"}, {"index": 1, "text": "b"}]})
            claim = {"id": "x", "scene": 1, "claim": "A sufficiently long synthetic claim",
                     "reference": "https://www.usgs.gov/x", "evidence_note": "n"}
            _w(d, "claims.json", {"claims": [claim]})
            self.assertIn("Scene 0 has no scientific evidence", science_gate.check_claims(d))
            _w(d, "claims.json", {"claims": [claim, dict(claim, id="y", scene=0)]})
            self.assertEqual(science_gate.check_claims(d), [])


if __name__ == "__main__":
    unittest.main()


class OriginalScore(unittest.TestCase):
    def test_score_is_deterministic_exact_length_and_ducks_under_the_voice(self):
        import music
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            durations = [10, 22, 22, 26, 29, 11]
            a = music.build_score(durations, d / "a.wav")
            b = music.build_score(durations, d / "b.wav")
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertAlmostEqual(build.probe_length(a), 120.0, delta=0.01)
            # ducking: a voice in scene 1 pushes the score down; the voiceless part keeps it
            tone(d / "v.mp3", 6.0)
            segments = [{"duration": 10}, {"duration": 12}]
            out = build.build_audio(segments, {1: d / "v.mp3"}, None, d / "mix.m4a", cwd=d, music=(a, -27.0))
            music_only, _ = build.loudness(["-ss", 2, "-t", 6, "-i", out], d)
            with_voice, _ = build.loudness(["-ss", 10.5, "-t", 5, "-i", out], d)
            self.assertGreater(with_voice - music_only, 6)
            self.assertAlmostEqual(build.probe_length(out), 22.0, delta=0.05)

    def test_wrong_scene_count_is_refused(self):
        import music
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(ValueError, "written for 6 scenes"):
            music.build_score([60, 60], Path(d) / "x.wav")


class MusicGates(unittest.TestCase):
    def test_music_field_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("assets.json", "claims.json", "narration.json", "timeline.json"):
                (root / name).write_bytes((build.ROOT / name).read_bytes())
            for bad in ({"file": "song.mp3", "lufs": -27}, {"file": "assets/music/score.wav", "lufs": -6},
                        {"file": "assets/music/score.wav"}, "score.wav"):
                t = _rd(root, "timeline.json")
                t["music"] = bad
                _w(root, "timeline.json", t)
                self.assertTrue(any("music must be" in e for e in validate_mod.validate(root=root)), bad)

    def test_timeline_approval_binds_the_score_bytes(self):
        import review_gate
        from fixture_project import make_project, write_review
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_project(root)
            (root / "assets/music").mkdir()
            (root / "assets/music/score.wav").write_bytes(b"score v1")
            t = _rd(root, "timeline.json")
            t["music"] = {"file": "assets/music/score.wav", "lufs": -27}
            _w(root, "timeline.json", t)
            h = review_gate.evidence_hashes(root, _rd(root, "assets.json")["assets"],
                                            _rd(root, "claims.json")["claims"], _rd(root, "narration.json"))
            write_review(root, lambda r: r["timeline"].update(approved_music_sha256=h["music_sha256"]))

            def gate():
                return review_gate.check_reviews(root, _rd(root, "group.json"), _rd(root, "review.json"),
                                                 _rd(root, "assets.json")["assets"], _rd(root, "claims.json")["claims"],
                                                 _rd(root, "narration.json"))
            self.assertEqual(gate(), [])
            (root / "assets/music/score.wav").write_bytes(b"score v2")
            self.assertTrue(any("Background score" in e for e in gate()))


class WatermarkOption(unittest.TestCase):
    def test_overlay_without_watermark_has_no_red_pill(self):
        with tempfile.TemporaryDirectory() as d, patch.object(build, "FONT_PATH", FONT):
            seg = {"heading": "H", "caption": "C"}
            build.make_overlay(Path(d) / "with.png", seg, {"agency_credit": "USGS"}, None, "REVIEW DRAFT")
            build.make_overlay(Path(d) / "without.png", seg, {"agency_credit": "USGS"}, None, None)
            band = (300, build.WATERMARK_Y - 10, 780, build.WATERMARK_Y + 10)
            red = lambda p: ImageStat.Stat(Image.open(p).convert("RGBA").crop(band)).mean
            self.assertGreater(red(Path(d) / "with.png")[3], 100)    # opaque pill present
            self.assertEqual(red(Path(d) / "without.png")[3], 0)     # fully transparent
