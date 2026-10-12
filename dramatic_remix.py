#!/usr/bin/env python3
"""Create an unapproved dramatic music edition from an existing documentary draft.

Reuses the exact encoded visual stream and original synchronized speech. All
music is deterministic oscillator synthesis, not purported field sound.
"""
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import build
import music
from qa import technical_problems, volume
from review_gate import audio_evidence, sha256_file
from validate import validate

REPO = Path(__file__).resolve().parent
NAME = "GE1013_Volcano_Hazards_DRAMATIC_DRAFT"


def score(durations, target):
    inputs, filters = [], []
    for i, (duration, (chord, level, pulse)) in enumerate(zip(durations, music.SCENES_9)):
        notes = [music.NOTE[n] for n in chord]
        seconds = duration + (2 if i < len(durations) - 1 else 0)
        channels = []
        for detune in (1.0, 1.003):
            base = music.pad(notes, level, 0, detune)
            # Soft upper harmonics suggest bowed strings; a low rhythmic tone is music.
            strings = '+'.join(f'(sin(2*PI*{f*2*detune:.4f}*t)+0.22*sin(2*PI*{f*4*detune:.4f}*t))'
                               for f in notes)
            ostinato = (f'0.055*sin(2*PI*{notes[0]*2*detune:.4f}*t)'
                        '*(1-exp(-100*mod(t,0.5)))*exp(-8*mod(t,0.5))')
            bass = f'0.07*sin(2*PI*{notes[0]*0.5*detune:.4f}*t)'
            rhythm = (f'{0.025+0.08*pulse:.4f}*sin(2*PI*55*t)'
                      '*(1-exp(-120*mod(t,1.0)))*exp(-8*mod(t,1.0))')
            channels.append(f'{base}+0.025*({strings})+{bass}+{ostinato}+{rhythm}')
        inputs += ['-f', 'lavfi', '-i', f"aevalsrc='{'|'.join(channels)}':s=48000:d={seconds}"]
    last = '[0:a]'
    for i in range(1, len(durations)):
        filters.append(f'{last}[{i}:a]acrossfade=d=2:c1=qsin:c2=qsin[x{i}]')
        last = f'[x{i}]'
    total = sum(durations)
    filters.append(f'{last}highpass=f=35,lowpass=f=5000,aecho=0.8:0.6:120|240:0.15|0.1,'
                   f'afade=t=in:d=1.2,afade=t=out:st={total-4}:d=4,atrim=end={total}[m]')
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *inputs, '-filter_complex',
                    ';'.join(filters), '-map', '[m]', '-c:a', 'pcm_s16le', str(target)], check=True)


def prepare(source, destination):
    if destination.exists():
        raise ValueError('Destination already exists; choose a new --root to preserve previous editions')
    destination.mkdir(parents=True)
    for name in ('assets.json', 'claims.json', 'narration.json', 'group.json'):
        shutil.copyfile(source / name, destination / name)
    assets = destination / 'assets'
    assets.mkdir()
    for original in (source / 'assets').iterdir():
        if original.name == 'music':
            continue
        if original.name == 'audio':
            shutil.copytree(original, assets / original.name)
        else:
            os.symlink(original.resolve(), assets / original.name)
    timeline = json.loads((source / 'timeline.json').read_text())
    timeline['music'] = {'file': 'assets/music/score.wav', 'lufs': -22}
    timeline['edition_note'] = ('UNAPPROVED dramatic music edition: identical documentary visuals, '
                                'speech, captions and claim wording; fuller original score at -22 LUFS before ducking')
    (destination / 'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+'\n')
    return timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=REPO / 'variants/volcano_hazards')
    parser.add_argument('--source-video', type=Path,
                        default=REPO / 'output/GE1013_Volcanoes_Turn_Deadly_DRAFT.mp4')
    parser.add_argument('--root', type=Path, default=REPO / 'variants/volcano_hazards_dramatic')
    args = parser.parse_args()
    source, root, video = args.source.resolve(), args.root.resolve(), args.source_video.resolve()
    # Check the source draft's own receipt before reusing its encoded captions/visuals.
    from review_gate import sha256_object
    receipt = json.loads(video.with_suffix('.manifest.json').read_text())
    narration = json.loads((source / 'narration.json').read_text())
    source_timeline = json.loads((source / 'timeline.json').read_text())
    group = json.loads((source / 'group.json').read_text())
    evidence, errors = audio_evidence(source, narration, group)
    if (errors or not evidence or receipt['video_sha256'] != sha256_file(video)
            or receipt['timeline_sha256'] != sha256_object(source_timeline)
            or receipt['narration_sha256'] != sha256_object(narration)
            or receipt['audio_digest'] != evidence['sha256']):
        raise ValueError('Source draft is stale or its audio does not match the current narration')
    timeline = prepare(source, root)
    problems = validate(strict=False, root=root)
    if problems:
        raise ValueError(problems)
    segments = timeline['segments']
    music_file = root / timeline['music']['file']
    score([float(s['duration']) for s in segments], music_file)
    out = REPO / 'output'
    scratch = root / 'output'
    scratch.mkdir()
    speech = {s['index']: root / 'assets/audio' / f"{s['index']:02d}.mp3" for s in narration['segments']}
    audio = build.build_audio(segments, speech, None, scratch / 'dramatic_mix.m4a', cwd=root,
                              music=(music_file, -22))
    target = out / f'{NAME}.mp4'
    if target.exists():
        raise ValueError('Output exists; preserve it before running another remix')
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(video), '-i', str(audio),
                    '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-movflags', '+faststart', str(target)], check=True)
    problems = technical_problems(root, target)
    inputs = [root / n for n in ('assets.json','claims.json','narration.json','timeline.json')]
    inputs += list((root / 'assets/audio').glob('*')) + [music_file, video, Path(__file__), REPO / 'build.py']
    manifest = {'status': 'UNAPPROVED_REVIEW_DRAFT', 'created_utc': datetime.now(timezone.utc).isoformat(),
                'video_sha256': sha256_file(target), 'source_mp4_sha256': sha256_file(video),
                'inputs': {str(p.relative_to(REPO)): sha256_file(p) for p in inputs if p.is_file()},
                'music_target_lufs_before_ducking': -22, 'previous_music_target_lufs': -28,
                'audio_provider': 'edge-tts', 'technical_qa_problems': problems, 'audio_levels': volume(target),
                'human_listening_review': 'PENDING', 'human_approval': 'PENDING'}
    target.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shutil.copyfile(video.with_suffix('.srt'), target.with_suffix('.srt'))
    print('DRAMATIC DRAFT:', target, flush=True)
    print('TECHNICAL QA:', problems or 'PASS', flush=True)
    if problems:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
