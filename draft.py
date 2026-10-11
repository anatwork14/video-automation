#!/usr/bin/env python3
"""Render an UNAPPROVED review draft so the team can watch it BEFORE approving anything.

- Uses timeline.proposed.json (editorial proposals: start_seconds, crop, intro/outro
  background footage, field-audio beds) when present, else timeline.json.
- Enforces every technical gate: manifest structure, science registry, English-only
  (for English narration), source hashes + provenance, TTS audio bound to the current
  script, and post-render technical QA.
- Does NOT require, read, create or imply approvals or signatures. Every frame carries
  a red "REVIEW DRAFT · NOT APPROVED" watermark, so it cannot pass for a release.
- Missing private information (group.json) and logos are rendered as explicit
  placeholders; nothing is invented.

Output: <root>/output/<name>.mp4, .srt and <name>.manifest.json (default name GE1013_Kilauea_2018_DRAFT).
The approved release path is still: validate --strict -> build.py -> qa.py -> release_check.py.
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import build
from build_provenance import tool_versions
from media_audit import audit as audit_media
from qa import technical_problems
from review_gate import audio_evidence, sha256_file, sha256_object
from validate import english_problems, validate

ROOT = Path(__file__).resolve().parent
DRAFT_NAME = "GE1013_Kilauea_2018_DRAFT.mp4"
WATERMARK = "REVIEW DRAFT · NOT APPROVED · DO NOT UPLOAD"
PROJECT_FILES = ("assets.json", "claims.json", "narration.json")


def placeholder_group(language):
    return {"group_number": "[TBD]", "course": "Earth Science (GE1013)", "language": language,
            "team_members": [{"name": "[Member names]", "student_id": "[student IDs: added locally]"}]}


def prepare_workspace(root, timeline_file):
    """output/review_workspace: copies of the project JSON + the chosen timeline, assets symlinked."""
    workspace = root / "output" / "review_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    for name in PROJECT_FILES:
        shutil.copyfile(root / name, workspace / name)
    shutil.copyfile(root / timeline_file, workspace / "timeline.json")
    os.symlink(os.path.relpath(root / "assets", workspace), workspace / "assets")
    narration = json.loads((root / "narration.json").read_text(encoding="utf-8"))
    placeholders = []
    group_file = root / "group.json"
    if group_file.is_file():
        group = json.loads(group_file.read_text(encoding="utf-8"))
        if not str(group.get("group_number", "")).strip():
            group["group_number"] = "[number missing]"
            placeholders.append("group.json has no group_number: shown as [number missing]")
    else:
        group = placeholder_group(narration.get("language"))
        placeholders.append("group.json missing: group number, member names and student IDs shown as placeholders")
    if not (root / "assets/logos_from_assignment.png").is_file():
        placeholders.append("assets/logos_from_assignment.png missing: logo placeholder shown")
    (workspace / "group.json").write_text(json.dumps(group, ensure_ascii=False, indent=2), encoding="utf-8")
    return workspace, group, narration, placeholders


def gate(workspace, group, narration):
    errors = validate(strict=False, root=workspace)
    errors += audit_media(workspace)
    if narration.get("language") == "en":
        timeline = json.loads((workspace / "timeline.json").read_text(encoding="utf-8"))
        errors += english_problems(timeline["segments"], narration, group)
    evidence, audio_errors = audio_evidence(workspace, narration, group)
    errors += audio_errors
    return errors, evidence


def render_review_draft(root=ROOT, timeline_file=None, no_subtitles=False, watermark=True, voice_label=True,
                        name=DRAFT_NAME):
    root = Path(root)
    if timeline_file is None:
        timeline_file = "timeline.proposed.json" if (root / "timeline.proposed.json").is_file() else "timeline.json"
    workspace, group, narration, placeholders = prepare_workspace(root, timeline_file)
    errors, evidence = gate(workspace, group, narration)
    if errors or not evidence:
        for issue in errors or ["No usable narration audio"]:
            print("STOP:", issue)
        raise SystemExit(1)
    mode = evidence["mode"]
    # disclose unless a human recorded the voice, or the owner chose to omit the on-screen label
    synthetic = mode in ("edge_tts", "manual_scene") and voice_label
    rendered = build.render_film(workspace, group, synthetic, mode, no_subtitles,
                                 WATERMARK if watermark else None, name)
    problems = technical_problems(workspace, rendered)
    out = root / "output"
    final = out / name
    shutil.move(str(rendered), final)
    captions = workspace / "output" / "captions.srt"
    if captions.is_file():
        shutil.copyfile(captions, out / name.replace(".mp4", ".srt"))
    manifest = {
        "status": "UNAPPROVED_REVIEW_DRAFT",
        "watermark": WATERMARK if watermark else None,
        "synthetic_voice_label_on_screen": synthetic,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video_file": final.name, "video_sha256": sha256_file(final),
        "timeline_file": timeline_file,
        "timeline_sha256": sha256_object(json.loads((root / timeline_file).read_text(encoding="utf-8"))),
        "narration_sha256": sha256_object(narration), "audio_mode": mode, "audio_digest": evidence["sha256"],
        "placeholders": placeholders, "technical_qa_problems": problems,
        "tools": tool_versions(build.FONT_PATH),
        "note": "Not approved. The team must review sources, footage windows, script and audio, "
                "then approve + sign and render through build.py; only release_check.py may export FINAL.",
    }
    (out / name.replace(".mp4", ".manifest.json")).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    return final, problems, placeholders


def main(argv=None):
    from project import take_root
    root, argv = take_root(argv, ROOT)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timeline", default=None, help="timeline file (default: timeline.proposed.json if present)")
    parser.add_argument("--no-subtitles", action="store_true")
    parser.add_argument("--no-watermark", action="store_true",
                        help="omit the on-frame watermark (the file is STILL unapproved; manifest says so)")
    parser.add_argument("--name", default=DRAFT_NAME, help="output file name inside <root>/output")
    parser.add_argument("--no-voice-label", action="store_true",
                        help="omit the on-screen synthetic-voice label (owner's choice; disclose at upload instead)")
    args = parser.parse_args(argv)
    final, problems, placeholders = render_review_draft(root, args.timeline, args.no_subtitles,
                                                        watermark=not args.no_watermark,
                                                        voice_label=not args.no_voice_label,
                                                        name=args.name)
    for item in placeholders:
        print("PLACEHOLDER:", item)
    for problem in problems:
        print("QA FAIL:", problem, file=sys.stderr)
    note = "watermarked; do not upload" if not args.no_watermark else "no watermark at the owner's request"
    print("REVIEW DRAFT:", final.as_posix(), f"(UNAPPROVED; {note})")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
