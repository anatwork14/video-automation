#!/usr/bin/env python3
"""Produce GE1013 DRAFT video from ONLY human-approved authentic USGS footage.

Input: group.json, review.json, approved USGS MP4s, logo and per-scene TTS
or legacy voiceover.wav. Output is not published or scientifically approved.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from subtitles import generate as generate_subtitles
from validate import validate

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "output"
TMP = OUT / "segments"
W, H, FPS = 1080, 1920, 30
FONT_PATH = None  # Resolved by main(); defined for test patching.
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def run_ffmpeg(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *[str(x) for x in args]],
                   cwd=ROOT, check=True)


def probe_length(path):
    proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                          capture_output=True, text=True, check=True)
    return float(proc.stdout.strip())


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


def make_card(file, seg, intro, group):
    image = Image.new("RGB", (W, H), "#081b2d")
    d = ImageDraw.Draw(image)
    if intro:
        logo = Image.open(ASSETS / "logos_from_assignment.png").convert("RGB")
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
        label = ("AUTHENTIC USGS FOOTAGE · NO AI-GENERATED IMAGES"
                 if group.get("language") == "en"
                 else "VIDEO THẬT: USGS · KHÔNG SỬ DỤNG HÌNH AI")
        d.text((W // 2, 1610), label,
               font=font(27), anchor="mm", fill="#c8e2f8")
        if group.get("_synthetic_voice"):
            disclosure = ("SYNTHETIC VOICE: EDGE TTS" if group.get("language") == "en"
                          else "GIỌNG ĐỌC TỔNG HỢP: EDGE TTS")
            d.text((W // 2, 1710), disclosure,
                   font=font(28), anchor="mm", fill="#ffe3a1")
    image.save(file)


def make_overlay(file, seg, media):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((22, 85, 1058, 235), radius=24, fill=(0, 0, 0, 202))
    d.text((46, 105), seg["heading"], font=font(32), fill="white")
    d.text((46, 165), seg["caption"], font=font(27), fill="#f4eacf")
    d.rectangle((0, 1842, W, H), fill=(0, 0, 0, 195))
    for k, line in enumerate(wrap(media["agency_credit"], 66)):
        d.text((W // 2, 1852 + 27*k), line, anchor="mt", font=font(22), fill="white")
    image.save(file)


def render_video(index, seg, asset_index, group):
    duration = float(seg["duration"])
    base = TMP / f"{index:02d}_visual.mp4"
    if seg["kind"] in ("intro", "outro"):
        still = TMP / f"{index:02d}_card.png"
        make_card(still, seg, seg["kind"] == "intro", group)
        run_ffmpeg(["-loop", "1", "-framerate", FPS, "-i", still, "-t", duration,
                    "-vf", "fps=30,format=yuv420p", "-an", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "21", base])
        return base
    media = asset_index[seg["asset_id"]]
    src = ASSETS / media["filename"]
    start = float(seg.get("start_seconds", 0))
    available = probe_length(src) - start
    if available <= 0:
        raise ValueError(f"No usable source frames for {media['id']}")
    if available < duration:
        raise ValueError(
            f"Insufficient REAL footage for {media['id']}: only {available:.2f}s remaining, "
            f"scene requires {duration:.2f}s. Find another verified source or revise storyboard."
        )
    overlay = TMP / f"{index:02d}_overlay.png"
    make_overlay(overlay, seg, media)
    vf = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
          f"trim=duration={duration},"
          "setpts=PTS-STARTPTS[bg];[bg][1:v]overlay=0:0:format=auto,"
          "format=yuv420p[v]")
    run_ffmpeg(["-ss", start, "-i", src, "-loop", "1", "-i", overlay,
                "-filter_complex", vf, "-map", "[v]", "-an", "-t", duration,
                "-r", FPS, "-c:v", "libx264", "-preset", "medium", "-crf", "21", base])
    return base


def attach_audio(index, visual, duration, selected_audio):
    result = TMP / f"{index:02d}.mp4"
    audio = selected_audio.get(index)
    if audio:
        d = probe_length(audio)
        if d > duration + .05:
            raise ValueError(f"Scene {index}: narration {d:.1f}s exceeds {duration:.1f}s. "
                             "Shorten narration or extend segment; never silently trim speech.")
        run_ffmpeg(["-i", visual, "-i", audio, "-filter_complex",
                    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
                    f"apad,atrim=duration={duration}[a]",
                    "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2",
                    "-b:a", "160k", "-t", duration, result])
    else:
        run_ffmpeg(["-i", visual, "-f", "lavfi", "-t", duration,
                    "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v:0",
                    "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-t", duration, result])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-subtitles", action="store_true",
                        help="Skip word-synchronized TTS captions (manually align subtitles for real voiceover)")
    args = parser.parse_args()
    failures = validate(strict=True)
    if failures:
        for issue in failures:
            print("STOP:", issue)
        raise SystemExit(1)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("Install ffmpeg and ffprobe first")
    global FONT_PATH
    FONT_PATH = next((p for p in FONTS if Path(p).exists()), None)
    if not FONT_PATH:
        raise SystemExit("Unicode bold font missing. Install DejaVu Sans.")
    OUT.mkdir(exist_ok=True)
    TMP.mkdir(exist_ok=True)
    group = json.loads((ROOT / "group.json").read_text(encoding="utf-8"))
    timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    asset_index = {x["id"]: x for x in json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))["assets"]}
    scene_indices = [s["index"] for s in json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))["segments"]]
    scene_audio = {i: ASSETS / "audio" / f"{i:02d}.mp3" for i in scene_indices}
    scene_mode = all(p.is_file() for p in scene_audio.values())
    if not scene_mode:
        print("Using LEGACY global voiceover; assumes speech begins right AFTER intro (10s).")
        scene_audio = {}
    group["_synthetic_voice"] = scene_mode and all(
        (ASSETS / "audio" / f"{i:02d}.timings.json").is_file()
        for i in scene_indices
    )
    segments = []
    for index, seg in enumerate(timeline["segments"]):
        visual = render_video(index, seg, asset_index, group)
        segments.append(attach_audio(index, visual, float(seg["duration"]), scene_audio))
    concat = TMP / "concat.txt"
    concat.write_text("".join("file " + repr(str(p)) + "\n" for p in segments), encoding="utf-8")
    merged = OUT / "merged.mp4"
    if scene_mode:
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-map", "0:v:0",
                    "-map", "0:a:0", "-c", "copy", "-movflags", "+faststart", merged])
    else:
        legacy = ROOT / group.get("narration_audio_file", "assets/voiceover.wav")
        intro_duration = float(timeline["segments"][0]["duration"])
        allowable_duration = float(timeline["duration_seconds"]) - intro_duration
        actual_duration = probe_length(legacy)
        if actual_duration > allowable_duration + 0.05:
            raise ValueError(
                f"Legacy narration is {actual_duration:.2f}s, but only "
                f"{allowable_duration:.2f}s fit after intro. Shorten it; NEVER trim speech."
            )
        intro_ms = round(intro_duration * 1000)
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", concat, "-i", legacy,
                    "-filter_complex",
                    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,"
                    f"adelay={intro_ms}|{intro_ms},apad,"
                    f"atrim=duration={timeline['duration_seconds']}[a]",
                    "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-t",
                    timeline["duration_seconds"], "-movflags", "+faststart", merged])
    final = OUT / "GE1013_Kilauea_2018_DRAFT.mp4"
    if args.no_subtitles or not scene_mode:
        if not scene_mode and not args.no_subtitles:
            print("RECORDED VOICE: no TTS timing available. Skipping automatic subtitles.")
            print("Add manually aligned captions in Descript; NEVER invent timestamps.")
        shutil.copyfile(merged, final)
    else:
        captions = generate_subtitles()
        print("Subtitle cues use original TTS word timings; review punctuation and names before release.")
        # Run FFmpeg relative to ROOT, where the SRT path has no special punctuation.
        subpath = captions.relative_to(ROOT).as_posix()
        run_ffmpeg(["-i", merged, "-vf",
                    f"subtitles={subpath}:force_style='FontName=DejaVu Sans,FontSize=14,"
                    "BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=32'",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                    "-c:a", "copy", "-movflags", "+faststart", final])
    from build_provenance import write_build_receipt
    receipt = write_build_receipt(ROOT, final)
    print("BUILD RECEIPT:", receipt)
    print("CREATED DRAFT:", final)
    print("NEXT: python qa.py; visually audit logos, dates, captions, licensing and TTS pronunciation.")


if __name__ == "__main__":
    main()
