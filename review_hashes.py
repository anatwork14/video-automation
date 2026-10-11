#!/usr/bin/env python3
"""Show SHA256 digests to put in review.json AFTER a real member has reviewed each artifact.

This script NEVER modifies review.json and NEVER approves anything automatically.
Do not paste student names/IDs into the public repository.
"""
import json
from pathlib import Path
from review_gate import evidence_hashes

ROOT = Path(__file__).resolve().parent
assets = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))["assets"]
claims = json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))["claims"]
narration = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
print(json.dumps(evidence_hashes(ROOT, assets, claims, narration), ensure_ascii=False, indent=2))
print("\nThis is technical evidence ONLY. Verify source pages, rights, audio, and video yourself.")
