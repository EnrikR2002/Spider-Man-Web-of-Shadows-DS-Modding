"""Eight frozen Skitter-only cues; native/player/music and other voices remain exact."""
from pathlib import Path
import argparse
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'reference/audio/skitter-finish-v1'
PARENT_DIR = ROOT / 'reference/audio/midnight-voltage-v1'
ROWS = {'alert': 791, 'tell': 792, 'death': 793, 'hurt': 794, 'step': 795,
        'strike-0': 820, 'strike-1': 821, 'strike-2': 822}


def waves(raw):
    from tools import wos_tool as w
    count, size = w.u32(raw, 0x38), w.u32(raw, 8)
    offsets = [w.u32(raw, 0x3c+i*4) for i in range(count)] + [size]
    return [raw[a:b] for a, b in zip(offsets, offsets[1:])]


def sound_data(raw, *, muted=False):
    from tools import sdat, wos_tool as w
    archive = sdat.Sdat.parse(raw)
    file_id = archive.file_id(3, 0)
    parent = archive.blob(file_id)
    samples = waves(parent)
    manifest = json.loads((DIR / 'manifest.json').read_text(encoding='utf-8'))
    if len(samples) != 833:
        raise ValueError('Expected the published 833-row sound bank')
    modified = set()
    for entry in manifest['samples']:
        row = entry['row']
        if row != ROWS[entry['role']] or row in modified:
            raise ValueError('Skitter audio ownership differs')
        if w.sha256(samples[row]) != entry['parent_sha256']:
            raise ValueError('Skitter source waveform differs from the accepted parent')
        payload = (DIR / entry['file']).read_bytes()
        if w.sha256(payload) != entry['sha256']:
            raise ValueError('Frozen Skitter cue changed')
        samples[row] = payload[:12] + bytes(len(payload)-12) if muted else payload
        modified.add(row)
    if modified != set(ROWS.values()):
        raise ValueError('Incomplete Skitter cue set')
    first = w.u32(parent, 0x3c)
    out = bytearray(parent[:first])
    for i, payload in enumerate(samples):
        struct.pack_into('<I', out, 0x3c+i*4, len(out))
        out.extend(payload)
    struct.pack_into('<I', out, 8, len(out))
    struct.pack_into('<I', out, 0x14, len(out)-0x10)
    result = archive.replace({file_id: bytes(out) + parent[w.u32(parent, 8):]})
    check = sdat.Sdat.parse(result)
    old_samples, new_samples = waves(parent), waves(check.blob(file_id))
    if any(a != b for i, (a, b) in enumerate(zip(old_samples, new_samples)) if i not in modified):
        raise ValueError('Unowned sound waveform changed')
    return result, {'rows': sorted(modified), 'manifest': str((DIR / 'manifest.json').relative_to(ROOT)),
                    'unchanged_waveforms': len(samples)-len(modified),
                    'scope': 'Only eight already-owned Skitter PCM waves; sequence/bank rows and every other SDAT file retained.'}


def author():
    """Optional offline authoring with bundled NumPy; shipping reads frozen PCM."""
    import numpy as np
    import wave
    from tools import wos_tool as w
    manifest = json.loads((PARENT_DIR / 'manifest.json').read_text(encoding='utf-8'))
    by_name = {Path(v['file']).stem: v for v in manifest['samples']}
    DIR.mkdir(parents=True, exist_ok=True)
    out = ROOT / 'work/chapter-finish/audio'
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0x291021)
    entries, reel = [], []
    def band(values, rate, lo, hi):
        frequency = np.fft.rfftfreq(len(values), 1/rate)
        hp = np.clip((frequency-lo*.6)/(lo*.4), 0, 1)
        lp = np.clip((hi*1.18-frequency)/(hi*.18), 0, 1)
        return np.fft.irfft(np.fft.rfft(values)*hp*lp, n=len(values))
    durations = {'alert': .28, 'tell': .19, 'death': .62, 'hurt': .14, 'step': .065,
                 'strike-0': .16, 'strike-1': .20, 'strike-2': .23}
    targets = {'alert': 3400, 'tell': 3800, 'death': 3600, 'hurt': 3200, 'step': 700,
               'strike-0': 4700, 'strike-1': 4900, 'strike-2': 5000}
    for role, row in ROWS.items():
        entry = by_name['skitter-'+role]
        original = (PARENT_DIR / entry['file']).read_bytes()
        if w.sha256(original) != entry['sha256'] or original[0] != 1:
            raise ValueError('Expected immutable PCM16 Skitter source')
        rate = w.u16(original, 2)
        source = np.frombuffer(original[12:], dtype='<i2').astype(float)
        n = round(durations[role]*rate)
        t = np.arange(n)/rate
        # Short dry organic rasp under a new chitin click; no cavern/reverb tail
        # or recognizable humanoid vocal is added. Each role has a clear envelope.
        source = np.interp(np.linspace(0, len(source)-1, n), np.arange(len(source)), source)
        source = band(source, rate, 180 if role != 'death' else 100, 4300)
        source /= max(1, float(np.sqrt(np.mean(source*source))))
        noise = band(rng.normal(0, 1, n), rate, 900, 5200)
        noise /= max(.001, float(np.sqrt(np.mean(noise*noise))))
        if role.startswith('strike'):
            envelope = (t/.025)*np.exp(1-t/.025)
            rasp = np.exp(-t/.065)
            body = .58*source*rasp + .42*noise*envelope
            body += .12*np.sin(math_tau*(680*t-1100*t*t))*np.exp(-t/.045)
        elif role == 'step':
            body = .75*noise*np.exp(-t/.012) + .25*source*np.exp(-t/.023)
        elif role == 'death':
            # Falling breath/glottal pulse, then a short final shell tick.
            envelope = (1-t/durations[role])**1.2
            pulses = .55+.45*np.sin(math_tau*(23*t-9*t*t))**2
            body = source*envelope*pulses + .1*noise*envelope
        else:
            frequency = 32 if role == 'tell' else 24 if role == 'alert' else 40
            pulses = .3+.7*np.maximum(0, np.sin(math_tau*frequency*t))**2
            envelope = np.exp(-t/(durations[role]*.48))
            body = .8*source*pulses*envelope + .2*noise*envelope
        fade = min(round(.006*rate), n//4)
        body[:fade] *= np.linspace(0, 1, fade)
        body[-fade:] *= np.linspace(1, 0, fade)
        body *= targets[role]/max(.001, float(np.sqrt(np.mean(body*body))))
        body = np.tanh(body/24000)*24000
        pcm = np.rint(body).astype('<i2').tobytes()
        pcm += bytes(-len(pcm) % 4)
        payload = struct.pack('<BBHHHI', 1, 0, rate, int(16756991/rate), 0, len(pcm)//4) + pcm
        filename = 'skitter-'+role+'.swavdata'
        (DIR / filename).write_bytes(payload)
        with wave.open(str(out / ('skitter-'+role+'.wav')), 'wb') as stream:
            stream.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
            stream.writeframes(pcm)
        entries.append({'role': role, 'row': row, 'file': filename, 'sha256': w.sha256(payload),
                        'parent_sha256': w.sha256(original), 'rate': rate,
                        'rms': round(float(np.sqrt(np.mean(body*body))), 2),
                        'peak': round(float(np.max(np.abs(body)))), 'seconds': len(pcm)/2/rate})
        reel.extend((np.frombuffer(pcm, dtype='<i2'), np.zeros(rate//5, dtype='<i2')))
    with wave.open(str(out / 'skitter-cues.wav'), 'wb') as stream:
        stream.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes(np.concatenate(reel).astype('<i2').tobytes())
    w.write_json(DIR / 'manifest.json', {'schema_version': 1, 'samples': entries,
        'provenance': manifest['provenance'], 'source_manifest': str((PARENT_DIR/'manifest.json').relative_to(ROOT)),
        'processing': 'Deterministic short organic/chitin cues from own CC0-derived Skitter recordings; band-limited seeded foley, dry envelopes, quiet steps, role-specific headroom. No native/game recording sampled.'})


math_tau = 6.283185307179586

if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--author', action='store_true', required=True)
    parser.parse_args()
    author()
