"""Continuous airborne cast, braced two-arm reel and open-claw recovery."""
import struct
from tools.kit_choreography import Clip, author
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob, encode_backrefs


REEL = Clip('hunter_reel_in', 14, {
    'root': [(0, (0., 4.3, .5)), (2, (0., 4.15, .9)), (5, (0., 4.6, -.4)),
             (8, (0., 4.8, -.8)), (10, (0., 4.55, -.2)), (13, (0., 4.3, .5))],
    'pitch': [(0, 16.), (2, 30.), (4, 12.), (7, -18.), (9, -12.), (13, 12.)],
    'yaw': [(0, -14.), (2, 12.), (5, -18.), (8, -32.), (11, -8.), (13, -10.)],
    'spine_pitch': [(0, 12.), (2, 22.), (4, 4.), (7, -18.), (10, -4.), (13, 6.)],
    'spine_twist': [(0, -12.), (2, 18.), (5, -10.), (8, -28.), (13, -10.)],
    'head_pitch': [(0, 8.), (3, 14.), (7, 4.), (10, -6.), (13, -5.)],
    'hand_l': [(0, (1.1, .6, 1.8)), (2, (.6, -1.5, 3.8)), (4, (.7, -1., 3.2)),
               (7, (1.1, -.2, .3)), (9, (1.8, .6, -1.2)), (11, (1.6, 1., -.6)),
               (13, (1.1, .8, 2.2))],
    'hand_r': [(0, (-1.5, .5, -.7)), (3, (-.8, -1.2, 3.4)), (5, (-1., -.7, 2.2)),
               (8, (-1.6, .1, -.8)), (10, (-2.1, .8, -1.1)), (13, (-1.6, .8, -.8))],
    'elbow_l': [(0, (2.5, -.4, -1.)), (3, (2.1, -1.1, 1.2)),
                (8, (2.8, .2, -1.6)), (13, (2.3, -.5, -1.2))],
    'elbow_r': [(0, (-2.4, -.3, -1.5)), (4, (-2.2, -1., 1.)),
                (9, (-2.9, .4, -1.4)), (13, (-2.3, -.5, -1.2))],
    'foot_l': [(0, (.9, -2.5, 1.7)), (3, (.8, -2., 2.2)),
               (7, (.9, -1.7, 2.3)), (10, (1., -2.5, .9)), (13, (.9, -3.2, -.8))],
    'foot_r': [(0, (-.9, -3.6, -1.2)), (3, (-.9, -3.5, -1.8)),
               (7, (-.9, -2.8, -.8)), (10, (-.9, -2., 1.8)), (13, (-.9, -2.3, 2.2))],
    'point_l': [(0, .5), (8, .7), (13, .5)],
    'point_r': [(0, .6), (8, .5), (13, .6)],
})


def resources(names, blobs, parents):
    """Private motion and idle collision only; the utility has no attack boxes."""
    sca, _ = author(blobs[names.index('spd_ThrowObjectAirDown.sca')],
                    blobs[names.index('spd_Idle.sca')], parents, REEL)
    idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    raw = struct.pack('<4H', idle.unknown_u16_00, REEL.samples, len(idle.channels), idle.unknown_u16_06)
    for c in idle.channels:
        raw += struct.pack('<hH', c.kind, c.unknown_u16_02)
        raw += b''.join(c.records[min(f, len(c.records)-1)] for f in range(REEL.samples))
    assert Gmb.parse(raw).to_bytes() == raw
    return {'zz_R36_Reel.sca': sca, 'zz_R36_Reel.gmb': encode_backrefs(raw),
            'zz_R36_Reel.gab': b'\xff'*6+b'\0\0'}
