# WHEN VOLCANOES TURN DEADLY — Earthquakes, Ash Clouds & Tsunamis

Second video option for GE1013 (the original Kīlauea 2018 option is unchanged: `output/GE1013_Kilauea_2018_DRAFT.mp4`, SHA256 `186645aa…ddeafd`).

**Status: UNAPPROVED REVIEW DRAFT. Work was stopped on request on 2026-10-11 with known open issues (section 5). Not approved for upload or submission.** No human has reviewed sources, rights, science, crops or captions; no `review.json`, signature or approval exists for this project.

## 1. Deliverable

| Item | Value |
|---|---|
| File | `output/GE1013_Volcanoes_Turn_Deadly_DRAFT.mp4` (also `variants/volcano_hazards/output/`) |
| SHA256 | `7a20c9101c3d16efb16dc2548513f0464b9408919bf306c98bea29432b236d19` |
| Size | 31,946,176 bytes |
| Video | H.264 High, 1080×1920, 30 fps, 3,600 frames, one colour range (TV/limited) |
| Audio | AAC-LC 48 kHz stereo; narration + original synthesized score (sidechain-ducked) |
| Duration | 120.000 s |
| Subtitles | burned in (Manrope, TikTok-safe band) + `GE1013_Volcanoes_Turn_Deadly_DRAFT.srt` |
| Manifest | `GE1013_Volcanoes_Turn_Deadly_DRAFT.manifest.json` (status `UNAPPROVED_REVIEW_DRAFT`, technical QA `[]`) |
| Watermark / per-scene voice label | off at the owner's request; the synthetic voice is credited on the credits card |

Real material only: USGS/HVO footage and photos, NOAA NESDIS GOES-17 imagery, NOAA NCTR model products (labelled MODEL), USGS ShakeMap (labelled), 1888 Royal Society report plates (labelled HISTORICAL ILLUSTRATION, with dates), one USGS photo (Nehalem, Oregon). Plus three team-made schematic diagrams (labelled "Illustration, not to scale (team-made)") and two typography-only fact cards with a source line. No AI-generated or recreated imagery.

## 2. Structure (as rendered)

| Time | Part | Shots (cut on narration cues by `sync_shots.py`) |
|---|---|---|
| 0–8 s | Hook + title (GE1013, group, members, school logo) | Fissure 22 drone (22 May 2018) · Kīlauea summit explosion (24 May 2018) |
| 8–25 s | 01 Earthquakes | Leilani Estates cracks (4 May 2018) · USGS ShakeMap M6.9 · summit clip (30 Jun 2018) |
| 25–44 s | 02 Tsunamis | diagram 1 · diagram 2 · NOAA NCTR Japan 2011 model · diagram 3 |
| 44–57 s | 03 Ash clouds | Kīlauea summit explosion (24 May 2018) · GOES-17 umbrella cloud, Tonga (15 Jan 2022) |
| 57–69 s | 04 Gas & laze | Fissure 22 (22 May 2018) · Kapoho Bay laze (4 Jun 2018) |
| 69–86 s | 05 Krakatau 1883 | Plate I lithograph (after a photo of 27 May 1883) · Plate XIX tide-gauge records (27–28 Aug 1883) · fact card 2004 Sumatra |
| 86–103 s | 06 Tonga 2022 | GOES-17 (15 Jan 2022) · NOAA NCTR max-amplitude map · NOAA water-vapour globe |
| 103–115 s | 07 Stay safe | Tsunami evacuation sign (Nehalem, OR) · fact card (NWS natural warnings) |
| 115–120 s | Credits | silent credits card |

Exact narration: `narration.json`. Claims with verbatim evidence: `claims.json` (15 claims). Media manifest with source pages, direct URLs, dates, credits and rights notes: `assets.json` (18 items).

## 3. How it was made / how to reproduce

```bash
# from the repository root; private files (group.json, logo) stay local and git-ignored
python download_assets.py --root variants/volcano_hazards      # originals + SHA256 + provenance
python diagrams.py        --root variants/volcano_hazards      # team-made schematics (deterministic)
python voiceover.py       --root variants/volcano_hazards      # Edge TTS en-US-GuyNeural + word timings
python sync_shots.py      --root variants/volcano_hazards      # cut points from narration word timings
python music.py           --root variants/volcano_hazards      # original score (9-part arc)
python draft.py --root variants/volcano_hazards --name GE1013_Volcanoes_Turn_Deadly_DRAFT.mp4 \
                --no-watermark --no-voice-label                # render + technical QA (no approvals used)
```

Opening/tsunami treatments: three ~21 s previews were rendered and compared (A headline cold-open, B question + schematic, C evidence-led). The draft uses a hybrid (A's hook, B's schematic, C's labelled evidence). **This choice has not been approved.**

## 4. Verification evidence (automated; not a human review)

- FFprobe and full decode: values in section 1; decode clean.
- `qa.technical_problems`: no issues — length = timeline, 30 fps, single pixel format/colour range, per-scene narration loudness −16.5 to −18.3 LUFS, no clipping, no black/frozen frames in any footage shot (stills and fact cards excluded from the freeze test by design).
- Non-strict validation of this project: pass (structure, claims coverage per narrated scene, English-only gate, shot labels).
- Media audit: all 18 files match their SHA256 and provenance records (USGS/NOAA/NASA hosts, Internet Archive only for the 1888 plates).
- English: all 41 subtitle cues pass the English-only checker.
- Intelligibility (Whisper small.en on the final mix): WER 4.1 % (1.2 % with place-name hints). Needs a human ear: "Krakatau" sounds like "Krakato"; "Haʻapai" loses the glottal stop; "Kapoho" and "laze" are only recognised with hints.
- Tests: the full CI-mode suite was stopped at the request to stop work; 84 of ~178 tests had run, all passing. Not a full green run.

## 5. Open issues found by the independent review (NOT fixed)

Full report: `research/independent_review.md` (27 issues: 0 blocker, 1 high, ~10 medium). Main ones:

1. **HIGH — Tonga map (≈92–94 s):** the NOAA NCTR image itself states "Tsunami component induced by shockwave not included", yet it is shown while the narration names both the explosion and the pressure wave; it is a still of *amplitude*, but the tag says "model animation · max tsunami height"; subtitles cover its logo/legend.
2. **25–44 s:** "Yet the sea rose only about 40 cm … Big tsunamis need …" implies a cause for the small 2018 tsunami that no source states; the Kapoho caption stays on screen over the Japan 2011 model; diagrams show only the earthquake mechanism while volcanic sources are listed.
3. **69–86 s:** the Krakatau heading/"36,000 dead" caption remains over the 2004 card; Plate I shows May 1883 (three months before the deadly eruption) while the voice says "exploded and collapsed"; tide-gauge plate not identified as Indian-coast gauges.
4. **57–69 s:** "Volcanic smoke is mostly gas" plays over lava footage and the laze caption appears 6 s before the ocean shot; "Ash is rock, NOT SMOKE" heading clashes with "volcanic smoke is …".
5. **16–25 s:** the 30 Jun 2018 summit clip is nearly static (no visible collapse) and tagged "rockfall" (not in `assets.json`); caption still says "4 May" over it; "each drop … then" overstates sequence.
6. **86–103 s:** "57 km" lacks "about / at its top"; the two named tsunami sources read as a complete list (Lynett: "including"); the water-vapour globe shows no visible pressure wave and its GOES-17 attribution is unproven.
7. **Credits:** list NASA Earth Observatory though no NASA image remains in the cut; text small and only 5 s.
8. Low: hook text over lava while saying "without lava"; ShakeMap should read "modelled shaking intensity"; several mid-phrase subtitle breaks; safety card drops "long" and "inland"; 2004 toll lacks "counts vary"; ash clip frames 10–12.6 s repeated.

## 6. Human decisions still required

1. Approve or replace the treatment choice (hybrid A+B+C), every shot window/crop, all on-screen text and the team-made diagrams.
2. Rights per file (see `research/footage_and_rights.md`): NOAA NESDIS/NCTR and NASA items rest on site-wide statements; the 1888 plates are public domain by age but the Internet Archive scan states no licence; USGS items have per-file "Public Domain" lines.
3. Science sign-off on the 15 claims (`research/science_verification.md`), incl. premise corrections: the 2018 M6.9 *did* make a small tsunami (~40 cm at Kapoho); 2004 toll "about 230,000 (NOAA)"; Krakatau "more than 36,000".
4. Listen for pronunciation (Krakatau, Hunga Tonga-Hunga Haʻapai, Kapoho, laze).
5. Confirm the title card's names/student IDs (from local `group.json`, not committed).
6. Then: fill and sign `review.json`, render through `build.py`, watch the full MP4, sign `output/final_review.json`, run `release_check.py --export-final`, upload manually.

## 7. Engineering added for this option (repository-wide)

`editorial.py` (TikTok-safe Barlow Condensed + Manrope layout, multi-shot labelled media, stills, hook/title/credits cards, fact cards), `sources.py` (official-host allowlist), `project.py` (`--root`), `diagrams.py`, `sync_shots.py`, nine-part score in `music.py`, colour-range normalisation (JPEG stills previously caused a mid-stream full/limited range switch), QA fixes (output-side `-t` windows; mixed-range detection). Fonts: SIL OFL 1.1, licence texts in `fonts/`.
