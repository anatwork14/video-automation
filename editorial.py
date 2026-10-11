"""Editorial (TikTok-safe) renderer: Barlow Condensed + Manrope, multi-shot scenes, labelled media.

Used by build.render_film when timeline.json has "style": "editorial". The classic
renderer in build.py is untouched, so earlier videos stay reproducible.

Layout keeps every text element inside the mobile safe area (TikTok covers roughly
the top 140 px, the bottom 420 px and a 120 px strip on the right with its UI):
  kicker + heading + caption box ... y 150..<=520
  per-shot identification tag (TYPE · place · date) directly under the box
  footage (fit, never cropped unless an approved `crop` says so; blurred same-shot fill)
  subtitles ......................... y 1240..1440 (two lines max)
  credit line ....................... y ~1462 (bottom of the safe area)
Every shot names what it is: REAL FOOTAGE / PHOTO / SATELLITE OBSERVATION /
HISTORICAL ILLUSTRATION / MODEL ANIMATION / DIAGRAM, plus place, date and credit.
Text is shrunk to fit and NEVER truncated (too long -> the build stops).
"""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import build

ROOT = Path(__file__).resolve().parent
HEAD_FONT = ROOT / "fonts" / "BarlowCondensed-Bold.ttf"
BODY_FONT = ROOT / "fonts" / "Manrope[wght].ttf"
W, H = build.W, build.H
SAFE_L, SAFE_R = 60, 960
SAFE_W = SAFE_R - SAFE_L
BOX_TOP, BOX_MAX = 150, 520
SUB_TOP, SUB_BOTTOM = 1240, 1440
CREDIT_Y = 1462
WATERMARK_Y = 100
ACCENT, INK, PAPER = "#FFB547", "#101418", "#F2EEE3"
STILL_SUFFIXES = (".png", ".jpg", ".jpeg")
MEDIA_LABELS = {
    "real_video": "REAL FOOTAGE", "photo": "PHOTO", "satellite_observation": "SATELLITE OBSERVATION",
    "historical_illustration": "HISTORICAL ILLUSTRATION", "model_animation": "MODEL ANIMATION",
    "diagram": "DIAGRAM",
}


@lru_cache(maxsize=None)
def head(size):
    return ImageFont.truetype(str(HEAD_FONT), size)


@lru_cache(maxsize=None)
def body(size, weight=700):
    face = ImageFont.truetype(str(BODY_FONT), size)
    face.set_variation_by_axes([weight])
    return face


def body_text(text):
    """Manrope has no ʻokina (U+02BB); the visually identical ‘ (U+2018) is used in body text."""
    return str(text).replace("ʻ", "‘")


def wrap_px(text, face, width):
    lines, line = [], ""
    for token in str(text).split():
        candidate = (line + " " + token).strip()
        if line and face.getlength(candidate) > width:
            lines.append(line)
            line = token
        else:
            line = candidate
    return lines + ([line] if line else [])


def fit(text, make_face, size, min_size, width, max_lines, what):
    for current in range(size, min_size - 1, -2):
        face = make_face(current)
        lines = wrap_px(text, face, width)
        if len(lines) <= max_lines and all(face.getlength(x) <= width for x in lines):
            return face, current, lines
    raise ValueError(f"{what} is too long for the safe area: {text!r}. Shorten it (and re-approve).")


def balanced(lines, face, width):
    if len(lines) != 2:
        return lines
    words = " ".join(lines).split()
    pairs = [(" ".join(words[:k]), " ".join(words[k:])) for k in range(1, len(words))]
    ok = [p for p in pairs if max(face.getlength(x) for x in p) <= width]
    return list(min(ok, key=lambda p: max(face.getlength(x) for x in p))) if ok else lines


def is_still(media):
    return Path(media["filename"]).suffix.lower() in STILL_SUFFIXES


def shot_tag(media, shot):
    kind = MEDIA_LABELS.get(media.get("type"), "FOOTAGE")
    return f"{kind} · {shot['label']}" if shot.get("label") else kind


# ----------------------------------------------------------------------------- overlays
def draw_box(d, seg):
    """Kicker, heading (Barlow Condensed) and caption (Manrope) on a translucent panel."""
    y = BOX_TOP + 26
    parts = []
    if seg.get("kicker"):
        face, size, lines = fit(body_text(seg["kicker"]).upper(), lambda s: body(s, 800), 26, 20, SAFE_W - 56, 1, "Kicker")
        parts.append((face, lines, ACCENT, round(size * 1.5)))
    face, size, lines = fit(seg["heading"].upper(), head, 74, 48, SAFE_W - 56, 2, "Heading")
    parts.append((face, lines, "white", round(size * 1.02)))
    if seg.get("caption"):
        face, size, lines = fit(body_text(seg["caption"]), lambda s: body(s, 600), 30, 22, SAFE_W - 56, 2, "Caption")
        parts.append((face, lines, PAPER, round(size * 1.35)))
    bottom = y + sum(len(lines) * step for _, lines, _, step in parts) + 22
    if bottom > BOX_MAX:
        raise ValueError(f"Heading box would cover the footage: {seg['heading']!r}")
    d.rounded_rectangle((SAFE_L, BOX_TOP, SAFE_R, bottom), radius=28, fill=(10, 12, 16, 178))
    for face, lines, colour, step in parts:
        for line in lines:
            d.text((SAFE_L + 28, y), line, font=face, fill=colour)
            y += step
    return (SAFE_L, BOX_TOP, SAFE_R, bottom)


def draw_tag(d, text, y):
    face, size, lines = fit(body_text(text).upper(), lambda s: body(s, 800), 22, 16, SAFE_W - 40, 1, "Shot tag")
    width = face.getlength(lines[0])
    box = (SAFE_L, y, round(SAFE_L + width + 32), y + size + 20)
    d.rounded_rectangle(box, radius=(size + 20) // 2, fill=ACCENT)
    d.text((SAFE_L + 16, y + 9), lines[0], font=face, fill=INK)
    return box


def draw_credit(d, text):
    face, size, lines = fit(body_text(text), lambda s: body(s, 600), 24, 16, SAFE_W - 4, 1, "Credit")
    d.text((SAFE_L + 2, CREDIT_Y), lines[0], font=face, fill=(255, 255, 255, 230), stroke_width=2,
           stroke_fill=(0, 0, 0, 200))
    return d.textbbox((SAFE_L + 2, CREDIT_Y), lines[0], font=face, stroke_width=2)


def draw_watermark(d, text):
    face, _, lines = fit(text, lambda s: body(s, 800), 22, 16, SAFE_W, 1, "Watermark")
    width = face.getlength(lines[0])
    box = (round(W / 2 - width / 2 - 18), WATERMARK_Y - 20, round(W / 2 + width / 2 + 18), WATERMARK_Y + 20)
    d.rounded_rectangle(box, radius=20, fill=(150, 20, 20, 215))
    d.text((W // 2, WATERMARK_Y), lines[0], font=face, anchor="mm", fill="white")
    return box


def subtitle_image(text):
    stroke = 6
    width = SAFE_W - 2 * stroke  # the outline is drawn outside the glyphs: keep it inside the safe area
    face, size, lines = fit(body_text(text), lambda s: body(s, 800), 50, 36, width, 2, "Subtitle cue")
    lines = balanced(lines, face, width)
    image = Image.new("RGBA", (W, SUB_BOTTOM - SUB_TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    step = round(size * 1.24)
    y = image.height - 6 - step * len(lines)
    for line in lines:
        d.text((SAFE_L + SAFE_W // 2, y), line, font=face, anchor="mt", fill="white", stroke_width=stroke,
               stroke_fill="black")
        y += step
    box = image.getbbox() or (0, 0, 0, 0)
    return image, (box[0], SUB_TOP + box[1], box[2], SUB_TOP + box[3])


def shot_overlay(file, seg, media, shot, credit_suffix="", watermark=None):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    box = draw_box(d, seg)
    boxes = [box, draw_tag(d, shot_tag(media, shot), box[3] + 16),
             draw_credit(d, "Credit: " + media["agency_credit"] + credit_suffix)]
    if watermark:
        boxes.append(draw_watermark(d, watermark))
    image.save(file)
    return boxes


def card_overlay(file, seg, group, assets_dir, media=None, shot=None, credit_suffix="", watermark=None):
    """hook / title / credits cards drawn over dimmed real footage (or a dark panel)."""
    layout = seg.get("layout", "title" if seg["kind"] == "intro" else "credits")
    image = Image.new("RGBA", (W, H), (6, 10, 16, 110 if media else 255))
    d = ImageDraw.Draw(image)
    boxes = []
    if layout == "hook":
        y = 560
        for k, line in enumerate(seg["hook_lines"]):
            face, size, lines = fit(line.upper(), head, 150, 80, SAFE_W, 1, "Hook line")
            d.text((SAFE_L, y), lines[0], font=face, fill=ACCENT if k == len(seg["hook_lines"]) - 1 else "white",
                   stroke_width=3, stroke_fill=(0, 0, 0, 160))
            y += round(size * 1.0)
        if y > SUB_TOP - 20:
            raise ValueError("Hook text runs into the subtitle band")
    elif layout == "title":
        logo = assets_dir / "logos_from_assignment.png"
        if logo.is_file():
            mark = Image.open(logo).convert("RGBA")
            mark.thumbnail((640, 220), Image.Resampling.LANCZOS)
            image.alpha_composite(mark, ((W - mark.width) // 2, 150))
        else:
            d.rounded_rectangle((SAFE_L, 150, SAFE_R, 330), radius=18, outline=ACCENT, width=3)
            d.text((W // 2, 240), "[School / course / sponsor logos]", font=body(28), anchor="mm", fill=ACCENT)
        y = 400
        for text, make, size, low, lines_max, colour, step in (
                (seg["heading"].upper(), head, 104, 64, 2, "white", 0.98),
                (body_text(seg.get("caption", "")), lambda s: body(s, 600), 36, 26, 2, PAPER, 1.3),
                (body_text(group["course"]), lambda s: body(s, 700), 32, 24, 1, PAPER, 1.4),
                (build.labels(group)["team"] + str(group["group_number"]), lambda s: body(s, 800), 40, 28, 1, ACCENT, 1.4)):
            if not text:
                continue
            face, sz, lines = fit(text, make, size, low, SAFE_W, lines_max, "Title card text")
            for line in balanced(lines, face, SAFE_W):
                d.text((W // 2, y), line, font=face, anchor="mt", fill=colour)
                y += round(sz * step)
            y += 14
        for member in group["team_members"]:
            face, sz, lines = fit(body_text(f"{member['name']} · {member['student_id']}"),
                                  lambda s: body(s, 600), 30, 22, SAFE_W, 1, "Member line")
            d.text((W // 2, y), lines[0], font=face, anchor="mt", fill="white")
            y += round(sz * 1.45)
        if y > SUB_TOP - 10:
            raise ValueError("Title card runs into the subtitle band")
    else:  # credits
        face, size, lines = fit(seg["heading"].upper(), head, 84, 54, SAFE_W, 2, "Credits heading")
        y = 170
        for line in lines:
            d.text((SAFE_L, y), line, font=face, fill="white")
            y += round(size * 1.0)
        y += 20
        for entry in seg.get("credits", []):
            face, sz, lines = fit(body_text(entry), lambda s: body(s, 600), 27, 19, SAFE_W, 3, "Credit entry")
            for line in lines:
                d.text((SAFE_L, y), line, font=face, fill=PAPER)
                y += round(sz * 1.32)
            y += 8
        if y > SUB_TOP - 10:
            raise ValueError("Credits run into the subtitle band; shorten the list")
    if media:
        y_tag = SUB_TOP - 60 if layout != "hook" else 470
        boxes.append(draw_tag(d, shot_tag(media, shot or {}), y_tag))
        boxes.append(draw_credit(d, "Credit: " + media["agency_credit"] + credit_suffix))
    if watermark:
        boxes.append(draw_watermark(d, watermark))
    image.save(file)
    return boxes


# ----------------------------------------------------------------------------- rendering
def shots_of(seg):
    if seg.get("shots"):
        return seg["shots"]
    if seg.get("kind") == "video":
        return [dict(seg, duration=seg["duration"])]
    if seg.get("background"):
        return [dict(seg["background"], duration=seg["duration"])]
    return []


def picture_graph(media, shot, src, frames, cover):
    """Filter chain producing [bg] (exactly `frames` frames) for one real video/still."""
    if is_still(media):
        # Slow push-in on a genuine still; the whole picture stays visible (fit + blurred same-image fill).
        zoom = f"zoompan=z='1+0.05*on/{max(frames - 1, 1)}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={build.FPS}"
        head_chain = f"[0:v]{build.crop_filter(shot, src)}format=rgb24,setsar=1"
    else:
        zoom = None
        head_chain = (f"[0:v]{build.crop_filter(shot, src)}fps={build.FPS},trim=end_frame={frames},"
                      "setpts=PTS-STARTPTS")
    darken = ",eq=brightness=-0.16:saturation=0.9" if cover else ""
    if cover:
        chain = [f"{head_chain},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}{darken}[pic]"]
    else:
        chain = [f"{head_chain},split[full][back]",
                 f"[back]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 "gblur=sigma=28,eq=brightness=-0.24:saturation=0.8[blurred]",
                 f"[full]scale={W}:{H}:force_original_aspect_ratio=decrease[fit]",
                 "[blurred][fit]overlay=(W-w)/2:(H-h)/2[pic]"]
    if zoom:
        chain.append(f"[pic]{zoom},trim=end_frame={frames},setpts=PTS-STARTPTS,setsar=1[bg]")
    else:
        chain.append("[pic]setsar=1[bg]")
    return ";".join(chain)


def cue_chain(prefix, cues, tmp_dir, first_input, label):
    inputs, chain = [], []
    for k, (start, end, text) in enumerate(cues):
        png = tmp_dir / f"{prefix}_cue{k:02d}.png"
        subtitle_image(text)[0].save(png)
        inputs += ["-loop", "1", "-i", png]
        chain.append(f"[{label}{k}][{first_input + k}:v]overlay=0:{SUB_TOP}:shortest=1:format=auto:"
                     f"enable='between(t,{start:.3f},{end:.3f})'[{label}{k + 1}]")
    return inputs, chain, f"{label}{len(cues)}"


def render_scene(index, seg, asset_index, group, assets_dir, tmp_dir, cues=(), disclosure=None, watermark=None):
    duration = float(seg["duration"])
    shots = shots_of(seg)
    credit_suffix = " · Voice: synthetic (Edge TTS)" if disclosure else ""
    parts, offset = [], 0.0
    if not shots:  # pure card (no footage)
        shots = [{"duration": duration}]
    for k, shot in enumerate(shots):
        length = float(shot["duration"])
        frames = build.frames_for(length)
        prefix = f"{index:02d}_{k:02d}"
        media = asset_index.get(shot.get("asset_id")) if shot.get("asset_id") else None
        overlay = tmp_dir / f"{prefix}_overlay.png"
        if seg["kind"] == "video":
            shot_overlay(overlay, seg, media, shot, credit_suffix, watermark)
        else:
            card_overlay(overlay, seg, group, assets_dir, media, shot, credit_suffix, watermark)
        local = [(max(0.0, s - offset), min(length, e - offset), t) for s, e, t in cues
                 if e > offset and s < offset + length]
        if media:
            src = assets_dir / media["filename"]
            if is_still(media):
                inputs = ["-loop", "1", "-framerate", build.FPS, "-i", src]
            else:
                _, src, start = build.source_window(asset_index, assets_dir, shot, length)
                inputs = ["-ss", start, "-i", src]
            graph = picture_graph(media, shot, src, frames, cover=seg["kind"] != "video")
        else:
            inputs = ["-f", "lavfi", "-i", f"color=c=0x0a1018:s={W}x{H}:r={build.FPS}"]
            graph = f"[0:v]trim=end_frame={frames},setpts=PTS-STARTPTS,setsar=1[bg]"
        extra, chain, last = cue_chain(prefix, local, tmp_dir, 2, "s")
        fade = []
        if k == 0:
            fade.append(f"fade=t=in:st=0:d={build.FADE}")
        if k == len(shots) - 1:
            fade.append(f"fade=t=out:st={length - build.FADE:.3f}:d={build.FADE}")
        tail = ",".join(fade + ["format=yuv420p"])
        full = ";".join([graph, "[bg][1:v]overlay=0:0:shortest=1:format=auto[s0]", *chain, f"[{last}]{tail}[v]"])
        out = tmp_dir / f"{prefix}_shot.mp4"
        build.run_ffmpeg([*inputs, "-loop", "1", "-i", overlay, *extra, "-filter_complex", full,
                          "-map", "[v]", "-an", "-frames:v", frames, *build.VIDEO_ARGS, out])
        if build.count_frames(out) != frames:
            raise ValueError(f"Scene {index} shot {k}: wrong frame count; refusing to pad or freeze")
        parts.append(out)
        offset += length
    base = tmp_dir / f"{index:02d}_visual.mp4"
    if len(parts) == 1:
        parts[0].replace(base)
    else:
        listing = tmp_dir / f"{index:02d}_shots.txt"
        listing.write_text("".join(build.concat_line(p) for p in parts), encoding="utf-8")
        build.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", base])
    if build.count_frames(base) != build.frames_for(duration):
        raise ValueError(f"Scene {index}: shots do not add up to {duration}s")
    return base
