"""Lossless DeSmuME v0 DSV wrapper; the game's battery payload stays opaque.

Format source: TASEmulators/desmume, desmume/doc/dsv.txt and src/mc.cpp.
Only the footer is interpreted. This does not validate game checksums/progress.
"""
from dataclasses import dataclass
import struct

COOKIE = b'|-DESMUME SAVE-|'


@dataclass(frozen=True)
class Dsv:
    raw: bytes
    footer_words: tuple[int, ...]
    payload: bytes
    middle: bytes

    @classmethod
    def parse(cls, raw: bytes):
        if len(raw) < 40 or raw[-16:] != COOKIE:
            raise ValueError('Missing DeSmuME DSV footer/cookie')
        words = struct.unpack('<6I', raw[-40:-16])
        written, padded, _, address_size, _, version = words
        if version != 0:
            raise ValueError('Unsupported DeSmuME DSV version')
        if not 0 < padded <= len(raw) - 40 or written > padded:
            raise ValueError('DeSmuME DSV payload/footer sizes are inconsistent')
        if address_size not in (1, 2, 3):
            raise ValueError('Unsupported DeSmuME DSV address size')
        return cls(raw, words, raw[:padded], raw[padded:-40])

    def to_bytes(self):
        return self.raw
