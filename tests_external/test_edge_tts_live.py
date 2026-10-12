"""LIVE external-service test (Microsoft Edge read-aloud via edge-tts). NOT part of deterministic CI.

Run only on purpose:  RUN_EXTERNAL=1 python -m unittest discover -s tests_external -v
It sends one short test sentence to the online service and checks that word
boundaries (needed for subtitles) still arrive. Requires Internet + ffprobe.
"""
import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import voiceover  # noqa: E402


@unittest.skipUnless(os.environ.get("RUN_EXTERNAL") == "1", "set RUN_EXTERNAL=1 to call the live Edge TTS service")
class LiveEdgeTTS(unittest.TestCase):
    def test_vietnamese_voice_returns_word_boundaries(self):
        with tempfile.TemporaryDirectory() as d, patch.object(voiceover, "ROOT", Path(d)):
            asyncio.run(voiceover.synthesize_segment(1, "Núi lửa Kīlauea phun trào.", 10.0,
                                                     "vi-VN-NamMinhNeural", "-5%"))
            meta = (Path(d) / "assets/audio/01.timings.json").read_text(encoding="utf-8")
            self.assertIn('"provider": "edge-tts"', meta)
            self.assertIn("Kīlauea", meta)


if __name__ == "__main__":
    unittest.main()
