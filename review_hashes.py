#!/usr/bin/env python3
"""Show SHA256 digests to put in review.json AFTER a real member has reviewed each artifact.

This script NEVER modifies review.json and NEVER approves anything automatically.
It prints no student names/IDs. Do not paste personal data into the public repository.
"""
import json
from pathlib import Path

from review_gate import evidence_hashes, load_optional_json

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    from project import take_root
    root, _ = take_root(argv, ROOT)
    assets = json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]
    claims = json.loads((root / "claims.json").read_text(encoding="utf-8"))["claims"]
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))
    group = load_optional_json(root / "group.json", {})
    print(json.dumps(evidence_hashes(root, assets, claims, narration, group), ensure_ascii=False, indent=2))
    print("\nThis is technical evidence ONLY. Verify source pages, rights, audio, timeline and video yourself.")
    print("After review.json is final, EACH reviewer signs it with their own key (see RUNBOOK.md).")


if __name__ == "__main__":
    main()
