"""`--root DIR` support: run any tool on another project folder with the same layout.

The repository root is the original Kīlauea project; alternative videos live in
variants/<name>/ (assets.json, claims.json, narration.json, timeline.json, assets/,
output/). Code and fonts are always taken from the repository.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent


def take_root(argv=None, default=REPO):
    """Return (project root, remaining argv) after removing `--root DIR`."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            raise SystemExit("--root needs a directory")
        root = Path(argv[i + 1]).resolve()
        del argv[i:i + 2]
        if not (root / "timeline.json").is_file():
            raise SystemExit(f"{root} is not a project folder (no timeline.json)")
        return root, argv
    return default, argv
