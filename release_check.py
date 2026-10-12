#!/usr/bin/env python3
"""Final gate before a HUMAN uploads: technical QA + a signed human approval of THIS exact MP4.

Never uploads, publishes or submits anything. Passing it means: the rendered file
is the one the build receipt describes, it passes qa.py, and a registered member
declared (and signed) that they watched and listened to the whole file and checked
captions/credits. It does not certify scientific accuracy or rights.

output/final_review.json (written by a human, never by automation):
  {"video_sha256": "<sha256 of output/GE1013_Kilauea_2018_DRAFT.mp4>",
   "approved": true, "watched_full_video": true, "listened_full_audio": true,
   "checked_captions_and_credits": true,
   "reviewed_by": "<exact member name>", "reviewed_at": "<ISO8601 with timezone>"}
Signature: ssh-keygen -Y sign -f ~/.ssh/id_ed25519 -n ge1013-review output/final_review.json
           -> move output/final_review.json.sig to output/final_review.sigs/<reviewer_id>.sig
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from qa import OUTPUT, run_qa
from review_gate import load_optional_json, reviewer_problems, sha256_file
from review_signatures import verify_review_signatures

ROOT = Path(__file__).resolve().parent
FINAL_REVIEW = "output/final_review.json"
FINAL_SIGNATURES = "output/final_review.sigs"
DECLARATIONS = ("watched_full_video", "listened_full_audio", "checked_captions_and_credits")


def release_problems(root=ROOT, output=None):
    root = Path(root)
    output = Path(output) if output else root / "output" / OUTPUT.name
    errors = run_qa(root, output)
    path = root / FINAL_REVIEW
    try:
        raw = path.read_bytes()
        final = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError):
        return errors + [f"Missing or invalid {FINAL_REVIEW}: a member must watch the MP4 and approve it"]
    if not isinstance(final, dict):
        return errors + [f"{FINAL_REVIEW} must be a JSON object"]
    group = load_optional_json(root / "group.json", {})
    members = group.get("team_members", []) if isinstance(group, dict) else []
    names = {m["name"] for m in members if isinstance(m, dict) and isinstance(m.get("name"), str) and m["name"].strip()}
    errors.extend("Final review: " + p for p in reviewer_problems(final, names))
    for key in DECLARATIONS:
        if final.get(key) is not True:
            errors.append(f"Final review: {key} must be boolean true")
    if not output.is_file() or final.get("video_sha256") != sha256_file(output):
        errors.append("Final review approves a different MP4 (re-rendered since?); watch the new file and re-approve")
    who = final.get("reviewed_by")
    errors.extend(verify_review_signatures(root, group, raw, final, FINAL_SIGNATURES, FINAL_REVIEW,
                                           names=[who] if isinstance(who, str) and who in names else []))
    return errors


FINAL_NAME = "GE1013_Kilauea_2018_FINAL.mp4"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-final", action="store_true",
                        help=f"after a PASS, copy the approved MP4 to output/{FINAL_NAME}")
    args = parser.parse_args(argv)
    problems = release_problems(ROOT)
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print("RELEASE CHECK PASS for this exact MP4. Upload and submit MANUALLY; nothing was published.")
    if args.export_final:
        target = ROOT / "output" / FINAL_NAME
        shutil.copyfile(ROOT / "output" / OUTPUT.name, target)
        if sha256_file(target) != sha256_file(ROOT / "output" / OUTPUT.name):
            raise SystemExit("FINAL copy does not match the approved MP4")
        print("EXPORTED:", "output/" + FINAL_NAME, sha256_file(target))


if __name__ == "__main__":
    main()
