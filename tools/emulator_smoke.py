#!/usr/bin/env python3
"""Optional Windows x64 headless boot capture using a pinned melonDS DS core.

Run --fetch-core once to download the official v1.1.5 libretro release to work/.
The main build workflow needs no emulator or dependencies. This harness runs a
bounded input sequence and captures frames; inspect the images to assess gameplay.
No game save is loaded or persisted. Source ROMs are read only.
"""
from __future__ import annotations
import argparse
import ctypes as c
import io
import os
from pathlib import Path
import struct
import sys
import urllib.request
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w
from tools.nitro_texture import png_rgb

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


def run(rom_path, frames, captures):
    if os.name != 'nt' or c.sizeof(c.c_void_p) != 8: raise ValueError('Pinned emulator harness requires Windows x64')
    if w.sha256(CORE_PATH.read_bytes()) != CORE_SHA256: raise ValueError('Emulator core integrity check failed')
    rom_data = rom_path.read_bytes(); report = w.validate_rom(rom_data, target=True)
    dest = w.PROJECT / 'build/boot-tests' / (rom_path.stem + '-' + report['sha256'][:8])
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
    state = {'frame': 0, 'last': None, 'pixel_format': 1}

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
        return int(device == 1 and port == 0 and frame > 600 and frame % 120 < 8 and button in (3, 8))

    for name, callback in [('environment', environment), ('video_refresh', video), ('audio_sample', audio),
                           ('audio_sample_batch', batch), ('input_poll', poll), ('input_state', input_state)]:
        method = getattr(library, 'retro_set_' + name)
        method.argtypes = [type(callback)]; method.restype = None; method(callback)
    library.retro_init.restype = None
    library.retro_load_game.argtypes = [c.POINTER(Game)]; library.retro_load_game.restype = c.c_bool
    for name in ('retro_run', 'retro_unload_game', 'retro_deinit'): getattr(library, name).restype = None
    buffer = c.create_string_buffer(rom_data)
    game = Game(str(rom_path).encode('utf-8'), c.cast(buffer, c.c_void_p), len(rom_data), None)
    library.retro_init(); loaded = False
    screenshots = []
    try:
        if not library.retro_load_game(c.byref(game)): raise ValueError('melonDS DS rejected ROM')
        loaded = True
        for frame in range(frames):
            state['frame'] = frame; library.retro_run()
            if frame in captures:
                if state['last'] is None: raise ValueError('Core has not produced a video frame')
                png = frame_png(state['last'], state['pixel_format'])
                path = dest / f'frame-{frame:05d}.png'; w.atomic_write(path, png)
                screenshots.append({'frame': frame, 'path': path.relative_to(w.PROJECT).as_posix(), 'png_sha256': w.sha256(png),
                                    'width': state['last'][1], 'height': state['last'][2]})
                print(f'Captured {path}', flush=True)
        w.write_json(dest / 'boot.json', {'rom_sha256': report['sha256'], 'core_version': 'melonDS DS 1.1.5',
                     'core_sha256': CORE_SHA256, 'core_url': CORE_URL, 'frames': frames,
                     'input_sequence': 'For frame>600, each 120-frame period presses Start+A during its first 8 frames; no other input.',
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
    args = parser.parse_args()
    try:
        if not 1 <= args.frames <= 10000: raise ValueError('--frames must be 1..10000')
        captures = {int(value) for value in args.capture.split(',')}
        if any(not 0 <= frame < args.frames for frame in captures): raise ValueError('Capture frame outside run')
        if args.fetch_core: fetch_core()
        if not CORE_PATH.exists(): raise ValueError('Core not present: run with --fetch-core once')
        path = Path(args.rom); path = path if path.is_absolute() else w.PROJECT / path
        print(f'Boot capture complete: {run(path.resolve(), args.frames, captures)}')
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
