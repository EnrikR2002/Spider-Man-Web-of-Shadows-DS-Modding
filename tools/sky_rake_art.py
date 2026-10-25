"""Four continuous airborne talon rakes and a rising flip kick on the native rig."""
from tools.kit_choreography import Clip, author
from tools.gmb import Gmb
from tools.custom_formats import Gab
from tools.grip_compression import CompressedBlob, encode_backrefs
import struct


GUARD = dict(root=(0., 3.92, -.22), pitch=12., yaw=0., spine_pitch=12.,
    hand_l=(1.7, .1, 2.2), hand_r=(-1.7, .1, 2.2),
    foot_l=(1., -2.6, 1.3), foot_r=(-1., -2.1, -.7),
    elbow_l=(2.8, -.3, -.5), elbow_r=(-2.8, -.3, -.5), point_l=.4, point_r=.4)


def rake(name, samples, keys):
    channels = {k: [(0, v), (samples-1, v)] for k, v in GUARD.items()}
    for key, values in keys.items():
        channels[key] = [(0, GUARD.get(key, Clip.CHANNELS[key])), *values,
                         (samples-1, GUARD.get(key, Clip.CHANNELS[key]))]
    return Clip(name, samples, channels)


CLIPS = (
    rake('sky_double_rake', 11, {
        'yaw': [(1, -35.), (3, 30.), (5, 20.), (6, 38.), (8, -32.)],
        'spine_twist': [(1, -22.), (3, 28.), (5, 15.), (6, 28.), (8, -25.)],
        'spine_pitch': [(1, 4.), (3, 22.), (6, 3.), (8, 25.)],
        'hand_l': [(1, (2.6, 1.8, -.8)), (2, (1.4, 1.1, 3.)),
                   (3, (-.4, -.9, 4.1)), (5, (-.2, -1.4, 1.1)), (8, (1.9, -.3, .6))],
        'hand_r': [(1, (-1.8, .2, 2.)), (4, (-2., -.3, 1.)),
                   (6, (-2.7, 1.9, -.7)), (7, (-1.1, 1.0, 3.3)), (8, (.5, -.8, 4.1))],
        'foot_l': [(3, (1.2, -2., 1.7)), (7, (.8, -2.8, 1.))],
        'foot_r': [(3, (-.9, -2.8, -.6)), (8, (-1.1, -1.9, 1.5))],
    }),
    rake('sky_cross_rake', 7, {
        'yaw': [(1, -30.), (3, 32.), (4, 36.)],
        'spine_twist': [(1, -20.), (3, 26.), (4, 28.)],
        'hand_l': [(1, (.7, -1.8, -.8)), (2, (.8, -.8, 3.5)),
                   (3, (.6, 1.7, 4.)), (4, (2.3, 2., .7))],
        'hand_r': [(1, (-1.7, .8, 2.)), (3, (-2.3, -.3, .7)), (4, (-1.6, -.8, 1.4))],
        'foot_l': [(3, (1., -2., 1.7))], 'foot_r': [(3, (-1.1, -2.8, -.5))],
    }),
    rake('sky_backhand_rake', 8, {
        'yaw': [(1, 35.), (3, 10.), (4, -38.), (5, -32.)],
        'spine_twist': [(1, 24.), (4, -28.), (5, -20.)],
        'hand_l': [(1, (1.5, -.6, 1.4)), (4, (2., .4, 1.))],
        'hand_r': [(1, (-.8, -1.6, -.9)), (3, (-.8, -.7, 3.6)),
                   (4, (-.6, 1.5, 4.2)), (5, (-2.5, 2., .6))],
        'foot_l': [(4, (1.1, -2.8, -.6))], 'foot_r': [(4, (-1., -1.8, 1.6))],
    }),
    Clip('sky_rising_flip', 17, {
        **{k: [(0, v), (16, v)] for k, v in GUARD.items()},
        'pitch': [(0, 12.), (2, -28.), (4, -95.), (5, -150.), (7, -240.),
                  (9, -320.), (12, -350.), (16, -348.)],
        'spine_pitch': [(0, 12.), (2, 28.), (5, 14.), (8, 30.), (12, 6.), (16, 12.)],
        'hand_l': [(0, GUARD['hand_l']), (2, (2.4, -1.1, -.3)), (5, (1.8, -.8, 1.7)),
                   (8, (1.2, -1.7, 1.5)), (12, (2.8, .8, .5)), (16, GUARD['hand_l'])],
        'hand_r': [(0, GUARD['hand_r']), (2, (-2.4, -1., -.3)), (5, (-1.8, -.7, 1.6)),
                   (8, (-1.2, -1.6, 1.5)), (12, (-2.8, .8, .5)), (16, GUARD['hand_r'])],
        'foot_l': [(0, GUARD['foot_l']), (2, (.8, -1.5, 1.8)), (4, (.8, -1.6, 1.6)),
                   (7, (.8, -1.3, 1.4)), (12, (1.1, -2.8, .8)), (16, GUARD['foot_l'])],
        'foot_r': [(0, GUARD['foot_r']), (2, (-.7, -1.3, 2.1)), (4, (-.6, -3.6, 1.5)),
                   (5, (-.6, -4., .5)), (6, (-.6, -3.7, -.6)), (8, (-.8, -1.3, 1.2)),
                   (12, (-1., -2.8, -.4)), (16, GUARD['foot_r'])],
    }),
)
CONTACTS = ((3, 8), (3,), (4,), (5,))
TEMPLATES = ('spd_ThrowObjectAir.sca', 'spd_AirAttack3.sca', 'spd_RollDodge.sca', 'spd_AirAttack4.sca')


def resources(names, blobs, parents):
    """Retain native body channels and contact payloads; author only their clocks."""
    extras = {}
    for i, (clip, contacts) in enumerate(zip(CLIPS, CONTACTS), 1):
        base = f'spd_AirAttack{i}'
        sca, _ = author(blobs[names.index(TEMPLATES[i-1])], blobs[names.index('spd_Idle.sca')], parents, clip)
        g = Gmb.parse(CompressedBlob.parse(blobs[names.index(base+'.gmb')]).decoded)
        parts = [struct.pack('<4H', g.unknown_u16_00, clip.samples, len(g.channels), g.unknown_u16_06)]
        for c in g.channels:
            parts.append(struct.pack('<hH', c.kind, c.unknown_u16_02))
            attack = c.kind == 3 and {c.words(f)[5] for f in range(g.record_count)} == {0, 1}
            on = next((r for r in c.records if struct.unpack_from('<i', r, 20)[0] == 1), None) if attack else None
            off = next((r for r in c.records if struct.unpack_from('<i', r, 20)[0] == 0), None) if attack else None
            parts.extend((on if f in contacts else off) if attack else c.records[min(f, g.record_count-1)]
                         for f in range(clip.samples))
        raw = b''.join(parts)
        assert Gmb.parse(raw).to_bytes() == raw
        events = [(1, 1, 5)]
        if i == 1:
            events.append((5, 7, 0))  # A separate native contact collection for the second claw.
        if i == 4:
            events = [(1, 1, 1), (4, 1, 5), (12, 8, 0)]
        gab = b''.join(struct.pack('<3H', *e) for e in events)+b'\xff'*6
        gab += bytes(-len(gab) % 4)
        assert Gab.parse(gab).to_bytes() == gab
        extras.update({f'zz_S35_Air{i}.sca': sca, f'zz_S35_Air{i}.gmb': encode_backrefs(raw),
                       f'zz_S35_Air{i}.gab': gab})
    return extras
