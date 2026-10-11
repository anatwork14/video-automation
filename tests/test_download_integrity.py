"""Downloader fails closed on truncated/corrupt transfers and records full provenance (real ffprobe/ffmpeg)."""
import contextlib
import http.client
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import download_assets
import media_audit
from fixture_project import _asset, ffmpeg


class Resp:
    def __init__(self, body, url, headers=None, fail_after=None):
        self.body, self.url, self.headers, self.fail_after, self.sent = body, url, headers or {}, fail_after, 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def geturl(self):
        return self.url

    def read(self, n=-1):
        if self.fail_after is not None and self.sent >= self.fail_after:
            raise http.client.IncompleteRead(b"", 10)
        out, self.body = self.body[:n], self.body[n:]
        self.sent += len(out)
        return out


class DownloadIntegrity(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        clip = self.root / "clip.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30", "-t", 3, "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", clip)
        self.mp4 = clip.read_bytes()
        self.item = _asset(1)

    def get(self, body, **kw):
        response = Resp(body, self.item["download_url"], **kw)
        with patch.object(download_assets.urllib.request, "urlopen", return_value=response), \
             contextlib.redirect_stdout(io.StringIO()):
            return download_assets.get_one(self.item, self.root)

    def assertNothingTrusted(self):
        leftovers = sorted(p.name for p in (self.root / "assets").glob("*"))
        self.assertEqual(leftovers, [])

    def test_valid_download_records_url_etag_sha_and_media(self):
        dest = self.get(self.mp4, headers={"Content-Length": str(len(self.mp4)), "ETag": '"abc"',
                                           "Last-Modified": "Wed, 05 Nov 2025 05:29:41 GMT"})
        record = json.loads(dest.with_suffix(".provenance.json").read_text())
        self.assertEqual(record["download_url"], self.item["download_url"])
        self.assertEqual(record["etag"], '"abc"')
        self.assertEqual(record["bytes"], len(self.mp4))
        self.assertEqual(record["sha256"], media_audit.hash_video(dest))
        self.assertEqual((record["media"]["width"], record["media"]["height"]), (320, 180))
        self.assertAlmostEqual(record["media"]["duration_seconds"], 3.0, delta=0.1)
        self.assertEqual(download_assets.get_one(self.item, self.root), dest)  # idempotent re-verify

    def test_short_body_vs_content_length_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Truncated download"):
            self.get(self.mp4[: len(self.mp4) // 2], headers={"Content-Length": str(len(self.mp4))})
        self.assertNothingTrusted()

    def test_incomplete_read_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Truncated download"):
            self.get(self.mp4, fail_after=256 * 1024 if len(self.mp4) > 256 * 1024 else 0)
        self.assertNothingTrusted()

    def test_undecodable_media_without_length_header_rejected(self):
        corrupt = self.mp4[:4096] + bytes(len(self.mp4) - 4096)
        with self.assertRaises(Exception):
            self.get(corrupt)
        self.assertNothingTrusted()

    def test_manifest_url_change_invalidates_existing_download(self):
        self.get(self.mp4)
        self.item["download_url"] = self.item["download_url"].replace("a1.mp4", "other.mp4")
        with self.assertRaisesRegex(RuntimeError, "different URL"):
            download_assets.get_one(self.item, self.root)


if __name__ == "__main__":
    unittest.main()
