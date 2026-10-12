"""Small synthetic TEST FIXTURE validates renderer wiring with REAL FFmpeg, NOT submitted footage.

FFmpeg is mandatory: these tests fail (not skip) when it is missing, as in CI.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build


def make_input(path, seconds, size="640x360"):
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30",
        "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ], capture_output=True, text=True, check=True)


class RenderSmokeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        (self.folder / "assets").mkdir()
        (self.folder / "segments").mkdir()
        font = next((x for x in build.FONTS if Path(x).is_file()), None)
        self.assertIsNotNone(font, "CI requires Unicode font to run actual renderer test")
        patcher = patch.object(build, "FONT_PATH", font)
        patcher.start()
        self.addCleanup(patcher.stop)

    def render(self, scene, item):
        return build.render_video(1, scene, {item["id"]: item}, {}, self.folder / "assets", self.folder / "segments")

    def test_verified_source_render_codec(self):
        make_input(self.folder / "assets/camera_source.mp4", 1.2)
        item = {"id": "test", "filename": "camera_source.mp4",
                "agency_credit": "Real footage in production; test pattern here"}
        scene = {"kind": "video", "asset_id": "test", "duration": 0.8,
                 "heading": "VERIFIED MEDIA TEST", "caption": "Smoke test only"}
        output = self.render(scene, item)
        info = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
            "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets", "-of", "csv=p=0", str(output)
        ], capture_output=True, text=True, check=True)
        self.assertEqual(info.stdout.strip(), "1080,1920,30/1,24")  # exactly 0.8 s * 30 fps

    def test_short_source_is_rejected(self):
        make_input(self.folder / "assets/short.mp4", 0.6)
        scene = {"kind": "video", "asset_id": "short", "duration": 2.0}
        with self.assertRaisesRegex(ValueError, "Insufficient REAL footage"):
            self.render(scene, {"filename": "short.mp4", "id": "short"})

    def test_start_seconds_window_must_fit(self):
        make_input(self.folder / "assets/clip.mp4", 2.0)
        scene = {"kind": "video", "asset_id": "c", "duration": 1.5, "start_seconds": 1.0}
        with self.assertRaisesRegex(ValueError, "Insufficient REAL footage"):
            self.render(scene, {"filename": "clip.mp4", "id": "c"})

    def test_crop_is_applied_and_bounds_checked(self):
        make_input(self.folder / "assets/wide.mp4", 1.0, size="1920x1080")
        item = {"id": "w", "filename": "wide.mp4", "agency_credit": "test"}
        scene = {"kind": "video", "asset_id": "w", "duration": 0.5, "heading": "H", "caption": "C",
                 "crop": {"w": 608, "h": 1080, "x": 656, "y": 0}}
        self.assertTrue(self.render(scene, item).is_file())
        scene["crop"] = {"w": 608, "h": 1080, "x": 1400, "y": 0}
        with self.assertRaisesRegex(ValueError, "outside the 1920x1080 source"):
            self.render(scene, item)


if __name__ == "__main__":
    unittest.main()
