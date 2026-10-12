# Footage and Rights Research: "WHEN VOLCANOES TURN DEADLY" (120 s, 1080x1920)

Researcher: Footage and Rights agent. Date of research: 2026-10-11. Repo was read-only (AGENTS.md, CLAUDE.md, assets.json, download_assets.py, timeline*.json read; nothing written there).

Work dir (all downloads untrusted, Python run with `-I`):
`S=<scratchpad>/deadly_footage`
- downloads: `$S/dl/` (kilauea, eq, noaa_tonga, noaa_honshu, tonga_sat, krakatau, safety, tsunami_diagrams)
- scripts: `$S/tools/` (wb.sh = Wayback id_ fetch, captions.py/vids.py/scan.py = page parsers, probe.sh, sheet.sh = 1 fps contact sheet, montage.py)
- previews (contact sheets / stills, all VIEWED): `$S/previews/`
- saved source pages (for rights quotes): `$S/dl/pages/`

Legend for rights status: PD-FILE = per-file "Public domain" statement seen on the agency media page; PD-SITE = only a site-wide / US-government-work statement, no per-file line (AGENTS.md: human must confirm); FLAG = third-party credit or doubt.
Nothing below is "approved"; per AGENTS.md only the group may approve rights, claims and assets. All durations/resolutions measured with ffprobe after download; every video decoded cleanly with `ffmpeg -xerror ... -f null -` (DECODE_OK).

---------------------------------------------------------------------

## Part 1. HOOK (about 6 s)

| Rank | Candidate | Type | Window | Notes |
|---|---|---|---|---|
| 1 | Reuse `assets/may22_fissure22.mp4` (USGS UAS, 22 May 2018, fissure 22, 1920x1080, 130.4 s, already in assets.json, PD-FILE "Public Domain") | REAL_FOOTAGE | 5.0 to 11.0 s (matches existing timeline.proposed.json intro bg start 5.0) | Title overlay in first ~3 s ("UAV Overflight of Fissure Complex and Lava Flows May 22, 2018") so start at 5 s. Small USGS logo bottom-left (agency credit). Contact sheet: `previews/reuse_may22_fissure22.jpg` (1 tile = 2.5 s). Blackdetect: footage until 123.6 s, end card after. |
| 2 | Photo vhp_img6058.jpg (Pu'u 'O'o ash column after M6.9 quake, 4000x3000) | PHOTO | still, Ken Burns | See Part 2. Strong hook image because it is tied to the quake. |
| 3 | `may16_fissure18` window 7 to 13 s (spatter + field audio) | REAL_FOOTAGE | per timeline.proposed.json start 7.0 | Reuse only if the quake story should open with lava. |

Recommended: #1 for motion, or open on photo #2 (ash column right after the quake) to link hook to Part 2.

---------------------------------------------------------------------

## Part 2. KILAUEA M6.9 EARTHQUAKE, 4 May 2018

Event facts (USGS ComCat via FDSN API, `https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=hv70116556&format=geojson`, saved `dl/eq/event.json`): M 6.9 (Mw), 18 km SSW of Leilani Estates, 2018-05-04 22:32:54 UTC = 12:32:54 HST, depth 5.8 km, tsunami flag = 1. USGS chronology page (May 4) says "12:33 p.m. Magnitude 6.9". Not found: any HVO video of the quake itself (no rockfall/dust webcam video on May 4 to 6 chronology pages; searched all May 2 to Jun 30 chronology pages, video list below in Gaps).

| Rank | Item | Type | Direct file URL | Page URL | Size / date taken | What it shows | Credit, rights evidence |
|---|---|---|---|---|---|---|---|
| 1 | vhp_img6058.jpg | PHOTO | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/vhp_img6058.jpg | https://www.usgs.gov/media/images/1244-pm-a-column-robust-reddish-brown-ash-plume-occurre (Wayback 20210422235804id_) ; chronology https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-4-2018 | 4000x3000, taken Fri 4 May 2018 | "At 12:44 p.m. HST, a column of robust, reddish-brown ash plume occurred after a magnitude 6.9 earthquake shook" (aerial view of a crater with the column) | USGS / HVO. Media page: "(Public domain.)" and "Date Taken: Friday, May 4, 2018". PD-FILE. UNVERIFIED: caption does not name the crater; it is visually Pu'u 'O'o, USGS captions elsewhere say Pu'u 'O'o crater collapsed 30 Apr. Confirm location text with HVO before writing "Pu'u 'O'o". |
| 2 | vhp_img6054.jpg | PHOTO | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/vhp_img6054.jpg | https://www.usgs.gov/media/images/steaming-cracks-leilani-street-view-looking-rift-crack-i (Wayback 20210420034514id_) | 2250x3000 (portrait), taken 4 May 2018 | Steaming cracks on Leilani Street, Leilani Estates; "crack in foreground opened during the 12:33 p.m. Magnitude 6.9 South flank of Kilauea earthquake" | USGS Volcano Hazards Program. Media page "(Public domain.)". PD-FILE. Portrait orientation fits 9:16 directly. |
| 3 | USGS ShakeMap intensity map, event hv70116556 (labelled graphic) | DIAGRAM (model product, label "ShakeMap") | https://earthquake.usgs.gov/product/shakemap/hv70116556/atlas/1594331340758/download/intensity.jpg | https://earthquake.usgs.gov/earthquakes/eventpage/hv70116556 | 787x998 | Macroseismic intensity map; Hawaii island, star at epicentre, intensity scale table; title burned in: "ShakeMap ... May 04, 2018 22:32:54 UTC M6.9 ... ID:hv70116556" | USGS Earthquake Hazards Program. PD-SITE (USGS site policy https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits: "While the content of most USGS websites is in the U.S. Public Domain, not all ... are"); no per-file line on product. NOTE: this "atlas" version says "Version 1: Processed 2020-06-05" (reprocessed; not the 2018 real-time map). A 2018 version (us, 612x638): .../shakemap/hv70116556/us/1536375199192/download/intensity.jpg. |
| 4 | USGS M6.9 Hawaii earthquake summary poster | DIAGRAM/graphic | https://earthquake.usgs.gov/product/poster/20180504/us/1525712175350/poster.jpg (10804x7200); medium 944x629 | event page above | 10804x7200 | Epicentral map, PAGER, DYFI, finite-fault model, seismic hazard; crop-friendly panels | PD-SITE. FLAG: poster header says "05 May 2018 04:32:55 UTC" which contradicts ComCat (4 May 22:32:54 UTC). Do not copy the poster time. It also mentions the 1975 Kalapana M7.1 quake with a local tsunami (useful bridge to Part 3; verify the claim in the poster text before use). |

Other usable May 4 to 6 USGS stills (rights on chronology page not file-level for the May 4 set; media pages needed): vhp_img6049 (fissure 2 spatter, 1 a.m.), 6050-6056, 6059-6060 (fissures 2-5, Leilani Estates), vhp_img6066 (5 May 12:26 crack in Pohoiki Rd). May 6 and 17 items have "Sources/Usage: Public Domain" on the chronology page. Contact images: `previews/img6058.jpg`, `previews/img6054.jpg`, `previews/eq_shakemap_atlas.jpg`, `previews/eq_poster.jpg`.
Recommended pick: #1 + #2 (photos, one Ken Burns each, 3 to 4 s) then #3 ShakeMap labelled "USGS ShakeMap (model estimate)".

---------------------------------------------------------------------

## Part 3. TSUNAMI MECHANISM (about 16 s)

Honest finding: no agency diagram of tsunami generation was found at video-grade resolution. The USGS "Tsunami Diagram" (https://www.usgs.gov/media/images/tsunamigif, file .../media/images/TSUNAMI.gif) is only 387x148 and its Sources/Usage field is blank (FLAG). So the rank list is model animations, which show propagation, not generation.

| Rank | Item | Type | Direct file URL | Page | Measured | Window / notes | Credit and rights |
|---|---|---|---|---|---|---|---|
| 1 | NOAA NCTR Tohoku 2011 global propagation animation `Honshu2011.mp4` | MODEL_ANIMATION | https://nctr.pmel.noaa.gov/honshu20110311/Honshu2011.mp4 | https://nctr.pmel.noaa.gov/honshu20110311/ | 1920x1080, 25 fps, 27.44 s, mpeg4, no audio (10.4 MB), decodes OK | Use 0.3 to 22.0 s (expanding wave fronts over the Pacific; by 23 s a max-amplitude map). Burned-in: NCTR colour bar and label "NCTR - NOAA Center for Tsunami Research Honshu 11 Mar 2011 (Mw=9.0) 16:42 UTC" top-left and a NOAA emblem top-right (agency, keep as credit). Vertical crop of the Pacific centre or blur-fill. It is an EARTHQUAKE tsunami; script must say so. | NOAA / PMEL / Center for Tsunami Research, "NOAA NCTR research product, Not an official forecast". PD-SITE: page requests credit only. No per-file rights quote found (www.noaa.gov/disclaimer and /copyright blocked or silent). |
| 2 | NOAA NCTR Tonga 2022 pressure-wave-forced model `ha_in_blast_Tonga_Lamb_pacific4m_ha.mp4` | MODEL_ANIMATION | https://nctr.pmel.noaa.gov/tonga20220115/ha_in_blast_Tonga_Lamb_pacific4m_ha.mp4 | https://nctr.pmel.noaa.gov/tonga20220115/ | 880x576, 8 fps, 15.1 s, h264 (3.5 MB), DECODE_OK | Whole file 0.0 to 15.1 s usable. Small globe in frame (title "Wave Amplitude", colour bar in cm): needs crop to globe + heavy upscale; low-res. Sheet: `previews/ha_in_blast_Tonga_Lamb_pacific4m_ha.jpg`. Also `ha_in_force_Lamb_pacific_4m_nocaribbean2_ha.mp4` (880x576, 4.0 s, wave amplitude in metres, 4 s only). | NOAA NCTR; page text: "NOAA NCTR research product, Not an official forecast ... please credit NOAA / PMEL / Center for Tsunami Research." PD-SITE. Page also says "Multiple tsunami generation mechanisms were at play ... not all fully understood" - narration must not state a single cause. |
| 3 | NOAA NCTR still figures (Tonga) | MODEL/DIAGRAM | https://nctr.pmel.noaa.gov/tonga20220115/images/tonga_maxamp_newinv.png (3000x2304), .../tonga_max_height_in_blast_Tonga_Lamb_pacific4m_ha.png (3300x2142), .../tonga_comparison_model_amplitude_and_DART.png (4751x2422: DART buoy records black vs model red), .../tonga_new_inversioDARTSnCircles.png (1743x1250), .../tonga_event_gauge_comparison_newinv.png (3429x5304 tide gauges) | same page | as listed | "Maximum Wave Amplitude, January 15, 2022 Tonga" (blue to red; includes NOAA emblem and "Not an official forecast" burned in). Real DART/tide-gauge records appear as black traces. | same as above. Previews: `previews/nctr_tonga_maxamp.jpg`, `previews/nctr_tonga_dart_cmp.jpg`. |
| 4 | NCTR DART station map `tsunami_monitoring_NDBC.png` | DIAGRAM/map | https://nctr.pmel.noaa.gov/images/tsunami_monitoring_NDBC.png | https://nctr.pmel.noaa.gov/Dart/ | 1326x922 | Map of DART buoys (yellow/red diamonds); good for "how we watch for tsunamis". No title, third-party ESRI-style basemap look (FLAG: basemap credit unknown). | PD-SITE, FLAG. `previews/nctr_monitoring.jpg` |

Fallback for the generation step itself: a team-made, clearly captioned schematic (see Gaps).

---------------------------------------------------------------------

## Part 4. ASH CLOUDS (about 14 s)

| Rank | Item | Type | Direct URL | Page | Measured / date | Window and on-screen text | Credit and rights |
|---|---|---|---|---|---|---|---|
| 1 | Video: Kilauea summit explosion, 24 May 2018 about 6:00 p.m. HST, ash cloud to 10,000 ft asl | REAL_FOOTAGE | https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/atoms/video/multimediaFile-2114.mp4 | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-25-2018 (Wayback 2025) | 1920x1080, 29.97 fps, 37.84 s, h264 + AAC audio, 46.6 MB, DECODE_OK; sha256 prefix 1b33a67cdb715396 | USE 4.3 to 30.0 s. 0 to 4.2 s = USGS logo + title card; 30 to 31.5 s fade; 31.6 s to end = text + logo card. During footage: small USGS logo bottom-left only. Ground-level view of the plume growing and spreading; wind-sheared top. Sheets: `previews/k2114.jpg`, `previews/k2114_tail.jpg`. | USGS / HVO. Chronology page: "Sources/Usage: Public Domain." PD-FILE. Page says "Video from the U.S. Geological Survey Hawaiian Volcano Observatory". Does not show an umbrella cloud proper; call it an "ash plume". |
| 2 | Photos 15 May 2018 Overlook crater ash plumes: multimediaFile-2026.jpg (11:05 a.m., Jaggar Museum, 5472x3648), multimediaFile-2028.jpg (1:38 p.m., 5472x3648), -2029.jpg (ash falling on Ka'u Desert), -2022.jpg (Civil Air Patrol aerial, 3000x2250) | PHOTO | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/multimediaFile-2026.jpg (same pattern for 2028, 2029, 2022) | https://www.usgs.gov/volcanoes/kilauea/news/photo-and-video-chronology-kilauea-may-15-2018 | dates 15 May 2018 | Dark ash columns rising from Halema'uma'u with visible ash fall. Stills: `previews/kilauea_ash_stills.jpg` | USGS / HVO; each has "Sources/Usage: Public Domain." on the chronology page. PD-FILE (chronology-level per item). |
| 3 | Photo vhp_img6385.jpg: 6 June 2018 4:07 p.m. explosion, plume to about 10,000 ft | PHOTO | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/vhp_img6385.jpg | .../photo-and-video-chronology-kilauea-june-7-2018 | 5472x3648 | caption also states "energy equivalent to that of a magnitude-5.6 earthquake" | "Sources/Usage: Public Domain." PD-FILE. |
| Umbrella cloud | see Part 7 (GOES-17 imagery of Tonga) | SATELLITE_OBSERVATION | | | | | |
| other | USGS webcam frame vhp_img6182.png (Mauna Loa webcam, 17 May 2018 05:10:04 HST plume, 981x599) | REAL webcam frame | .../s3fs-public/vhp_img6182.png | may-17 chronology | 981x599 | low-res, burned-in "Moku'aweoweo Caldera 2018-05-17 05:10:04 (HST)" and "USGS-HVO" | "Sources/Usage: Public Domain." PD-FILE. |

Recommended: #1 video 4.3 to 18 s plus 2 to 3 stills from #2 (15 May) for variety.

---------------------------------------------------------------------

## Part 5. LAZE (about 10 s)

| Rank | Item | Window | Notes |
|---|---|---|---|
| 1 | Reuse `assets/jun04_kapoho.mp4` (68.5 s, 1920x1080, USGS, in assets.json, PD-FILE) | Video 1 (6:15 a.m. overflight): 11.0 to 38.5 s (title cards 0 to 10.8 s and a "Video 2" card at 39.2 to 41.6 s via blackdetect). Video 2 (1:38 p.m., clear water, laze + new delta + houses): 41.8 to 54.3 s. End text card from 54.9 s. | Small USGS logo bottom-left. Contact sheet: `previews/reuse_jun04_kapoho.jpg` (tile = 2.5 s). Recommended 10 s: 41.8 to 51.8 s (colour, laze plume against blue ocean) or 12 to 22 s (dense white laze). |
| 2 | multimediaFile-2091.mp4 (21 May 2018 overflight showing laze) and multimediaFile-2214.mp4 (9 June 2018 ocean entry) | not downloaded | Page URLs: chronology May 21 and June 9; both "Public Domain". |
| 3 | Stills: vhp_img6417 / multimediaFile-2218.png / vhp_img6463 (laze plumes) | stills | PD per chronology pages (not downloaded). |

Science caveat for narration: USGS caption describes laze as steam + hydrochloric acid + glass particles (June 4/7 chronology pages).

---------------------------------------------------------------------

## Part 6. KRAKATAU 1883 (about 16 s)

Source of all items below: Royal Society, "The eruption of Krakatoa, and subsequent phenomena. Report of the Krakatoa Committee of the Royal Society", ed. G. J. Symons (London: Trubner and Co., printed by Harrison and Sons, 1888). Digitised by Wellesley College Library via the Internet Archive: https://archive.org/details/eruptionofkrakat00roya . Archive metadata has no licence/rights field. Publication 1888 means public-domain-by-age (US pre-1929; authors died 1885 to 1916), but the scan host did not state a licence: PD-by-age (FLAG for human confirmation). Direct per-page JPEG: `https://archive.org/download/eruptionofkrakat00roya/page/n<LEAF>_w2000.jpg` (leaf numbers measured from `_scandata.xml`/thumbnail review; verified downloadable with curl). A 2726x3468 Commons copy of Plate I exists (https://commons.wikimedia.org/wiki/File:Krakatoa_eruption_lithograph.jpg, licence "Public domain", credit "Plate 1 ... Trubner & Co., 1888", artist "Parker & Coward") and cross-checks the same plate; the Royal Society picture library lists it as RS.10670 with a copyright line ("(c) The Royal Society" = their scan claim, do not use that source).

| Rank | Item | Type | Direct file | Size | What it shows | Caveat |
|---|---|---|---|---|---|---|
| 1 | Plate I, "View of Krakatoa during the Earlier Stage of the Eruption, from a Photograph taken on Sunday the 27th of May, 1883." Lithograph Parker and Coward, imp. West, Newman and Co. | HISTORICAL_ILLUSTRATION (lithograph after a photograph) | https://archive.org/download/eruptionofkrakat00roya/page/n29_w2000.jpg | 2793x3845 | Dramatic ash column with falling ash curtains and glowing vent, sea in foreground; portrait, fits 9:16 with a crop of page margins | DEPICTS 27 MAY 1883 (early phase), NOT the 26/27 Aug 1883 paroxysm. Label it exactly. Page margin has header "Krakatoa. Rep. Roy. Soc. Com." and "Plate I." (crop out). Preview `previews/krak_plate1_view.jpg`. |
| 2 | Plate XIX, tide-gauge records 27 to 28 Aug 1883 (Port Blair, Negapatam, Madras, Vizagapatam, False Point) | HISTORICAL_ILLUSTRATION / scientific record (DIAGRAM) | https://archive.org/download/eruptionofkrakat00roya/page/n222_w2000.jpg | 3238x4022 | Real instrument curves with the disturbance after the eruption (arrival times labelled e.g. 13h55) | Text is period typography; narration must not read values it does not support. More tide plates at leaves 224, 230, 232, 234, 238, 240 (thumbnails reviewed). `previews/krak_n222.jpg` |
| 3 | Plates XXXII and XXXIII, "Sunda Strait before the eruption of Aug. 1883" and after (admiralty-style charts with soundings) | HISTORICAL_ILLUSTRATION (map) | https://archive.org/download/eruptionofkrakat00roya/page/n248_w2000.jpg (before, 3425x3153) and .../n250_w2000.jpg (after, 3474x3041) | as stated | Krakatoa island group before vs after (island largely gone) | Use as a before/after cross-fade; I viewed n248 (before); n250 is the matching after plate (thumbnail viewed). `previews/krak_n248.jpg`, `previews/krak_n250.jpg` |
| 4 | Plate II "Two views of Krakatoa after August" and the air-wave/barograph plates (part II) | HISTORICAL_ILLUSTRATION | leaves not extracted (Plate II location unresolved; wave-track plates around leaves 146, 148, 442) | | | Left for a second pass; `previews/krak_c.jpg` shows thumbnails of leaves 146 to 446. |

NOAA NCEI hazard image library: no Krakatau 1883 item found via search (the library's site was reachable at ncei.noaa.gov but no Krakatau record surfaced). Not claimed.
Crop suggestions (vertical): Plate I portrait with ~6 % crop top/bottom; slow push-in from the base to the plume top (about 8 s). Add a lower caption "Lithograph, 1888, after a photograph of 27 May 1883".

---------------------------------------------------------------------

## Part 7. TONGA 2022 (about 20 s)

| Rank | Item | Type | Direct URL | Page | Measured | Window / on-screen text | Credit and rights |
|---|---|---|---|---|---|---|---|
| 1 | NOAA NESDIS "Tongan Eruption Ripples Around the Globe" text-free MP4 (Earth from Orbit; GOES-17 visible/IR/water-vapour sequences) | SATELLITE_OBSERVATION (some segments derived products) | https://www.nesdis.noaa.gov/s3dl?path=/s3/2022-01/Tonga_EfO_4k_clean.mp4 (curl needs a browser User-Agent) | https://www.nesdis.noaa.gov/news/the-hunga-tonga-hunga-haapai-eruption-multi-hazard-event | 3840x2160, 29.97 fps, 111.18 s, h264 + AAC (347.6 MB), DECODE_OK; sha256 prefix 03771562a42ef0e6 | Cut list by scene detection: 0.3 to 12.0 s GOES-17 close-up of the umbrella cloud forming (clean, no text; `previews/nesdis_goes_6.jpg`). 12.3 to 22.2 s = Himawari-8 GeoColor (JMA, FLAG third-party). 25.2 to 29.5 s GOES panels with lat/long grid lines. 38.9 to 52.9 s false-colour IR with burned-in yellow text "METAR/Maritime/LDADMo ... GOES-17 C8-13 ... Sat 09:46Z" bottom-right (crop out or skip). 53.0 to 66.0 s pink globe: water-vapour difference showing waves around the Earth; NOAA's captioned version labels this segment "atmospheric shockwaves traveling around the world" (use NOAA's own wording). 66 s onward: aerial/ground photos of the island (Nov 2014 / Jan 2015) and Gemini webcam in the captioned version; third-party credit lines in the captioned file ("International Gemini Observatory/NOIRLab/NSF/AURA"): AVOID. | NOAA NESDIS. NESDIS news page offers the file for download; no per-file licence statement on the page. PD-SITE (US government work) - human must confirm. Himawari-8 portions are JMA data. Contact sheets: `previews/nesdis_EfO_clean_a.jpg`, `nesdis_EfO_0_30.jpg`, `nesdis_EfO_48_78.jpg`, `nesdis_EfO_64_112.jpg`; captioned version for identification only `nesdis_EfO_final.jpg` (file `Tonga_EfO_4k_final.mp4`, 117.5 s). |
| 2 | NASA Earth Observatory still: GOES-17 sequence of the 15 Jan 2022 plume (8 panels, 2880x1440) `hungatonga_goes_2022015_lrg.jpg` | SATELLITE_OBSERVATION | https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/149000/149474/hungatonga_goes_2022015_lrg.jpg | https://science.nasa.gov/earth/earth-observatory/tonga-volcano-plume-reached-the-mesosphere-149474/ (Visible Earth 149474) | 2880x1440 | Each panel about 720x720 can be cut out; plume with shadows; no burned-in text. `previews/tonga_goes_still.jpg` | "GOES-17 imagery courtesy of NOAA and NESDIS" (NASA EO credits Joshua Stevens). NASA media policy (https://www.nasa.gov/nasa-brand-center/images-and-media/): "NASA content ... generally are not subject to copyright in the United States ... NASA should be acknowledged as the source." PD-SITE. |
| 3 | NASA EO video `tonga_goeshmw_2022015.mp4` stereo height retrieval of the plume (data visualisation) | MODEL/derived DATA VISUALISATION from GOES-17 + Himawari-8 | https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/149000/149474/tonga_goeshmw_2022015.mp4 | same | 1920x1080, 29.97 fps, 33.1 s, h264 (45.5 MB), DECODE_OK | White background, colour bar, UTC labels and a looping "REPLAY" plus caption text burned in ("The initial eruption sent the plume to an altitude of 58 kilometers..."). Not natural imagery. Use only as a labelled "NASA height analysis" about 5 s at most. `previews/tonga_goeshmw.jpg` | NASA Earth Observatory images and video by Joshua Stevens, data courtesy of Kristopher Bedka and Konstantin Khlopenkov / NASA Langley, GOES-17 courtesy NOAA/NESDIS; also uses Himawari-8 (JAXA/JMA) FLAG. NASA policy quoted above. |
| 4 | NASA SVS 31277 "Gravity waves from Hunga Tonga Eruption", GOES-17 water-vapour difference | derived SATELLITE product | page https://svs.gsfc.nasa.gov/31277 ; files hunga_tonga_btemp_diff_g17_b08_1080p15.mp4 (1080x1080, 30 MB), ..._crop_1080p15.mp4 (1920x1080, 72.7 MB), three_geo_sats_1080p15.mp4, himawari_..._1080p15.mp4 under https://svs.gsfc.nasa.gov/vis/a030000/a031200/a031277/ | | I downloaded `..._crop_1080p15.mp4` through the Internet Archive copy (http://web.archive.org/web/20250419041358id_/https://svs.gsfc.nasa.gov/vis/a030000/a031200/a031277/hunga_tonga_btemp_diff_g17_b08_crop_1080p15.mp4): 1920x1080, 15 fps, only 5.07 s, DECODE_OK (the direct svs.gsfc.nasa.gov host reset the TLS connection from this machine, so the direct URL is UNTESTED here) | Title block "2022-01-15 hhmm" + colour bar are burned in. Shows ring-shaped gravity waves in difference imagery; this is NOT the barometric Lamb wave. Rings visible from about 0510 to 0740 UTC only. `previews/svs31277_g17.jpg` | Credit "NASA's Goddard Space Flight Center, Visualizer Marit Jentoft-Nilsen". NASA policy as above. Does not display a copyright mark. SVS mentions Himawari/GOES-16 variants (Himawari = JMA). |
| 5 | NASA EO Landsat 8 OLI, Tongatapu: 11 May 2020 vs 25 Jan 2022, ash cover | SATELLITE_OBSERVATION | https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/149000/149391/tonga_oli_2020132_lrg.jpg and .../tonga_oli_2022025_lrg.jpg (both 3189x3189) | https://science.nasa.gov/earth/earth-observatory/island-nation-hit-hard-by-eruption-149391/ | 3189x3189 | Before/after of the main island: green to ash-grey/tan; no text | NASA/USGS Landsat 8 OLI; PD-SITE. (Companion ALOS-2 damage-proxy map `tonga_alos_2022022_lrg.jpg` is based on JAXA ALOS-2 data (the NASA page credits JAXA as operator): FLAG, derived damage product, not recommended.) |
| 6 | NOAA NCTR DART/tide-gauge model comparison figures and wave animations | MODEL_ANIMATION / plots | see Part 3 | | | | PD-SITE |

NOAA image of the 13 Jan 2022 eruption (GOES West GIF `20220113-HungaVolcanoA.gif`, 2.9 MB downloaded) is a DIFFERENT eruption from 15 Jan; do not label it 15 Jan.
Real photos of tsunami damage: none rights-clear found (see Rights concerns).
Recommended 20 s: 0.3 to 8.3 s of #1 (umbrella cloud forming) -> 2 s #2 panel stills -> 6 s #1 53.0 to 59.0 s (globe water-vapour waves, using NOAA's wording) -> 3 s Part 3 NCTR max-amplitude figure -> 3 s #5 Tongatapu ash before/after.

---------------------------------------------------------------------

## Part 8. SAFETY LESSON (about 14 s)

| Rank | Item | Type | Direct file | Page | Measured | Notes | Credit and rights |
|---|---|---|---|---|---|---|---|
| 1 | "Tsunami Evacuation Sign": official blue "TSUNAMI EVACUATION ROUTE" sign + blue arrow, Nehalem, Oregon | PHOTO | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/Nehalem_cropped.jpg | https://www.usgs.gov/media/images/tsunami-evacuation-sign (Wayback 20260711051300) ; same photo on https://www.usgs.gov/media/images/tsunami-evacuation-route-sign with credit line | 1078x711, ffprobe OK; identical sha256 to the 2017 "Cars Sign.jpg" | Sign right-hand third of frame; vertical crop 400x711 would be upscaled about 2.7x (soft). Incidental business signs ("Nehalem Food Mart"), parked cars, licence plates, small pedestrian: decide whether to blur. `dl/safety/Nehalem_cropped.jpg` | "Sources/Usage: Public Domain." on the tsunami-evacuation-sign page; other page: "Photograph credit: Nathan Wood, USGS". PD-FILE. |
| 2 | USGS illustration "Entering Tsunami Evacuation Area Sign" (TsunamiMessaging_0.gif) | DIAGRAM/illustration | https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/TsunamiMessaging_0.gif | https://www.usgs.gov/media/images/entering-tsunami-evacuation-area-sign | not downloaded | "Sign used in tsunami evacuation zones to let people know of the tsunami risk in that area." | "Sources/Usage: Public Domain." PD-FILE; resolution unchecked. |
| 3 | NOAA NWS Tsunami Safety page images (coast600.png etc.) | PHOTO | https://www.weather.gov/images/safety/slider/coast600.png | https://www.weather.gov/safety/tsunami | 600x346 | FLAG: photo credit "Bettie Miner", burned-in caption text, 600 px wide: reject. | NWS disclaimer https://www.weather.gov/disclaimer: "The information on National Weather Service (NWS) Web pages are in the public domain, unless specifically noted otherwise ... " |
| other | USGS sign pages "Tsunami Evacuation Route" and "Tsunami Hazard Zone" (usgs.gov/media/images/tsunami-evacuation-route, /tsunami-hazard-zone) | PHOTO | not resolved: not in Wayback; try from a normal browser | | | | listed by search as USGS; UNVERIFIED |
| other | NOAA OER "Tsunami Evacuation Sign" old San Juan (sign-500.jpg 47 KB) | PHOTO | linked on oceanexplorer.noaa.gov/okeanos/explorations/ex1502/logs/apr27/media/sign.html | | low-res | "Image courtesy of the NOAA Office of Ocean Exploration and Research". Too small. | |

"Real footage of a receding sea": none found that is rights-clear and agency-originated (see Gaps).
Recommended: sign photo (PD-FILE) + on-screen text lines taken from NOAA/USGS sources (the "Earthquake, go high" wording must come from a cited NWS/USGS source; the NWS tsunami pages were not read for exact wording). Add a team-made text card for the three steps.

---------------------------------------------------------------------

## Rights concerns (read before approving)

1. Per AGENTS.md, no "public domain" of a page counts for every image: only these items have a per-file line that I saw: vhp_img6058, vhp_img6054 (media pages "(Public domain.)"); multimediaFile-2114 video, multimediaFile-2022/2026/2028/2029, vhp_img6385, vhp_img6182 (chronology page lists "Sources/Usage: Public Domain." under each item); USGS tsunami-evacuation-sign (Nehalem). Everything from NOAA NESDIS/NCTR and NASA rests on site-wide statements (NASA media guidelines; NOAA "credit NOAA/PMEL"); no per-file licence text. The group must record who verified each and when.
2. USGS caution: "not all information, illustrations, or photographs on our site are [public domain]". On May 12, 2018 chronology page multimediaFile-2007.mp4 is "Some content may have restrictions" (University of Hawai'i, Cheryl Gansecki): DO NOT USE. May 5 thermal map overlays a "copyrighted satellite image (used with permission) provided by Digital Globe": DO NOT USE.
3. Himawari-8 imagery (JMA; the NASA EO video also credits JAXA) appears inside the NOAA "Earth from Orbit" video 12.3 to 22.2 s and in some NASA products. ALOS-2 (JAXA) in the NASA damage map. Treat as third-party: skip or get permission/terms.
4. NOAA "Earth from Orbit" captioned version credits "International Gemini Observatory/NOIRLab/NSF/AURA" and island photos (Nov 2014 / Jan 2015, uncredited in the clean file): use only the cleared windows listed above.
5. Krakatau scan: host is Internet Archive / Wellesley College Library; no licence field. Work is 1888 (public-domain-by-age) but archive.org makes no statement; Royal Society's own image library asserts (c): not used.
6. Wikimedia Commons file (Plate I) is only a cross-check of PD status; not needed as a source.
7. Identifiable people/likeness: the Nehalem sign photo shows small pedestrians and licence plates; Kapoho/Nehalem images show houses; Plate I none. USGS site policy: personnel likeness/voice may carry publicity rights for commercial use (not applicable to a class project).
8. NASA SVS direct host failed TLS from this machine; the SVS file in dl/ came from a Wayback copy of the NASA URL (byte-identical origin not provable).
9. NCTR products carry "Not an official forecast / research product" in the images; keep that disclaimer on screen when used.

## Gaps and honest ways to fill them

- No HVO video of the 4 May 2018 earthquake itself (no webcam/rockfall/dust clip on the May 4 to 6 chronology pages; the May 9, 11 and 15 summit ash events appear there only as stills, and the May 11 video multimediaFile-2005.mp4 is a Pu'u 'O'o crater overflight, not the quake). Fill: two PD photos (6054, 6058) + ShakeMap labelled "model estimate", with narration stating that the footage is a still photo, not the quake moment.
- No agency tsunami-generation diagram at usable resolution. USGS TSUNAMI.gif is 387x148 with blank rights. Fill with a team-drawn flat schematic (plain vector, labelled "Illustration, not to scale. Team-made.") built after the human approves wording; or show NOAA NCTR propagation animation and say it shows spread, not generation. Note volcanic tsunamis involve multiple mechanisms (NCTR text).
- Real photos/video of Tonga tsunami effects: none rights-clear (NZDF photos "Crown copyright", Reuters/Maxar commercial). Fill with NASA Landsat before/after (#5) and NOAA NCTR DART plots.
- Real footage of a receding sea: none rights-clear and agency-originated found. Fill with the Nehalem sign PD photo and a text card that explains the natural warning (strong long shaking, ocean drawing back, loud roar), sourced to NWS/NOAA text which must be read and cited by the group.
- Krakatau climactic eruption (26/27 Aug 1883): Plate I shows the 27 May early phase only. For the paroxysm use the tide-gauge Plates (XIX etc.) and Sunda Strait before/after charts; no genuine illustration of the paroxysm found yet. NOAA NCEI hazard library: no Krakatau record found.
- Pressure wave (Lamb wave) from Tonga: NOAA's pink-globe segment is a water-vapour difference product; NCTR Figure 4 (barometric observations animation) has no downloadable mp4 on the page; `ha_in_force...mp4` is only a 4 s forcing model.
- Need more clean, text-free GOES-17 true colour: NESDIS 0.3 to 12.0 s is the only fully clean umbrella-cloud window found.

## Evidence already in hand (what exists)

Downloaded and decodable under `$S/dl/` with sha256 (first 16 hex): vhp_img6058.jpg 89701a55f643c13b; vhp_img6054.jpg 3d92c857771d538c; multimediaFile-2114.mp4 1b33a67cdb715396; multimediaFile-2026.jpg ad970c03b71bb0e1; multimediaFile-2028.jpg ff1d190bf1c59998; vhp_img6385.jpg f5355d450f7595f3; Honshu2011.mp4 48e7fcdc7a55e956; ha_in_blast_Tonga_Lamb_pacific4m_ha.mp4 07b94cf0a5943b5d; Tonga_EfO_4k_clean.mp4 03771562a42ef0e6; hungatonga_goes_2022015_lrg.jpg 69d6503c349981ca; tonga_oli_2022025_lrg.jpg 7040fb2279de31f8; tonga_oli_2020132_lrg.jpg 949541ff2175a9cd; n29_w2000.jpg f87974afd163a5f6 (Plate I); n222 8aa3b4bec6e6b99b; n248 42bfac383d2179b1; n250 76c18aa8ddf3fc41; Nehalem_cropped.jpg ae3376b1bb1f5ffa; shakemap_atlas_intensity.jpg c3d7823812dddb20.

## Not validated

- Scientific claims in any caption beyond what the cited agency page says (e.g. "58 km", "500 km umbrella", "1975 Kalapana tsunami killed 2") are not verified against claims.json.
- Location text for vhp_img6058 (Pu'u 'O'o) and the exact time-stamps of NESDIS segments (cut points from scene detection at 480 px, not frame-reviewed).
- The window numbers are proposals from 1 fps / 0.5 fps contact sheets; AGENTS.md: a human must watch each window before values go to timeline.json. None applied.
- Direct SVS download URLs untested (TLS reset); usgs.gov blocks scripts, media pages were read from Wayback copies (dated in the Page column; content may have changed since).
- No colour/loudness/audio assessment. Audio exists in 2114 (field audio, not reviewed by ear) and the NESDIS file (music/audio: not checked; the "clean" file has an AAC track of unknown content).

## Reproduce (examples)

```
S=<scratchpad>/deadly_footage
curl -sL -o $S/dl/kilauea/multimediaFile-2114.mp4 https://usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/atoms/video/multimediaFile-2114.mp4
curl -sL -o $S/dl/kilauea/vhp_img6058.jpg https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/vhp_img6058.jpg
curl -sL -A "Mozilla/5.0" -o $S/dl/tonga_sat/Tonga_EfO_4k_clean.mp4 "https://www.nesdis.noaa.gov/s3dl?path=/s3/2022-01/Tonga_EfO_4k_clean.mp4"
curl -sL -o $S/dl/krakatau/n29_w2000.jpg https://archive.org/download/eruptionofkrakat00roya/page/n29_w2000.jpg
curl -sL -o $S/dl/noaa_honshu/Honshu2011.mp4 https://nctr.pmel.noaa.gov/honshu20110311/Honshu2011.mp4
$S/tools/probe.sh <file>                      # ffprobe + decode test
$S/tools/sheet.sh <video> out.jpg 1           # 1 fps, 6x5, 320 px tiles
ffmpeg -ss 4.3 -to 30.0 -i multimediaFile-2114.mp4 ...   # (example window; not applied)
```
Page evidence is under `$S/dl/pages/` (usgs chronology pages May 2 to Jun 30 2018 via Wayback id_, NASA/NOAA pages).

## Limits of the automation

Searches found candidates; I did not approve usage rights, claims, or windows, did not edit assets.json/timeline.json/review.json, and did not write any signature or manifest. Contact sheets were read by me, not by a second reviewer. A reviewer should re-watch each cut window, confirm captions/dates against the source pages, and the group (human) must approve usage rights and scripts before any publication.
