"""Small synthetic TEST FIXTURE validates renderer wiring, NOT actual submitted footage."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build


class RenderSmokeTest(unittest.TestCase):
    def test_verified_source_render_codec(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "assets").mkdir()
            (folder / "segments").mkdir()
            test_input = folder / "assets" / "camera_source.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
                "-t", "1.2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(test_input),
            ], capture_output=True, text=True, check=True)
            font = next((x for x in build.FONTS if Path(x).is_file()), None)
            self.assertIsNotNone(font, "CI requires Unicode font to run actual renderer test")
            item = {
                "id": "test",
                "filename": test_input.name,
                "agency_credit": "Real footage in production; test pattern here",
            }
            scene = {
                "kind": "video", "asset_id": "test", "duration": 0.8,
                "heading": "VERIFIED MEDIA TEST", "caption": "Smoke test only",
            }
            with patch.multiple(build, ASSETS=folder / "assets",
                                TMP=folder / "segments", W=320, H=576,
                                FONT_PATH=font):
                output = build.render_video(1, scene, {"test": item}, {})
                self.assertTrue(output.exists())
                self.assertGreater(output.stat().st_size, 1000)
                info = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                    "-of", "csv=p=0", str(output)
                ], capture_output=True, text=True, check=True)
                self.assertIn("320,576", info.stdout)

    def test_short_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "assets").mkdir()
            (folder / "segments").mkdir()
            test_input = folder / "assets" / "short.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=256x144:r=15",
                "-t", ".5", "-c:v", "mpeg4", str(test_input)
            ], capture_output=True, text=True, check=True)
            scene = {"kind": "video", "asset_id": "short", "duration": 2.0}
            item = {"filename": test_input.name, "id": "short"}
            with patch.multiple(build, ASSETS=folder / "assets", TMP=folder / "segments"):
                with self.assertRaisesRegex(ValueError, "Insufficient REAL footage"):
                    build.render_video(1, scene, {"short": item}, {})


if __name__ == "__main__":
    unittest.main()
