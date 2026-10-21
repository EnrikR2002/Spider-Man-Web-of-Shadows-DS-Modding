"""Deterministic numbered releases: native version labels and guarded upgrade prices."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w, oscorp_resources
from tools.qol_suits_menu import StringSlots

VERSION = '0.1.1'
RELEASE_DATE = '2026-10-05'
PROFILE = f'tasm-v{VERSION}'
PARENT_PROFILE = 'tasm-v0.1.0'
PARENT_ROM_SHA = 'e1b66ebdad90856f7af5a508bd2bcd78ade0640c6926e6668da2c6b36cee1451'
PARENT_RECIPE_SHA = '6267bb27ead9e4efe35b9cba76aeedf4174621f5d9b14ae3a75a03af25aa7814'
PRICE_TABLE = 0x120340
OLD_PRICES = (100, 200, 600, 400, 600, 800, 1000)
PRICES = (50, 100, 150, 150, 200, 250, 350)
SHARED_PRICE_TABLE = 0x120260
SHARED_NAMES = ('Launching Uppercut', 'Enemy Kick-Off', 'Drill Kick', 'Jackhammer Stomp',
                'Air Dodge', 'Enhanced Dodge', 'Quick Recovery')
SHARED_BITS = (6, 12, 7, 8, 10, 9, 11)
OLD_SHARED_PRICES = (50, 200, 400, 600, 200, 800, 800)
SHARED_PRICES = (25, 50, 100, 150, 50, 200, 150)
TEXT_EDITS = {50: f'TASM v{VERSION}\nPress a button to start',
              74: f'Options v{VERSION}'}
# Exact authored parent plus the Red and Both Suits price words.
ARM9_SHA256 = '322fbd7bd597f91f875957f65eadc6fcb7611480c64e76db6a14a0ef736ed6f6'
PROFILE_INFO = {
    'tasm-v0.1.0': {'version': '0.1.0', 'date': '2026-10-05',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350), 'shared_prices': None,
                    'arm9_sha256': 'da50ad8a0f249ad95461fe63157c61957bb6bfa6b5c1361a7bdef6d107d3e86e'},
    PROFILE: {'version': VERSION, 'date': RELEASE_DATE,
              'red_prices': (50, 100, 150, 150, 200, 250, 350),
              'shared_prices': (25, 50, 100, 150, 50, 200, 150),
              'arm9_sha256': ARM9_SHA256},
    # Red "never stand still" kit over v0.1.1 (tools/tasm_kit.py); same prices.
    'tasm-v0.2.0': {'version': '0.2.0', 'date': '2026-10-05', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '99392f5df4a0d2b37652ca5e0d040ae0d2a14702bd6a4fdfc1be3dbe0a91db77'},
    # Spin Cycle aims each contact and glides into reach; straight blade-leg spin clip.
    'tasm-v0.2.1': {'version': '0.2.1', 'date': '2026-10-05', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'e0f1c3d333712efca521782ddb83fde50c3d23fd981bded13daafa1790a1ee16'},
    # Perch spring/head-hop, Reflex back tuck, Sense vs ranged (CHANGES v0.3.0).
    'tasm-v0.3.0': {'version': '0.3.0', 'date': '2026-10-05', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '0483dc4044cb6221ab90d3b0db89f615e14e2d8d7751e7039f1b80465c2bec70'},
    # Skyjack spike bowls nearby enemies with a replayed native hit (CHANGES v0.4.0).
    'tasm-v0.4.0': {'version': '0.4.0', 'date': '2026-10-05', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'b4e91fdd3b90d033d849306028756a014f71d79ed2343d923bca197a2e933fdc'},
    # Freeze/clip fix: Sense dashes (no teleport/heap writes), Leapfrog and Perch
    # move by velocity, pointer checks, neutral Reflex consumes R (CHANGES v0.4.1).
    'tasm-v0.4.1': {'version': '0.4.1', 'date': '2026-10-06', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'b806e50864957323fe8a92a856166d22627d5548b9e4340ab68e82f352a7cf6f'},
    # Test Upgrades sparring: three attacking Brutes, 30 s heal, no lethal hits (CHANGES v0.5.0).
    'tasm-v0.5.0': {'version': '0.5.0', 'date': '2026-10-06', 'kit': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '88328d560f095a0f46fe07a2476922fb957e4933cb429ca831105113ed650f97'},
    # Midnight Line first station: five appended rooms behind Sewer_Save02 (CHANGES v0.6.0).
    # The kit ARM9 above is composed first; mod.create_build then applies the chapter.
    'tasm-v0.6.0': {'version': '0.6.0', 'date': '2026-10-07', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'efab33e0f8154f6ad76fcf453c70d9d7146165b83e04ee1d4ea2cfd6b1b7b621'},
    # Player feedback fixes: matching door kinds, visible entrance doorway, Platform
    # train-roof fight, Sewer map in chapter rooms (CHANGES v0.6.1). v0.6.0 stays
    # identified by its published ROM; current chapter code builds v0.6.1 only.
    'tasm-v0.6.1': {'version': '0.6.1', 'date': '2026-10-07', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '817c23a4de435e0333f9b120e6a7f16e7e16a2b7408da7f89f711c2a29d3aab3'},
    # The Nest: nine more chapter rooms (Hive clones + Venom's rooftop boss arena),
    # the chapter drawn on the Sewer touch-screen map (CHANGES v0.7.0).
    'tasm-v0.7.0': {'version': '0.7.0', 'date': '2026-10-07', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'a19896dbcc2d62889eaf787d6d7900c9ed803d25847fcf8b99da959d48b692a9'},
    # Power puzzle (Stairs breaker cuts the Platform's track power so the boiler
    # can be lifted off the Nest grate), chapter dialogue and the Refuge
    # objective board (CHANGES v0.8.0). v0.7.0's chapter bytes stay identified by its ROM.
    'tasm-v0.8.0': {'version': '0.8.0', 'date': '2026-10-08', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'dc4911d7774bfbbc5f4a6cc7d7e6f4d679657926b94c2abf5acffe6da4310263'},
    # Walkable Nest (player softlock in the Gate): no Sledgehammer Slam floors, no ichor door
    # seals, boss arena entered from its exit corridor, Stairs grate locked until the loop is
    # done (CHANGES v0.8.1). v0.8.0's chapter bytes stay identified by its ROM.
    'tasm-v0.8.1': {'version': '0.8.1', 'date': '2026-10-11', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '4bdceb45a69e77cea7f1e1688c552d97734ea46f4466a0aa09c8089ef32ce384'},
    # The Yard: the unused prototype warehouse (proto01) as room 90 behind a new Refuge door,
    # with a Pier gang camp (CHANGES v0.9.0). v0.8.1's chapter bytes stay identified by its ROM.
    'tasm-v0.9.0': {'version': '0.9.0', 'date': '2026-10-11', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'e54fa1aaf4cd27ad68f72188c8377c2f44c158c448e71c512503df11ac6b9534'},
    # Three new Red shop rows on free ability bits 74..76: Web Rush, Ricochet, Momentum, in a
    # second kit code block (CHANGES v0.10.0). v0.9.0's bytes stay identified by its ROM.
    'tasm-v0.10.0': {'version': '0.10.0', 'date': '2026-10-11', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'c6e2992a21cb365d00e3575ae89a46933241aa99f86bd975efec16d902c96b2c'},
    # Player feedback on v0.10.0: Reflex/Sense speed 1.10/1.20, Momentum one tier earlier, three
    # Vitality rows (Both Suits, bits 77..79), the chapter's own map screen (area 5), closed dead
    # hatches, a strength dial for the Nest (CHANGES v0.11.0). v0.10.0's bytes stay identified by its ROM.
    'tasm-v0.11.0': {'version': '0.11.0', 'date': '2026-10-12', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'caa8403335641e6faa60d2f5b10ca5f2ade05f4ca15dd2277a9efc17d7fcda6a'},
    # The Substation: three rooms built from nothing with the room compiler (Switchyard, Relay Hall,
    # Control Roof), a door at the Yard's left wall, the map's visited test for rooms above 91
    # (CHANGES v0.12.0). Kit code unchanged. v0.11.0's bytes stay identified by its ROM.
    'tasm-v0.12.0': {'version': '0.12.0', 'date': '2026-10-12', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'a212585a168ec9757b737ed0ebaf006ffcfb1273c4c40e0ac7586ba43b49f474'},
    # Three more Red shop rows on ability bits 80..82: Overclock, Dragnet, Vortex (the kit's own web
    # lines and built hits), the Substation's crews stronger and its looks reworked (far skylines,
    # no black gaps) (CHANGES v0.13.0). v0.12.0's bytes stay identified by its ROM.
    'tasm-v0.13.0': {'version': '0.13.0', 'date': '2026-10-13', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'db0911844f23b68bc2a9a8731415018e4a45918b5d26aeb1ad316d2b35c038fe'},
    'tasm-v0.14.0': {'version': '0.14.0', 'date': '2026-10-13', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'f0f822458dacbc77b25a8f325bfad5144b8115c7816970e6b853a74de6c643cd'},
    'tasm-v0.15.0': {'version': '0.15.0', 'date': '2026-10-13', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': 'f4b5fdc94bd3b0891b511e532937a83f559fc36fe4f82991adc0850a99518f6b'},
    'tasm-v0.15.1': {'version': '0.15.1', 'date': '2026-10-14', 'kit': True, 'chapter': True, 'parent': 'tasm-v0.1.1',
                     'red_prices': (50, 100, 150, 150, 200, 250, 350),
                     'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                     'arm9_sha256': '117c9f7c21c6b2212e95aaf021b3537128de7d6b831cc328e7620021635d6da6'},
    # Independent Crane Row post-pass preserves the exact v0.15.1 kit/chapter
    # composition; it owns its version strings, new rooms/maps and adapters.
    'tasm-v0.16.0': {'version': '0.16.0', 'date': '2026-10-14', 'kit': True, 'chapter': True,
                    'crane': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'abfbb1120c6e2d3237b437fefa742bb12aa0c3a1c57a08664282274c6cc0f722'},
    'tasm-v0.16.1': {'version': '0.16.1', 'date': '2026-10-14', 'kit': True, 'chapter': True,
                    'crane': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'abfbb1120c6e2d3237b437fefa742bb12aa0c3a1c57a08664282274c6cc0f722'},
    'tasm-v0.16.2': {'version': '0.16.2', 'date': '2026-10-15', 'kit': True, 'chapter': True,
                    'crane': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': 'abfbb1120c6e2d3237b437fefa742bb12aa0c3a1c57a08664282274c6cc0f722'},
    'tasm-v0.16.3': {'version': '0.16.3', 'date': '2026-10-15', 'kit': True, 'chapter': True,
                    'crane': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '2dea03146357efb53241218a92c8331115de8652691b68af8e2ba25c42e47b64'},
    'tasm-v0.17.0': {'version': '0.17.0', 'date': '2026-10-15', 'kit': True, 'chapter': True,
                    'crane': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '51c8273fa174eac3527ebbf2cf66a50be707640a972c01e5874081baebecaf22'},
    'tasm-v0.18.0': {'version': '0.18.0', 'date': '2026-10-15', 'kit': True, 'chapter': True,
                    'crane': True, 'creatures': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '805460f9bcdccdc5d0c7ad674fd6270640b3fa26519d1a6bee74db7fd107f87e'},
    'tasm-v0.19.0': {'version': '0.19.0', 'date': '2026-10-16', 'kit': True, 'chapter': True,
                    'crane': True, 'creatures': True, 'compose_parent': 'tasm-v0.15.1', 'parent': 'tasm-v0.1.1',
                    'red_prices': (50, 100, 150, 150, 200, 250, 350),
                    'shared_prices': (25, 50, 100, 150, 50, 200, 150),
                    'arm9_sha256': '9b04b02a74cd634901c1435a5bb7708c073c127467cc9971b3bc9a5d1c6a10e3'},
}
PROFILE_INFO['tasm-v0.20.0'] = {
    **PROFILE_INFO['tasm-v0.19.0'], 'version':'0.20.0', 'date':'2026-10-16',
    'crane_parent':'0.19.0', 'midnight_rework':True,
    'arm9_sha256':'854b07a0e37faa49df3dd895df126aa4eb32e0243ca986190e0373aafe24f8b7',
    'rom_sha256':'4b4e739eb9e85699942afe29cb0f9e809d7f9302dcee9154e338717516139888',
}
PROFILE_INFO['tasm-v0.21.0'] = {
    **PROFILE_INFO['tasm-v0.20.0'], 'version':'0.21.0', 'date':'2026-10-17',
    'chapter_renewal':True,
    'arm9_sha256':'0439571a1bf87182caf548bbc33cdc4ce1f867f09430c0541c4bb7b60c430fc3',
    'rom_sha256':'60a974f33a3ca2f57dbe2cf11a7a12b585c172be8565cc0968301544b3a11340',
}
PROFILE_INFO['tasm-v0.22.0'] = {
    **PROFILE_INFO['tasm-v0.21.0'], 'version':'0.22.0', 'date':'2026-10-17',
    'creature_forge':True,
    'arm9_sha256':'571d0d51090d427e024306b55a86728c7adcfda2068e8683c47e125c3eee5eb2',
    'rom_sha256':'69082fda16d7c0491f9bc945e6ebef11c526f7c7622a98a89959ea294b4f2eb2',
}
PROFILE_INFO['tasm-v0.22.1'] = {
    **PROFILE_INFO['tasm-v0.22.0'], 'version':'0.22.1', 'creature_texture_fix':True,
    'rom_sha256':'1613d74662c7dfa9d5166da0b8c8ed08ec048c605a7e9167edf3e320ac4d2a75',
}
PROFILE_INFO['tasm-v0.23.0'] = {
    **PROFILE_INFO['tasm-v0.22.1'], 'version':'0.23.0', 'date':'2026-10-17',
    'chapter_spectacle':True,
    'arm9_sha256':'28bd1cd188d94c5422f6c0b2192c3ea060bb295aabba3b0ec54c4bdd8f979241',
    'rom_sha256':'534c9df52d91f6dbb4102f4deb9143fbaea6b8324f9e7525db4a3880d226e18c',
}
PROFILE_INFO['tasm-v0.24.0'] = {
    **PROFILE_INFO['tasm-v0.23.0'], 'version':'0.24.0', 'date':'2026-10-18',
    'midnight_rebuild':True,
    'arm9_sha256':'dd30eb25ada17e7d95bc1419588d46f96f6367ebbc1213faba21749d161b39e3',
    'rom_sha256':'c31bae4c60869133f9cf4dd3e8b0b2895123d1a2e99d91599231cc8d983b1393',
}
PROFILE_INFO['tasm-v0.25.0'] = {
    **PROFILE_INFO['tasm-v0.24.0'], 'version':'0.25.0', 'date':'2026-10-18',
    'midnight_encore':True,
    'arm9_sha256':'f060152924d74cb5400e620be39a9e9217f96dab4e88ece8153186e9790c6ba2',
    'rom_sha256':'0817ec91a44f85a31135f4d99ef90452dd8c30870689e803743b3594ddadb314',
}
PROFILE_INFO['tasm-v0.26.0'] = {
    **PROFILE_INFO['tasm-v0.25.0'], 'version':'0.26.0', 'date':'2026-10-19',
    'midnight_voltage':True,
    'arm9_sha256':'2ac0e269d709689f94f06ae8b89c75b456fec4fb767f3e3e9660b0c4c704383d',
    'rom_sha256':'21bd1b19c8b8f74f24fca06e238204dac0f78b02630e04629fd8ae78f978a947',
}
PROFILE_INFO['tasm-v0.27.0'] = {
    **PROFILE_INFO['tasm-v0.26.0'], 'version':'0.27.0', 'date':'2026-10-19',
    'midnight_finale':True,
    'arm9_sha256':'88475ec2d8bec8e1d521cf92ff2560e1e72f26b00e73ceefaa525e9d608977aa',
    'rom_sha256':'1b1e4e37d48f4a5661b77ac10032e694d1985347b7eb0f70fdd5d828226cdc4d',
}
PROFILE_INFO['tasm-v0.28.0'] = {
    **PROFILE_INFO['tasm-v0.27.0'], 'version':'0.28.0', 'date':'2026-10-19',
    'midnight_reliability':True,
    'arm9_sha256':'ccc2e83bae9d1b31004834b3be0192dc4ba506d9ad809f9bbd9e69c1c9dd0ea9',
    'rom_sha256':'6819cb91e824961552b86690c3fdd112930bbd1cbb70d5c3c76978b5ce932a20',
}
PROFILES = tuple(PROFILE_INFO)
HISTORY = Path(__file__).resolve().parents[1] / 'reference/releases.json'


def check_version_reuse(version, digest, history=None):
    """A published version must always identify one exact ROM."""
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('Expected a major.minor.patch version')
    path = HISTORY if history is None else Path(history)
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema_version': 1, 'releases': []}
    if data.get('schema_version') != 1 or not isinstance(data.get('releases'), list):
        raise ValueError('Invalid release history')
    for row in data['releases']:
        if row.get('version') == version and row.get('rom_sha256') != digest:
            raise ValueError('Version already identifies a different published ROM; bump the version')
    return data


def register_release(version, digest, *, date, previous, history=None):
    data = check_version_reuse(version, digest, history)
    path = HISTORY if history is None else Path(history)
    if not any(row.get('version') == version for row in data['releases']):
        data['releases'].append({'version': version, 'date': date,
                                'rom_sha256': digest, 'previous_rom_sha256': previous})
        w.write_json(path, data)


def apply_rom(rom, profile=PROFILE):
    if profile not in PROFILE_INFO:
        raise ValueError('Unknown numbered release profile')
    info = PROFILE_INFO[profile]
    header = w.parse_header(rom)
    start, size = header['arm9_offset'], header['arm9_size']
    raw = rom[start:start + size]
    if w.sha256(raw) != oscorp_resources.ARM9_SHA256:
        raise ValueError('Versioned prices require the exact authored Rush parent')
    result = bytearray(rom)
    edits = []
    groups = [('red', PRICE_TABLE, tuple(range(13, 20)), OLD_PRICES, info['red_prices'])]
    if info['shared_prices']:
        groups.append(('shared', SHARED_PRICE_TABLE, SHARED_BITS, OLD_SHARED_PRICES, info['shared_prices']))
    for group, table, bits, old_prices, prices in groups:
        for row, (bit, old, new) in enumerate(zip(bits, old_prices, prices)):
            offset = table + row * 32 + 28
            if w.u32(raw, offset) != old or w.u32(raw, offset - 28) != bit + 309:
                raise ValueError(f'Native {group} purchase record differs')
            struct.pack_into('<I', result, start + offset, new)
            edits.append({'field': f'{group}_upgrade_price', 'arm9_offset': offset,
                          'ability_bit': bit, 'old': old, 'new': new})
    if w.sha256(result[start:start + size]) != info['arm9_sha256']:
        raise ValueError('Unexpected versioned price ARM9')
    return bytes(result), edits


def generate(output=None):
    import mod
    from tools import combat_profile as cp
    dest = w.safe_output(mod.project_path(output or f'build/version-{VERSION}'))
    if not dest.is_relative_to((mod.ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    rom, glob, manifest = mod.load_clean()
    entries = {e['name']: e for e in manifest['entries']}
    recipe_path = mod.ROOT / 'reference/gameplay_profile.json'
    overlays = mod.overlay_files(mod.ROOT / 'mods', list(entries),
                                 added_names=oscorp_resources.EXTRA_NAMES)
    recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
    current = cp.load_recipe(recipe_path, overlays)
    if current != PARENT_PROFILE or w.sha256(recipe_path.read_bytes()) != PARENT_RECIPE_SHA:
        raise ValueError('Version candidate requires the exact accepted parent recipe')
    if set(overlays) != set(recipe['required_overlays']):
        raise ValueError('Explicit merge required for additional overlays')
    parent, _, _ = mod.create_build(rom, glob, manifest, overlays, gameplay_profile=current)
    if w.sha256(parent) != PARENT_ROM_SHA:
        raise ValueError('Parent release is not the measured current release')
    before = dict(overlays)
    for name in ('English.strings', 'American.strings'):
        e = entries[name]
        clean = glob[e['offset']:e['offset'] + e['size']]
        overlays[name] = StringSlots(clean).repack(overlays[name], TEXT_EDITS)
    for name, data in overlays.items():
        w.atomic_write(dest / 'mods' / name, data, (mod.DEFAULT_ROM,))
    recipe = {'schema_version': 1, 'profile': PROFILE, 'release_version': VERSION,
              'required_overlays': {name: w.sha256(data) for name, data in overlays.items()}}
    w.write_json(dest / 'gameplay_profile.json', recipe)
    result, _, log = mod.create_build(rom, glob, manifest, overlays, gameplay_profile=PROFILE)
    log['release_version'] = VERSION
    path = dest / 'Versioned.nds'
    w.atomic_write(path, result, (mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'), log)
    h = w.parse_header(result)
    report = {'version': VERSION, 'rom_sha256': w.sha256(result),
              'arm9_sha256': w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]),
              'parent_rom_sha256': PARENT_ROM_SHA, 'old_prices': OLD_PRICES, 'prices': PRICES,
              'old_shared_prices': OLD_SHARED_PRICES, 'shared_prices': SHARED_PRICES,
              'text_edits': TEXT_EDITS,
              'unchanged_overlays': [n for n in overlays if overlays[n] == before[n]],
              'qualification': 'Structural candidate; boot/options/buy/refund checks required.'}
    w.write_json(dest / 'release.json', report)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=f'build/version-{VERSION}')
    args = parser.parse_args()
    try:
        print(generate(args.out))
        return 0
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
