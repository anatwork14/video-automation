import json
import unittest
from pathlib import Path

from validate import validate
from subtitles import chunks, stamp

ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_non_strict_structure(self):
        self.assertEqual(validate(strict=False), [])

    def test_duration(self):
        data = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(s["duration"] for s in data["segments"]), 120)

    def test_unique_asset_ids(self):
        data = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))
        ids = [x["id"] for x in data["assets"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_subtitle_chunks(self):
        self.assertEqual(chunks("Một hai ba bốn", 2), ["Một hai", "ba bốn"])
        self.assertEqual(stamp(62.5), "00:01:02,500")

    def test_strict_requires_private_approval(self):
        # The public repository is deliberately missing group.json / review.json
        if not (ROOT / "group.json").exists():
            self.assertTrue(any("group.json" in x for x in validate(strict=True)))


if __name__ == "__main__":
    unittest.main()
