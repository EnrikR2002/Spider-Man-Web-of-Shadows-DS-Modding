"""Continuous reaching grab, tucked forward flip, descending drive and planted impact."""
import struct
from tools.kit_choreography import Clip, author
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob, encode_backrefs


CATCH = Clip('meteor_catch', 18, {
    'root': [(0, (0., 4.3, .2)), (3, (0., 4.4, 1.)), (7, (0., 4.8, .4)),
             (11, (0., 4.5, -.1)), (14, (0., 4.1, .5)), (17, (0., 3.7, .9))],
    'pitch': [(0, 8.), (3, 48.), (7, 163.), (11, 282.), (14, 350.), (17, 390.)],
    'yaw': [(0, -12.), (4, 8.), (8, 14.), (12, -8.), (17, -20.)],
    'spine_pitch': [(0, 8.), (3, 14.), (7, 24.), (11, 20.), (14, 10.), (17, 14.)],
    'spine_twist': [(0, -12.), (5, 12.), (11, -8.), (17, -18.)],
    'head_pitch': [(0, -8.), (4, 10.), (10, 18.), (14, -10.), (17, -16.)],
    'hand_l': [(0, (1.5, .8, 2.2)), (3, (.6, 1., 3.7)), (7, (.7, .4, 2.5)),
               (11, (.8, .3, 2.3)), (14, (.7, -1.1, 3.1)), (17, (.9, -1.9, 2.8))],
    'hand_r': [(0, (-1.9, .2, -.8)), (3, (-.7, .7, 3.5)), (7, (-.8, .3, 2.3)),
               (11, (-.8, .3, 2.2)), (14, (-.8, -1.2, 3.)), (17, (-1., -1.8, 2.6))],
    'elbow_l': [(0, (2.5, -.4, -.7)), (4, (2.2, -.4, 1.6)), (10, (2.2, 0., 1.)), (17, (2.1, -1., .7))],
    'elbow_r': [(0, (-2.6, -.4, -1.2)), (4, (-2.3, -.5, 1.5)), (10, (-2.2, 0., .8)), (17, (-2.2, -1., .6))],
    'foot_l': [(0, (.9, -2.4, 1.6)), (4, (.9, -1.4, 2.2)), (8, (.9, -.9, 2.)),
               (12, (.9, -1.3, 2.)), (15, (.9, -2.1, 1.6)), (17, (1., -2.5, 1.4))],
    'foot_r': [(0, (-.9, -3.6, -1.4)), (4, (-.9, -1.7, 1.1)), (8, (-.9, -1., 1.7)),
               (12, (-.9, -1.6, .5)), (15, (-.9, -3., -1.2)), (17, (-1., -3., -1.8))],
    'point_l': [(0, .5), (8, .8), (17, .2)],
    'point_r': [(0, .7), (8, .8), (17, .3)],
})

DIVE = Clip('meteor_dive', 24, {
    'root': [(0, (0., 3.7, .9)), (8, (0., 3.6, 1.)), (16, (0., 3.7, .9)), (23, (0., 3.7, .9))],
    'pitch': [(0, 30.), (8, 34.), (16, 30.), (23, 30.)],
    'yaw': [(0, -20.), (12, -22.), (23, -20.)],
    'spine_pitch': [(0, 14.), (12, 16.), (23, 14.)],
    'spine_twist': [(0, -18.), (23, -18.)],
    'head_pitch': [(0, -16.), (23, -16.)],
    'hand_l': [(0, (.9, -1.9, 2.8)), (23, (.9, -1.9, 2.8))],
    'hand_r': [(0, (-1., -1.8, 2.6)), (23, (-1., -1.8, 2.6))],
    'elbow_l': [(0, (2.1, -1., .7)), (23, (2.1, -1., .7))],
    'elbow_r': [(0, (-2.2, -1., .6)), (23, (-2.2, -1., .6))],
    'foot_l': [(0, (1., -2.5, 1.4)), (23, (1., -2.5, 1.4))],
    'foot_r': [(0, (-1., -3., -1.8)), (23, (-1., -3., -1.8))],
    'point_l': [(0, .2), (23, .2)], 'point_r': [(0, .3), (23, .3)],
})

IMPACT = Clip('meteor_impact', 10, {
    'root': [(0, (0., 5.6, .5)), (2, (0., 5., .8)), (5, (0., 5.1, .4)), (9, (0., 3.92, -.22))],
    'pitch': [(0, 22.), (2, 28.), (5, 15.), (9, 0.)],
    'yaw': [(0, -20.), (3, -28.), (6, -12.), (9, 0.)],
    'spine_pitch': [(0, 16.), (2, 22.), (5, 8.), (9, 0.)],
    'spine_twist': [(0, -18.), (3, -12.), (9, 0.)],
    'head_pitch': [(0, -16.), (3, -10.), (6, -12.), (9, 0.)],
    'hand_l': [(0, (.9, -1.9, 2.8)), (2, (1., -2.5, 2.6)), (5, (1.4, -.6, 1.8)), (9, (1.3, .4, 1.5))],
    'hand_r': [(0, (-1., -1.8, 2.6)), (2, (-1.2, -2.3, 2.4)), (5, (-1.8, -.4, .4)), (9, (-1.5, .3, -.6))],
    'foot_l': [(0, (1., -2.5, 1.4)), (3, (1., -2.4, 1.7)), (9, (.9, -3.2, 1.2))],
    'foot_r': [(0, (-1., -3., -1.8)), (3, (-1., -2.6, -1.4)), (9, (-.9, -3.2, -1.))],
    'plant_l': [(0, .9), (9, 1.)], 'world_l': [(0, (1., .78, 2.1)), (9, (1., .78, 2.1))],
    'plant_r': [(0, .5), (4, 1.), (9, 1.)], 'world_r': [(0, (-1., .78, -1.7)), (9, (-1., .78, -1.7))],
})
CLIPS = (CATCH, DIVE, IMPACT)


def grip_path(idle, parents):
    """Mean authored wrists, including the existing 12.5% Black render-height scale."""
    from tools.kit_choreography import Rig
    from tools.sca import Sca
    frames = Rig(Sca.parse(idle), parents).bake(CATCH)[2]
    return b''.join(struct.pack('<3i', *(round((pose[9][axis]+pose[19][axis])*.5*scale)
        for axis, scale in enumerate((4096, 4608, 4096)))) for pose in frames)


def resources(names, blobs, parents):
    """Private clips retain native idle collision; only the actual floor impact builds damage."""
    idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    result = {}
    for part, clip, template in zip(('Catch', 'Dive', 'Impact'), CLIPS,
                                   ('spd_GroundAttack1.sca', 'spd_HammerSlamDive.sca', 'spd_GrapplePullAttack.sca')):
        stem = 'zz_M37_'+part
        result[stem+'.sca'], _ = author(blobs[names.index(template)],
                                        blobs[names.index('spd_Idle.sca')], parents, clip)
        raw = struct.pack('<4H', idle.unknown_u16_00, clip.samples, len(idle.channels), idle.unknown_u16_06)
        for channel in idle.channels:
            raw += struct.pack('<hH', channel.kind, channel.unknown_u16_02)
            raw += b''.join(channel.records[min(f, len(channel.records)-1)] for f in range(clip.samples))
        assert Gmb.parse(raw).to_bytes() == raw
        result[stem+'.gmb'] = encode_backrefs(raw)
        result[stem+'.gab'] = b'\xff'*6+b'\0\0'
    return result
