"""Talon Pounce windup, low tackle and rising rake on the native player rig."""
import struct

from tools.custom_formats import Gab
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob, encode_backrefs
from tools.kit_choreography import Clip, author


READY = {
    'root': (0., 2.55, -1.1), 'pitch': 34., 'yaw': -21., 'roll': -8.,
    'spine_pitch': 13., 'spine_twist': -22., 'head_pitch': -34.,
    'hand_l': (1.95, -.95, 1.45), 'hand_r': (-2.4, .2, -.95),
    'elbow_l': (2.55, -.7, -.1), 'elbow_r': (-2.8, .3, -1.8),
    'foot_l': (1.05, -1.75, 2.25), 'foot_r': (-1.1, -2.5, -.8),
    'world_l': (1.05, .7, 1.75), 'world_r': (-1.05, .7, -2.2),
}
COIL = Clip('pounce_coil', 16, {
    'root': [(0, (0., 3.95, -.4)), (4, (0., 3.23, -.5)), (9, (0., 2.65, -1.2)), (15, READY['root'])],
    'pitch': [(0, -2.), (5, 17.), (10, 29.), (15, READY['pitch'])],
    'yaw': [(0, -25.), (4, -12.), (11, -24.), (15, READY['yaw'])],
    'roll': [(0, -4.), (6, 4.), (12, -11.), (15, READY['roll'])],
    'spine_pitch': [(0, 0.), (7, 21.), (15, READY['spine_pitch'])],
    'spine_twist': [(0, -29.), (5, -8.), (10, -26.), (15, READY['spine_twist'])],
    'head_pitch': [(0, 2.), (6, -25.), (15, READY['head_pitch'])],
    'hand_l': [(0, (1.8, .75, .7)), (5, (2.35, -.25, 1.6)), (10, (2.15, -1.1, 1.15)),
               (15, READY['hand_l'])],
    'hand_r': [(0, (-1.75, .8, -1.6)), (5, (-2.15, -.75, .7)), (10, (-2.7, -.1, -1.1)),
               (15, READY['hand_r'])],
    'elbow_l': [(0, (2.5, -.3, -1.25)), (15, READY['elbow_l'])],
    'elbow_r': [(0, (-2.6, .8, -2.)), (15, READY['elbow_r'])],
    'world_l': [(0, (1.05, .7, 1.55)), (4, READY['world_l']), (15, READY['world_l'])],
    'world_r': [(0, (-1.05, .7, -1.35)), (5, READY['world_r']), (15, READY['world_r'])],
    'plant_l': [(0, 1.)], 'plant_r': [(0, 1.)],
})
QUICK = Clip('pounce_quick', 9, {
    channel: [(sample * 8 / 15, value) for sample, value in keys]
    for channel, keys in COIL.keys.items()
})


def leap(name, **keys):
    """Both trajectories push off from the same planted coil."""
    channels = {key: [(0, value)] for key, value in READY.items()}
    for key, curve in keys.items():
        channels[key] = [(0, READY.get(key, Clip.CHANNELS[key])), *curve]
    channels['plant_l'] = [(0, 1.), (1, .45), (2, 0.)]
    channels['plant_r'] = [(0, 1.), (1, .65), (2, 0.)]
    return Clip(name, 17, channels)


LOW = leap('pounce_low',
    root=[(1, (0., 2.9, -.6)), (3, (0., 3.75, .2)), (6, (0., 3.65, .65)),
          (9, (0., 3.05, .55)), (11, (0., 2.8, .3)), (16, (0., 3.92, -.22))],
    pitch=[(2, 47.), (5, 65.), (7, 60.), (10, 26.), (16, 8.)],
    yaw=[(2, -29.), (5, 14.), (9, 24.), (13, -9.), (16, 0.)],
    roll=[(3, -13.), (8, 11.), (13, 2.), (16, 0.)],
    spine_pitch=[(3, -10.), (7, -16.), (10, 5.), (16, 0.)],
    spine_twist=[(2, -28.), (5, 28.), (8, 17.), (12, -9.), (16, 0.)],
    head_pitch=[(3, -42.), (8, -43.), (12, -22.), (16, 0.)],
    hand_l=[(2, (1.7, 1.1, 2.95)), (5, (1.25, 2.5, 2.25)), (8, (1.3, 2.55, 2.15)),
            (11, (2.4, .3, 1.8)), (16, (1.3, .1, 1.25))],
    hand_r=[(2, (-2.6, -.4, -.3)), (5, (-1.75, 1.9, 2.5)), (8, (-.75, 2.6, 2.55)),
            (11, (-1.6, -.2, 2.55)), (16, (-1.5, .25, -.6))],
    elbow_l=[(3, (2.5, -.1, .2)), (8, (2.5, .85, .15)), (16, (2.25, -.35, -.6))],
    elbow_r=[(3, (-2.5, -.5, -1.)), (7, (-2.65, .9, .35)), (16, (-2.5, -.2, -1.35))],
    foot_l=[(1, (.95, -2.8, 1.7)), (3, (.9, -1.65, 2.25)), (6, (1., -2.5, 1.6)),
            (9, (1.1, -2.05, 2.55)), (11, (1.05, -1.85, 1.95)), (16, (1.05, -3.2, 1.15))],
    foot_r=[(1, (-1.05, -3.65, -1.2)), (4, (-1.1, -3.85, -1.0)), (7, (-.8, -3.15, -.85)),
            (9, (-.95, -2.2, .05)), (11, (-1.05, -2.45, -1.2)), (16, (-1., -3.6, -1.2))],
    point_l=[(3, .55), (6, .95), (10, .1)], point_r=[(2, 1.), (6, .9), (10, .1)],
)
HIGH = leap('pounce_high',
    root=[(1, (0., 3.05, -.65)), (4, (0., 4.5, .25)), (8, (0., 4.55, .35)),
          (12, (0., 4.2, .1)), (16, (0., 3.92, -.22))],
    pitch=[(2, 10.), (4, -19.), (7, -27.), (10, -6.), (13, 22.), (16, 12.)],
    yaw=[(2, -37.), (6, -5.), (9, 24.), (13, -12.), (16, 0.)],
    roll=[(2, -14.), (6, -18.), (10, 15.), (16, 0.)],
    spine_pitch=[(2, -9.), (6, -7.), (10, 10.), (16, 12.)],
    spine_twist=[(2, -26.), (6, 17.), (10, 24.), (16, 0.)],
    head_pitch=[(2, -16.), (5, -13.), (9, -18.), (16, -8.)],
    hand_l=[(2, (1.5, .35, 2.65)), (5, (.9, 3.0, 1.8)), (8, (1.35, 3.05, 1.8)),
            (11, (2.35, .55, 1.55)), (16, (1.7, .1, 2.2))],
    hand_r=[(2, (-2.65, .05, -.8)), (5, (-2., 1.2, 1.85)), (8, (-.95, 3.15, 2.)),
            (12, (-1.8, .8, 2.35)), (16, (-1.7, .1, 2.2))],
    elbow_l=[(4, (2.55, .85, .75)), (8, (2.3, 1.4, .3)), (16, (2.8, -.3, -.5))],
    elbow_r=[(4, (-2.7, .5, -.6)), (8, (-2.4, 1.2, .4)), (16, (-2.8, -.3, -.5))],
    foot_l=[(2, (.95, -1.55, 2.25)), (5, (.95, -1.75, 2.4)), (8, (1., -2.45, 2.2)),
            (13, (1.1, -2.65, 1.65)), (16, (1., -2.6, 1.3))],
    foot_r=[(2, (-.95, -3.7, -.95)), (5, (-1., -3.7, -1.4)), (8, (-1.05, -3.2, -1.3)),
            (13, (-.95, -2.15, -.75)), (16, (-1., -2.1, -.7))],
    point_l=[(4, .75), (8, .8), (16, .4)], point_r=[(2, 1.), (8, .9), (16, .4)],
)
CLIPS = (COIL, QUICK, LOW, HIGH)
PARTS = ('Coil', 'Quick', 'Low', 'High')
TEMPLATES = ('spd_Crawl.sca', 'spd_GroundAttack5.sca', 'spd_AirAttack4.sca', 'spd_AirAttack4.sca')


def resources(names, blobs, parents):
    """Keep native body collision, with a forward volume only during the rake."""
    idle = blobs[names.index('spd_Idle.sca')]
    native = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    result = {}
    for part, clip, template in zip(PARTS, CLIPS, TEMPLATES):
        stem = 'zz_P42_' + part
        flight = part in ('Low', 'High')
        result[stem+'.sca'], _ = author(blobs[names.index(template)], idle, parents, clip)
        parts = [struct.pack('<4H', native.unknown_u16_00, clip.samples, len(native.channels), native.unknown_u16_06)]
        for c in native.channels:
            parts.append(struct.pack('<hH', c.kind, c.unknown_u16_02))
            if c.kind == 3 and c.words(0)[7] == 0x2000:
                high = part == 'High'
                cy, reach, width = (0x6600, 0x2400, 0x1400) if high else (0x4600, 0x4000, 0x2800)
                parts.extend(struct.pack('<8i', 0, cy, min(reach, 0x2000+f*0x700),
                                         0x5c00, width, int(flight and 1 <= f <= 10), 0, 0x2000)
                             for f in range(clip.samples))
            else:
                parts.append(c.records[0] * clip.samples)
        raw = b''.join(parts)
        assert Gmb.parse(raw).to_bytes() == raw
        result[stem+'.gmb'] = encode_backrefs(raw)
        events = ((1, 1, 1), (3, 1, 5)) if flight else ((clip.samples-2, 1, 19),)
        gab = b''.join(struct.pack('<3H', *event) for event in events) + b'\xff'*6
        gab += bytes(-len(gab) % 4)
        assert Gab.parse(gab).to_bytes() == gab
        result[stem+'.gab'] = gab
    return result
