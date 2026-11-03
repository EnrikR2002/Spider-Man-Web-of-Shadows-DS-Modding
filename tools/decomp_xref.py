"""Query the external EUR decomp's function table and call graph at USA CS5E addresses.

Reads dsd `symbols.txt`/`relocs.txt` from a private checkout of
github.com/liolu/spider-man-web-of-shadows-decomp (EUR CS5X, documented at
commit d5b8e42) under work/decomp; never copy its files into this repository.
USA ARM9/ITCM code equals EUR below EUR 0x02084AA4 and is EUR-4 from there to
the end of .init (one shorter literal pool in the title-language switch).
Data, rodata and BSS do not map linearly: check each one in the USA bytes.
`verify` re-checks every call relocation against the clean USA ARM9
(work/rom/arm9.bin from `python mod.py extract`). See TECHNICAL
"External EUR decompilation".
"""
from __future__ import annotations

import argparse
import bisect
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SHIFT_AT = 0x02084AA4    # first EUR main-code address that is 4 bytes lower in USA
CODE_END = 0x021193C0    # EUR end of .init; .rodata/.data/.bss are not mapped
ITCM, ITCM_END = 0x01FF8000, 0x02000000
ITCM_SOURCE = 0x13E140   # ITCM image offset inside the USA ARM9 binary


def usa(eur: int) -> int:
    """USA address of a EUR code address; data addresses raise."""
    if ITCM <= eur < SHIFT_AT: return eur
    if SHIFT_AT <= eur < CODE_END: return eur - 4
    raise ValueError(f'{eur:#x} is not decomp code; map data by reading USA literals')


def eur(address: int) -> int:
    """EUR address of a USA code address."""
    return address if address < SHIFT_AT - 4 else address + 4


def load(config: Path):
    """Return (sorted [(usa_start, size, eur_name)], [(from, kind, eur_to, module, from_is_usa_code)]).

    Relocations sourced in data (vtables, pointer tables) keep their EUR from address.
    """
    funcs = []
    relocs = []
    for sub in ('', 'itcm/'):
        text = (config / f'{sub}symbols.txt').read_text(encoding='utf-8')
        for name, size, at in re.findall(r'^(\S+) kind:function\(\w+,size=0x([0-9a-f]+)\) addr:0x([0-9a-f]+)', text, re.M):
            funcs.append((usa(int(at, 16)), int(size, 16), name))
        text = (config / f'{sub}relocs.txt').read_text(encoding='utf-8')
        for frm, kind, to, module in re.findall(r'from:0x([0-9a-f]+) kind:(\w+) to:0x([0-9a-f]+)(?: add:\S+)? module:(\w+)', text):
            frm = int(frm, 16)
            code = ITCM <= frm < CODE_END
            relocs.append((usa(frm) if code else frm, kind, int(to, 16), module, code))
    return sorted(funcs), relocs


def owner(funcs, address: int):
    i = bisect.bisect_right(funcs, (address, 1 << 32)) - 1
    return funcs[i] if i >= 0 and address < funcs[i][0] + funcs[i][1] else None


def word(arm9: bytes, address: int) -> int:
    offset = address - 0x02000000 if address >= ITCM_END else ITCM_SOURCE + address - ITCM
    return struct.unpack_from('<I', arm9, offset)[0]


def verify(arm9: bytes, relocs) -> dict:
    """Count ARM BL/B relocations whose USA instruction reaches the mapped target."""
    counts = {'ok': 0, 'bad': 0}
    for frm, kind, to, _, code in relocs:
        if not code or kind not in ('arm_call', 'arm_branch'): continue
        w = word(arm9, frm)
        target = frm + 8 + (((w & 0xFFFFFF) ^ 0x800000) - 0x800000) * 4
        counts['ok' if (w >> 25) & 7 == 5 and target == usa(to) else 'bad'] += 1
    return counts


def callers(funcs, relocs, address: int):
    """Owning functions of code relocations that target a USA address."""
    hits = {((owner(funcs, frm) if code else None) or (frm, 0, '?' if code else 'eur-data'))[0:3:2] + (kind,)
            for frm, kind, to, m, code in relocs
            if m in ('main', 'itcm') and ITCM <= to < CODE_END and usa(to) == address}
    return sorted(hits)


def callees(funcs, relocs, address: int):
    """Relocation targets inside the function owning a USA address (data stays EUR)."""
    f = owner(funcs, address)
    if not f: raise ValueError(f'{address:#x} is not inside a decomp function')
    out = []
    for frm, kind, to, m, from_code in relocs:
        if from_code and f[0] <= frm < f[0] + f[1]:
            code = m in ('main', 'itcm') and ITCM <= to < CODE_END and kind != 'load'
            out.append((frm, kind, usa(to) if code else to, 'usa' if code else f'eur-{m}'))
    return f, out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('command', choices=('verify', 'func', 'callers', 'callees'))
    parser.add_argument('address', nargs='?', help='USA hex address (func/callers/callees)')
    parser.add_argument('--decomp', type=Path, default=ROOT / 'work/decomp', help='decomp checkout (default work/decomp)')
    parser.add_argument('--arm9', type=Path, default=ROOT / 'work/rom/arm9.bin')
    args = parser.parse_args(argv)
    funcs, relocs = load(args.decomp / 'config/x/arm9')
    if args.command == 'verify':
        print(len(funcs), 'functions;', verify(args.arm9.read_bytes(), relocs)); return
    if not args.address: parser.error('address required')
    address = int(args.address, 16)
    f = owner(funcs, address)
    print(f'{address:#010x} in ' + (f'{f[2]} usa {f[0]:#010x} size {f[1]:#x}' if f else 'no decomp function'))
    if args.command == 'callers':
        for start, name, kind in callers(funcs, relocs, address): print(f'  {start:#010x} {name} {kind}')
    elif args.command == 'callees':
        for frm, kind, to, space in callees(funcs, relocs, address)[1]: print(f'  {frm:#010x} {kind} -> {to:#010x} {space}')


if __name__ == '__main__':
    main()
