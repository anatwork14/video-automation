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
              "-r", str(FPS), "-video_track_timescale", "30000"]
AUDIO_FORMAT = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
# Fixed, non-overlapping layout bands (pixels in the 1080x1920 frame).
MARGIN, TEXT_WIDTH = 22, 990
TOP_Y, TOP_MAX = 70, 380            # heading/caption box (16:9 footage starts at y=656)
SUB_TOP, SUB_BOTTOM = 1390, 1610    # subtitles: two lines max, below 16:9 footage (ends y=1264)
LABEL_Y = 1700                      # synthetic-voice disclosure pill
CARD_LABEL_Y = 1772                 # authentic-footage label on intro/outro cards
CREDIT_TOP = 1842                   # agency credit bar


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


def subtitle_image(text):
    """Transparent strip for the subtitle band; returns (image, bbox in frame coordinates)."""
    face, size, lines = fit_text(text, 56, 40, TEXT_WIDTH, 2, "Subtitle cue")
    image = Image.new("RGBA", (W, SUB_BOTTOM - SUB_TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    step = round(size * 1.22)
    y = image.height - 8 - step * len(lines)
    for line in lines:
        d.text((W // 2, y), line, font=face, anchor="mt", fill="white", stroke_width=5, stroke_fill="black")
        y += step
    box = image.getbbox() or (0, 0, 0, 0)
    return image, (box[0], SUB_TOP + box[1], box[2], SUB_TOP + box[3])


def make_card(file, seg, intro, group, assets_dir, disclosure=None):
    image = Image.new("RGB", (W, H), "#081b2d")
    d = ImageDraw.Draw(image, "RGBA")
    if intro:
        logo = Image.open(assets_dir / "logos_from_assignment.png").convert("RGB")
        logo.thumbnail((1000, 220), Image.Resampling.LANCZOS)
        image.paste(logo, ((W - logo.width) // 2, 160))
    else:
        d.text((W // 2, 250), "USGS · 2018", font=font(41), anchor="mm", fill="#add9f0")
    y = 525
    for line in wrap(seg["heading"], 17):
        d.text((W // 2, y), line, font=font(78), anchor="mm", fill="white")
        y += 108
    y += 50
    for line in wrap(seg["caption"], 34):
        d.text((W // 2, y), line, font=font(37), anchor="mm", fill="#cee5f7")
        y += 58
    boxes = []
    if intro:
        y = max(y + 90, 1110)
        team_label = "GROUP " if group.get("language") == "en" else "NHÓM "
        d.text((W // 2, y), team_label + str(group["group_number"]), font=font(54),
               anchor="mm", fill="#ffe3a1")
        y += 90
        for member in group["team_members"]:
            for line in wrap(f"{member['name']} — {member['student_id']}", 34):
                d.text((W // 2, y), line, font=font(31), anchor="mm", fill="white")
                y += 52
        d.text((W // 2, 1810), group["course"], font=font(38), anchor="mm", fill="#c8e2f8")
    else:
        if y > SUB_TOP:
            raise ValueError(f"Card text runs into the subtitle band: {seg['heading']!r}")
        label = ("AUTHENTIC USGS FOOTAGE · NO AI-GENERATED IMAGES"
                 if group.get("language") == "en"
                 else "VIDEO THẬT: USGS · KHÔNG SỬ DỤNG HÌNH AI")
        d.text((W // 2, CARD_LABEL_Y), label, font=font(27), anchor="mm", fill="#c8e2f8")
        boxes.append(d.textbbox((W // 2, CARD_LABEL_Y), label, font=font(27), anchor="mm"))
    if disclosure:
        boxes.append(draw_disclosure(d, disclosure))
    image.save(file)
    return boxes


def make_overlay(file, seg, media, disclosure=None):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    boxes = [draw_top_box(d, seg), draw_credit(d, media["agency_credit"])]
    if disclosure:
        boxes.append(draw_disclosure(d, disclosure))
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


def render_video(index, seg, asset_index, group, assets_dir, tmp_dir, cues=(), disclosure=None):
    duration = float(seg["duration"])
    frames = frames_for(duration)
    base = tmp_dir / f"{index:02d}_visual.mp4"
    if seg["kind"] in ("intro", "outro"):
        still = tmp_dir / f"{index:02d}_card.png"
        make_card(still, seg, seg["kind"] == "intro", group, assets_dir, disclosure)
        extra, chain, last = cue_overlays(index, cues, tmp_dir, 1, "c")
        graph = ";".join([f"[0:v]trim=end_frame={frames},setpts=PTS-STARTPTS[c0]", *chain,
                          f"[{last}]format=yuv420p[v]"])
        run_ffmpeg(["-loop", "1", "-framerate", FPS, "-i", still, *extra, "-filter_complex", graph,
                    "-map", "[v]", "-an", "-frames:v", frames, *VIDEO_ARGS, base])
    else:
        media = asset_index[seg["asset_id"]]
        src = assets_dir / media["filename"]
        start = float(seg.get("start_seconds", 0))
        available = probe_length(src) - start
        if available <= 0:
            raise ValueError(f"No usable source frames for {media['id']}")
        if available < duration:
            raise ValueError(
                f"Insufficient REAL footage for {media['id']}: only {available:.2f}s remaining, "
                f"scene requires {duration:.2f}s. Find another verified source or revise storyboard."
            )
        overlay = tmp_dir / f"{index:02d}_overlay.png"
        make_overlay(overlay, seg, media, disclosure)
        extra, chain, last = cue_overlays(index, cues, tmp_dir, 2, "s")
        graph = ";".join([
            f"[0:v]{crop_filter(seg, src)}fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"trim=end_frame={frames},setpts=PTS-STARTPTS[bg]",
            "[bg][1:v]overlay=0:0:shortest=1:format=auto[s0]", *chain, f"[{last}]format=yuv420p[v]"])
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


def build_audio(segments, scene_audio, recorded, target, cwd=ROOT):
    """One AAC encode for the whole film. Speech is padded with silence, never trimmed."""
    total = sum(float(s["duration"]) for s in segments)
    inputs, chains = [], []
    if scene_audio:
        for i, seg in enumerate(segments):
            duration = float(seg["duration"])
            k = inputs.count("-i")  # FFmpeg input index of the next input
            if i in scene_audio:
                check_narration_fits(i, scene_audio[i], duration)
                inputs += ["-i", scene_audio[i]]
                chains.append(f"[{k}:a]{AUDIO_FORMAT},apad=whole_dur={duration}[a{i}]")
            else:
                inputs += ["-f", "lavfi", "-t", duration, "-i", "anullsrc=r=48000:cl=stereo"]
                chains.append(f"[{k}:a]{AUDIO_FORMAT}[a{i}]")
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
    run_ffmpeg([*inputs, "-filter_complex", ";".join(chains), "-map", "[a]",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", target], cwd=cwd)
    produced = probe_length(target)
    if produced < total - 0.05:
        raise ValueError(f"Audio track is {produced:.2f}s, expected {total:.2f}s")
    return target


def voice_disclosure(group, mode):
    if not group.get("_synthetic_voice"):
        return None
    english = group.get("language") == "en"
    text = "Synthetic AI voice" if english else "Giọng đọc tổng hợp (AI)"
    return text + (" · Edge TTS" if mode == "edge_tts" else "")


def build_draft(root=ROOT, no_subtitles=False):
    global FONT_PATH
    root = Path(root)
    failures = validate(strict=True, root=root)
    if failures:
        for issue in failures:
            print("STOP:", issue)
        raise SystemExit(1)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("Install ffmpeg and ffprobe first")
    FONT_PATH = FONT_PATH or next((p for p in FONTS if Path(p).exists()), None)
    if not FONT_PATH:
        raise SystemExit("Unicode bold font missing. Install DejaVu Sans.")
    before = snapshot(root)
    assets_dir, out_dir = root / "assets", root / "output"
    tmp_dir = out_dir / "segments"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    group = json.loads((root / "group.json").read_text(encoding="utf-8"))
    review = json.loads((root / "review.json").read_text(encoding="utf-8"))
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
    group["_synthetic_voice"] = review["audio"]["synthetic_voice"] is True
    disclosure = voice_disclosure(group, review["audio"].get("mode"))
    narrated = set(scene_indices)
    cues = {}
    if scene_mode and not no_subtitles:
        cues = scene_cues(root)
        generate_subtitles(root)  # output/captions.srt sidecar for review / platform captions
        print("Subtitle cues use original TTS word timings; review punctuation and names before release.")
    elif not scene_mode and not no_subtitles:
        print("RECORDED VOICE: no TTS timing available. Skipping automatic subtitles.")
        print("Add manually aligned captions in Descript; NEVER invent timestamps.")
    visuals = [render_video(i, seg, asset_index, group, assets_dir, tmp_dir, cues.get(i, ()),
                            disclosure if i in narrated else None)
               for i, seg in enumerate(segments)]
    concat = tmp_dir / "concat.txt"
    concat.write_text("".join(concat_line(p) for p in visuals), encoding="utf-8")
    audio = build_audio(segments, scene_audio, recorded, tmp_dir / "narration.m4a", cwd=root)
    final = out_dir / FINAL_NAME
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
                "-c", "copy", "-movflags", "+faststart", final], cwd=root)
    expected = sum(frames_for(s["duration"]) for s in segments)
    if count_frames(final) != expected:
        raise ValueError(f"Final video has {count_frames(final)} frames, expected {expected}")
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
