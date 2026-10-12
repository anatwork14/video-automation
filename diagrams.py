#!/usr/bin/env python3
"""Team-made explanatory diagrams (plain vector drawings), clearly labelled, never presented as footage.

Generates assets/diagram_tsunami_1..3.png for a project root: a three-step build of
how a sudden seafloor shove makes a tsunami (shove -> water column rises -> long
waves spread). Every image carries "Illustration, not to scale (team-made)".
Deterministic: same code -> same bytes. Writes .sha256 and .provenance.json
(origin "team_made", generator diagrams.py) so media_audit can verify the files.
It must be approved by a human like any other asset (science wording + design).

Usage: python diagrams.py --root variants/volcano_hazards
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

import editorial
from project import take_root

W, H = 1000, 900
SEA, FLOOR, ROCK, INK = "#1f5f8b", "#3a2a1a", "#7a5c3a", "#0d1b2a"
STEPS = ["The seafloor is suddenly shoved", "The whole water column rises", "Long waves race outward"]
LABEL = "Illustration, not to scale (team-made)"


def panel(d, top, step, shown):
    title_face = editorial.body(40, 800)
    colour = "#FFB547" if shown else "#4a5866"
    d.text((40, top), f"{step + 1}  {STEPS[step]}", font=title_face, fill=colour)
    sea, floor = top + 110, top + 230
    if not shown:
        d.rounded_rectangle((40, sea - 30, W - 40, floor + 20), radius=14, outline="#2b3a48", width=3)
        return
    d.rectangle((40, sea, W - 40, floor), fill=SEA)
    if step == 0:  # floor block jumps up with an arrow
        d.polygon([(40, floor), (440, floor), (520, floor - 40), (W - 40, floor - 40), (W - 40, floor + 22),
                   (40, floor + 22)], fill=ROCK)
        d.line([(480, floor + 10), (480, floor - 70)], fill="white", width=7)
        d.polygon([(462, floor - 64), (498, floor - 64), (480, floor - 94)], fill="white")
        return
    d.rectangle((40, floor, W - 40, floor + 22), fill=ROCK)
    if step == 1:  # hump of water above the shove
        d.polygon([(330, sea), (500, sea - 52), (670, sea)], fill=SEA)
        d.line([(500, floor - 8), (500, sea - 40)], fill="white", width=5)
    else:  # two waves moving apart
        for cx in (230, 770):
            d.polygon([(cx - 120, sea), (cx, sea - 38), (cx + 120, sea)], fill=SEA)
        d.text((500, sea + 50), "←     →", font=editorial.body(44, 800), fill="white", anchor="mm")


def draw(step_count):
    image = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(image)
    for step in range(3):
        panel(d, 30 + step * 280, step, step < step_count)
    d.text((W - 30, H - 18), LABEL, font=editorial.body(24, 600), fill="#cfd8e3", anchor="rs")
    return image


def write(root):
    out = Path(root) / "assets"
    out.mkdir(parents=True, exist_ok=True)
    code = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    made = []
    for k in (1, 2, 3):
        path = out / f"diagram_tsunami_{k}.png"
        draw(k).save(path, optimize=False)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
        path.with_suffix(".provenance.json").write_text(json.dumps({
            "id": path.stem, "origin": "team_made", "generator": "diagrams.py", "generator_sha256": code,
            "download_url": None, "source_page": None, "bytes": path.stat().st_size, "sha256": digest,
            "note": "Team-made explanatory illustration, not to scale; not footage.",
        }, indent=2) + "\n", encoding="utf-8")
        made.append(path)
    return made


def main(argv=None):
    root, _ = take_root(argv)
    for path in write(root):
        print("Team-made diagram:", path.as_posix())


if __name__ == "__main__":
    main()
