# Academic ElevenLabs edition — narration and storyboard

**UNAPPROVED REVIEW DRAFT.** Free-account George synthetic voice, original stronger score, Barlow Condensed headings and Manrope captions. No approvals or signatures were copied.

## Exact narration and claim sources

### Scene 0: Volcanic hazards

Volcanic hazards extend beyond lava. They include earthquakes, ash clouds and tsunamis, produced by different physical processes.

- `tsunami_definition`: https://www.noaa.gov/education/resource-collections/ocean-coasts/tsunamis
- `volcano_earthquakes`: https://www.usgs.gov/programs/VHP/monitoring-volcano-seismicity-provides-insight-volcanic-structure

### Scene 1: Magma intrusion & summit collapse

On May 4, 2018, pressure from magma intruding into Kīlauea's rift likely triggered a magnitude 6.9 earthquake. As the summit magma system drained, 62 collapse events released energy comparable to earthquakes of about magnitude five.

- `kilauea_m69`: https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea
- `collapse_quakes`: https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea

### Scene 2: What makes a tsunami

The May 4 earthquake generated a small tsunami: about 40 centimeters amplitude at the Kapoho tide gauge. Tsunamis result from sudden displacement of a large volume of water, usually during earthquakes. Volcanic sources include landslides, caldera collapse, underwater explosions and pyroclastic flows.

- `kilauea_small_tsunami`: https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/5678
- `tsunami_sources`: https://www.tsunami.gov/?page=tsunamiFAQ

### Scene 3: Ash is rock, not smoke

Explosive eruptions shatter rock into ash: sharp fragments of rock and glass smaller than two millimeters, not soot. The plume rises, then spreads into an umbrella cloud.

- `ash_definition`: https://volcanoes.usgs.gov/volcanic_ash/ash.html
- `umbrella_cloud`: https://science.nasa.gov/earth/earth-observatory/hunga-tonga-hunga-haapai-erupts-149347/

### Scene 4: Not every white cloud is ash

Water vapor dominates volcanic gases, followed by carbon dioxide and sulfur dioxide. Ocean-entry laze contains seawater steam, hydrochloric acid and fine volcanic glass.

- `volcanic_gases`: https://pubs.usgs.gov/of/1995/0085
- `laze`: https://www.usgs.gov/observatories/hvo/lava-entering-ocean

### Scene 5: Krakatau, Indonesia

Krakatau's 1883 eruption caused more than 36,000 deaths, mostly from tsunamis. Its tsunami mechanism remains debated. Separately, the 2004 Sumatra earthquake generated a tsunami with about 230,000 deaths, according to NOAA.

- `krakatau_1883`: https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/1142
- `sumatra_2004`: https://www.tsunami.gov/?page=tsunamiFAQ

### Scene 6: Hunga Tonga-Hunga Haʻapai

In 2022, Hunga Tonga-Hunga Haʻapai's plume reached about 57 kilometers at its highest point. Its tsunamis had multiple sources, including the underwater explosion and an atmospheric pressure pulse that circled Earth.

- `tonga_plume`: https://science.nasa.gov/earth/earth-observatory/tonga-volcano-plume-reached-the-mesosphere-149474/
- `tonga_tsunami`: https://ncei.noaa.gov/news/january-15-2022-tonga-volcanic-eruption-and-tsunami

### Scene 7: Nature's tsunami warnings

Near the coast, a strong or long earthquake, sudden sea-level change or an ocean roar can warn of a tsunami. Move safely to high ground or inland; don't wait for an official warning.

- `tsunami_warning_signs`: https://www.weather.gov/safety/tsunami-during

## Editorial corrections

- Replaced the Tonga amplitude map that excludes the shock-wave component and the unverified later satellite globe with sourced mechanism fact cards.
- Identified the Japan 2011 model separately from the May 2018 Kapoho gauge reading; no causal explanation for the small tsunami is inferred.
- Used separate headers for Krakatau 1883 and Sumatra 2004; death estimates remain attributed to NOAA and uncertainty is visible.
- Replaced "smoke" with volcanic gas terminology, added "about" and "highest point" to the Tonga plume figure, and restored long-earthquake / inland safety language.
- Added per-shot captions to prevent a May 4 earthquake date being shown as the June 30 summit recording date.
- Changed the main ash window to 15.1 seconds and the later GOES-17 window to 5.7 seconds to avoid replaying source frames from the opening/ash scenes. These are draft editorial selections, not human-approved windows.

## Provenance and review

Exact inputs are in the local assets.json, claims.json, narration.json and timeline.json; the rendered draft manifest fingerprints media provenance, speech timestamps, score, code and fonts. Human footage, rights, pronunciation and scientific review remain pending. The original projects and their narration were preserved.

Shot cut times were synchronized to the exact ElevenLabs word-boundary cues (sync_shots.py), snapped to 30 fps. The Tonga source windows are disjoint and end before the source switches to Himawari imagery: ash section 0.3–5.2333 s; Tonga section 5.3–12.1 s. Main ash footage starts at 15.1 s, beyond the opening 10–15 s window.

Owner requested removal of the bottom credit/source line from every scene. show_bottom_credit=false is set on every segment. Source metadata and the closing Sources & credits card retain attribution and synthetic-voice disclosure. The deliverable has no review watermark.

Owner requested removal of synthetic-voice and ElevenLabs text from the closing Sources & credits card. Visual and science credits, diagram labels and music credit remain. Speech audio and real timestamps are unchanged. For publication of this free-plan audio, the title must include elevenlabs.io or 11.ai under the current provider terms: https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform .
