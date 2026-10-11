"""Batch 3: readable, collision-free layout; TTS-timed burned-in subtitles; synthetic-voice disclosure."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

import build
import footage_report
from fixture_project import ffmpeg
from subtitles import align_to_script, group_boundaries

FONT = next(f for f in build.FONTS if Path(f).is_file())


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def frame(path, t):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(t), "-i", str(path),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return Image.frombytes("L", (build.W, build.H), raw)


class AlignmentTests(unittest.TestCase):
    def words(self, *texts):
        return [{"start_seconds": k * 0.5, "duration_seconds": 0.4, "text": t} for k, t in enumerate(texts)]

    def test_merged_date_boundary_keeps_script_punctuation(self):
        script = "USGS ghi hình vào ngày 16 tháng 5. Đây là thật."
        aligned = align_to_script(self.words("USGS", "ghi", "hình", "vào", "ngày 16 tháng 5", "Đây", "là", "thật"), script)
        self.assertEqual([w["text"] for w in aligned][3:6], ["vào", "ngày 16 tháng 5.", "Đây"])
        self.assertEqual(aligned[-1]["text"], "thật.")
        self.assertEqual([w["start_seconds"] for w in aligned], [k * 0.5 for k in range(8)])  # timing untouched

    def test_mismatch_falls_back_to_none(self):
        self.assertIsNone(align_to_script(self.words("Núi", "lửa", "khác"), "Núi lửa Kīlauea."))
        self.assertIsNone(align_to_script(self.words("Núi"), "Núi lửa Kīlauea."))  # unspoken script words

    def test_nfd_script_aligns(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "Núi lửa.")
        self.assertEqual([w["text"] for w in align_to_script(self.words("Núi", "lửa"), nfd)], ["Núi", "lửa."])

    def test_cues_fit_two_lines(self):
        with patch.object(build, "FONT_PATH", FONT):
            words = self.words(*("dung nham chảy vào biển tạo ra luồng hơi khí nguy hiểm gọi là laze".split()))
            for _, _, text in group_boundaries(words):
                image, box = build.subtitle_image(text)
                self.assertGreaterEqual(box[1], build.SUB_TOP)
                self.assertLessEqual(box[3], build.SUB_BOTTOM)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(build, "FONT_PATH", FONT)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_longest_real_texts_do_not_collide(self):
        timeline = json.loads((build.ROOT / "timeline.json").read_text(encoding="utf-8"))
        credit = max((a["agency_credit"] for a in json.loads((build.ROOT / "assets.json").read_text())["assets"]), key=len)
        disclosure = "Giọng đọc tổng hợp (AI) · Edge TTS"
        for seg in timeline["segments"]:
            if seg["kind"] != "video":
                continue
            image = Image.new("RGBA", (build.W, build.H))
            d = ImageDraw.Draw(image)
            boxes = [build.draw_top_box(d, seg), build.draw_credit(d, credit), build.draw_disclosure(d, disclosure),
                     build.subtitle_image("Dòng dung nham từ khe nứt số 8 tiến đến vịnh Kapoho và bắt đầu")[1]]
            for k, a in enumerate(boxes):
                self.assertTrue(0 <= a[0] and a[2] <= build.W and 0 <= a[1] and a[3] <= build.H, a)
                for b in boxes[k + 1:]:
                    self.assertFalse(overlap(a, b), (seg["heading"], a, b))
            self.assertLessEqual(boxes[0][3], build.TOP_MAX)

    def test_overlong_scientific_caption_is_refused_not_truncated(self):
        d = ImageDraw.Draw(Image.new("RGBA", (build.W, build.H)))
        with self.assertRaisesRegex(ValueError, "too long"):
            build.draw_top_box(d, {"heading": "H", "caption": "rất dài " * 60})

    def test_outro_card_label_and_disclosure_do_not_collide_with_subtitles(self):
        with tempfile.TemporaryDirectory() as tmp:
            boxes = build.make_card(Path(tmp) / "c.png", {"heading": "KĪLAUEA 2018", "caption": "Nguồn hình ảnh: USGS"},
                                    False, {"language": "vi"}, Path(tmp), "Giọng đọc tổng hợp (AI) · Edge TTS")
        band = (0, build.SUB_TOP, build.W, build.SUB_BOTTOM)
        self.assertEqual(len(boxes), 2)
        self.assertFalse(any(overlap(b, band) for b in boxes))
        self.assertFalse(overlap(boxes[0], boxes[1]))


class BurnInTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        for patcher in (patch.object(build, "FONT_PATH", FONT),):
            patcher.start()
            self.addCleanup(patcher.stop)

    def band_brightness(self, path, t):
        return max(frame(path, t).crop((0, build.SUB_TOP, build.W, build.SUB_BOTTOM)).getdata())

    def test_cue_visible_only_inside_its_tts_window_on_footage(self):
        ffmpeg("-f", "lavfi", "-i", "color=c=0x202020:s=640x360:r=30", "-t", 4, "-c:v", "libx264",
               "-pix_fmt", "yuv420p", self.dir / "src.mp4")
        item = {"id": "x", "filename": "src.mp4", "agency_credit": "USGS test credit"}
        seg = {"kind": "video", "asset_id": "x", "duration": 3, "heading": "H", "caption": "C"}
        out = build.render_video(1, seg, {"x": item}, {}, self.dir, self.dir, [(1.0, 2.0, "Núi lửa Kīlauea")],
                                 "Giọng đọc tổng hợp (AI) · Edge TTS")
        self.assertLess(self.band_brightness(out, 0.5), 100)
        self.assertGreater(self.band_brightness(out, 1.5), 200)
        self.assertLess(self.band_brightness(out, 2.5), 100)
        label = frame(out, 0.2).crop((300, build.LABEL_Y - 20, 780, build.LABEL_Y + 20))
        self.assertGreater(max(label.getdata()), 150)  # disclosure visible for the whole scene
        self.assertEqual(build.count_frames(out), 90)

    def test_card_scene_cues(self):
        out = build.render_video(5, {"kind": "outro", "duration": 2, "heading": "KĪLAUEA", "caption": "Nguồn"},
                                 {}, {"language": "vi"}, self.dir, self.dir, [(0.5, 1.5, "Cảnh báo hiểm họa")])
        self.assertLess(self.band_brightness(out, 0.2), 100)
        self.assertGreater(self.band_brightness(out, 1.0), 200)


class FootageReportTests(unittest.TestCase):
    def test_recommends_clean_window_and_pillarbox_crop_without_editing_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            # 1920x1080 file with a 720-wide picture (pillar-boxed) and a 2 s USGS-style black slate at 0-2 s.
            ffmpeg("-f", "lavfi", "-i", "testsrc2=size=720x1080:rate=30", "-t", 12, "-vf",
                   "pad=1920:1080:600:0:black,drawbox=c=black:t=fill:enable='lt(t,2)'",
                   "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", root / "assets/clip.mp4")
            (root / "assets.json").write_text(json.dumps({"assets": [{"id": "c", "filename": "clip.mp4"}]}))
            timeline = {"segments": [{"kind": "intro", "duration": 1},
                                     {"kind": "video", "asset_id": "c", "duration": 6}, {"kind": "outro", "duration": 1}]}
            (root / "timeline.json").write_text(json.dumps(timeline))
            before = hashlib.sha256((root / "timeline.json").read_bytes()).hexdigest()
            row = footage_report.report(root)[0]
            self.assertFalse(row["current_window_clean"])
            self.assertGreaterEqual(row["suggested_start_seconds"], 2.0)
            self.assertEqual(row["suggested_crop_of_bars"], {"w": 720, "h": 1080, "x": 600, "y": 0})
            self.assertTrue((root / row["preview"]).is_file())
            self.assertIn("RECOMMENDATION ONLY", row["status"])
            self.assertEqual(before, hashlib.sha256((root / "timeline.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
