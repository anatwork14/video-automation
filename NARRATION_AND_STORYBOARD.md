# Kīlauea 2018 — narration & storyboard (English deliverable)

**DRAFT. The final GE1013 video is 100% English** (narration, on-screen text, labels, course text, voice).
Source dates were checked against USGS text by the team's research step; the video may only be submitted after the team approves content and footage.
Real USGS footage only (no AI-generated images or video). The default narration voice is the **synthetic** Edge TTS voice `en-US-GuyNeural`, disclosed on screen.

| Time | Authentic footage and on-screen text |
|---|---|
| 00–10 s | Intro: video title, group number, 3–5 names + student IDs, GE1013 course name, university/course/sponsor logos |
| 10–32 s | USGS, 16 May 2018, fissure 18 — "16 MAY 2018 \| FISSURE 18" |
| 32–54 s | USGS drone near fissure 22, filmed 22 May 2018 (posted 24 May) — "22 MAY 2018 \| LAVA ON THE MOVE" |
| 54–80 s | USGS Kapoho Bay footage filmed 4 June; ocean entry began late 3 June — "4 JUNE 2018 \| KAPOHO BAY" (**source BLOCKED, see SCIENCE_AUDIT.md**) |
| 80–109 s | USGS, 30 June, summit collapse event at Halemaʻumaʻu (posted 2 July) — "30 JUNE 2018 \| SUMMIT COLLAPSE EVENT" |
| 109–120 s | Outro: summary and credits |

## Exact narration in narration.json (single source of truth)

### Scene 1

In 2018, Kīlauea Volcano in Hawaii opened a series of eruptive fissures. This is not a reconstruction. USGS scientists filmed lava spattering from fissure 18 on May 16.

### Scene 2

Why did lava appear so far from the summit? Before the eruption, magma moved underground along the East Rift Zone. Starting on May 3, new eruptive fissures opened in the lower part of the rift zone.

### Scene 3

Lava from fissure 8 reached Kapoho Bay and began entering the ocean late on June 3, 2018. USGS recorded this footage on June 4. Where hot lava meets seawater, it creates a hazardous plume called laze.

### Scene 4

While lava erupted in the lower rift zone, magma drained from the shallow reservoir beneath the summit. The overlying rock lost its support and collapsed again and again. USGS footage from June 30 shows rockfall and a small plume of dust and gas at the crater.

### Scene 5

A volcano can change both underground and at the surface. Research and direct observation help us understand these hazards and warn people about them.


## Translation notes for reviewers (Vietnamese draft → English)
The English text keeps the meaning of the earlier Vietnamese draft, but uses the wording of the USGS-sourced claims in claims.json where the independent review flagged the Vietnamese as overstated:
- Scene 1: "dung nham trào lên" (lava surging up) → "lava spattering from fissure 18" (claim `fissures`).
- Scene 4 heading: "ĐỈNH NÚI SỤT LÚN" (summit collapse) → "SUMMIT COLLAPSE EVENT" (claim `summit`: a collapse/explosion event with rockfall and a small plume).
- Scene 3: "tối ngày 3 tháng 6" (evening of June 3) → "late on June 3" (claim `kapoho`: entry by 10:30 PM).
These are wording decisions for the team to confirm; nothing is approved by this change.

## Sources
- Magma history and mechanism: https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea
- 16 May: https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-16-2018
- 24 May: https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-24-2018
- 4 June and the 3 June ocean entry (page NOT located by the independent review): https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-june-4-2018
- Independent source for "laze": https://www.usgs.gov/news/featured-story/kilauea-volcano-erupts
- 30 June video posted 2 July: https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-july-2-2018
- Neal et al. (2019): https://www.usgs.gov/publications/2018-rift-eruption-and-summit-collapse-kilauea-volcano

Every narrated **scene** has at least one claim in claims.json (checked by science_gate.py). Not every **sentence** has its own claim — see SCIENCE_AUDIT.md. Changing narration.json or timeline.json invalidates the script, timeline and audio approvals (hash-bound); regenerate audio with `python voiceover.py --force` and have the team re-review and re-sign.
