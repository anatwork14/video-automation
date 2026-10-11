"""Editorial renderer (TikTok-safe layout, Barlow Condensed + Manrope, multi-shot scenes, stills)."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

import build
import draft
import editorial
from fixture_project import _rd, _w, ffmpeg, make_renderable_project

TIMELINE = {"duration_seconds": 120, "style": "editorial", "segments": [
    {"kind": "intro", "layout": "hook", "duration": 3, "heading": "Hook", "caption": "",
     "hook_lines": ["Volcanoes can kill", "without lava"],
     "background": {"asset_id": "a1", "start_seconds": 1, "label": "Synthetic test pattern"}},
    {"kind": "intro", "layout": "title", "duration": 7, "heading": "When volcanoes turn deadly",
     "caption": "Earthquakes, ash clouds & tsunamis",
     "background": {"asset_id": "a2", "start_seconds": 2, "label": "Synthetic test pattern"}},
    {"kind": "video", "duration": 50, "kicker": "01 · Test", "heading": "Two shots in one scene",
     "caption": "A video shot, then a still image",
     "shots": [{"asset_id": "a1", "start_seconds": 4, "duration": 30, "label": "Test lab · 2026"},
               {"asset_id": "s1", "duration": 20, "label": "Test still · 1888"}]},
    {"kind": "video", "duration": 50, "heading": "Single asset scene", "caption": "Classic schema",
     "asset_id": "a2", "start_seconds": 0, "label": "Test lab · 2026"},
    {"kind": "outro", "layout": "credits", "duration": 10, "heading": "Sources",
     "credits": ["Footage: synthetic test patterns", "Science: none (test)"]},
]}


def setup_project(root):
    make_renderable_project(root, mode="tts", speech=(2.0, 8.0, 8.0, 4.0))
    narration = _rd(root, "narration.json")
    narration["segments"] = [{"index": i, "text": f"Scene {i} narration text"} for i in range(5)]
    _w(root, "narration.json", narration)
    Image.new("RGB", (1600, 1000), "#3a4a6a").save(root / "assets/s1.png")
    assets = _rd(root, "assets.json")
    assets["assets"].append({**assets["assets"][0], "id": "s1", "filename": "s1.png", "type": "historical_illustration",
                             "download_url": "https://www.ngdc.noaa.gov/x/s1.png",
                             "source_page": "https://www.ngdc.noaa.gov/x"})
    _w(root, "assets.json", assets)
    _w(root, "timeline.json", TIMELINE)
    claims = _rd(root, "claims.json")
    claims["claims"] = [dict(claims["claims"][0], id=f"c{i}", scene=i) for i in range(5)]
    _w(root, "claims.json", claims)
    from fixture_project import add_tts_audio, _source_provenance, tone
    import review_gate
    for i in range(5):
        tone(root / f"assets/audio/{i:02d}.mp3", 1.5)
        words = f"Scene {i} narration text".split()
        _w(root, f"assets/audio/{i:02d}.timings.json", {
            "provider": "edge-tts", "voice": "test", "rate": "+0%", "duration_seconds": 1.5,
            "text_sha256": review_gate.text_sha256(f"Scene {i} narration text"),
            "audio_sha256": review_gate.sha256_file(root / f"assets/audio/{i:02d}.mp3"),
            "boundaries": [{"start_seconds": 0.1 + 0.3 * k, "duration_seconds": 0.25, "text": w}
                           for k, w in enumerate(words)]})
    _source_provenance(root, assets["assets"][-1])


class EditorialRender(unittest.TestCase):
    def test_full_editorial_draft_renders_and_passes_technical_qa(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            setup_project(root)
            fast = [x if x != "medium" else "ultrafast" for x in build.VIDEO_ARGS]
            with patch.object(build, "VIDEO_ARGS", fast), contextlib.redirect_stdout(io.StringIO()):
                final, problems, _ = draft.render_review_draft(root, "timeline.json", name="TEST_EDITORIAL.mp4",
                                                               watermark=False, voice_label=False)
            self.assertEqual(problems, [])
            self.assertEqual(build.count_frames(final), 3600)
            self.assertTrue((root / "output/TEST_EDITORIAL.manifest.json").is_file())

    def test_layout_stays_in_tiktok_safe_area_and_does_not_collide(self):
        image = Image.new("RGBA", (build.W, build.H))
        d = ImageDraw.Draw(image)
        seg = {"kicker": "03 · Tsunami mechanism", "heading": "Why most tsunamis start with an earthquake",
               "caption": "A sudden shove of the seafloor lifts the whole water column above it"}
        box = editorial.draw_box(d, seg)
        tag = editorial.draw_tag(d, "SATELLITE OBSERVATION · NOAA GOES-17 · Tonga · 15 Jan 2022", box[3] + 16)
        credit = editorial.draw_credit(d, "Credit: NOAA / CIRA (GOES-17) · public domain")
        sub = editorial.subtitle_image("Hunga Tonga‑Hunga Haʻapai blasted a plume into the mesosphere")[1]
        for b in (box, tag, credit, sub):
            self.assertTrue(editorial.SAFE_L <= b[0] and b[2] <= editorial.SAFE_R, b)
            self.assertTrue(140 <= b[1] and b[3] <= 1500, b)
        for a, b in ((box, tag), (tag, sub), (sub, credit)):
            self.assertLessEqual(a[3], b[1], (a, b))

    def test_okina_has_a_glyph_in_body_text(self):
        self.assertEqual(editorial.body_text("Haʻapai"), "Ha‘apai")

    def test_overlong_heading_refused(self):
        d = ImageDraw.Draw(Image.new("RGBA", (build.W, build.H)))
        with self.assertRaisesRegex(ValueError, "too long"):
            editorial.draw_box(d, {"heading": "very long heading " * 20})


if __name__ == "__main__":
    unittest.main()
