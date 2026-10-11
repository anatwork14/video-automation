---
name: video-render-qa
description: Assemble 9:16 documentary from approved real footage and validate delivery quality.
---

# Render & QA
1. Require group.json, review.json, downloaded originals, logo and narration before final render.
2. Preserve originals' aspect ratios with letterboxing (do not misleadingly crop).
3. Target 120 s, allow 108–132 s, 1080x1920, audible narration, original source credit and course intro.
4. Detect/fix subtitle timing only from human-reviewed narration; do not invent speech.
5. Run validate.py --strict, build.py, qa.py; review the rendered video visually and aurally.
6. DRAFT output is never equivalent to published/approved. Do not auto upload to TikTok or course form.
