#!/usr/bin/env python3
"""Extract a coarse strip of logos from page 5 of the provided assignment PDF.
Review/replace it with official logos after extraction; the PDF is not committed.
"""
import sys
from pathlib import Path

try:
    import fitz
except ImportError as exc:
    raise SystemExit("Install requirements.txt (PyMuPDF) first") from exc

if len(sys.argv) != 2:
    raise SystemExit("Usage: python extract_logos.py /path/to/GE1013_TIKTOK.pdf")
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit("PDF not found: " + str(path))
doc = fitz.open(path)
if len(doc) < 5:
    raise SystemExit("Expected at least 5 PDF pages")
page = doc[4]
rect = page.rect
# Approximate logo strip on illustrated PDF page 5, requires visual review.
clip = fitz.Rect(rect.x0 + rect.width * .235,
                 rect.y0 + rect.height * .765,
                 rect.x0 + rect.width * .963,
                 rect.y0 + rect.height * .95)
target = Path(__file__).resolve().parent / "assets" / "logos_from_assignment.png"
target.parent.mkdir(exist_ok=True)
page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False).save(str(target))
print("Saved:", target)
print("STOP AND REVIEW: crop may need adjustments; logos and sponsors must match your class.")
