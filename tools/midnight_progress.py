"""Candidate chapter encoding in native flag padding, never a save-file editor.

Native logical flags end at 290. This layout uses bits 291..311 in the final
storage word (stats+0x40). Copied-save round trips prove storage preservation;
allocation remains a publication gate until every native flag access is audited.
"""
from dataclasses import dataclass

MASK = 0x00FFFFF8
MAGIC = 0x004D4C00
VERSION = 1


@dataclass(frozen=True)
class Progress:
    discovered: bool = False
    main_power: bool = False
    completed: bool = False

    def __post_init__(self):
        if any(type(v) is not bool for v in (self.discovered, self.main_power, self.completed)):
            raise ValueError('Chapter milestones must be booleans')
        if (self.main_power and not self.discovered) or (self.completed and not self.main_power):
            raise ValueError('Chapter milestone prerequisites are inconsistent')


def decode(word: int):
    if type(word) is not int or not 0 <= word <= 0xFFFFFFFF:
        raise ValueError('Expected native u32 flag word')
    region = word & MASK
    if not region: return Progress()
    if region & 0x00FFFF00 != MAGIC:
        raise ValueError('Chapter allocation occupied by unknown data')
    if (region >> 6) & 3 != VERSION:
        raise ValueError('Unsupported chapter persistence version')
    return Progress(bool(region & 8), bool(region & 16), bool(region & 32))


def encode(word: int, progress: Progress):
    """Preserve native low flags and all unallocated bits; refuse collisions."""
    decode(word)
    if not isinstance(progress, Progress): raise ValueError('Expected chapter Progress')
    flags = 8 * progress.discovered + 16 * progress.main_power + 32 * progress.completed
    chapter = MAGIC | VERSION << 6 | flags if flags else 0
    return (word & ~MASK) | chapter
