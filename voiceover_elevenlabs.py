#!/usr/bin/env python3
"""Optional ElevenLabs free-account narration with real alignment timestamps.

Loads a local key without printing it. Checks the free tier and remaining quota
before generation; never upgrades a plan or enables billing. Existing audio is
preserved unless --force is explicit. Text is sent to ElevenLabs for synthesis.
"""
import argparse
import base64
import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from review_gate import sha256_file, text_sha256
from voiceover import probe_duration

REPO = Path(__file__).resolve().parent
API = 'https://api.elevenlabs.io/v1'


def credentials(path):
    values = dict(os.environ)
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.removeprefix('export ').split('=', 1)
            values.setdefault(key.strip(), value.strip().strip('\"\''))
    key = values.get('ELEVENLABS_API_KEY') or values.get('EVENLABS_API_KEY')
    if not key:
        raise ValueError('Set ELEVENLABS_API_KEY in the local .env file; never put keys in source code')
    return key, values.get('ELEVENLABS_VOICE_ID')


def request(key, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data,
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Never print response bodies, keys, or full request headers.
        raise ValueError(f'ElevenLabs HTTP {exc.code}; check key permissions, account quota and voice access') from None


def aligned_words(alignment, text):
    if not isinstance(alignment, dict):
        raise ValueError('ElevenLabs returned no original-text alignment; no estimated caption timing allowed')
    chars = alignment.get('characters', [])
    starts = alignment.get('character_start_times_seconds', [])
    ends = alignment.get('character_end_times_seconds', [])
    if ''.join(chars) != text or not len(chars) == len(starts) == len(ends):
        raise ValueError('Alignment does not match the exact narration text')
    if any(len(c) != 1 for c in chars):
        raise ValueError('Expected character-level alignment')
    for i, (start, end) in enumerate(zip(starts, ends)):
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start <= end):
            raise ValueError('Invalid character timestamps')
        if i and start < starts[i-1]:
            raise ValueError('Character timestamps are not ordered')
    words = []
    for match in re.finditer(r'\S+', text):
        start, end = starts[match.start()], ends[match.end()-1]
        if end <= start:
            raise ValueError('Word has no usable timing')
        words.append({'text': match.group(), 'start_seconds': round(start, 4),
                      'duration_seconds': round(end-start, 4)})
    if not words:
        raise ValueError('Empty aligned narration')
    return words


def main(argv=None):
    from project import take_root
    root, argv = take_root(argv, REPO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=REPO / '.env')
    parser.add_argument('--voice-id', default=None, help='Accessible premade voice ID; no cloning')
    parser.add_argument('--speed', type=float, default=1.12)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--scene', type=int, action='append', help='Generate only this scene (repeat for multiple scenes)')
    parser.add_argument('--check', action='store_true', help='Check free account/quota only; generate no speech')
    args = parser.parse_args(argv)
    if not .7 <= args.speed <= 1.2:
        raise ValueError('Use a narration speed between 0.7 and 1.2')
    key, configured_voice = credentials(args.env_file)
    voice = args.voice_id or configured_voice or 'JBFqnCBsd6RMkjVDRZzb'
    narration = json.loads((root / 'narration.json').read_text())
    timeline = json.loads((root / 'timeline.json').read_text())['segments']
    out = root / 'assets/audio'
    pending = []
    for item in narration['segments']:
        index, text = item['index'], item['text'].strip()
        if args.scene is not None and index not in args.scene:
            continue
        if not isinstance(index, int) or not 0 <= index < len(timeline) or not text:
            raise ValueError('Invalid narration segment')
        audio = out / f'{index:02d}.mp3'
        timings = audio.with_suffix('.timings.json')
        if audio.exists() and not args.force and not args.check:
            saved = json.loads(timings.read_text()) if timings.exists() else {}
            if (saved.get('provider') == 'elevenlabs' and saved.get('text_sha256') == text_sha256(text)
                    and saved.get('audio_sha256') == sha256_file(audio)
                    and saved.get('voice') == voice and saved.get('speed') == args.speed):
                continue
            raise ValueError(f'Scene {index}: existing audio preserved; use a separate project or explicit --force')
        pending.append((index, text))
    subscription = request(key, '/user/subscription')
    if subscription.get('tier') != 'free':
        raise ValueError('Free-only mode: this key does not report a free account; no synthesis was requested')
    remaining = int(subscription['character_limit']) - int(subscription['character_count'])
    required = sum(len(text) for _, text in pending)
    if remaining < required:
        raise ValueError(f'Free quota insufficient: need {required} characters; {remaining} remain')
    print(f'ElevenLabs free account: {remaining} credits remaining; up to {required} characters requested', flush=True)
    try:
        selected = request(key, '/voices/' + voice)
    except ValueError as exc:
        # Restricted keys can allow TTS/subscription read but deny voice metadata.
        # Only the documented premade George preset is allowed without metadata.
        if voice != 'JBFqnCBsd6RMkjVDRZzb' or not any(f'HTTP {code}' in str(exc) for code in (401, 403)):
            raise
        selected = {'category': 'premade', 'name': 'George (documented preset; voice metadata permission unavailable)'}
    if selected.get('category') not in ('premade', 'default'):
        raise ValueError('Free-only mode requires an accessible premade voice; no voice cloning')
    print('Premade voice:', selected.get('name', voice), flush=True)
    if args.check:
        return
    out.mkdir(parents=True, exist_ok=True)
    for index, text in pending:
        # Recheck quota before each call; do not retry requests that might consume credits.
        current = request(key, '/user/subscription')
        if current.get('tier') != 'free' or int(current['character_limit']) - int(current['character_count']) < len(text):
            raise ValueError('Free-account tier/quota changed; stopped before synthesis')
        result = request(key, f'/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',
                         {'text': text, 'model_id': 'eleven_multilingual_v2',
                          'voice_settings': {'stability': .55, 'similarity_boost': .75,
                                             'style': .3, 'use_speaker_boost': True, 'speed': args.speed}})
        boundaries = aligned_words(result.get('alignment'), text)
        audio = out / f'{index:02d}.mp3'
        partial = audio.with_suffix('.partial.mp3')
        try:
            partial.write_bytes(base64.b64decode(result['audio_base64'], validate=True))
            duration = probe_duration(partial)
            if duration > float(timeline[index]['duration']) - .3:
                raise ValueError(f'Scene {index}: {duration:.2f}s speech exceeds scene window; no speech was cut')
            if boundaries[-1]['start_seconds'] + boundaries[-1]['duration_seconds'] > duration + .1:
                raise ValueError('Timestamp extends beyond actual speech audio')
            payload = {'provider': 'elevenlabs', 'synthetic_voice': True, 'voice': voice,
                       'model': 'eleven_multilingual_v2', 'speed': args.speed,
                       'text_sha256': text_sha256(text), 'audio_sha256': sha256_file(partial),
                       'duration_seconds': duration, 'boundaries': boundaries,
                       'usage_note': 'Generated on free plan; noncommercial use with ElevenLabs attribution; human rights review pending'}
            metadata = audio.with_suffix('.timings.json')
            temp_meta = metadata.with_suffix('.partial.json')
            temp_meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
            partial.replace(audio)
            temp_meta.replace(metadata)
            print(f'Created scene {index}: {duration:.2f}s, exact alignment timestamps', flush=True)
        finally:
            partial.unlink(missing_ok=True)
    print('Synthetic ElevenLabs speech generated; human pronunciation and rights review required')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, urllib.error.URLError) as exc:
        raise SystemExit(str(exc)) from None
