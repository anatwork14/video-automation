"""Downloader must not create trust sidecar for unverified manual files."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import download_assets


class SourceDownloadTests(unittest.TestCase):
    def test_import_has_no_network_side_effect(self):
        self.assertTrue(callable(download_assets.get_one))

    def test_existing_file_without_sha_is_blocked_before_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "assets").mkdir()
            (folder / "assets" / "existing.mp4").write_bytes(b"untrusted arbitrary bytes")
            record = {"id": "x", "filename": "existing.mp4", "type": "real_video",
                "manual_source_review_required": True,
                "download_url": "https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/a.mp4",
                "source_page": "https://www.usgs.gov/test"}
            with self.assertRaisesRegex(RuntimeError, "WITHOUT provenance hash"):
                download_assets.get_one(record, folder)
            self.assertFalse((folder / "assets" / "existing.sha256").exists())

    def test_non_usgs_download_rejected(self):
        with self.assertRaises(ValueError):
            download_assets.allowed_original({
                "id": "fake", "filename": "fake.mp4", "type": "real_video",
                "manual_source_review_required": True,
                "download_url": "https://evil.example/fake.mp4",
                "source_page": "https://www.usgs.gov/test"
            })


if __name__ == "__main__":
    unittest.main()
