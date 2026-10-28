"""Continuous shoulder cling, crossing talon rake, two-arm rip and kick-off."""
import struct
from tools.kit_choreography import Clip, author
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob, encode_backrefs


HOLD_POSE = {
    'root': (0., 2.6, .3), 'pitch': 24., 'yaw': -18., 'spine_pitch': 18.,
    'spine_twist': -16., 'head_pitch': -18.,
    'hand_l': (1.2, -.5, 2.8), 'hand_r': (-1.1, -.2, 2.6),
    'elbow_l': (2.7, -.5, .5), 'elbow_r': (-2.5, -.6, .2),
    'foot_l': (1., -2., 1.8), 'foot_r': (-1., -2.4, -1.4),
    'point_l': .2, 'point_r': .2,
}

LATCH = Clip('boarding_latch', 6, {
    'root': [(0, (0., 3.8, -.5)), (2, (0., 3.4, .4)), (3, (0., 2.9, .8)), (5, HOLD_POSE['root'])],
    'pitch': [(0, -12.), (2, 8.), (3, 32.), (5, 24.)],
    'yaw': [(0, 12.), (2, -26.), (5, -18.)],
    'spine_pitch': [(0, -8.), (2, 12.), (3, 26.), (5, 18.)],
    'spine_twist': [(0, 10.), (2, -24.), (5, -16.)],
    'head_pitch': [(0, -10.), (3, -26.), (5, -18.)],
    'hand_l': [(0, (1.4, .4, 1.4)), (2, (1.5, 1.9, 3.3)), (3, (.8, .5, 3.5)), (5, HOLD_POSE['hand_l'])],
    'hand_r': [(0, (-1.5, .3, -.8)), (2, (-1.4, 1.6, 3.1)), (3, (-.9, .6, 3.2)), (5, HOLD_POSE['hand_r'])],
    'elbow_l': [(0, (2.5, -.4, -.5)), (2, (2.8, .5, 1.)), (5, HOLD_POSE['elbow_l'])],
    'elbow_r': [(0, (-2.6, -.5, -1.)), (2, (-2.8, .1, .8)), (5, HOLD_POSE['elbow_r'])],
    'foot_l': [(0, (.9, -3.2, 1.2)), (2, (1., -1.5, 2.)), (5, HOLD_POSE['foot_l'])],
    'foot_r': [(0, (-.9, -3.2, -1.)), (2, (-1., -2.2, -2.)), (5, HOLD_POSE['foot_r'])],
    'point_l': [(0, .8), (2, 1.), (5, .2)], 'point_r': [(0, .8), (2, 1.), (5, .2)],
})

HOLD = Clip('boarding_hold', 24, {
    key: [(0, value), (12, (value[0], value[1]+.12, value[2]) if isinstance(value, tuple) else value+1.), (23, value)]
    for key, value in HOLD_POSE.items()
})

RAKE = Clip('boarding_rake', 14, {
    **{key: [(0, value), (13, value)] for key, value in HOLD_POSE.items()},
    'root': [(0, HOLD_POSE['root']), (3, (0., 2.9, -.1)), (6, (0., 2.3, 1.)), (10, (0., 2.4, .9)), (13, HOLD_POSE['root'])],
    'yaw': [(0, -18.), (3, -48.), (6, 38.), (10, 14.), (13, -18.)],
    'spine_twist': [(0, -16.), (3, -32.), (6, 32.), (10, 12.), (13, -16.)],
    'hand_l': [(0, HOLD_POSE['hand_l']), (3, (2.6, 1.4, -.6)), (5, (2., .7, 2.6)), (7, (-1.3, -1.8, 3.3)), (10, (.3, -1.1, 2.7)), (13, HOLD_POSE['hand_l'])],
    'elbow_l': [(0, HOLD_POSE['elbow_l']), (3, (3.1, .5, -1.5)), (6, (1.8, -.1, 1.8)), (10, (2.4, -.7, 1.1)), (13, HOLD_POSE['elbow_l'])],
    'hand_r': [(0, HOLD_POSE['hand_r']), (4, (-1., -.5, 2.9)), (8, (-1.3, -.8, 2.5)), (13, HOLD_POSE['hand_r'])],
    'point_l': [(0, .2), (3, 1.), (8, .8), (13, .2)],
})

RIP = Clip('boarding_rip', 15, {
    **{key: [(0, value), (14, value)] for key, value in HOLD_POSE.items()},
    'root': [(0, HOLD_POSE['root']), (3, (0., 2.3, 1.)), (7, (0., 2.6, 1.2)), (10, (0., 3.6, -.9)), (14, (0., 3.2, -1.))],
    'pitch': [(0, 24.), (4, 42.), (7, 24.), (11, -28.), (14, -14.)],
    'yaw': [(0, -18.), (4, -4.), (8, 16.), (11, -24.), (14, -34.)],
    'spine_pitch': [(0, 18.), (4, 28.), (8, 8.), (11, -22.), (14, -12.)],
    'hand_l': [(0, HOLD_POSE['hand_l']), (3, (.8, -.9, 3.4)), (7, (.7, -.7, 3.3)), (10, (2.7, 1., -.9)), (14, (2.3, .6, -1.4))],
    'hand_r': [(0, HOLD_POSE['hand_r']), (4, (-.7, -.8, 3.3)), (7, (-.8, -.5, 3.1)), (11, (-2.8, .7, -1.)), (14, (-2.3, .4, -1.5))],
    'elbow_l': [(0, HOLD_POSE['elbow_l']), (5, (2.2, -1., 1.6)), (11, (3.1, .1, -1.7)), (14, (2.8, -.3, -1.5))],
    'elbow_r': [(0, HOLD_POSE['elbow_r']), (5, (-2.1, -.9, 1.5)), (11, (-3.1, -.1, -1.8)), (14, (-2.8, -.4, -1.6))],
    'foot_l': [(0, HOLD_POSE['foot_l']), (7, (1., -1.8, 2.2)), (11, (1., -2.7, 1.8)), (14, (1., -2.8, 1.9))],
    'foot_r': [(0, HOLD_POSE['foot_r']), (8, (-1., -2., .4)), (12, (-1., -2.7, 1.6)), (14, (-1., -2.7, 1.8))],
    'point_l': [(0, .2), (5, .2), (11, 1.), (14, .8)], 'point_r': [(0, .2), (6, .2), (11, 1.), (14, .8)],
})

KICK = Clip('boarding_kick', 16, {
    'root': [(0, (0., 3.2, -1.)), (4, (0., 3.6, -1.3)), (9, (0., 4., -.8)), (15, (0., 3.92, -.22))],
    'pitch': [(0, -14.), (4, -48.), (9, -26.), (15, 0.)],
    'yaw': [(0, -34.), (5, -46.), (10, -20.), (15, 0.)],
    'spine_pitch': [(0, -12.), (5, -24.), (10, -8.), (15, 0.)],
    'spine_twist': [(0, -16.), (6, -28.), (15, 0.)],
    'hand_l': [(0, (2.3, .6, -1.4)), (5, (2.5, 1., -.8)), (10, (1.9, .9, .8)), (15, (1.3, .4, 1.5))],
    'hand_r': [(0, (-2.3, .4, -1.5)), (5, (-2.6, .7, -1.1)), (10, (-2., .5, -.8)), (15, (-1.5, .3, -.6))],
    'foot_l': [(0, (1., -2.8, 1.9)), (3, (.9, -2.8, 3.)), (7, (1., -1.8, 2.6)), (15, (.9, -3.2, 1.2))],
    'foot_r': [(0, (-1., -2.7, 1.8)), (4, (-1., -2.7, 2.9)), (9, (-.9, -1.9, .4)), (15, (-.9, -3.2, -1.))],
    'point_l': [(0, .8), (15, .2)], 'point_r': [(0, .8), (15, .2)],
})

CLIPS = (LATCH, HOLD, RAKE, RIP, KICK)
PARTS = ('Latch', 'Hold', 'Rake', 'Rip', 'Kick')


def resources(names, blobs, parents):
    """Keep native idle collision and build damage only at authored talon contacts."""
    idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    result = {}
    templates = ('spd_AirAttack1.sca', 'spd_GroundAttack6.sca',
        'spd_BreakingOutOfGrapple.sca', 'spd_FallHolding.sca', 'spd_Crawl.sca')
    for part, clip, template in zip(PARTS, CLIPS, templates):
        stem = 'zz_B38_'+part
        for side, sign in (('', -1), ('Left', 1)):
            keys = dict(clip.keys)
            keys['root'] = [(f, (sign*8.5*(min(f/4, 1) if part == 'Latch' else
                max(0, (clip.samples-1-f)/5) if part == 'Kick' and f > clip.samples-6 else 1), y, z))
                for f, (_, y, z) in clip.keys['root']]
            visible = Clip(clip.name+side, clip.samples, keys)
            result[stem+side+'.sca'], _ = author(blobs[names.index(template)],
                blobs[names.index('spd_Idle.sca')], parents, visible)
        raw = struct.pack('<4H', idle.unknown_u16_00, clip.samples, len(idle.channels), idle.unknown_u16_06)
        for channel in idle.channels:
            raw += struct.pack('<hH', channel.kind, channel.unknown_u16_02)
            raw += b''.join(channel.records[min(f, len(channel.records)-1)] for f in range(clip.samples))
        assert Gmb.parse(raw).to_bytes() == raw
        result[stem+'.gmb'] = encode_backrefs(raw)
        result[stem+'.gab'] = b'\xff'*6+b'\0\0'
    return result
