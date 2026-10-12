#!/usr/bin/env python3
"""Produce GE1013 DRAFT video from ONLY human-approved authentic USGS footage.

Input: group.json, review.json, approved USGS MP4s, logo and per-scene TTS
or a recorded voiceover. Output is not published or scientifically approved.

Guarantees enforced here (and re-checked by qa.py):
- every segment has exactly round(duration*FPS) frames; no loop/freeze padding;
- narration is only ever padded with silence, never trimmed;
- one audio encode for the whole film (no per-segment AAC seams);
- inputs are snapshotted before rendering and must be unchanged afterwards;
- fixed layout bands (caption box / footage / subtitles / voice disclosure / credit),
  text is shrunk to fit and NEVER truncated (too long -> build stops);
- subtitles are drawn with Pillow and overlaid during each scene's single encode,
  timed only by TTS WordBoundary events (no libass, no second re-encode).
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_provenance import snapshot, write_build_receipt
from review_gate import recorded_voice_path
from subtitles import generate as generate_subtitles, scene_cues
from validate import validate

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FINAL_NAME = "GE1013_Kilauea_2018_DRAFT.mp4"
FONT_PATH = None  # Resolved by build_draft(); defined for test patching.
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
# Identical encoder settings for every segment so the concat demuxer can copy streams.
VIDEO_ARGS = ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
              "-color_range", "tv", "-r", str(FPS), "-video_track_timescale", "30000"]
AUDIO_FORMAT = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
# Fixed, non-overlapping layout bands (pixels in the 1080x1920 frame).
MARGIN, TEXT_WIDTH = 22, 990
TOP_Y, TOP_MAX = 70, 380            # heading/caption box (16:9 footage starts at y=656)
SUB_TOP, SUB_BOTTOM = 1390, 1610    # subtitles: two lines max, below 16:9 footage (ends y=1264)
LABEL_Y = 1700                      # synthetic-voice disclosure pill
CARD_LABEL_Y = 1772                 # authentic-footage label on intro/outro cards
CREDIT_TOP = 1842                   # agency credit bar
WATERMARK_Y = 32                    # review-draft watermark (above the caption box)
FADE = 0.25                         # dip-to-black transition at every scene boundary (seconds)
TARGET_LUFS, TRUE_PEAK = -16.0, -1.5  # whole-mix loudness for mobile playback


def run_ffmpeg(args, cwd=ROOT):
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
                    *[str(x) for x in args]], cwd=cwd, check=True)


def probe_length(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                          capture_output=True, text=True, check=True)
    return float(proc.stdout.strip())


def probe_video(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height", "-of", "json", str(path)],
                          capture_output=True, text=True, check=True)
    stream = json.loads(proc.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def count_frames(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                           "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True, check=True)
    return int(proc.stdout.strip().split(",")[0])


def frames_for(duration):
    return round(float(duration) * FPS)


def concat_line(path):
    """FFmpeg concat-demuxer quoting: wrap in '...' and escape ' as '\\''."""
    return "file '" + str(path).replace("'", "'\\''") + "'\n"


# Every fixed on-screen string, per language. An English video must use ONLY the "en" set.
LABELS = {
    "en": {"team": "GROUP ", "authentic": "AUTHENTIC USGS FOOTAGE · NO AI-GENERATED IMAGES",
           "synthetic_voice": "Synthetic AI voice"},
    "vi": {"team": "NHÓM ", "authentic": "VIDEO THẬT: USGS · KHÔNG SỬ DỤNG HÌNH AI",
           "synthetic_voice": "Giọng đọc tổng hợp (AI)"},
}


def labels(group):
    return LABELS["en" if group.get("language") == "en" else "vi"]


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def wrap(text, count=30):
    lines, line = [], ""
    for token in text.split():
        if line and len(line) + len(token) + 1 > count:
            lines.append(line)
            line = token
        else:
            line = (line + " " + token).strip()
    return lines + ([line] if line else [])


def pixel_wrap(text, face, max_width):
    lines, line = [], ""
    for token in str(text).split():
        candidate = (line + " " + token).strip()
        if line and face.getlength(candidate) > max_width:
            lines.append(line)
            line = token
        else:
            line = candidate
    return lines + ([line] if line else [])


def fit_text(text, size, min_size, max_width, max_lines, what):
    """Shrink until the text fits; never truncate on-screen (scientific) text silently."""
    for current in range(size, min_size - 1, -2):
        face = font(current)
        lines = pixel_wrap(text, face, max_width)
        if len(lines) <= max_lines and all(face.getlength(x) <= max_width for x in lines):
            return face, current, lines
    raise ValueError(f"{what} is too long for the 1080x1920 layout: {text!r}. Shorten it (and re-approve).")


def draw_top_box(d, seg):
    heading, hs, hl = fit_text(seg["heading"], 44, 30, TEXT_WIDTH, 2, "Scene heading")
    caption, cs, cl = fit_text(seg["caption"], 34, 24, TEXT_WIDTH, 2, "Scene caption")
    bottom = TOP_Y + 22 + len(hl) * round(hs * 1.25) + 10 + len(cl) * round(cs * 1.3) + 18
    if bottom > TOP_MAX:
        raise ValueError(f"Scene heading/caption box would cover the footage area: {seg['heading']!r}")
    d.rounded_rectangle((MARGIN, TOP_Y, W - MARGIN, bottom), radius=24, fill=(0, 0, 0, 202))
    y = TOP_Y + 22
    for line in hl:
        d.text((MARGIN + 24, y), line, font=heading, fill="white")
        y += round(hs * 1.25)
    y += 10
    for line in cl:
        d.text((MARGIN + 24, y), line, font=caption, fill="#f4eacf")
        y += round(cs * 1.3)
    return (MARGIN, TOP_Y, W - MARGIN, bottom)


def draw_disclosure(d, text):
    face, _, lines = fit_text(text, 30, 22, TEXT_WIDTH - 40, 1, "Voice disclosure")
    width = face.getlength(lines[0])
    box = (round(W / 2 - width / 2 - 22), LABEL_Y - 28, round(W / 2 + width / 2 + 22), LABEL_Y + 28)
    d.rounded_rectangle(box, radius=26, fill=(0, 0, 0, 190))
    d.text((W // 2, LABEL_Y), lines[0], font=face, anchor="mm", fill="#ffe3a1")
    return box


def draw_credit(d, credit):
    face, size, lines = fit_text(credit, 26, 18, TEXT_WIDTH, 2, "Agency credit")
    d.rectangle((0, CREDIT_TOP, W, H), fill=(0, 0, 0, 195))
    for k, line in enumerate(lines):
        d.text((W // 2, CREDIT_TOP + 10 + k * round(size * 1.2)), line, anchor="mt", font=face, fill="white")
    return (0, CREDIT_TOP, W, H)


def balance_lines(lines, face):
    """Re-split a two-line subtitle so both lines have similar width (no stranded last word)."""
    if len(lines) != 2:
        return lines
    words = " ".join(lines).split()
    splits = [(" ".join(words[:k]), " ".join(words[k:])) for k in range(1, len(words))]
    fitting = [pair for pair in splits if max(face.getlength(x) for x in pair) <= TEXT_WIDTH]
    return list(min(fitting, key=lambda pair: max(face.getlength(x) for x in pair))) if fitting else lines


def subtitle_image(text):
    """Transparent strip for the subtitle band; returns (image, bbox in frame coordinates)."""
    face, size, lines = fit_text(text, 56, 40, TEXT_WIDTH, 2, "Subtitle cue")
    lines = balance_lines(lines, face)
    image = Image.new("RGBA", (W, SUB_BOTTOM - SUB_TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    step = round(size * 1.22)
    y = image.height - 8 - step * len(lines)
    for line in lines:
        d.text((W // 2, y), line, font=face, anchor="mt", fill="white", stroke_width=5, stroke_fill="black")
        y += step
    box = image.getbbox() or (0, 0, 0, 0)
    return image, (box[0], SUB_TOP + box[1], box[2], SUB_TOP + box[3])


def draw_watermark(d, text):
    face, _, lines = fit_text(text, 26, 18, TEXT_WIDTH, 1, "Watermark")
    width = face.getlength(lines[0])
    box = (round(W / 2 - width / 2 - 18), WATERMARK_Y - 22, round(W / 2 + width / 2 + 18), WATERMARK_Y + 22)
    d.rounded_rectangle(box, radius=20, fill=(150, 20, 20, 215))
    d.text((W // 2, WATERMARK_Y), lines[0], font=face, anchor="mm", fill="white")
    return box


def centered_lines(d, text, y, size, min_size, max_lines, fill, what, step=1.25):
    face, current, lines = fit_text(text, size, min_size, TEXT_WIDTH, max_lines, what)
    for line in balance_lines(lines, face):
        d.text((W // 2, y), line, font=face, anchor="mt", fill=fill)
        y += round(current * step)
    return y


def make_card(file, seg, intro, group, assets_dir, disclosure=None, background=None, watermark=None):
    """Intro/outro card. With `background` the card is a transparent layer over dimmed real footage."""
    if background:
        image = Image.new("RGBA", (W, H), (4, 16, 30, 120))
    else:
        image = Image.new("RGBA", (W, H), (8, 27, 45, 255))
    d = ImageDraw.Draw(image, "RGBA")
    boxes = []
    if intro:
        logo_path = assets_dir / "logos_from_assignment.png"
        if logo_path.is_file():
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((1000, 240), Image.Resampling.LANCZOS)
            image.alpha_composite(logo, ((W - logo.width) // 2, 110))
        else:  # never invent logos: show an explicit placeholder in review drafts
            d.rounded_rectangle((90, 110, W - 90, 290), radius=18, outline=(255, 227, 161, 255), width=3)
            d.text((W // 2, 200), "[School / course / sponsor logos: from the assignment PDF]",
                   font=font(30), anchor="mm", fill="#ffe3a1")
        y = centered_lines(d, seg["heading"], 390, 96, 60, 2, "white", "Intro title", 1.1)
        y = centered_lines(d, seg["caption"], y + 24, 44, 30, 2, "#cee5f7", "Intro caption")
        y = centered_lines(d, group["course"], y + 40, 40, 28, 2, "#c8e2f8", "Course")
        y = centered_lines(d, labels(group)["team"] + str(group["group_number"]), y + 40, 52, 34, 1,
                           "#ffe3a1", "Group number")
        for member in group["team_members"]:
            y = centered_lines(d, f"{member['name']} — {member['student_id']}", y + 8, 34, 26, 2,
                               "white", "Member line")
        if y > SUB_TOP - 20:
            raise ValueError("Intro names run into the subtitle band; shorten or reduce members")
    else:
        y = 250
        d.text((W // 2, y), "USGS · 2018", font=font(41), anchor="mm", fill="#add9f0")
        y = centered_lines(d, seg["heading"], 470, 78, 54, 2, "white", "Outro title", 1.15)
        y = centered_lines(d, seg["caption"], y + 30, 38, 28, 3, "#cee5f7", "Outro caption", 1.35)
        if y > SUB_TOP:
            raise ValueError(f"Card text runs into the subtitle band: {seg['heading']!r}")
    footer = labels(group)["authentic"]
    if background:
        footer = background["credit"]
    face, _, lines = fit_text(footer, 27, 20, TEXT_WIDTH, 1, "Card footer")
    d.text((W // 2, CARD_LABEL_Y), lines[0], font=face, anchor="mm", fill="#c8e2f8")
    boxes.append(d.textbbox((W // 2, CARD_LABEL_Y), lines[0], font=face, anchor="mm"))
    if disclosure:
        boxes.append(draw_disclosure(d, disclosure))
    if watermark:
        boxes.append(draw_watermark(d, watermark))
    image.save(file)
    return boxes


def make_overlay(file, seg, media, disclosure=None, watermark=None):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    boxes = [draw_top_box(d, seg), draw_credit(d, media["agency_credit"])]
    if disclosure:
        boxes.append(draw_disclosure(d, disclosure))
    if watermark:
        boxes.append(draw_watermark(d, watermark))
    image.save(file)
    return boxes


def crop_filter(seg, src):
    crop = seg.get("crop")
    if not crop:
        return ""
    width, height = probe_video(src)
    w, h, x, y = (int(crop[k]) for k in ("w", "h", "x", "y"))
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
        raise ValueError(f"Crop {crop} lies outside the {width}x{height} source")
    return f"crop={w}:{h}:{x}:{y},"


def cue_overlays(index, cues, tmp_dir, first_input, label):
    """Inputs + filter chain burning each cue during its exact TTS time window."""
    inputs, chain = [], []
    for k, (start, end, text) in enumerate(cues):
        png = tmp_dir / f"{index:02d}_cue{k:02d}.png"
        subtitle_image(text)[0].save(png)
        inputs += ["-loop", "1", "-i", png]
        chain.append(f"[{label}{k}][{first_input + k}:v]overlay=0:{SUB_TOP}:shortest=1:format=auto:"
                     f"enable='between(t,{start:.3f},{end:.3f})'[{label}{k + 1}]")
    return inputs, chain, f"{label}{len(cues)}"


def source_window(asset_index, assets_dir, ref, duration):
    """Resolve and length-check a real-footage window {asset_id, start_seconds}."""
    media = asset_index[ref["asset_id"]]
    src = assets_dir / media["filename"]
    start = float(ref.get("start_seconds", 0))
    available = probe_length(src) - start
    if available <= 0:
        raise ValueError(f"No usable source frames for {media['id']}")
    if available < duration:
        raise ValueError(
            f"Insufficient REAL footage for {media['id']}: only {available:.2f}s remaining, "
            f"scene requires {duration:.2f}s. Find another verified source or revise storyboard."
        )
    return media, src, start


def fades(duration):
    return f"fade=t=in:st=0:d={FADE},fade=t=out:st={duration - FADE:.3f}:d={FADE}"


def render_video(index, seg, asset_index, group, assets_dir, tmp_dir, cues=(), disclosure=None, watermark=None):
    duration = float(seg["duration"])
    frames = frames_for(duration)
    base = tmp_dir / f"{index:02d}_visual.mp4"
    if seg["kind"] in ("intro", "outro"):
        still = tmp_dir / f"{index:02d}_card.png"
        background = seg.get("background")
        if background:
            media, src, start = source_window(asset_index, assets_dir, background, duration)
            background = dict(background, credit=background.get("credit") or media["agency_credit"])
        make_card(still, seg, seg["kind"] == "intro", group, assets_dir, disclosure, background, watermark)
        if background:
            # Real footage, dimmed and softened so the title reads; credited on the card footer.
            extra, chain, last = cue_overlays(index, cues, tmp_dir, 2, "c")
            graph = ";".join([
                f"[0:v]{crop_filter(background, src)}fps={FPS},"
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
                "eq=brightness=-0.18:saturation=0.85,gblur=sigma=3,"
                f"trim=end_frame={frames},setpts=PTS-STARTPTS[bg]",
                "[bg][1:v]overlay=0:0:shortest=1:format=auto[c0]", *chain,
                f"[{last}]{fades(duration)},format=yuv420p[v]"])
            run_ffmpeg(["-ss", start, "-i", src, "-loop", "1", "-i", still, *extra, "-filter_complex", graph,
                        "-map", "[v]", "-an", "-frames:v", frames, *VIDEO_ARGS, base])
        else:
            extra, chain, last = cue_overlays(index, cues, tmp_dir, 1, "c")
            graph = ";".join([f"[0:v]trim=end_frame={frames},setpts=PTS-STARTPTS[c0]", *chain,
                              f"[{last}]{fades(duration)},format=yuv420p[v]"])
            run_ffmpeg(["-loop", "1", "-framerate", FPS, "-i", still, *extra, "-filter_complex", graph,
                        "-map", "[v]", "-an", "-frames:v", frames, *VIDEO_ARGS, base])
    else:
        media, src, start = source_window(asset_index, assets_dir, seg, duration)
        overlay = tmp_dir / f"{index:02d}_overlay.png"
        make_overlay(overlay, seg, media, disclosure, watermark)
        extra, chain, last = cue_overlays(index, cues, tmp_dir, 2, "s")
        head = f"[0:v]{crop_filter(seg, src)}fps={FPS},trim=end_frame={frames},setpts=PTS-STARTPTS"
        if seg.get("fill") == "blur":
            # Same genuine shot, blurred and darkened behind the full uncropped picture (no black bars).
            frame = [f"{head},split[full][back]",
                     f"[back]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     "gblur=sigma=28,eq=brightness=-0.22:saturation=0.8[blurred]",
                     f"[full]scale={W}:{H}:force_original_aspect_ratio=decrease[fit]",
                     "[blurred][fit]overlay=(W-w)/2:(H-h)/2,setsar=1[bg]"]
        else:
            frame = [f"{head},scale={W}:{H}:force_original_aspect_ratio=decrease,"
                     f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[bg]"]
        graph = ";".join([*frame, "[bg][1:v]overlay=0:0:shortest=1:format=auto[s0]", *chain,
                          f"[{last}]{fades(duration)},format=yuv420p[v]"])
        run_ffmpeg(["-ss", start, "-i", src, "-loop", "1", "-i", overlay, *extra,
                    "-filter_complex", graph, "-map", "[v]", "-an", "-frames:v", frames, *VIDEO_ARGS, base])
    rendered = count_frames(base)
    if rendered != frames:
        raise ValueError(f"Scene {index}: rendered {rendered} frames, expected {frames}. "
                         "Refusing to pad, loop or freeze footage.")
    return base


def check_narration_fits(index, audio, duration):
    d = probe_length(audio)
    if d > duration:
        raise ValueError(f"Scene {index}: narration {d:.2f}s exceeds {duration:.2f}s. "
                         "Shorten narration or extend segment; never silently trim speech.")
    return d


def loudness(args, cwd=ROOT):
    """EBU R128 integrated loudness (LUFS) and true peak (dBFS) of an FFmpeg input spec."""
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", *map(str, args),
                             "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                            capture_output=True, text=True, cwd=cwd)
    level = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", result.stderr)
    peak = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", result.stderr)
    if result.returncode or not level:
        raise ValueError("Could not measure loudness")
    return float(level[-1]), float(peak[-1]) if peak else 0.0


def bed_windows(segments, asset_index, assets_dir):
    """{scene: (source, start, target LUFS)} for scenes that request authentic field audio."""
    beds = {}
    for i, seg in enumerate(segments):
        ref = seg if seg.get("kind") == "video" else seg.get("background")
        if not ref or seg.get("shots") or ref.get("field_audio_lufs") is None:
            continue
        src = assets_dir / asset_index[ref["asset_id"]]["filename"]
        beds[i] = (src, float(ref.get("start_seconds", 0)), float(ref["field_audio_lufs"]))
    return beds


def build_audio(segments, scene_audio, recorded, target, cwd=ROOT, beds=None, music=None):
    """One AAC encode for the whole film. Speech is padded with silence, never trimmed.

    Optional per-scene beds of the clip's own field audio are loudness-matched and
    mixed under the narration; the whole mix is then normalised to TARGET_LUFS with
    a TRUE_PEAK ceiling (gain only, no compression of the speech).
    """
    beds = beds or {}
    total = sum(float(s["duration"]) for s in segments)
    inputs, chains = [], []
    if scene_audio or beds:
        for i, seg in enumerate(segments):
            duration = float(seg["duration"])
            k = inputs.count("-i")  # FFmpeg input index of the next input
            if i in scene_audio:
                check_narration_fits(i, scene_audio[i], duration)
                inputs += ["-i", scene_audio[i]]
                chains.append(f"[{k}:a]{AUDIO_FORMAT},apad=whole_dur={duration}[v{i}]")
            else:
                inputs += ["-f", "lavfi", "-t", duration, "-i", "anullsrc=r=48000:cl=stereo"]
                chains.append(f"[{k}:a]{AUDIO_FORMAT}[v{i}]")
            if i in beds:
                src, start, lufs = beds[i]
                measured, _ = loudness(["-ss", start, "-t", duration, "-i", src], cwd)
                if measured <= -69.5:  # ebur128 reports its absolute gate (-70 LUFS) for silence
                    raise ValueError(f"Scene {i}: field audio requested but the source window is silent")
                gain = min(lufs - measured, 15.0)
                k = inputs.count("-i")
                inputs += ["-ss", start, "-t", duration, "-i", src]
                # Limiter keeps transients (e.g. a vent explosion) from dominating the mix.
                chains.append(f"[{k}:a]{AUDIO_FORMAT},volume={gain:.2f}dB,alimiter=limit=0.25:level=false,"
                              f"afade=t=in:d={FADE},"
                              f"afade=t=out:st={duration - FADE:.3f}:d={FADE},apad=whole_dur={duration}[b{i}]")
                chains.append(f"[v{i}][b{i}]amix=inputs=2:normalize=0:duration=first[a{i}]")
            else:
                chains.append(f"[v{i}]anull[a{i}]")
        chains.append("".join(f"[a{i}]" for i in range(len(segments)))
                      + f"concat=n={len(segments)}:v=0:a=1[a]")
    else:
        intro = float(segments[0]["duration"])
        speech = probe_length(recorded)
        if speech > total - intro:
            raise ValueError(f"Recorded narration is {speech:.2f}s, but only {total - intro:.2f}s fit "
                             "after the intro. Shorten it; NEVER trim speech.")
        inputs += ["-i", recorded]
        chains.append(f"[0:a]{AUDIO_FORMAT},adelay={round(intro * 1000)}:all=1,apad=whole_dur={total}[a]")
    out_label = "[a]"
    if music:
        # Original score under everything; the voice ducks it (sidechain) so speech stays clear.
        src, lufs = music
        measured, _ = loudness(["-i", src], cwd)
        k = inputs.count("-i")
        inputs += ["-i", src]
        chains[-1] = chains[-1][:-len("[a]")] + "[dry]"
        chains += ["[dry]asplit=2[mixin][key]",
                   f"[{k}:a]{AUDIO_FORMAT},volume={lufs - measured:.2f}dB,apad=whole_dur={total},"
                   f"atrim=end={total}[score]",
                   "[score][key]sidechaincompress=threshold=0.02:ratio=6:attack=30:release=600[ducked]",
                   "[mixin][ducked]amix=inputs=2:normalize=0:duration=first[a]"]
    mix = Path(target).with_suffix(".mix.wav")
    run_ffmpeg([*inputs, "-filter_complex", ";".join(chains), "-map", out_label, "-c:a", "pcm_s16le",
                "-ar", "48000", mix], cwd=cwd)
    level, peak = loudness(["-i", mix], cwd)
    gain = min(TARGET_LUFS - level, TRUE_PEAK - peak) if level > -69.5 else 0.0
    run_ffmpeg(["-i", mix, "-af", f"volume={gain:.2f}dB", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                target], cwd=cwd)
    produced = probe_length(target)
    if produced < total - 0.05:
        raise ValueError(f"Audio track is {produced:.2f}s, expected {total:.2f}s")
    return target


def voice_disclosure(group, mode):
    if not group.get("_synthetic_voice"):
        return None
    text = labels(group)["synthetic_voice"]
    provider = {"edge_tts": "Edge TTS", "elevenlabs_tts": "ElevenLabs"}.get(mode)
    return text + (" · " + provider if provider else "")


def render_film(root, group, synthetic_voice, audio_mode, no_subtitles=False, watermark=None,
                final_name=FINAL_NAME):
    """Render the whole film from root/{timeline,narration,assets}.json. Callers do the gating."""
    global FONT_PATH
    root = Path(root)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("Install ffmpeg and ffprobe first")
    FONT_PATH = FONT_PATH or next((p for p in FONTS if Path(p).exists()), None)
    if not FONT_PATH:
        raise SystemExit("Unicode bold font missing. Install DejaVu Sans.")
    assets_dir, out_dir = root / "assets", root / "output"
    tmp_dir = out_dir / "segments"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((root / "timeline.json").read_text(encoding="utf-8"))
    segments = timeline["segments"]
    asset_index = {x["id"]: x for x in json.loads((root / "assets.json").read_text(encoding="utf-8"))["assets"]}
    scene_indices = [s["index"] for s in json.loads((root / "narration.json").read_text(encoding="utf-8"))["segments"]]
    scene_audio = {i: assets_dir / "audio" / f"{i:02d}.mp3" for i in scene_indices}
    scene_mode = all(p.is_file() for p in scene_audio.values())
    recorded = None
    if not scene_mode:
        recorded = recorded_voice_path(root, group)
        print("RECORDED VOICE:", recorded.relative_to(root).as_posix(), "starts right AFTER the intro.")
        scene_audio = {}
    group = dict(group, _synthetic_voice=synthetic_voice is True)
    disclosure = voice_disclosure(group, audio_mode)
    narrated = set(scene_indices)
    cues = {}
    if scene_mode and not no_subtitles:
        cues = scene_cues(root)
        generate_subtitles(root)  # output/captions.srt sidecar for review / platform captions
        print("Subtitle cues use original TTS word timings; review punctuation and names before release.")
    elif not scene_mode and not no_subtitles:
        print("RECORDED VOICE: no TTS timing available. Skipping automatic subtitles.")
        print("Add manually aligned captions in Descript; NEVER invent timestamps.")
    if timeline.get("style") == "editorial":
        import editorial  # TikTok-safe typography, multi-shot scenes, labelled media
        render = editorial.render_scene
    else:
        render = render_video
    visuals = [render(i, seg, asset_index, group, assets_dir, tmp_dir, cues.get(i, ()),
                      disclosure if i in narrated else None, watermark)
               for i, seg in enumerate(segments)]
    concat = tmp_dir / "concat.txt"
    concat.write_text("".join(concat_line(p) for p in visuals), encoding="utf-8")
    music = None
    if timeline.get("music"):
        music = (root / timeline["music"]["file"], float(timeline["music"]["lufs"]))
    audio = build_audio(segments, scene_audio, recorded, tmp_dir / "narration.m4a", cwd=root,
                        beds=bed_windows(segments, asset_index, assets_dir), music=music)
    final = out_dir / final_name
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
                "-c", "copy", "-movflags", "+faststart", final], cwd=root)
    expected = sum(frames_for(s["duration"]) for s in segments)
    if count_frames(final) != expected:
        raise ValueError(f"Final video has {count_frames(final)} frames, expected {expected}")
    return final


def build_draft(root=ROOT, no_subtitles=False):
    """Strict build: every human approval and signature must verify first."""
    root = Path(root)
    failures = validate(strict=True, root=root)
    if failures:
        for issue in failures:
            print("STOP:", issue)
        raise SystemExit(1)
    before = snapshot(root)
    group = json.loads((root / "group.json").read_text(encoding="utf-8"))
    review = json.loads((root / "review.json").read_text(encoding="utf-8"))
    final = render_film(root, group, review["audio"]["synthetic_voice"], review["audio"].get("mode"),
                        no_subtitles)
    receipt = write_build_receipt(root, final, before=before, font_path=FONT_PATH)
    print("BUILD RECEIPT:", receipt.relative_to(root).as_posix())
    print("CREATED DRAFT:", final.relative_to(root).as_posix())
    print("NEXT: python qa.py; visually audit logos, dates, captions, licensing and TTS pronunciation.")
    return final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-subtitles", action="store_true",
                        help="Skip word-synchronized TTS captions (manually align subtitles for real voiceover)")
    args = parser.parse_args()
    build_draft(ROOT, no_subtitles=args.no_subtitles)


if __name__ == "__main__":
    main()
