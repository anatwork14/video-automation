"""Review is tied to exact content; never trust string 'false' or an AI signature."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from review_gate import reviewer_problems, sha256_object, audio_evidence


class ReviewIntegrityTests(unittest.TestCase):
    def test_string_false_rejected(self):
        row = {"approved": "false", "rights_checked": "true",
               "reviewed_by": "AI", "reviewed_at": "not a date"}
        failures = reviewer_problems(row, {"Nguyễn Văn A"}, require_rights=True)
        self.assertTrue(any("boolean" in x for x in failures))
        self.assertTrue(any("real registered member" in x for x in failures))
        self.assertTrue(any("ISO8601" in x for x in failures))

    def test_valid_fields_need_registered_member_and_timezone(self):
        row = {"approved": True, "rights_checked": True,
               "reviewed_by": "Nguyễn Văn A", "reviewed_at": "2026-10-11T13:30:00+07:00"}
        self.assertEqual(reviewer_problems(row, {"Nguyễn Văn A"}, require_rights=True), [])

    def test_claim_hash_invalidated_by_text_change(self):
        claim = {"claim": "A", "reference": "https://www.usgs.gov"}
        original = sha256_object(claim)
        claim["claim"] = "B"
        self.assertNotEqual(original, sha256_object(claim))

    def test_tts_audio_metadata_cannot_be_stale_even_without_subtitles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets/audio").mkdir(parents=True)
            (root / "narration.json").write_text(json.dumps({"language": "vi",
                "segments": [{"index": 1, "text": "Lời dẫn mới"}]}))
            (root / "assets/audio/01.mp3").write_bytes(b"audio sample")
            (root / "assets/audio/01.timings.json").write_text(json.dumps({
                "provider": "edge-tts", "text_sha256": hashlib.sha256("Lời cũ".encode()).hexdigest(),
                "boundaries": [{"text": "Lời", "start_seconds": 0, "duration_seconds": 0.1}]
            }))
            _, errors = audio_evidence(root, {"segments": [{"index": 1, "text": "Lời dẫn mới"}]})
            self.assertTrue(any("STALE AUDIO" in problem for problem in errors))


if __name__ == "__main__":
    unittest.main()
