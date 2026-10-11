"""Fail-closed source provenance and scientific registry tests."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from media_audit import hash_video, read_sha256
from science_gate import check_claims

ROOT = Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_current_manifest_has_evidence_per_scene(self):
        self.assertEqual(check_claims(ROOT), [])

    def test_kapoho_started_june3_not_june4(self):
        content = json.loads((ROOT / "claims.json").read_text())
        c = next(x for x in content["claims"] if x["id"] == "kapoho")
        self.assertIn("June 3", c["claim"])
        self.assertIn("June 4", c["claim"])

    def test_hash_sidecar_detects_mutation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "source.mp4"
            path.write_bytes(b"original bits")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            path.with_suffix(".sha256").write_text(digest + "  source.mp4\n")
            self.assertEqual(read_sha256(path), hash_video(path))
            path.write_bytes(b"tampered bits")
            self.assertNotEqual(read_sha256(path), hash_video(path))

    def test_claim_without_source_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "timeline.json").write_text(json.dumps({
                "segments": [{"kind": "intro", "duration": 10}, {"kind": "video", "duration": 15}]
            }))
            (root / "claims.json").write_text(json.dumps({"claims": [
                {"id": "x", "scene": 1, "claim": "Unproven but detailed false assertion",
                 "reference": "https://example.invalid", "evidence_note": "untested"}
            ]}))
            self.assertTrue(any("official USGS" in problem for problem in check_claims(root)))


if __name__ == "__main__":
    unittest.main()
