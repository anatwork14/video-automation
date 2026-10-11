"""Build manifest detects any changed scientific script or MP4 output."""
import tempfile
import unittest
from pathlib import Path

from build_provenance import write_build_receipt, verify_build_receipt


class BuildReceiptTests(unittest.TestCase):
    def test_stale_script_and_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "assets").mkdir()
            (root / "output").mkdir()
            (root / "assets/logos_from_assignment.png").write_bytes(b"logo")
            for p in ["assets.json","claims.json","narration.json","timeline.json",
                      "group.json","review.json","build.py","subtitles.py",
                      "voiceover.py","review_gate.py"]:
                (root / p).write_text("{}")
            (root / "assets.json").write_text('{"assets":[]}')
            (root / "narration.json").write_text('{"segments":[]}')
            (root / "assets/voiceover.wav").write_bytes(b"narration audio")
            final = root / "output/GE1013_Kilauea_2018_DRAFT.mp4"
            final.write_bytes(b"rendered MP4 placeholder for HASH test only")
            write_build_receipt(root, final)
            self.assertEqual(verify_build_receipt(root, final), [])
            (root / "narration.json").write_text('{"segments":[],"changed":true}')
            self.assertTrue(any("narration.json" in x for x in verify_build_receipt(root, final)))

    def test_changed_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "assets").mkdir()
            (root / "output").mkdir()
            (root / "assets/logos_from_assignment.png").write_bytes(b"logo")
            for p in ["assets.json","claims.json","narration.json","timeline.json",
                      "group.json","review.json","build.py","subtitles.py",
                      "voiceover.py","review_gate.py"]:
                (root / p).write_text("{}")
            (root / "assets.json").write_text('{"assets":[]}')
            (root / "narration.json").write_text('{"segments":[]}')
            (root / "assets/voiceover.wav").write_bytes(b"voice")
            final = root / "output/GE1013_Kilauea_2018_DRAFT.mp4"
            final.write_bytes(b"old rendered file")
            write_build_receipt(root, final)
            final.write_bytes(b"tampered")
            self.assertTrue(any("MP4 differs" in x for x in verify_build_receipt(root, final)))


if __name__ == "__main__":
    unittest.main()
