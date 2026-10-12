# Kīlauea 2018 — narration & storyboard (English deliverable)

**DRAFT. The final GE1013 video is 100% English.** Real USGS footage only (no AI-generated images or video). Narration voice: synthetic Edge TTS `en-US-GuyNeural`, disclosed on screen. Every material statement is backed by a claim in claims.json with a verbatim USGS excerpt (verified 2026-10-11 via Internet Archive copies of the USGS pages); the team must still read the sources and approve.

| Time | Scene | On-screen heading — caption | Footage (proposal in timeline.proposed.json; NOT yet approved) |
|---|---|---|---|
| 0–10 s | Intro | KĪLAUEA 2018 — When a volcano opens a neighborhood and its summit collapses | background may22_fissure22 from 5.0 s |
| 10–32 s | Scene 1 | 16 MAY 2018 | FISSURE 18 — About 2 a.m. HST · Lower East Rift Zone · USGS | may16_fissure18 from 7.0 s |
| 32–54 s | Scene 2 | 22 MAY 2018 | FISSURE 22 — Unmanned aircraft view · fountains and a lava channel | may22_fissure22 from 16.0 s |
| 54–80 s | Scene 3 | 4 JUNE 2018 | KAPOHO BAY — Filmed about 6:15 a.m. · Lava reached the sea late June 3 | jun04_kapoho from 12.0 s |
| 80–109 s | Scene 4 | 30 JUNE 2018 | 1 OF 62 COLLAPSE EVENTS — Rockfall on the caldera wall · filmed from Volcano House | jun30_summit from 24.0 s |
| 109–120 s | Outro | KĪLAUEA 2018 — Footage: USGS and U.S. DOI Office of Aviation Services · Science: USGS, Neal et al. (2019) | background may22_fissure22 from 91.0 s |

## Exact narration in narration.json (single source of truth)

### Intro (scene 0)

In 2018, Kīlauea erupted inside a Hawaii neighborhood as its summit collapsed. This is what USGS cameras recorded.

### Scene 1 (scene 1)

On May 3, eruptive fissures began opening inside Leilani Estates, a neighborhood on the lower East Rift Zone. Within days, at least ten had erupted. This USGS video shows fissure 18 spattering lava at about 2 a.m. on May 16.

### Scene 2 (scene 2)

Why so far from the summit? After a vent farther up the rift collapsed on April 30, magma pushed underground, down the rift zone, until it broke the surface. On May 22, an unmanned aircraft hovered above fissure 22, looking down on fountaining lava and a channel flowing toward the ocean, about five kilometers away.

### Scene 3 (scene 3)

Lava from fissure 8 rushed down a channel and reached the sea at Kapoho Bay late on June 3. USGS filmed the bay from a helicopter early on June 4. Where lava meets seawater, it creates laze: a corrosive plume of steam, hydrochloric acid and fine volcanic glass. Within two days, lava had filled the bay.

### Scene 4 (scene 4)

As lava poured out down the rift, magma drained from the shallow reservoir beneath the summit. The rock above lost its support, and the caldera floor collapsed in steps: sixty-two collapse events between May and early August, deepening it by more than five hundred meters in places. On June 30, a USGS observer filmed one of them: rockfall along the caldera wall and a small plume rising from Halemaʻumaʻu.

### Outro (scene 5)

By early August, the eruption had declined sharply. Careful monitoring had let scientists warn residents two days before lava reached the surface.


## Wording decisions for reviewers
- "This USGS video shows…" (not "USGS scientists filmed"): no USGS page names who filmed the May 16 clip.
- Scene 4 shows ONE event: "1 OF 62 COLLAPSE EVENTS", "rockfall along the caldera wall and a small plume" (USGS: "ash-poor plume"). The collapse mechanism and the 62 events / >500 m are stated as findings from the sources, not as something visible in the clip.
- "late on June 3": USGS June 4 page: "By 6:15 a.m., lava from fissure 8 had entered the ocean for over seven hours"; the 10:30 PM time is a local videographers' report quoted by HVO.
- "Within two days, lava had filled the bay": USGS: completely filled by the morning of June 5.
- "warn residents two days before": HVO warning on 1 May; first fissure 3 May.
- Total erupted volume is deliberately NOT stated (USGS sources give different figures).

## Sources (Internet Archive copies were used because www.usgs.gov blocks automated access)
- Overview: https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea
- Neal et al. (2019): https://www.usgs.gov/publications/2018-rift-eruption-and-summit-collapse-kilauea-volcano
- Feature story (laze, Kapoho, fissure count): https://www.usgs.gov/news/featured-story/kilauea-volcano-erupts
- May 16: https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-16-2018
- May 24 (May 22 UAS clip): https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-24-2018
- June 4 (Kapoho compilation.mp4): https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-june-4-2018
- July 2 (June 30 clip): https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-july-2-2018

Changing narration.json or timeline.json invalidates the script, timeline and audio approvals (hash-bound); regenerate audio with `python voiceover.py --force`, re-review and re-sign.
# Dramatic music edition — 2026-10-11

Separate output: `output/GE1013_Volcano_Hazards_DRAMATIC_DRAFT.mp4`.
The documentary visual stream, source labels, claim wording, narration and
word-aligned captions match the existing volcano-hazards draft. The musical
arrangement adds bass, layered upper harmonics and a restrained pulse; the music
target rises from −28 to −22 LUFS before voice ducking. Musical pulses are a score,
not recorded volcano or earthquake sounds. The project copy and exact new audio
hashes are recorded in `variants/volcano_hazards_dramatic` and the output manifest.
This music remix edition uses Edge TTS. The separate academic edition at
`variants/volcano_hazards_elevenlabs` uses the premade George voice on the verified
ElevenLabs free plan, with actual character alignment converted to word timings.
The initial key failed with HTTP 401; generation succeeded after the user updated it.
No human approvals or reviewer signatures have been created or reused.

The academic edition changes the opening heading to "Volcanic hazards", its
subtitle to "Mechanisms, observations & evidence", the hook to "Volcanic hazards / Beyond lava",
and the earthquake heading to "Magma intrusion & summit collapse". Corrected academic
narration, claim URLs and revised windows are documented in
`variants/volcano_hazards_elevenlabs/NARRATION_AND_STORYBOARD.md`.
The claims are narrowed and uncertainty made explicit. Disputed Tonga map/globe
shots are replaced by sourced mechanism cards. The credits identify ElevenLabs
(elevenlabs.io), free plan, and synthetic narration. Captions are rebuilt from the new voice's alignment, never copied from
the Edge TTS speech. All new inputs invalidate earlier human approvals.
