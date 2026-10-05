"""Authored Red-kit clips on the canonical CS5E 37-joint rig; procedural FK/IK.

Clips are keyed in an upright body frame (X = Spidey's left, Y up, Z forward)
relative to the chest (hands) and pelvis (feet), so flips and spins carry the
limbs with the body. Channels use Catmull-Rom curves: velocity stays continuous
through keys, which avoids the stop-start "dance" look of per-key easing.
Stored SCA rotations transpose to column-vector FK (see rush_choreography).
Native bone lengths, fingers and helper joints are retained; no scale edits.
"""
from __future__ import annotations
import math
from .sca import Sca
from .sca_author import repack_samples
from .rush_choreography import (Pose, IDENTITY, ROOT, mm, mv, axis, stored, align, add, sub, mul,
                                unit, length, transpose, tween_rotation, dot)

PELVIS, BACK, CHEST, NECK, HEAD = 1, 2, 3, 4, 5
ARMS = {'l': (7, 8, 9, 1), 'r': (17, 18, 19, -1)}      # shoulder, elbow, wrist, side
LEGS = {'l': (26, 27, 28, 1), 'r': (30, 31, 32, -1)}   # hip, knee, ankle, side


def catmull(keys, t, wrap=None):
    """Catmull-Rom through (time, value) keys; scalars or tuples. Clamped ends."""
    if t <= keys[0][0] and wrap is None: return keys[0][1]
    if t >= keys[-1][0] and wrap is None: return keys[-1][1]
    n = len(keys)
    if wrap:
        t = keys[0][0] + (t - keys[0][0]) % wrap
    for i in range(n - 1):
        (t1, p1), (t2, p2) = keys[i], keys[i + 1]
        if t1 <= t <= t2: break
    else:
        i = n - 2; (t1, p1), (t2, p2) = keys[i], keys[i + 1]
    def at(k):
        if 0 <= k < n: return keys[k]
        if wrap:
            q = keys[k % (n - 1)] if k >= n else keys[(k - 1) % (n - 1)]
            shift = wrap if k >= n else -wrap
            return (q[0] + shift, q[1])
        return keys[max(0, min(n - 1, k))]
    (t0, p0), (t3, p3) = at(i - 1), at(i + 2)
    u = (t - t1) / (t2 - t1) if t2 > t1 else 0.
    def comp(a, b, c, d):
        # Non-uniform Catmull-Rom tangents (time-scaled), Hermite basis.
        m1 = (c - a) / (t2 - t0) * (t2 - t1) if t2 != t0 else 0.
        m2 = (d - b) / (t3 - t1) * (t2 - t1) if t3 != t1 else 0.
        if i == 0 and not wrap: m1 = (c - b)
        if i == n - 2 and not wrap: m2 = (c - b)
        h00 = 2*u**3 - 3*u**2 + 1; h10 = u**3 - 2*u**2 + u; h01 = -2*u**3 + 3*u**2; h11 = u**3 - u**2
        return h00*b + h10*m1 + h01*c + h11*m2
    if isinstance(p1, tuple):
        return tuple(comp(a, b, c, d) for a, b, c, d in zip(p0, p1, p2, p3))
    return comp(p0, p1, p2, p3)


def body_rotation(yaw, pitch, roll):
    """World rotation of the upright body frame: yaw (Y), pitch (+ leans/flips
    forward about X), roll (about Z). Degrees; any magnitude (full flips)."""
    return mm(mm(axis('y', yaw), axis('x', pitch)), axis('z', roll))


class Clip:
    """A keyed clip: channels map to [(sample, value), ...]. See CHANNELS."""
    CHANNELS = {
        'root': (0., 3.92, -.22),          # pelvis position (world units)
        'yaw': 0., 'pitch': 0., 'roll': 0.,
        'spine_pitch': 0., 'spine_twist': 0., 'spine_roll': 0.,
        'head_pitch': 0., 'head_yaw': 0.,
        'hand_l': None, 'hand_r': None,     # chest-relative hand targets
        'elbow_l': (1.6, -.6, -1.4), 'elbow_r': (-1.6, -.6, -1.4),
        'foot_l': None, 'foot_r': None,     # pelvis-relative ankle targets
        'knee_l': (.9, .3, 2.5), 'knee_r': (-.9, .3, 2.5),
        'plant_l': 0., 'plant_r': 0.,       # 1 = ankle held at the world target below
        'world_l': (1.0, .78, 1.5), 'world_r': (-1.0, .78, -1.0),
        'point_l': 0., 'point_r': 0.,       # 1 = toes along the shin (kicks/flips)
    }

    def __init__(self, name, samples, keys, wrap=False):
        self.name, self.samples, self.keys, self.wrap = name, samples, keys, wrap
        unknown = set(keys) - set(self.CHANNELS)
        if unknown: raise ValueError(f'Unknown clip channel {sorted(unknown)}')

    def value(self, channel, sample):
        keys = self.keys.get(channel)
        if not keys: return self.CHANNELS[channel]
        return catmull(keys, sample, self.samples if self.wrap else None)


def safe_ik(p, upper, lower, end, target, pole, fallback):
    """Two-bone IK; if the pole is collinear with the limb, bend toward fallback."""
    _, pos = p.fk()
    v = sub(target, pos[upper]); w = sub(pole, pos[upper])
    if length(v) > 1e-6:
        d = unit(v)
        if length(sub(w, mul(d, dot(w, d)))) < 1e-3: pole = add(pos[upper], fallback)
    return p.ik(upper, lower, end, target, pole)


class Rig:
    def __init__(self, idle, parents):
        self.idle, self.parents = idle, parents
        neutral = Pose(idle, parents)
        self.bind_r, self.bind_p = neutral.fk()
        self.neutral = neutral
        # Default limb targets in the body frames, taken from the native idle.
        pel = self.bind_p[PELVIS]; che = self.bind_p[CHEST]
        rp = transpose(self._frame(neutral, PELVIS)); rc = transpose(self._frame(neutral, CHEST))
        self.rest = {'hand_l': mv(rc, sub(self.bind_p[9], che)), 'hand_r': mv(rc, sub(self.bind_p[19], che)),
                     'foot_l': mv(rp, sub(self.bind_p[28], pel)), 'foot_r': mv(rp, sub(self.bind_p[32], pel))}

    def _frame(self, pose, joint):
        r, _ = pose.fk()
        return mm(r[joint], transpose(self.bind_r[joint]))

    def pose(self, clip, s):
        v = {c: clip.value(c, s) for c in Clip.CHANNELS}
        p = Pose(self.idle, self.parents)
        body = body_rotation(v['yaw'], v['pitch'], v['roll'])
        p.r[0] = IDENTITY; p.t[0] = (0., 0., 0.)
        # Pelvis world rotation = body * native idle pelvis world rotation.
        p.r[PELVIS] = mm(body, self.bind_r[PELVIS]); p.t[PELVIS] = v['root']
        # Spine: bend the two spine joints in the body frame, split between them.
        bend = body_rotation(v['spine_twist'] * .5, v['spine_pitch'] * .5, v['spine_roll'] * .5)
        for joint in (BACK, CHEST):
            r, _ = p.fk(); parent = self.parents[joint]
            frame = mm(r[parent], transpose(self.bind_r[parent]))   # body frame at the parent
            native = mm(r[parent], self.neutral.r[joint])
            p.world_rotation(joint, mm(frame, mm(bend, mm(transpose(frame), native))))
        r, _ = p.fk()
        chest_frame = mm(r[CHEST], transpose(self.bind_r[CHEST]))
        look = body_rotation(v['head_yaw'], v['head_pitch'], 0.)
        p.world_rotation(HEAD, mm(chest_frame, mm(look, self.bind_r[HEAD])))
        # Legs: pelvis-relative ankle targets, optionally planted in world space.
        r, pos = p.fk()
        pelvis_frame = mm(r[PELVIS], transpose(self.bind_r[PELVIS]))
        for side, (hip, knee, ankle, sign) in LEGS.items():
            rel = v['foot_' + side] or self.rest['foot_' + side]
            target = add(pos[PELVIS], mv(pelvis_frame, rel))
            plant = v['plant_' + side]
            if plant > 0: target = add(mul(target, 1 - plant), mul(v['world_' + side], plant))
            pole = add(pos[PELVIS], mv(pelvis_frame, v['knee_' + side]))
            safe_ik(p, hip, knee, ankle, target, pole, mv(pelvis_frame, (0., 0., 3.)))
            r, pos = p.fk()
            foot = mm(pelvis_frame, self.bind_r[ankle])
            if plant > 0: foot = tween_rotation(foot, self.bind_r[ankle], plant)
            point = v['point_' + side]
            if point > 0:
                toe = mv(foot, self.neutral.t[ankle + 1])
                shin = sub(pos[ankle], pos[knee])
                pointed = mm(align(toe, add(unit(shin), mul(unit(toe), .35))), foot)
                foot = tween_rotation(foot, pointed, point)
            p.world_rotation(ankle, foot)
        # Arms: chest-relative wrist targets with elbow poles; knuckles follow the forearm.
        r, pos = p.fk()
        chest_frame = mm(r[CHEST], transpose(self.bind_r[CHEST]))
        for side, (shoulder, elbow, wrist, sign) in ARMS.items():
            rel = v['hand_' + side] or self.rest['hand_' + side]
            target = add(pos[CHEST], mv(chest_frame, rel))
            pole = add(pos[CHEST], mv(chest_frame, v['elbow_' + side]))
            safe_ik(p, shoulder, elbow, wrist, target, pole, mv(chest_frame, (sign * 2., 0., -2.)))
            r, pos = p.fk()
            forward = sub(pos[wrist], pos[elbow])
            hand = mm(chest_frame, self.bind_r[wrist])
            hand = mm(align(mv(hand, (-sign, 0., 0.)), forward), hand)
            p.world_rotation(wrist, hand)
        return p

    def bake(self, clip):
        rotations = {j: [] for j in range(37)}; translations = {j: [] for j in range(37)}; frames = []
        for s in range(clip.samples):
            p = self.pose(clip, s)
            _, pos = p.fk()
            for j in range(37):
                rotations[j].append(stored(p.r[j]))
                translations[j].append(tuple(round(x * 4096) for x in p.t[j]))
            frames.append(pos)
        return rotations, translations, frames


def author(raw, idle_raw, parents, clip):
    """Re-author an existing SCA's samples (same count) from a Clip."""
    a = Sca.parse(raw)
    if a.frame_count != clip.samples or a.joint_count != 37:
        raise ValueError(f'{clip.name}: source has {a.frame_count} samples, clip wants {clip.samples}')
    rig = Rig(Sca.parse(idle_raw), parents)
    rotations, translations, frames = rig.bake(clip)
    return repack_samples(raw, rotations=rotations, translations=translations), frames
