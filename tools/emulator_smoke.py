#!/usr/bin/env python3
"""Optional Windows x64 headless boot capture using a pinned melonDS DS core.

Run --fetch-core once to download the official v1.1.5 libretro release to work/.
The main build workflow needs no emulator or dependencies. This harness runs a
bounded input sequence and captures frames; inspect the images to assess gameplay.
Optional battery saves are copied into emulator memory, never written back.
Scripted inputs and RAM captures support paired, reproducible combat experiments.
Source ROMs and battery files are read only.
"""
from __future__ import annotations
import argparse
import ctypes as c
import io
import os
from pathlib import Path
import struct
import sys
import time
import statistics
import urllib.request
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w
from tools.nitro_texture import png_rgb
from tools.desmume_save import Dsv

CORE_URL = 'https://github.com/JesseTG/melonds-ds/releases/download/v1.1.5/melondsds_libretro-win32-x86_64-Release.zip'
ZIP_SHA256 = 'd93e78d28d8098966360d7654c5ad127db4583113cfecd9a7093a4ce013eaa9e'
CORE_SHA256 = '534e0a4f489107dd35491bc9a628e8a32d7a9c58460a4951851dac570403312b'
CORE_PATH = w.PROJECT / 'work/emulator/melondsds_libretro.dll'


def fetch_core():
    request = urllib.request.Request(CORE_URL, headers={'User-Agent': 'CS5E-personal-research'})
    with urllib.request.urlopen(request, timeout=30) as response: data = response.read()
    if w.sha256(data) != ZIP_SHA256: raise ValueError('Official core ZIP differs from pinned SHA256')
    archive = zipfile.ZipFile(io.BytesIO(data))
    prefix = 'melondsds_libretro-win32-x86_64-Release/cores/'
    core = archive.read(prefix + 'melondsds_libretro.dll')
    if w.sha256(core) != CORE_SHA256: raise ValueError('Core DLL differs from pinned SHA256')
    w.atomic_write(CORE_PATH, core)
    w.atomic_write(CORE_PATH.parent / 'melondsds-LICENSE.txt', archive.read(prefix + 'melondsds-LICENSE.txt'))
    w.write_json(CORE_PATH.parent / 'provenance.json', {'url': CORE_URL, 'zip_sha256': ZIP_SHA256, 'dll_sha256': CORE_SHA256})


ENV = c.CFUNCTYPE(c.c_bool, c.c_uint, c.c_void_p)
VIDEO = c.CFUNCTYPE(None, c.c_void_p, c.c_uint, c.c_uint, c.c_size_t)
AUDIO = c.CFUNCTYPE(None, c.c_int16, c.c_int16)
BATCH = c.CFUNCTYPE(c.c_size_t, c.POINTER(c.c_int16), c.c_size_t)
POLL = c.CFUNCTYPE(None)
INPUT = c.CFUNCTYPE(c.c_int16, c.c_uint, c.c_uint, c.c_uint, c.c_uint)


class Variable(c.Structure):
    _fields_ = [('key', c.c_char_p), ('value', c.c_char_p)]


class Game(c.Structure):
    _fields_ = [('path', c.c_char_p), ('data', c.c_void_p), ('size', c.c_size_t), ('meta', c.c_char_p)]


def frame_png(frame, pixel_format):
    data, width, height, pitch = frame
    rgb = bytearray()
    for y in range(height):
        for x in range(width):
            if pixel_format == 1:
                blue, green, red, _ = data[y * pitch + x * 4:y * pitch + x * 4 + 4]
                rgb.extend((red, green, blue))
            else:
                value = struct.unpack_from('<H', data, y * pitch + x * 2)[0]
                if pixel_format == 2:
                    red, green, blue = (value >> 11) & 31, (value >> 5) & 63, value & 31
                    rgb.extend((red * 255 // 31, green * 255 // 63, blue * 255 // 31))
                else:
                    red, green, blue = (value >> 10) & 31, (value >> 5) & 31, value & 31
                    rgb.extend((red * 255 // 31, green * 255 // 31, blue * 255 // 31))
    return png_rgb(width, height, bytes(rgb))


BUTTONS = {'B': 0, 'Y': 1, 'Select': 2, 'Start': 3, 'Up': 4, 'Down': 5,
           'Left': 6, 'Right': 7, 'A': 8, 'X': 9, 'L': 10, 'R': 11}


def input_schedule(rows):
    """Validate explicit half-open frame ranges and named DS joypad buttons."""
    if not isinstance(rows, list): raise ValueError('Input script must be a list')
    result = []
    for row in rows:
        start, end, buttons = row['start'], row['end'], row['buttons']
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= 10000:
            raise ValueError('Input frame range must be within 0..10000')
        if not isinstance(buttons, list) or any(b not in BUTTONS for b in buttons):
            raise ValueError('Unknown input button')
        result.append((start, end, frozenset(BUTTONS[b] for b in buttons)))
    return result


def run(rom_path, frames, captures, *, save_path=None, script=None, label=None, ram_captures=(), trace_frames=(), battery_captures=(), frame_hook=None, observer=None, core_options=None, timing_start=None):
    if os.name != 'nt' or c.sizeof(c.c_void_p) != 8: raise ValueError('Pinned emulator harness requires Windows x64')
    if w.sha256(CORE_PATH.read_bytes()) != CORE_SHA256: raise ValueError('Emulator core integrity check failed')
    rom_data = rom_path.read_bytes(); report = w.validate_rom(rom_data, target=True)
    if trace_frames:
        from tools import player_trace
        from tools.combat_profile import identify_arm9
        arm9_offset, _, _, arm9_size = struct.unpack_from('<IIII', rom_data, 0x20)
        identify_arm9(rom_data[arm9_offset:arm9_offset+arm9_size])
    dest = w.PROJECT / 'build/boot-tests' / (rom_path.stem + '-' + report['sha256'][:8])
    if label:
        if not label.replace('-', '').replace('_', '').isalnum(): raise ValueError('Invalid run label')
        dest = dest / label
    w.safe_output(dest)
    system = dest / 'system'; system.mkdir(parents=True, exist_ok=True)
    directory = str(system).encode('utf-8')
    library = c.CDLL(str(CORE_PATH))
    variables = {b'melonds_render_mode': b'software', b'melonds_console_mode': b'ds',
                 b'melonds_boot_mode': b'direct', b'melonds_sysfile_mode': b'builtin',
                 b'melonds_jit_fast_memory': b'disabled', b'melonds_threaded_renderer': b'disabled',
                 b'melonds_start_time_mode': b'absolute', b'melonds_start_time_absolute_year': b'2004',
                 b'melonds_start_time_absolute_month': b'1', b'melonds_start_time_absolute_day': b'1',
                 b'melonds_start_time_absolute_hour': b'0', b'melonds_start_time_absolute_minute': b'0'}
    if core_options:
        if any(not isinstance(k, bytes) or not isinstance(v, bytes) for k, v in core_options.items()):
            raise ValueError('Core option keys and values must be bytes')
        variables.update(core_options)
    state = {'frame': 0, 'last': None, 'pixel_format': 1}
    schedule = input_schedule(script) if script is not None else None

    @ENV
    def environment(cmd, pointer):
        if cmd in (9, 30, 31): c.cast(pointer, c.POINTER(c.c_char_p))[0] = directory; return True
        if cmd == 3: c.cast(pointer, c.POINTER(c.c_bool))[0] = True; return True
        if cmd == 10:
            state['pixel_format'] = c.cast(pointer, c.POINTER(c.c_int))[0]
            return state['pixel_format'] in (0, 1, 2)
        if cmd == 15:
            variable = c.cast(pointer, c.POINTER(Variable)).contents
            variable.value = variables.get(variable.key)
            return variable.value is not None
        if cmd == 16:
            rows = c.cast(pointer, c.POINTER(Variable)); i = 0
            while rows[i].key:
                variables.setdefault(rows[i].key, rows[i].value.split(b'; ', 1)[-1].split(b'|')[0]); i += 1
            return True
        if cmd in (17, 49): c.cast(pointer, c.POINTER(c.c_bool))[0] = False; return True
        if cmd in (39, 52): c.cast(pointer, c.POINTER(c.c_uint))[0] = 0; return True
        if cmd in (6, 7, 11, 18, 32, 34, 35, 36, 37, 55): return True
        # Optional hardware/VFS/microphone/log interfaces fall back to core defaults.
        return False

    @VIDEO
    def video(pointer, width, height, pitch):
        if pointer and pointer != c.c_void_p(-1).value:
            state['last'] = (c.string_at(pointer, height * pitch), width, height, pitch)

    @AUDIO
    def audio(left, right): pass
    @BATCH
    def batch(pointer, count): return count
    @POLL
    def poll(): pass
    @INPUT
    def input_state(port, device, index, button):
        frame = state['frame']
        if schedule is not None:
            return int(device == 1 and port == 0 and any(start <= frame < end and button in buttons
                       for start, end, buttons in schedule))
        return int(device == 1 and port == 0 and frame > 600 and frame % 120 < 8 and button in (3, 8))

    for name, callback in [('environment', environment), ('video_refresh', video), ('audio_sample', audio),
                           ('audio_sample_batch', batch), ('input_poll', poll), ('input_state', input_state)]:
        method = getattr(library, 'retro_set_' + name)
        method.argtypes = [type(callback)]; method.restype = None; method(callback)
    library.retro_init.restype = None
    library.retro_load_game.argtypes = [c.POINTER(Game)]; library.retro_load_game.restype = c.c_bool
    for name in ('retro_run', 'retro_unload_game', 'retro_deinit'): getattr(library, name).restype = None
    library.retro_get_memory_data.argtypes = [c.c_uint]; library.retro_get_memory_data.restype = c.c_void_p
    library.retro_get_memory_size.argtypes = [c.c_uint]; library.retro_get_memory_size.restype = c.c_size_t
    buffer = c.create_string_buffer(rom_data)
    game = Game(str(rom_path).encode('utf-8'), c.cast(buffer, c.c_void_p), len(rom_data), None)
    library.retro_init(); loaded = False
    screenshots = []
    memory_captures = []
    battery_snapshots = []
    player_samples = []
    battery = None
    observations, timings = [], []
    try:
        if not library.retro_load_game(c.byref(game)): raise ValueError('melonDS DS rejected ROM')
        loaded = True
        if save_path is not None:
            raw = Path(save_path).read_bytes()
            payload = Dsv.parse(raw).payload if Path(save_path).suffix.lower() == '.dsv' else raw
            size = library.retro_get_memory_size(0); pointer = library.retro_get_memory_data(0)
            if not pointer or size != len(payload): raise ValueError(f'Battery size {len(payload)} differs from core size {size}')
            c.memmove(pointer, payload, size)
            battery = {'source_sha256': w.sha256(raw), 'payload_sha256': w.sha256(payload), 'size': size}
        for frame in range(frames):
            state['frame'] = frame
            stamp = time.perf_counter_ns()
            library.retro_run()
            elapsed = time.perf_counter_ns() - stamp
            if timing_start is not None and frame >= timing_start:
                timings.append(elapsed / 1000000)
            # Optional research callbacks operate only on this disposable core.
            # No state is loaded and source battery files are never written.
            if frame_hook is not None:
                frame_hook(frame, library)
            if observer is not None:
                value = observer(frame, library)
                if value is not None: observations.append(value)
            if frame in captures:
                if state['last'] is None: raise ValueError('Core has not produced a video frame')
                png = frame_png(state['last'], state['pixel_format'])
                path = dest / f'frame-{frame:05d}.png'; w.atomic_write(path, png)
                screenshots.append({'frame': frame, 'path': path.relative_to(w.PROJECT).as_posix(), 'png_sha256': w.sha256(png),
                                    'width': state['last'][1], 'height': state['last'][2]})
                print(f'Captured {path}', flush=True)
            if frame in ram_captures:
                size = library.retro_get_memory_size(2); pointer = library.retro_get_memory_data(2)
                if not pointer or size != 4 * 1024 * 1024: raise ValueError(f'Unexpected DS system RAM size {size}')
                data = c.string_at(pointer, size); path = dest / f'ram-{frame:05d}.bin'
                w.atomic_write(path, data)
                memory_captures.append({'frame': frame, 'path': path.relative_to(w.PROJECT).as_posix(), 'sha256': w.sha256(data)})
            if frame in trace_frames:
                size = library.retro_get_memory_size(2); pointer = library.retro_get_memory_data(2)
                if not pointer or size != 4 * 1024 * 1024: raise ValueError('Unexpected DS main RAM')
                player_samples.append({'frame': frame, **player_trace.sample(c.string_at(pointer, size))})
            if frame in battery_captures:
                size = library.retro_get_memory_size(0); pointer = library.retro_get_memory_data(0)
                if not pointer or size != 512: raise ValueError('Expected CS5E 512-byte save RAM')
                data = c.string_at(pointer, size)
                path = dest / f'battery-{frame:05d}.sav'
                w.atomic_write(path, data, (Path(save_path),) if save_path else ())
                battery_snapshots.append({'frame': frame, 'path': path.relative_to(w.PROJECT).as_posix(),
                                          'size': size, 'sha256': w.sha256(data)})
        if player_samples: w.write_json(dest/'player-trace.json', player_samples)
        if observations: w.write_json(dest/'observations.json', observations)
        if timings:
            ordered = sorted(timings)
            w.write_json(dest/'frame-timing.json', {
                'first_frame': timing_start, 'last_frame': frames-1, 'samples': len(timings),
                'mean_ms': statistics.mean(timings), 'median_ms': statistics.median(timings),
                'p95_ms': ordered[int(0.95*len(ordered))], 'p99_ms': ordered[int(0.99*len(ordered))],
                'max_ms': max(timings), 'frame_ms': timings,
                'measure': 'Host wall time of retro_run, including video callback; not DS or DeSmuME FPS'})
        w.write_json(dest / 'boot.json', {'rom_sha256': report['sha256'], 'core_version': 'melonDS DS 1.1.5',
                     'core_sha256': CORE_SHA256, 'core_url': CORE_URL, 'frames': frames,
                     'input_sequence': script if script is not None else 'For frame>600, each 120-frame period presses Start+A during its first 8 frames; no other input.',
                     'battery_copy': battery, 'ram_captures': memory_captures,
                     'private_battery_captures': battery_snapshots,
                     'player_trace': 'player-trace.json' if player_samples else None,
                     'research_callbacks': {'frame_hook': frame_hook is not None, 'observer': observer is not None},
                     'options': {key.decode(): value.decode() for key, value in sorted(variables.items())},
                     'screenshots': screenshots, 'assessment': 'Captures require visual inspection; this is not a full gameplay test.'})
    finally:
        if loaded: library.retro_unload_game()
        library.retro_deinit()
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', nargs='?', default='build/Spider-Man-WoS-modded.nds')
    parser.add_argument('--fetch-core', action='store_true')
    parser.add_argument('--frames', type=int, default=1800)
    parser.add_argument('--capture', default='299,599,899,1199,1499,1799')
    parser.add_argument('--save', help='Read-only .dsv/.sav battery copy for this isolated run')
    parser.add_argument('--script', help='JSON list of {start,end,buttons} input ranges')
    parser.add_argument('--label', help='Separate run directory beneath the ROM hash')
    parser.add_argument('--ram-capture', default='', help='Comma-separated frame numbers for private RAM dumps')
    parser.add_argument('--player-trace', help='Half-open START:END range for read-only CS5E player telemetry')
    parser.add_argument('--battery-capture', default='', help='Private save-RAM captures; never updates source battery')
    parser.add_argument('--timing-start', type=int, help='Measure retro_run wall time from this frame; no FPS claim')
    parser.add_argument('--threaded-renderer', action='store_true', help='Isolated software-renderer experiment')
    args = parser.parse_args()
    try:
        if not 1 <= args.frames <= 10000: raise ValueError('--frames must be 1..10000')
        if args.timing_start is not None and not 0 <= args.timing_start < args.frames:
            raise ValueError('Timing start outside run')
        captures = {int(value) for value in args.capture.split(',')}
        ram_captures = {int(value) for value in args.ram_capture.split(',') if value}
        battery_captures = {int(value) for value in args.battery_capture.split(',') if value}
        trace_frames = set()
        if args.player_trace:
            start, end = (int(value) for value in args.player_trace.split(':'))
            if not 0 <= start < end <= args.frames: raise ValueError('Player trace range outside run')
            trace_frames = set(range(start, end))
        if any(not 0 <= frame < args.frames for frame in captures | ram_captures | battery_captures): raise ValueError('Capture frame outside run')
        if args.fetch_core: fetch_core()
        if not CORE_PATH.exists(): raise ValueError('Core not present: run with --fetch-core once')
        path = Path(args.rom); path = path if path.is_absolute() else w.PROJECT / path
        import json
        script = json.loads(Path(args.script).read_text(encoding='utf-8')) if args.script else None
        print(f'Boot capture complete: {run(path.resolve(), args.frames, captures, save_path=args.save,
              script=script, label=args.label, ram_captures=ram_captures, trace_frames=trace_frames,
              battery_captures=battery_captures, timing_start=args.timing_start,
              core_options={b'melonds_threaded_renderer': b'enabled'} if args.threaded_renderer else None)}')
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
