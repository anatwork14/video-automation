#!/usr/bin/env python3
"""Synthesize an ORIGINAL background score for the film (no samples, no third-party music).

The score is generated from sine-wave pads with FFmpeg's aevalsrc, so it is the
project's own work and carries no licence obligations; it is deterministic (same
timeline -> same bytes). One chord per scene follows the story:
intro (quiet, rising) -> fissures -> rift -> ocean entry -> summit collapse
(dominant tension + heartbeat pulse) -> outro (resolves to the tonic, fades out).
It is NOT a sound effect of the volcano and must never be presented as field audio.

Output: assets/music/score.wav (48 kHz stereo). build.py mixes it under the
narration (ducked by the voice) when timeline.json has a "music" entry.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = "assets/music/score.wav"
CROSSFADE = 2.0

# Hz. D minor: Dm(add9) - Dm - Bb - Gm - A (dominant) - Dm
NOTE = {"G2": 98.00, "A2": 110.00, "Bb2": 116.54, "D3": 146.83, "E3": 164.81, "F3": 174.61,
        "G3": 196.00, "A3": 220.00, "Bb3": 233.08, "Cs4": 277.18, "D4": 293.66, "E4": 329.63, "F4": 349.23}
SCENES = [  # (chord, pad level, pulse level)
    (["D3", "A3", "E4", "F4"], 0.55, 0.0),
    (["D3", "A3", "F4"], 0.70, 0.0),
    (["Bb2", "F3", "D4"], 0.75, 0.0),
    (["G2", "D3", "Bb3"], 0.80, 0.35),
    (["A2", "E3", "Cs4"], 0.85, 0.55),
    (["D3", "A3", "D4", "F4"], 0.65, 0.0),
]


def pad(freqs, level, pulse, detune):
    """Soft pad: each note = fundamental + gentle octave/twelfth partials, slow tremolo."""
    parts = []
    for f in freqs:
        f = f * detune
        parts.append(f"(sin(2*PI*{f:.3f}*t)+0.35*sin(2*PI*{2 * f * 1.002:.3f}*t)"
                     f"+0.12*sin(2*PI*{3 * f:.3f}*t))")
    voices = "+".join(parts)
    body = f"{level / len(freqs) * 0.32:.4f}*({voices})*(0.85+0.15*sin(2*PI*0.11*t))"
    drone = f"0.05*sin(2*PI*{73.42 * detune:.3f}*t)"
    # heartbeat: 30 ms attack ramp so each beat starts without a click
    beat = (f"{pulse * 0.22:.3f}*sin(2*PI*52*t)*(1-exp(-120*mod(t,1.0)))*exp(-7*mod(t,1.0))"
            if pulse else "0")
    return f"{body}+{drone}+{beat}"


def build_score(durations, target):
    if len(durations) != len(SCENES):
        raise ValueError(f"Score is written for {len(SCENES)} scenes; timeline has {len(durations)}")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    inputs, labels = [], []
    for k, ((chord, level, pulse), duration) in enumerate(zip(SCENES, durations)):
        length = duration + (CROSSFADE if k < len(SCENES) - 1 else 0)
        freqs = [NOTE[n] for n in chord]
        expr = pad(freqs, level, pulse, 1.0) + "|" + pad(freqs, level, pulse, 1.003)
        inputs += ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={length:.3f}"]
        labels.append(f"[{k}:a]")
    chain, last = [], labels[0]
    for k in range(1, len(labels)):
        out = f"[x{k}]"
        chain.append(f"{last}{labels[k]}acrossfade=d={CROSSFADE}:c1=qsin:c2=qsin{out}")
        last = out
    total = sum(durations)
    chain.append(f"{last}afade=t=in:d=3,afade=t=out:st={total - 4:.3f}:d=4,"
                 "highpass=f=40,lowpass=f=4500,aecho=0.8:0.6:180|360:0.25|0.15,"
                 f"atrim=end={total:.3f}[m]")
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", *inputs,
                    "-filter_complex", ";".join(chain), "-map", "[m]", "-c:a", "pcm_s16le", str(target)],
                   check=True)
    return target


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    timeline_file = argv[0] if argv else "timeline.json"
    timeline = json.loads((ROOT / timeline_file).read_text(encoding="utf-8"))
    out = build_score([float(s["duration"]) for s in timeline["segments"]], ROOT / TARGET)
    print("Original synthesized score written:", out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
