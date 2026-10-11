"""Verify reviewer signatures over the exact bytes of review.json (OpenSSH `ssh-keygen -Y`).

Digests prove WHAT was approved; signatures make each approval attributable to
a reviewer's private key instead of to whoever can edit a JSON file. Public keys
live in the git-tracked reviewers.allowed_signers, so substituting a key is a
visible, reviewable commit.

Limits (documented, not solvable in code): anyone holding an unlocked private
key, or allowed to commit a new public key, can still sign. Never sign for
someone else; automation must never sign.
"""
import re
import shutil
import subprocess
from pathlib import Path

NAMESPACE = "ge1013-review"
ALLOWED_SIGNERS = "reviewers.allowed_signers"
SIGNATURE_DIR = "review.sigs"
PRINCIPAL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
SECTIONS = ("script", "logos", "audio", "timeline")


def reviewer_names(review):
    names = set()
    if not isinstance(review, dict):
        return names
    rows = []
    for key in ("assets", "claims"):
        if isinstance(review.get(key), dict):
            rows.extend(review[key].values())
    rows.extend(review.get(key) for key in SECTIONS)
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("reviewed_by"), str) and row["reviewed_by"].strip():
            names.add(row["reviewed_by"])
    return names


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def trust_anchor_problems(root):
    """reviewers.allowed_signers must be committed and unmodified."""
    if not shutil.which("git"):
        return ["git is required to verify that reviewers.allowed_signers is committed"]
    if _git(root, "ls-files", "--error-unmatch", ALLOWED_SIGNERS).returncode:
        return [f"{ALLOWED_SIGNERS} must be committed to git (public keys only)"]
    if _git(root, "status", "--porcelain", "--", ALLOWED_SIGNERS).stdout.strip():
        return [f"{ALLOWED_SIGNERS} has uncommitted changes; commit them so key changes are reviewable"]
    return []


def verify_review_signatures(root, group, review_bytes, review):
    root = Path(root)
    if not shutil.which("ssh-keygen"):
        return ["ssh-keygen (OpenSSH 8.1+) is required to verify reviewer signatures"]
    allowed = root / ALLOWED_SIGNERS
    if not allowed.is_file():
        return [f"Missing {ALLOWED_SIGNERS}: commit each reviewer's SSH public key (see RUNBOOK.md)"]
    errors = trust_anchor_problems(root)
    members = group.get("team_members", []) if isinstance(group, dict) else []
    by_name = {}
    for number, member in enumerate(members, 1):
        if isinstance(member, dict) and isinstance(member.get("name"), str):
            by_name[member["name"]] = (number, member.get("reviewer_id"))
    names = reviewer_names(review)
    if not names:
        errors.append("review.json names no reviewers; nothing can be verified")
    for name in sorted(names):
        number, principal = by_name.get(name, (None, None))
        if number is None:
            continue  # review_gate reports unregistered reviewers without echoing names
        if not isinstance(principal, str) or not PRINCIPAL.fullmatch(principal):
            errors.append(f"group.json team_members[{number}] needs a reviewer_id matching {ALLOWED_SIGNERS}")
            continue
        signature = root / SIGNATURE_DIR / f"{principal}.sig"
        if not signature.is_file():
            errors.append(f"Missing {SIGNATURE_DIR}/{principal}.sig (reviewer must sign the final review.json)")
            continue
        result = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", principal,
             "-n", NAMESPACE, "-s", str(signature)],
            input=review_bytes, capture_output=True,
        )
        if result.returncode:
            errors.append(f"Signature of reviewer_id {principal} does not verify for the current review.json")
    return errors
