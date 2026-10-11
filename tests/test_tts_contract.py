"""Network-free regression tests of actual edge-tts boundary request."""
import asyncio
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import voiceover


class FreeTTSTests(unittest.TestCase):
    def test_word_boundary_is_explicitly_requested(self):
        parameters = {}
        class FakeCommunicate:
            def __init__(self, **kwargs):
                parameters.update(kwargs)
            async def stream(self):
                yield {"type": "audio", "data": b"x" * 2048}
                yield {"type": "WordBoundary", "offset": 1000000,
                       "duration": 1200000, "text": "Núi"}
        with tempfile.TemporaryDirectory() as directory:
            module = types.SimpleNamespace(Communicate=FakeCommunicate)
            with patch.dict(sys.modules, {"edge_tts": module}), \
                 patch.object(voiceover, "ROOT", Path(directory)), \
                 patch.object(voiceover, "probe_duration", return_value=2.0):
                asyncio.run(voiceover.synthesize_segment(1, "Núi lửa", 10.0,
                                                         "vi-VN-NamMinhNeural", "+0%"))
                self.assertEqual(parameters["boundary"], "WordBoundary")
                self.assertEqual(parameters["voice"], "vi-VN-NamMinhNeural")
                meta = json.loads((Path(directory) / "assets/audio/01.timings.json").read_text())
                self.assertEqual(meta["boundaries"][0]["text"], "Núi")
                self.assertEqual(meta["text_sha256"], hashlib.sha256("Núi lửa".encode()).hexdigest())

    def test_wrong_script_fails_before_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "assets/audio").mkdir(parents=True)
            (base / "assets/audio/01.mp3").write_bytes(b"z" * 2048)
            (base / "assets/audio/01.timings.json").write_text(json.dumps({
                "text_sha256": hashlib.sha256("old script".encode()).hexdigest(),
                "voice": "vi-VN-NamMinhNeural", "rate": "+0%"
            }))
            with patch.object(voiceover, "ROOT", base), \
                 patch.object(voiceover, "probe_duration", return_value=2.0):
                with self.assertRaisesRegex(ValueError, "stale"):
                    asyncio.run(voiceover.synthesize_segment(1, "new script", 9.0,
                                                             "vi-VN-NamMinhNeural", "+0%"))


if __name__ == "__main__":
    unittest.main()
