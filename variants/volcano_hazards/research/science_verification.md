# Science verification: "WHEN VOLCANOES TURN DEADLY - Earthquakes, Ash Clouds & Tsunamis"

Verifier: Science Verifier agent. Date of checks: 2026-10-11. Repo was read-only (AGENTS.md, CLAUDE.md, claims.json read; nothing in the repo changed). Scratch copies of every source text are in `.../scratchpad/deadly_science/` (see "Reproduce").

Status labels: VERIFIED = I read the source text myself (live fetch on 2026-10-11, or Internet Archive `id_` copy with timestamp given). SNIPPET = search-result text only. UNVERIFIED = not found / not read. Nothing here is a human approval; usage rights, script and output still need the team's sign-off.

Evidence-registry note: claims.json uses the fields `id / scene / claim / reference / evidence_note` with "SCI:" prefixes and verbatim excerpts. The tables below are written so each row can be pasted into that format (claim -> `claim`, URL -> `reference`, excerpt -> `evidence_note`).

---------------------------------------------------------------------

## Premise corrections (read first)

1. **"May 4, 2018 Kilauea M6.9 happened without generating a tsunami" is NOT accurate.**
   - The Pacific Tsunami Warning Center (PTWC) said, in real time, "NO TSUNAMI IS EXPECTED", and the USGS/HVO press release repeated "no tsunami was generated". But the same PTWC statement #3 (1:27 PM HST) reported tide-gauge readings: Hilo 20 cm, Kapoho 40 cm, Honuapo 15 cm amplitude. NOAA NCEI lists it as a tsunami event (max water height 0.4 m; 7 run-up/gauge records from Hawaii Island to Kauai).
   - NCEI text: "There was no threat of a tsunami, but a small tsunami was generated." A peer-reviewed model (Bai et al. 2018, GRL) says the uplift and seaward displacement of the south flank "generate a tsunami that wraps around Hawaii Island".
   - **Narration must say:** "only a small tsunami (about 40 cm at the nearest gauge)" or "no destructive tsunami". Never "no tsunami".
2. **"~228,000 deaths per USGS" is not safe.** NOAA NCEI database: 227,899 (event "deaths"). NOAA tsunami.gov FAQ: "approximately 230,000 deaths". The USGS event page (ComCat impact text, last modified 2014-11-06) instead says "more than 283,100 people were killed, 14,100 are still listed as missing", and a USGS feature story gives "at least 108,100 killed, 127,700 missing and presumed dead" for Aceh/Sumatera Utara alone. Different agencies count dead+missing differently. Use "about 230,000 (NOAA)" and cite NOAA, not USGS.
3. **Krakatau toll 36,417:** the 1888 Royal Society report (read in full text) gives **36,380**, not 36,417. 36,417 appears in the NOAA NCEI database (`deathsTotal`), with 34,417 as the NCEI "deaths" field. I could not find the original source of 36,417 (see Not verified). Use "more than 36,000" (Smithsonian GVP, Lynett et al. 2022 Nature "at least 36,000") or "about 36,000".
4. **Tonga 2022 plume "58 km":** 58 km is NASA's stereo estimate for the plume top; the Science paper (Proud et al.) says 57 km; a stereo paper (Carr et al., GRL) says overshooting tops reached 50-55 km. The umbrella cloud itself spread at about 30 km altitude (NASA), not 58 km. Say "about 57 km (roughly 35 miles) at its very top" and keep the umbrella separate.
5. **Tonga is not "only the eruption column / only a pressure wave".** Both: local waves from the water cavity/explosion (Lynett et al.) plus a global meteotsunami driven by the atmospheric pressure pulse. Also VEI disagreement (NOAA NCEI says VEI 5; a seismic paper estimates ~6): avoid putting a VEI number on screen.
6. **Magnitude of the Kilauea quake:** USGS M6.9 (Mw). Some papers (Liu/Lay group, Caltech-linked study titled "Mw 7.2") use other values. Use USGS 6.9 consistently.
7. **Hilina fault system vs decollement:** USGS says the M6.9 was on the nearly horizontal decollement beneath the Hilina fault system, not on the steep Hilina faults (the "pali" cliffs). Do not show Hilina Pali footage as "the fault that slipped".

---------------------------------------------------------------------

## Concept 1: Volcanoes and earthquakes (magma, pressure, faults, collapse)

**Narration-ready (2-4 sentences):**
"Volcanoes shake the ground in several ways. Magma pushing through the crust changes stress and breaks rock, and gas and magma moving in cracks make them resonate. At Kilauea in 2018, draining magma left the summit floor unsupported, so it dropped in steps of several meters, and each collapse was felt as an earthquake of about magnitude 5."

| Claim | Verbatim excerpt | URL (+archive ts) | Status |
|---|---|---|---|
| VT quakes = brittle rock failure; stress from moving magma can trigger them | "Volcano-tectonic (VT) earthquakes represent brittle failure of rock, the same process that occurs along purely "tectonic" faults such as the San Andreas Fault. At volcanoes, VT events can occur due to "normal" tectonic forces, changing stresses caused by moving magma, and movement of fluids through pre-existing cracks." | https://www.usgs.gov/programs/VHP/monitoring-volcano-seismicity-provides-insight-volcanic-structure (Archive 20261002100947) | VERIFIED |
| Long-period quakes = cracks resonating as magma/gas rise; not a guaranteed eruption warning | "Long-period (LP) or low-frequency (LF) earthquakes are caused by cracks resonating as magma and gases move toward the surface. They are often seen prior to volcanic eruptions, but their occurrence is also part of the normal background seismicity at some volcanoes and their occurrence does not necessarily indicate that an eruption is imminent." | same | VERIFIED |
| Dike progression tracked by earthquakes | "Progression of the dike down-rift was reflected in the similar spatial progression of earthquake activity, and on May 3, 2018, lava broke out onto the surface within Leilani Estates" | https://www.usgs.gov/volcanoes/kilauea/science/2018-lower-east-rift-zone-eruption-and-summit-collapse-kilauea (Archive 20260905011308) | VERIFIED |
| Summit collapse = piston-like drops, each with a ~M5 quake | "earthquakes in the summit region would increase until the unsupported floor of the caldera dropped-in a piston-like manner-down by several meters (several yards), after which earthquake activity would diminish." ... "Up to 700 earthquakes equal to or greater than magnitude 4 occurred between each summit collapse event, which culminated in a near-daily magnitude 5.2-5.4 earthquake." | same | VERIFIED |
| 62 collapse events; >60,000 quakes; caldera deepened >500 m | "In total, 62 collapse events occurred." / "more than 60,000 earthquakes that accompanied the summit collapse events" / "the summit caldera deepened by more than 500 meters (1600 feet)" | same | VERIFIED |
| Peer-reviewed energy equivalence | "The summit magma system partially drained, producing minor explosions and near-daily collapses releasing energy equivalent to M4.7-M5.4 earthquakes." (Neal et al. 2019, Science 363:367-374, DOI 10.1126/science.aav7046) | https://pubs.usgs.gov/publication/70203484 (live, abstract) | VERIFIED |
| Collapse is a quake source, not only a "consequence" | USGS also says shaking from big quakes caused additional Pu'u 'O'o crater collapses: "With each large earthquake, ground shaking causes additional collapse within the Pu'u 'O'o crater" (same USGS Kilauea 2018 page) | same | VERIFIED |

Say "about magnitude 5" on screen (sources give 5.2-5.4 and 4.7-5.4; "about M5" is safe).

---------------------------------------------------------------------

## Concept 2: The May 4, 2018 Kilauea M6.9 earthquake

**Narration-ready:**
"On May 4, 2018, at 12:32 p.m. Hawaii time, a magnitude 6.9 earthquake struck Kilauea's south flank, the strongest in Hawaii since 1975. USGS scientists say it was likely caused by pressure from magma intruding into the East Rift Zone, which pushed the south flank seaward by about 5 meters along a nearly flat fault beneath it. The seafloor moved enough to make only a small tsunami, about 40 centimeters at the nearest gauge, not a destructive one."

(The final sentence's reason is my synthesis of NOAA's general rule, see row "why small"; it should be softened or checked by the team.)

| Claim | Verbatim excerpt | URL (+archive ts) | Status |
|---|---|---|---|
| Time, size, location | USGS event hv70116556: Mw 6.9, "18 km SSW of Leilani Estates, Hawaii", origin 2018-05-04 22:32:54 UTC = 12:32:54 HST; lat 19.318, lon -155.000; depth 5.81 km (header: "the depth is now 6 km instead of 2 km"). HVO: "magnitude-6.9 earthquake on Friday, May 4, 2018, at approximately 12:32 p.m. HST. It is the strongest quake in Hawaii since 1975" | https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/hv70116556.geojson (live); https://earthquake.usgs.gov/earthquakes/eventpage/hv70116556 ; HVO press release https://www.usgs.gov/news/usgs-hvo-press-release-series-earthquakes-rattle-hawaii (Archive 20250810110712) | VERIFIED |
| Mechanism: reverse (thrust) faulting on the south flank | "occurred as a result of reverse faulting on the south flank of Kilauea volcano, in the east rift zone. Preliminary focal mechanism solutions indicate rupture occurred on shallow dipping thrust fault striking southwest" "This earthquake is directly associated with volcanic activity at Kilauea volcano" (USGS tectonic summary). Moment tensor nodal plane 1: strike 240, dip 20, rake 114 (shallow thrust). | USGS ComCat product general-text/moment-tensor (URL above) | VERIFIED |
| Fault = decollement, beneath the Hilina fault system | "Beneath this system lies the flat-lying decollement fault that has no visible surface expression but was responsible for the May 4, 2018, magnitude-6.9 earthquake." / "The decollement fault is a nearly horizontal fault at the boundary of the original ocean floor and overlying volcanic rocks." | https://www.usgs.gov/news/volcano-watch-new-research-sheds-light-relationship-between-hilina-fault-system-and-large (Archive 20260117173033) | VERIFIED |
| Hilina slump/pali did not fail | "in the days that followed, there was no evidence for widespread motion of the Hilina slump." "The only location with substantial movement during the earthquake, was a short (2.5 km, 1.5 mile) segment of a previously unmapped fault near the earthquake's epicenter." | same | VERIFIED |
| Relation to dike intrusion | "The earthquake was likely caused by pressure induced by the dike continuing to intrude into the lower East Rift Zone." and "dilated the rift zone by approximately 5 m (16 ft)" | USGS Kilauea 2018 page (Archive 20260905011308) | VERIFIED |
| Same, from HVO | "This earthquake was caused by the magmatic intrusion in Kilauea's East Rift Zone, which led to the 2018 eruption in the lower East Rift Zone." Also "Slip along the decollement can be produced as a combination of gravity and changes in pressure occurring in the volcano that sits above." | https://www.usgs.gov/observatories/hvo/news/volcano-watch-more-shaking-kilaueas-south-flank-did-you-feel-it (Archive 20251011113053) | VERIFIED (note "likely" vs "was caused": keep "likely") |
| Peer-reviewed slip | "A 4 May earthquake (M6.9) produced ~5 m of fault slip." (Neal et al. 2019, DOI 10.1126/science.aav7046). Bai et al. 2018 GRL, DOI 10.1029/2018GL079742: "a shallowly dipping thrust fault, plausibly on the decollement between the island volcanic edifice and the old Pacific seafloor." | https://pubs.usgs.gov/publication/70203484 ; https://repository.library.noaa.gov/view/noaa/49889 | VERIFIED |
| Foreshock | "About an hour prior to the M 6.9 event, a M 5.4 earthquake also struck in a similar location" (USGS tectonic summary); PTWC statement 1 logged M 5.6 at 11:33 AM HST | USGS ComCat (above); PTWC product TIBHWX | VERIFIED |
| 1975 comparison | "Regionally, this is the largest earthquake in Hawai'i since the Ms 7.1 (USGS) / Mw 7.4 (ISC-GEM) / Mw 7.7 (Nettles and Ekstrom, 2004) Kalapana earthquake in 1975, which also generated a local tsunami that took 2 lives." (magnitude for 1975 differs by author; don't put it on screen) | USGS ComCat tectonic summary | VERIFIED |
| Damage | "Minor damage to buildings and at least 4 landslides occurred on the coast." (USGS impact text); MMI VIII reported by HVO | USGS ComCat; HVO release | VERIFIED |

### The tsunami question (the critical premise check)

| Claim | Verbatim excerpt | URL | Status |
|---|---|---|---|
| Real-time PTWC product (Statement 1, 12:37 PM HST) said no tsunami expected | "NO TSUNAMI IS EXPECTED. REPEAT. NO TSUNAMI IS EXPECTED. HOWEVER...MANY AREAS MAY HAVE EXPERIENCED STRONG SHAKING." (initial magnitude 6.0) | NWS PTWC text product TIBHWX archived by Iowa Environmental Mesonet: https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil=TIBHWX&sdate=2018-05-04T21:00Z&edate=2018-05-05T12:00Z&limit=50&fmt=text | VERIFIED |
| Statement 2 (12:47 PM, M6.4) allowed for small changes | "SOME AREAS MAY EXPERIENCE SMALL SEA LEVEL FLUCTUATIONS." | same | VERIFIED |
| Statement 3 (1:27 PM HST, M6.9): small tide-gauge changes were measured | "NOTE THAT THE MAGNITUDE HAS INCREASED FROM 6.4 TO 6.9. ... THIS EARTHQUAKE GENERATED SMALL SEA LEVEL CHANGES AT SOME LOCATIONS ON THE BIG ISLAND. MEASUREMENTS INCLUDE HILO 20 CM AMPLITUDE KAPOHO 40 CM AMPLITUDE HONUAPO 15 CM AMPLITUDE AT ALL LOCATIONS THE FLUCTUATIONS ARE NOW DIMINISHING." Location line: "ON THE SOUTH FLANK OF KILAUEA VOLCANO". Evaluation still read "NO TSUNAMI IS EXPECTED" | same | VERIFIED |
| USGS/HVO press release repeated "no tsunami" | "According to the Pacific Tsunami Warning Center (PTWC) no tsunami was generated by today's earthquakes." (written before the gauge data were summarized) | https://www.usgs.gov/news/usgs-hvo-press-release-series-earthquakes-rattle-hawaii (Archive 20250810110712) | VERIFIED (this is where the "no tsunami" idea probably comes from) |
| NOAA NCEI Global Historical Tsunami Database lists it as a tsunami | Event id 5678, 2018-05-04 22:32:54 UTC, maxWaterHeight 0.4 m, 7 runup records: Kapoho 0.4 m, Hilo 0.2, Kawaihae 0.16, Honuapo 0.15, Kahului 0.15, Nawiliwili 0.04, Honolulu 0.03 m. Comment: "PTWC initially estimated it at a smaller magnitude, so they issued an information statement instead ... There was no threat of a tsunami, but a small tsunami was generated. McCreery said it you were at the coast, you would have seen the water level slowly go up and down. The wave was a little over a foot above normal sea level at Kapoho" | https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/5678 and ...runups?tsunamiEventId=5678 (live JSON) | VERIFIED |
| NCEI second reference | "The event involved seaward sliding of a wedge of the island offshore of the East Rift Zone, likely on the contact surface between the island and the Pacific Ocean seafloor. The resulting motion generated a modest tsunami that arrived on the shores of the major Hawaiian Islands in less than an hour." | same NCEI event 5678 comment (ref #12263) | VERIFIED (as quoted by NCEI) |
| Peer-reviewed | "The uplift and seaward displacement of Kilauea's south flank generate a tsunami that wraps around Hawaii Island, exposing all shores to direct arrivals..." (Bai, Ye, Yamazaki, Lay, Cheung 2018, GRL 45(20), DOI 10.1029/2018GL079742) | https://repository.library.noaa.gov/view/noaa/49889 | VERIFIED |
| Landslide contribution possible | A Seismological Society abstract says the earthquake-only source cannot fully explain the tsunami records and "likely, at least in part, driven by a coseismic landslide" (preliminary, 2019 meeting abstract) | https://seismosoc.secure-platform.com/a/solicitations/5/sessiongallery/126/application/3400 | SNIPPET |
| Why small: general NOAA rule | "Most tsunamis are generated by earthquakes with magnitudes over 7.0 that occur under or very near the ocean ... Generally, an earthquake must exceed magnitude 8.0 to generate a dangerous distant tsunami." and "The amount of movement of the ocean floor, the size of the area over which it occurs ..., and the depth of the water at its source are all important factors in the size of a resulting tsunami." | https://www.tsunami.gov/?page=tsunamiFAQ (live, section 2.2) | VERIFIED (generic rule). Applying it to Kilauea is my inference, no source states "this is why Kilauea's tsunami was small" |

**Safe wording:** "It also set off a small tsunami, only about 40 centimeters at the closest tide gauge, far from destructive." Alternative: "No destructive tsunami followed." Do NOT say "no tsunami", and do NOT show a "tsunami warning" graphic (no warning was issued; PTWC issued information statements only).

---------------------------------------------------------------------

## Concept 3: Why tsunamis happen and the volcano-related generators

**Narration-ready:**
"A tsunami starts when a huge volume of ocean water is suddenly displaced. Most come from large earthquakes where one tectonic plate thrusts under another. Volcanoes can do it too: by landslides and flank collapse, caldera collapse, explosions near the surface, avalanches of hot rock entering the sea, or even a powerful shock wave in the air."

| Claim | Verbatim excerpt | URL | Status |
|---|---|---|---|
| Definition + earthquakes dominant | "A tsunami is a series of extremely long waves caused by a large and sudden displacement of the ocean, usually the result of an earthquake below or near the ocean floor." / "Most tsunamis are caused by earthquakes on converging tectonic plate boundaries. According to the Global Historical Tsunami Database, since 1900, over 80% of likely tsunamis were generated by earthquakes. However, tsunamis can also be caused by landslides, volcanic activity, certain types of weather, and-possibly-near-earth objects" | https://www.noaa.gov/education/resource-collections/ocean-coasts/tsunamis (live) | VERIFIED |
| Same, tsunami.gov | "Large earthquakes below or near the ocean floor are the most common cause, but landslides, volcanic activity, certain types of weather, and near earth objects ... can also cause tsunamis. Most of the tsunamis (88%) in the Global Historical Tsunami Database were generated by earthquakes or landslides caused by earthquakes." | https://www.tsunami.gov/?page=tsunamiFAQ (live, 2.1) | VERIFIED |
| Earthquake mechanism: vertical seafloor motion | "An earthquake must be big enough and close enough to the ocean floor to cause the vertical movement of the ocean floor that typically sets a tsunami in motion. As the ocean floor rises or drops, so too does the water above it." | same (2.2) | VERIFIED |
| Volcanic generators list | "Tsunamis generated by volcanoes, both above and below water, are infrequent, but several types of volcanic activity can displace enough water to generate destructive tsunamis. These include: Pyroclastic flows (flowing mixtures of rock fragments, gas, and ash); Submarine explosions relatively near the ocean surface; Caldera formation (volcanic collapse); Landslides (e.g., flank collapse, debris flows); Lateral blasts (sideways eruptions). Like other nonseismic tsunamis, such as those generated by landslides, volcanic tsunamis usually lose energy quickly and rarely affect distant coastlines." | same (2.4) | VERIFIED |
| Weather/air-pressure generators | "Air pressure disturbances often associated with fast moving weather systems, like squall lines, can generate tsunamis. These "meteotsunamis" are similar to tsunamis generated by earthquakes." (volcanic pressure waves: see Concept 6) | same (2.5) | VERIFIED |
| Not all quakes | "Not all earthquakes cause tsunamis." | https://www.weather.gov/safety/tsunami-about | VERIFIED |
| Frequency | "Each year, there are approximately two tsunamis that cause damage near their source. Tsunamis that cause damage or deaths on distant shores (more than 1,000 kilometers, 620 miles, away) occur about twice per decade." | same | VERIFIED |
| Speed/height | "In the deep ocean, a tsunami can move as fast as a jet plane, over 500 mph ... in deep water, the top of the wave rarely reaches more than three feet higher than the ocean swell." | NOAA education page | VERIFIED |

---------------------------------------------------------------------

## Concept 4: Krakatau 1883 vs Indian Ocean 2004

**Narration-ready:**
"In August 1883, Krakatau in Indonesia exploded and collapsed over two days, and the tsunamis that followed killed more than 36,000 people. Scientists still debate exactly how the water was displaced: avalanches of hot rock entering the sea, collapse into the caldera, or underwater explosions. The deadliest tsunami in history was different: the 2004 magnitude 9.1 Sumatra-Andaman earthquake, where a plate boundary slipped and lifted the seafloor, killing about 230,000 people."

| Claim | Verbatim excerpt | URL (+archive ts) | Status |
|---|---|---|---|
| Dates and sequence | Royal Society 1888: "Eruption of August 26th, 27th, 1883"; "The first waves reached both the Javan and the Sumatran coasts between 6 and 7 on the evening of August the 26th". Lynett 2022: "On 27 August 1883, the Krakatau volcano ... produced four explosive eruptions over 5 h generating a series of tsunami waves". NCEI: climactic event 1883-08-27 02:59 UTC. | https://archive.org/details/eruptionkrakato00whipgoog (full text read); https://pmc.ncbi.nlm.nih.gov/articles/PMC9472183/ ; NCEI event 1142 | VERIFIED |
| Death toll, Royal Society 1888 | "the towns and villages along the coast devastated, two of the lighthouses swept away, and the lives of 36,380 of the inhabitants, among whom were 37 Europeans, sacrificed." | https://archive.org/download/eruptionkrakato00whipgoog/eruptionkrakato00whipgoog_djvu.txt | VERIFIED (36,380, not 36,417) |
| Smithsonian GVP | "This eruption caused more than 36,000 fatalities, most as a result of tsunamis that swept the adjacent coastlines of Sumatra and Java. Pyroclastic surges traveled 40 km across the Sunda Strait and reached the Sumatra coast." "Caldera collapse during the catastrophic 1883 eruption destroyed Danan and Perbuwatan, and left only a remnant of Rakata." | https://volcano.si.edu/volcano.cfm?vn=262000 (Archive 20261006185943; live site 403 to scripts) | VERIFIED |
| NOAA numbers | tsunami.gov: "The volcano Krakatau (Krakatoa) exploded and collapsed, generating one of the largest and most destructive tsunamis ever recorded. Waves reaching 135 feet high destroyed coastal towns and villages along the coasts of Java and Sumatra and killed more than 34,000 people." NCEI database event 1142: `deaths` 34,417; `deathsTotal` 36,417; `maxWaterHeight` 41 m; 102 run-ups. | https://www.tsunami.gov/?page=tsunamiFAQ (2.4); https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/1142 | VERIFIED (the 34,000 vs 36,000 difference is likely "tsunami deaths" vs "all deaths", but NCEI does not say so in what I read) |
| Main killer = tsunami | GVP (above): "most as a result of tsunamis". NCEI cause note: "The voluminous pyroclastic flows entered the sea where they generated tsunami". | GVP; NCEI event 1142 reference #9779 | VERIFIED |
| Mechanism is debated | Nomanbhoy & Satake 1995 GRL 22:509, DOI 10.1029/94GL03219: models "1) large-scale caldera collapse ... 2) emplacement of pyroclastic flow deposits; 3) submarine explosion ... The comparison shows that the submarine explosion model of 1 to 5 min duration best explains the generation of the largest tsunami." Maeno & Imamura 2011 JGR 116:B09205, DOI 10.1029/2011JB008253: "We conclude that a pyroclastic flow entering the sea is the most plausible mechanism of the 1883 Krakatau tsunami." | Crossref abstract for 10.1029/94gl03219 (live); Maeno & Imamura page 1 read from a PDF copy (https://luk.staff.ugm.ac.id/jurnal/freepdf/MaenoImamuraKrakatauTsunamiGeneration.pdf, an unofficial host; the DOI is the citable source) | VERIFIED (abstracts) |
| Air-pressure wave also recorded | NCEI ref: "It also caused an atmospheric pressure wave that was recorded on the tide gages at remote locations including South Georgia Island, Panama, France, England, Hawaii, Alaska, and San Francisco." | NCEI event 1142 comments | VERIFIED |
| 2004: M9.1, megathrust | USGS: "The devastating M 9.1 earthquake off the west coast of northern Sumatra on December 26, 2004, occurred as the result of thrust faulting on the interface of the India plate and the Burma microplate." "The sea floor overlying the thrust fault was uplifted by several meters as a result of the earthquake, causing the ensuing tsunami that devastated shores around the Indian Ocean." | https://earthquake.usgs.gov/earthquakes/eventpage/official20041226005853450_30 (ComCat general-text, live JSON) | VERIFIED |
| 2004: deaths (NOAA) | tsunami.gov: "A magnitude 9.1 earthquake generated the deadliest tsunami in history. ... Impacts included approximately 230,000 deaths, the displacement of 1.7 million people". NCEI event 2439: `deaths` 227,899; `maxWaterHeight` 50.9 m; 2,177 run-ups. | https://www.tsunami.gov/?page=tsunamiFAQ (2.2); https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/2439 | VERIFIED |
| 2004: USGS counts differ | USGS impact text: "In total, more than 283,100 people were killed, 14,100 are still listed as missing and 1,126,900 were displaced". USGS feature: "The 2004 tsunami was the deadliest and one of the most destructive in recorded history." | ComCat impact-text; https://www.usgs.gov/news/featured-story/indian-ocean-tsunami-remembered-scientists-reflect-2004-indian-ocean-killed (Archive 20260930010721) | VERIFIED (a conflict, see Premise 2) |

---------------------------------------------------------------------

## Concept 5: Ash, umbrella clouds, gases, steam, laze, Kilauea ash

**Narration-ready:**
"Volcanic ash is not soot or smoke. It is tiny fragments of rock, minerals and volcanic glass, smaller than 2 millimeters, blasted out when gas expands or water flashes to steam. The eruption column rises until it is no lighter than the surrounding air, then spreads sideways in an umbrella shape. Along with ash, volcanoes release steam, carbon dioxide and sulfur dioxide, and where lava meets the sea, 'laze' forms: steam with hydrochloric acid and glass particles."

| Claim | Verbatim excerpt | URL (+ts) | Status |
|---|---|---|---|
| Ash definition, not combustion | "Volcanic ash is not the product of combustion, like the soft fluffy material created by burning wood, leaves, or paper, but rather consists of fragments of rocks, minerals, and volcanic glass ranging in size from sand to clay-like (from 2 mm (1/12 in) to less than 0.004 mm (1/256th in) in diameter). Ash is hard, abrasive, mildly corrosive, conducts electricity when wet, and does not dissolve in water." | https://volcanoes.usgs.gov/volcanic_ash/ash.html (live) | VERIFIED |
| How ash forms | "Explosive eruptions occur when gases dissolved in molten rock (magma) expand as the magma rises, and then escape violently into the air, or when water is heated by magma and abruptly flashes into steam. The force of the escaping, expanding gas violently shatters solid rocks and shreds the magma blasting it into the air." | same | VERIFIED |
| Size | "Volcanic ash consists of fragments 2 mm or smaller in diameter and is a type of tephra" | https://volcanoes.usgs.gov/volcanic_ash/ash_particle_size.html (live) | VERIFIED |
| "Smoke" from volcanoes is gas | "'smoke' from volcanoes, once attributed by poets to be from Vulcan's forge, is actually volcanic gas naturally released from both active and many inactive volcanoes." | https://pubs.usgs.gov/of/1995/0085 (USGS OFR 95-85, live) | VERIFIED |
| Gases | "Water vapor is typically the most abundant volcanic gas, followed by carbon dioxide and sulfur dioxide. Other volcanic gases are hydrogen sulfide, hydrochloric acid, hydrogen, carbon monoxide, hydrofluoric acid, and other trace gases and volatile metals." Also "The term 'vog' refers to a hazy mixture of mostly SO2 gas and very small acidic particles." | pubs.usgs.gov/of/1995/0085 ; https://volcanoes.usgs.gov/volcanic_ash/ash_gas_vog.html | VERIFIED |
| Umbrella cloud (observed) | NASA: "a vast plume of material created what volcanologists call an umbrella cloud" ; Simon Carn (Michigan Tech): "The umbrella cloud was about 500 kilometers (300 miles) in diameter at its maximum extent" | https://science.nasa.gov/earth/earth-observatory/hunga-tonga-hunga-haapai-erupts-149347/ | VERIFIED |
| Neutral buoyancy | Prata et al., Volcanica 8(1) 2025, DOI 10.30909/vol.08.01.0129: "Analysis of thermal infrared satellite measurements of umbrella clouds ... suggests that asymptotic gravity current models of the temporal (t) radial (r) spreading ... of the umbrella-shaped intrusion do not adequately explain the observations. ... At the onset of neutral buoyancy, the radial spreading is better explained by a stronger dependence on time ..." | Crossref abstract (live) | VERIFIED (abstract uses "neutral buoyancy" and "umbrella-shaped intrusion"; it does not give a plain-language definition. The sentence "rises until it is no lighter than the air around it, then spreads sideways" is standard textbook wording that I could not tie to a USGS/NASA/NOAA page) |
| Laze | "This vigorous interaction also generates a billowy white "laze" plume composed of condensed seawater steam laced with hydrochloric acid and tiny shards of volcanic glass." / "This 'laze' (short for lava haze) plume, a byproduct of the lava-ocean interaction, is formed as hot lava boils seawater to dryness. ... a billowing white cloud composed of an irritating mixture of condensed, acidic seawater steam, hydrochloric acid gas, and tiny shards of volcanic glass. ... even the wispy edges of it can cause skin and eye irritation and breathing difficulties." | https://www.usgs.gov/news/volcano-watch-kilauea-ocean-entry-hazards-plume-not-your-friend (Archive 20260414223332); https://www.usgs.gov/observatories/hvo/lava-entering-ocean (Archive 20231129054454) | VERIFIED |
| Kilauea May 17, 2018 explosion | "At about 04:15 a.m. HST, an explosion from the Overlook crater at Kilauea Volcano's summit produced an eruption column that reached at least 30,000 ft. above sea level. The plume was blown by wind toward the northeast. This resulted in ash fall at the Hawaiian Volcano Observatory, and nearby Volcano Village and the Volcano Golf and Country Club Subdivsion." (typo "Subdivsion" is in the source) | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-17-2018 (Archive 20251107135550) | VERIFIED |
| Same, USGS FAQ | "On May 17 in 2018, an explosive eruption at the summit of Kilauea produced a volcanic cloud that reached as high as 30,000 feet above sea level." | https://www.usgs.gov/faqs/does-ash-ever-erupt-kilauea-volcano (Archive 20250805022553) | VERIFIED |
| Summit ash was mostly old rock, not fresh lava | "the primarily lithic-ash (composed of older rock material, as opposed to fresh lava) plumes and slightly increased SO2 emissions during the 2018 events"; "On May 16, the first of a dozen minor explosive events occurred, with a plume consisting of ash-sized fragments of the crater walls (no fresh lava was present)" ; "the 2018 events proceeded passively at the summit, with none of the anticipated violent explosions occurring" | USGS Kilauea 2018 page (Archive 20260905011308) | VERIFIED (important: do not describe the May 2018 summit plumes as a magma-driven Plinian eruption) |
| Smaller summit plumes | "the height of the ash plumes near the crater rose to more than 3 km (9,800 ft) above sea level, and downwind the plumes continued to rise to about 3.5 km" (an earlier/other day's flight, same USGS page) | same | VERIFIED (date of that flight not stated on the page text I read) |

Use "30,000 feet (about 9 km) above sea level". 30,000 ft = 9.1 km (my arithmetic).

---------------------------------------------------------------------

## Concept 6: Hunga Tonga-Hunga Ha'apai, 15 January 2022

**Narration-ready:**
"On January 15, 2022, the Hunga Tonga-Hunga Ha'apai volcano blasted a plume about 57 kilometers high, into the mesosphere, the highest volcanic plume ever measured by satellite. Its umbrella cloud spread roughly 500 kilometers wide. The eruption made tsunamis in two ways: local waves from the explosion and the water it displaced, and a global set of waves driven by a pressure pulse in the atmosphere that circled the Earth."

| Claim | Verbatim excerpt | URL | Status |
|---|---|---|---|
| Plume top ~57-58 km | Proud, Prata, Schmauss 2022, Science, DOI 10.1126/science.abo4076: "we find that the volcanic plume produced by this volcano reached an altitude of 57 kilometers at its highest extent. This places the plume in the lower mesosphere". NASA: "The team calculated that the plume from the January 15 volcanic eruption rose to 58 kilometers (36 miles) at its highest point. Gas, steam, and ash from the volcano reached the mesosphere" (the same NASA page's headline says "58 kilometers (38 miles)"; 58 km = 36 mi, the headline mile figure is a NASA typo) | Crossref abstract (live); https://science.nasa.gov/earth/earth-observatory/tonga-volcano-plume-reached-the-mesosphere-149474/ (live) | VERIFIED |
| Lower stereo estimate | Carr et al. 2022 GRL, DOI 10.1029/2022GL098131: "overshooting tops reaching 50-55 km altitude, a record in the satellite era ... much of the plume was lofted 30-40 km into the atmosphere" | Crossref abstract (live) | VERIFIED (author attribution Carr: from the paper's DOI/title; I did not open the author list) |
| Rise time | NASA: "the initial blast rapidly rose from the ocean surface to 58 kilometers in about 30 minutes." | NASA mesosphere page | VERIFIED |
| Umbrella cloud size/altitude | Carn via NASA: "about 500 kilometers (300 miles) in diameter at its maximum extent". NASA: "an umbrella of ash and gas spread out in the stratosphere at an altitude of about 30 kilometers (20 miles), eventually covering an area of 157,000 square kilometers (60,000 square miles), larger than the state of Georgia." Gupta et al. (Commun. Earth Environ.) report two umbrella layers, ~31 km and ~17 km | https://science.nasa.gov/earth/earth-observatory/hunga-tonga-hunga-haapai-erupts-149347/ ; mesosphere page | VERIFIED (NASA); Gupta = SNIPPET |
| Eruption timing | NCEI: "At approximately 4:47 pm local time (03:47 UTC/Z time) on January 15, the significant eruption reached its peak. The main phase of the eruption lasted approximately 11 hours." (Lynett et al. use ~04:15 UTC as the main explosion, so UTC times differ by source; avoid giving a minute-level time on screen.) | https://ncei.noaa.gov/news/january-15-2022-tonga-volcanic-eruption-and-tsunami (live) | VERIFIED |
| Tsunami mechanisms (peer-reviewed) | Lynett et al. 2022 Nature, DOI 10.1038/s41586-022-05170-6: "the explosive eruption generated waves through multiple mechanisms, including: (1) air-sea coupling with the initial and powerful shock wave radiating out from the explosion in the immediate vicinity of the eruption; (2) collapse of the water cavity created by the underwater explosion; and (3) air-sea coupling with the air-pressure pulse that circled the Earth several times, leading to a global tsunami. In the near field, tsunami impacts are strongly controlled by the water-cavity source whereas the far-field tsunami, which was unusually persistent, can be largely described by the air-pressure pulse mechanism." | https://pmc.ncbi.nlm.nih.gov/articles/PMC9472183/ (full text read) | VERIFIED |
| Tide-gauge study | Carvajal et al. 2022 GRL, DOI 10.1029/2022GL098153: "The Tonga tsunami was characterized by a uniformly small leading wave that arrived earlier than theoretically expected ... the largest waves, of up to +3 m high, were concentrated in the Pacific ... While the leading waves were caused by a previously reported fast-moving atmospheric pressure pulse generated in the volcanic explosion, the large waves observed later in the Pacific were likely originated in the vicinity of the volcano although its generation mechanism(s) cannot be identified by the tide gauge data alone." | Crossref abstract (live) | VERIFIED |
| NOAA summary | "While the HTHH eruption generated a large local tsunami in Tonga, it also caused a massive atmospheric pressure wave that generated a series of tsunamis observed around the world." NCEI/NGDC: "Atmospheric pressure from the event generated small meteorological tsunami waves observed globally." | NCEI news page (above); https://www.ngdc.noaa.gov/hazard/15jan2022.html | VERIFIED |
| Max local wave | NCEI: "a team of international scientists ... determined that the maximum tsunami height on land was about 22 meters (72 feet) on Tofua Island." NCEI runups: Tofua SW 22 m (field survey), Nomuka Iki cliff 20.5 m, Likualofa 18.7 m. Lynett: a weather-station tower at ~13 m elevation was toppled at Kanokupolu, "suggesting tsunami flow elevations significantly more than 13 m above mean sea level"; Nuku'alofa "less than 5 m". | NCEI news page; https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/runups?tsunamiEventId=5824 ; Lynett PMC | VERIFIED |
| Deaths (official-ish) | NCEI: "only four deaths in Tonga were attributed to the tsunami." "two fatalities reported in Peru were the first time in over 10 years that tsunami-related deaths occurred in the far-field." Lynett: "According to Peru's National Institute of Civil Defense, two people died because of the tsunami at Naylamp beach". Damage: "most of the $118 million (USD) in damages in Tonga were due to the tsunami." | NCEI news page; Lynett PMC | VERIFIED (NOAA/peer-reviewed). I did not find a final Tongan-government/OCHA/WHO document; early reports said three in Tonga (SNIPPET) |
| Why few deaths | NCEI: "This low number of casualties was attributed to multiple factors, including the event having occurred during the day, the early arrival of moderate tsunami waves prior to the largest and most destructive wave, and the effectiveness of recent tsunami awareness education and outreach campaigns." Lynett: the precursor wave "fortuitously acted as a warning and prompted initial evacuations in Tongatapu, probably averting loss of life." | same | VERIFIED |
| Far-field | Lynett: "In South America, widespread tsunami amplitudes of approximately 1 m were observed." NCEI/NGDC: "The tsunami registered over 1 meter at tide gauges in Tonga, Vanuatu, New Caledonia, Australia, Cook Islands, New Zealand, Hawaii, Japan, Chile, Alaska, and California." | Lynett PMC; NGDC page | VERIFIED |
| Caldera collapse as tsunami source | Not established by what I read: Lynett's near-field source is the "water cavity"; Carvajal says mechanism "cannot be identified by the tide gauge data alone"; NOAA's generic list includes caldera formation. | - | UNVERIFIED for Hunga (do not state caldera collapse caused the Tonga tsunami) |

---------------------------------------------------------------------

## Concept 7: Natural tsunami warning signs and response (NOAA / NWS)

**Narration-ready:**
"If you are near the coast and feel a strong or long earthquake, see the sea suddenly drain away or rush in, or hear a loud roar from the ocean, a tsunami may be minutes away. Do not wait for an official warning. Move right away to high ground or as far inland as you can, and stay away until officials say it is safe."

| Claim | Verbatim excerpt | URL | Status |
|---|---|---|---|
| Natural signs | "If you are in a tsunami hazard or evacuation zone or a low-lying coastal area and you feel a strong or long earthquake, the ocean acts strange (e.g., it looks like a fast-rising flood or a wall of water or it drains away suddenly, showing the ocean floor like a very low tide) OR there is a loud roar coming from the ocean, a tsunami is possible and could arrive within minutes." | https://www.weather.gov/safety/tsunami-during (live) | VERIFIED |
| Do not wait | "Do not wait for an official tsunami warning or for instructions from local officials." | same | VERIFIED |
| Where to go | "move quickly to your safe place outside the hazard or evacuation zone. If you do not have a safe place or cannot reach it, follow evacuation signs to safety or go as high or as far inland (away from the water) as possible." | same | VERIFIED |
| Beach rule | "If you are on the beach or near the water and feel an earthquake-no matter how big or how long it lasts-move quickly off the beach to high ground or inland (away from the water) as soon as you can do so safely." | same | VERIFIED |
| Stay away | "Stay out of the tsunami hazard or evacuation zone until local officials tell you it is safe. The first wave may not be the last or the largest and the danger may last for hours or days." | same | VERIFIED |
| NOAA education version | "There may not be time to wait for an official warning, so it is important to be able to recognize natural tsunami warnings. These include strong or long earthquakes, a loud roar (like that of a train or an airplane) coming from the ocean, and a sudden rise or fall of the sea level that is not related to the tide." / "Stay out of the tsunami hazard zone until local officials tell you it is safe, as the danger may last for hours or days." | https://www.noaa.gov/education/resource-collections/ocean-coasts/tsunamis (live) | VERIFIED |
| Earthquake safety first | "In case of an earthquake, protect yourself. Drop, cover and hold on." | weather.gov/safety/tsunami-during | VERIFIED |

---------------------------------------------------------------------

## Numbers safe to say on screen (exact wording)

| On-screen text | Backing |
|---|---|
| "May 4, 2018: M6.9 earthquake, Kilauea's south flank" | USGS hv70116556; HVO |
| "12:32 p.m. Hawaii time" | USGS ComCat origin 22:32:54 UTC; HVO "approximately 12:32 p.m. HST" |
| "Strongest Hawaii quake since 1975" | HVO release (quoted above) |
| "South flank moved about 5 meters" | USGS ("dilated the rift zone by approximately 5 m"); Neal: "~5 m of fault slip". Say "about 5 meters" |
| "Small tsunami, about 40 cm at the nearest gauge" | PTWC statement 3 (Kapoho 40 cm amplitude); NCEI 0.4 m |
| "No destructive tsunami" | consistent with PTWC/NCEI (max 0.4 m, no tsunami damage reported in what I read; I did not search for damage reports) |
| "62 summit collapses, each about magnitude 5" | USGS (62 events; M5.2-5.4 near-daily); Neal M4.7-5.4. "About M5" |
| "Ash is rock, minerals and glass, smaller than 2 mm" | USGS ash.html / ash_particle_size.html |
| "May 17, 2018: ash cloud 30,000 ft (about 9 km)" | USGS chronology and FAQ ("at least 30,000 ft", "as high as 30,000 feet above sea level") |
| "Over 80% of tsunamis are caused by earthquakes" | NOAA education page (since 1900, "over 80% of likely tsunamis"); tsunami.gov: 88% earthquakes or earthquake-triggered landslides |
| "Krakatau, 26-27 August 1883: more than 36,000 dead" | GVP "more than 36,000 fatalities"; Lynett "at least 36,000"; Royal Society 1888 36,380 |
| "2004 Sumatra M9.1: about 230,000 dead (NOAA)" | tsunami.gov "approximately 230,000 deaths" |
| "Tonga, Jan 15, 2022: plume about 57 km high" | Science paper 57 km; NASA 58 km |
| "Umbrella cloud about 500 km wide" | Carn quote on NASA page |
| "Tallest measured wave on land: about 22 m (Tofua Island)" | NCEI field survey |
| "Tonga: 4 deaths; Peru: 2 deaths" | NCEI news page |
| "Strong or long quake, sea drains or surges, loud roar: go to high ground now" | weather.gov/safety/tsunami-during |

Hard "do not say": "no tsunami" (Kilauea); "USGS says 228,000"; "36,417 (Royal Society)"; "VEI 6/5" for Tonga; "caldera collapse caused the Tonga tsunami"; "the Hilina fault slipped".

---------------------------------------------------------------------

## Oversimplification traps

1. "Volcanoes cause most tsunamis" - false. NOAA: over 80% (88% including quake-triggered landslides) come from earthquakes; volcanic tsunamis are "infrequent" and "rarely affect distant coastlines" (Hunga Tonga is the exception because of the pressure wave).
2. "Ash is smoke / ash is burnt material" - USGS: "not the product of combustion". Volcanic "smoke" is gas/steam or, in plume photos, mostly ash plus condensed steam.
3. "Kilauea's M6.9 was caused by lava" - USGS says "likely caused by pressure induced by the dike" (magma intruding underground, before and beside the surface eruption), with slip on the decollement. Lava on the surface did not cause the earthquake.
4. "Kilauea's 2018 summit explosions were magma-driven mega-blasts" - USGS: ash was "primarily lithic", with "none of the anticipated violent explosions".
5. "The tsunami came from the eruption column" (Tonga) - no: air-sea coupling by the explosion/pressure pulse, collapse of the water cavity, and the global Lamb-type pressure pulse; the column height is irrelevant to the wave.
6. "The Krakatau tsunami was caused by caldera collapse" - debated; two peer-reviewed models favor submarine explosion (Nomanbhoy & Satake) and pyroclastic flow entering the sea (Maeno & Imamura). Say "scientists still debate how".
7. "Krakatau and 2004 were the same kind of tsunami" - no: volcanic vs megathrust earthquake. Do not attribute 2004 to a volcano.
8. "A magnitude 6.9 can't make any tsunami" - it did, a small one. And "a big quake always means a tsunami" - NOAA: "Not all earthquakes cause tsunamis".
9. Footage/date traps (AGENTS.md): do not use May 3-4, 2018 Leilani/Kapoho lava footage as "the earthquake" or as the tsunami; do not show ocean-entry laze footage as the tide-gauge event; the May 4 quake time (12:32 HST) is not the time of Kapoho filming; a tsunami graphic must be labelled as a diagram, and never a real-looking "wave hits Hawaii" clip. Tonga: do not use Hunga footage for Krakatau or vice versa; Krakatau has no photographs of the eruption (1883 imagery is lithographs/engravings, public-domain status per file must be checked).
10. "Plume height" confusion: 57-58 km (top) vs ~30 km (umbrella cloud level) vs 30,000 ft (Kilauea 2018, a different volcano and ~9 km).
11. Kilauea 1975 quake size (Ms 7.1 / Mw 7.4 / Mw 7.7) differs by author - skip or say "magnitude 7+".
12. "Amplitude" vs "run-up" vs "height": PTWC reported gauge amplitude (40 cm); do not call 40 cm a "40 cm wave height on the coast" without the gauge wording.

---------------------------------------------------------------------

## Not verified (open items for the team)

- Original source/derivation of 36,417 (NCEI total; widely attributed to Dutch colonial authorities, only SNIPPET/secondary). The Royal Society 1888 report says 36,380. The split between tsunami deaths and pyroclastic-flow deaths is not established (NCEI 34,417 vs 36,417; NOAA FAQ "more than 34,000").
- A USGS/NASA/NOAA-hosted plain-language definition of "neutral buoyancy" for umbrella clouds (only a peer-reviewed abstract and the NASA umbrella cloud mention).
- A source that explains why the Kilauea May 4 tsunami was small (the generic NOAA rule is verified; the application to this event is my inference). Whether a coseismic landslide contributed is unresolved (SNIPPET only, conference abstract).
- USGS "volcanic gas" web page (usgs.gov returns 403 to scripts); I used USGS OFR 95-85 and the USGS ash/gas/vog page instead.
- Final official Tonga government/OCHA/WHO death count (NCEI says four in Tonga; early reports said three).
- Precise tsunami arrival times (HST) at Kapoho/Hilo for May 4, 2018 (only "arrived ... in less than an hour" from NCEI quoting a paper).
- Gupta et al. two-umbrella-cloud numbers (SNIPPET).
- The 2019 conference abstract on landslide contribution and Mw 7.2 geodetic study (SNIPPET; not needed for narration).
- Rights/licence of any image or footage: not examined. USGS pages mark many items "Public Domain" but AGENTS.md requires per-file checks, and NASA/NOAA/NCEI images may carry credits (e.g., NCEI Tonga photos credit Univ. of Auckland/Tonga Geological Services; not public domain by default).
- Human approvals: script, usage rights and publication remain with the team. I approved nothing and edited no review.json.

## Limits of automation

Search tools returned snippets that I discarded unless I re-read the primary text. Archive copies reflect the page state on the cited timestamp, not necessarily the state on the original event date. Several live pages (usgs.gov, volcano.si.edu) block scripts, so those quotes come from Internet Archive copies. APIs (NCEI Hazel, USGS ComCat, Iowa Mesonet) can be revised after the fact: re-run before final render. Crossref abstracts are publisher-deposited text; I did not read full papers except Neal (abstract only), Lynett (full text), Maeno & Imamura (first page) and the Royal Society 1888 report (text search).

## Reproduce (commands)

```
D=<scratchpad>
# USGS event + products (tectonic summary, impact text, moment tensor)
curl -sL --compressed https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/hv70116556.geojson
curl -sL --compressed https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/official20041226005853450_30.geojson
# PTWC statements 1-3 for May 4, 2018
curl -sL "https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil=TIBHWX&sdate=2018-05-04T21:00Z&edate=2018-05-05T12:00Z&limit=50&fmt=text"
# NOAA NCEI tsunami database
curl -sL --compressed https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/{5678,1142,2439,5824}
curl -sL --compressed "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/runups?tsunamiEventId=5678"
# Archive copies (CDX then id_), helper: $D/tools/fetcharc.sh <URL> <name>; text via $D/tools/h2t.py
# Royal Society 1888
curl -sL https://archive.org/download/eruptionkrakato00whipgoog/eruptionkrakato00whipgoog_djvu.txt | grep -n "36,380"
# Crossref abstracts: https://api.crossref.org/works/10.1126/science.abo4076 (etc.)
```
Scratch copies of the fetched sources: `$D/deadly_science/` (k2018.txt, hvo_pr.txt, hilina.txt, sf2.txt, ptwc_tib.txt, hv70116556.json, sumatra.json, faq.txt, noaa_tsu.html, wxd.html, lynett.txt, rs1888.txt, gvp_krak.txt, tonga_runups_all.json, etc.).
