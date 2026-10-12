"""The GE1013 deliverable is 100% English: narration, on-screen text, labels, voice and course text."""
import json
import re
import unicodedata
import unittest
from pathlib import Path

import build
import validate
from voiceover import select_voice

ROOT = Path(__file__).resolve().parents[1]
# Printable ASCII plus the Hawaiian/typographic characters the script legitimately uses.
ALLOWED_EXTRA = set("īĪʻ·–—")
# Common unaccented Vietnamese words: catches Vietnamese typed without diacritics.
VIETNAMESE_WORDS = {"cua", "nhung", "duoc", "khong", "nguoi", "nham", "nui", "lua", "va", "mot", "cac",
                    "nay", "tai", "dinh", "vinh", "khe", "nut", "ngay", "thang", "nhom", "giong", "doc"}


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def screen_and_voice_texts():
    timeline, narration = read("timeline.json"), read("narration.json")
    texts = {f"narration scene {s['index']}": s["text"] for s in narration["segments"]}
    for i, seg in enumerate(timeline["segments"]):
        texts[f"timeline scene {i} heading"] = seg["heading"]
        texts[f"timeline scene {i} caption"] = seg["caption"]
    for item in read("assets.json")["assets"]:
        texts[f"credit {item['id']}"] = item["agency_credit"]
    texts["course"] = read("group.example.json")["course"]
    for key, value in build.LABELS["en"].items():
        texts[f"label {key}"] = value
    texts["voice disclosure"] = build.voice_disclosure({"language": "en", "_synthetic_voice": True}, "edge_tts")
    return texts


def problems(text):
    found = []
    nfc = unicodedata.normalize("NFC", text)
    bad = sorted({c for c in nfc if not (32 <= ord(c) < 127) and c not in ALLOWED_EXTRA})
    if bad:
        found.append(f"non-English characters {bad}")
    if validate.contains_vietnamese_prose(nfc):
        found.append("Vietnamese diacritics")
    words = set(re.findall(r"[a-z]+", nfc.lower())) & VIETNAMESE_WORDS
    if words:
        found.append(f"Vietnamese words {sorted(words)}")
    return found


class EnglishOnly(unittest.TestCase):
    def test_project_language_is_english(self):
        self.assertEqual(read("narration.json")["language"], "en")
        self.assertEqual(read("group.example.json")["language"], "en")

    def test_every_spoken_and_on_screen_text_is_english(self):
        for where, text in screen_and_voice_texts().items():
            self.assertEqual(problems(text), [], f"{where}: {text!r}")

    def test_strict_english_gate_accepts_this_project(self):
        timeline, narration = read("timeline.json"), read("narration.json")
        self.assertEqual(validate.english_problems(timeline["segments"], narration, read("group.example.json")), [])

    def test_gate_and_checker_catch_vietnamese_including_nfd_and_unaccented(self):
        for sample in ("Dung nham chảy ra biển", unicodedata.normalize("NFD", "Núi lửa"), "Dung nham chay ra bien"):
            self.assertTrue(problems(sample), sample)
        segments = [{"heading": "OK", "caption": "Dung nham chảy ra biển"}]
        self.assertTrue(validate.english_problems(segments, {"segments": []}, {"course": "Earth Science"}))

    def test_english_documentary_voice_is_the_default(self):
        self.assertEqual(select_voice("en", None), "en-US-GuyNeural")
        with self.assertRaises(ValueError):
            select_voice("en", "vi-VN-NamMinhNeural")

    def test_english_labels_are_selected_for_english_groups(self):
        self.assertIs(build.labels({"language": "en"}), build.LABELS["en"])
        self.assertEqual(set(build.LABELS["en"]), set(build.LABELS["vi"]))


if __name__ == "__main__":
    unittest.main()
