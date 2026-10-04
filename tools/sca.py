"""Lossless CS5E SCA4 joint-animation layout and bounded pose edits.

Fixed timing, pool sizes, track descriptors, unknown header bytes and alignment
bytes are preserved. Rotation editing rejects constant or aliased tracks. This
does not edit movement physics, hit events, purchase routes or animation timing.
Original loader/sampler evidence: docs/ANIMATION_RESEARCH.md.
"""
from dataclasses import dataclass
import math
import struct

MAGIC = b'4ACS'
Q12 = 4096


def align4(value):
    return (value + 3) & ~3


def _matrix(values):
    values = tuple(values)
    if len(values) != 9 or any(type(v) is not int or not -32768 <= v <= 32767 for v in values):
        raise ValueError('Rotation requires nine signed Q12 int16 matrix entries')
    return values


def rotation_q12(axis, degrees):
    """Construct an ordinary 3x3 axis rotation; calibrate model axis/sign in-game."""
    if axis not in ('x', 'y', 'z') or not isinstance(degrees, (int, float)) or not math.isfinite(degrees):
        raise ValueError('Expected x/y/z axis and a finite angle')
    angle = math.radians(degrees)
    cosine, sine = round(math.cos(angle) * Q12), round(math.sin(angle) * Q12)
    return {
        'x': (Q12, 0, 0, 0, cosine, -sine, 0, sine, cosine),
        'y': (cosine, 0, sine, 0, Q12, 0, -sine, 0, cosine),
        'z': (cosine, -sine, 0, sine, cosine, 0, 0, 0, Q12),
    }[axis]


def multiply_q12(left, right):
    """Multiply two row-indexed 3x3 matrices with nearest Q12 integer rounding."""
    left, right = _matrix(left), _matrix(right)
    return _matrix((sum(left[3 * row + k] * right[3 * k + column] for k in range(3)) + 2048) >> 12
                   for row in range(3) for column in range(3))


@dataclass(frozen=True)
class Pool:
    translations: tuple[tuple[int, ...], ...]
    scales: tuple[tuple[int, ...], ...]
    rotations: tuple[tuple[int, ...], ...]
    padding: bytes

    @classmethod
    def parse(cls, raw, start, counts, end):
        position, groups = start, []
        for count, fmt in zip(counts, ('<3i', '<6i', '<9h')):
            size = struct.calcsize(fmt)
            groups.append(tuple(struct.unpack_from(fmt, raw, position + i * size) for i in range(count)))
            position += count * size
        if position > end:
            raise ValueError('SCA pool extends beyond its declared boundary')
        return cls(*groups, raw[position:end])

    def to_bytes(self):
        return b''.join(struct.pack(fmt, *entry)
                        for group, fmt in zip((self.translations, self.scales, self.rotations), ('<3i', '<6i', '<9h'))
                        for entry in group) + self.padding


@dataclass(frozen=True)
class Sca:
    header: bytes
    frame_count: int
    joint_count: int
    static_pool_size: int
    frame_stride: int
    counts: tuple[int, ...]
    descriptors: tuple[tuple[int, int, int], ...]
    descriptor_padding: bytes
    static_pool_start: int
    frames_start: int
    static_pool: Pool
    frames: tuple[Pool, ...]

    @classmethod
    def parse(cls, raw: bytes):
        if len(raw) < 28 or len(raw) % 4 or raw[:4] != MAGIC:
            raise ValueError('Expected an aligned CS5E SCA4 animation')
        frame_count, joint_count, pool_size, stride = struct.unpack_from('<4I', raw, 4)
        if not 1 <= frame_count <= 65535 or not 1 <= joint_count <= 65535:
            raise ValueError('SCA counts exceed the original loader u16 range')
        counts = tuple(raw[20:26])
        expected_pool = counts[0] * 12 + counts[1] * 24 + counts[2] * 18
        expected_stride = align4(counts[3] * 12 + counts[4] * 24 + counts[5] * 18)
        if pool_size != expected_pool or stride != expected_stride:
            raise ValueError('SCA pool size / frame stride does not match channel counts')
        static_start = 28 + align4(joint_count * 3)
        frames_start = static_start + align4(pool_size)
        if frames_start + frame_count * stride != len(raw):
            raise ValueError('SCA section bounds do not exactly account for the file')
        descriptors = tuple(struct.unpack_from('<BBB', raw, 28 + i * 3) for i in range(joint_count))
        for descriptor in descriptors:
            for channel, value in enumerate(descriptor):
                count = counts[(0, 2, 1)[channel] + (0 if value & 1 else 3)]
                if value >> 1 >= count:
                    raise ValueError('SCA joint descriptor references a nonexistent channel')
        return cls(raw[:28], frame_count, joint_count, pool_size, stride, counts, descriptors,
                   raw[28 + joint_count * 3:static_start], static_start, frames_start,
                   Pool.parse(raw, static_start, counts[:3], frames_start),
                   tuple(Pool.parse(raw, frames_start + i * stride, counts[3:], frames_start + (i + 1) * stride)
                         for i in range(frame_count)))

    def to_bytes(self):
        return (self.header + b''.join(struct.pack('<BBB', *d) for d in self.descriptors)
                + self.descriptor_padding + self.static_pool.to_bytes()
                + b''.join(frame.to_bytes() for frame in self.frames))

    def track(self, joint, channel='rotation'):
        if type(joint) is not int or not 0 <= joint < self.joint_count:
            raise ValueError('Joint index outside the parsed animation')
        if channel not in ('translation', 'rotation', 'scale'):
            raise ValueError('Expected translation/rotation/scale channel')
        component = ('translation', 'rotation', 'scale').index(channel)
        value = self.descriptors[joint][component]
        return {'static': bool(value & 1), 'index': value >> 1,
                'joints': tuple(i for i, descriptor in enumerate(self.descriptors) if descriptor[component] == value)}

    def rotation(self, joint, frame):
        self._check_frame(frame)
        track = self.track(joint)
        pool = self.static_pool if track['static'] else self.frames[frame]
        return pool.rotations[track['index']]

    def _check_frame(self, frame):
        if type(frame) is not int or not 0 <= frame < self.frame_count:
            raise ValueError('Frame index outside the parsed animation')

    def rotation_offset(self, joint, frame):
        """Locate the selected matrix without changing storage or track aliases."""
        self._check_frame(frame)
        track = self.track(joint)
        counts = self.counts[:3] if track['static'] else self.counts[3:]
        start = self.static_pool_start if track['static'] else self.frames_start + frame * self.frame_stride
        return start + counts[0] * 12 + counts[1] * 24 + track['index'] * 18

    def replace_rotation(self, joint, frame, values):
        """Change one independent dynamic matrix; reject constant/shared tracks."""
        matrix = _matrix(values)
        self._check_frame(frame)
        track = self.track(joint)
        if track['static']:
            raise ValueError('Constant rotation spans all frames; keep it unchanged')
        if track['joints'] != (joint,):
            raise ValueError('Rotation track is shared by multiple joints; keep its aliases unchanged')
        data = bytearray(self.to_bytes())
        offset = self.rotation_offset(joint, frame)
        struct.pack_into('<9h', data, offset, *matrix)
        output = bytes(data)
        if Sca.parse(output).rotation(joint, frame) != matrix:
            raise ValueError('Edited SCA rotation failed round trip')
        return output

    def rotate_joint(self, joint, frame, axis, degrees, side='right'):
        """Compose a bounded pose delta; side/axis orientation need visual calibration."""
        if side not in ('left', 'right'):
            raise ValueError('Matrix composition side must be left or right')
        original, delta = self.rotation(joint, frame), rotation_q12(axis, degrees)
        matrix = multiply_q12(original, delta) if side == 'right' else multiply_q12(delta, original)
        return self.replace_rotation(joint, frame, matrix)
