"""Recover the game's C++ classes, inheritance and vtables from the ARM9's own RTTI.

The CS5E ARM9 keeps Itanium-ABI run-time type information: every polymorphic
class has a type_info record {vptr, mangled-name pointer, bases}, and every
vtable is [offset-to-top, type_info pointer, virtual functions...]. This reads
those records only; it never guesses a class from behaviour. Run it to rewrite
reference/engine_classes.json from the clean ROM in original/. Query the result
with tools/engine_map.py. See TECHNICAL "Engine map".
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x02000000
CODE_END = 0x021193BC      # USA end of .init (TECHNICAL "External EUR decompilation")
ITCM = 0x01FF8000
CATALOG = ROOT / 'reference/engine_classes.json'
KINDS = ('__class_type_info', '__si_class_type_info', '__vmi_class_type_info')
BUILTIN = dict(v='void', b='bool', c='char', a='signed char', h='unsigned char', s='short',
               t='unsigned short', i='int', j='unsigned', l='long', m='unsigned long',
               x='long long', y='unsigned long long', f='float', d='double', w='wchar_t')


def demangle(name: str) -> str:
    """Readable form of an Itanium-mangled type name; the input unchanged if unsupported."""
    subs: list[str] = []
    pos = 0

    def source():
        nonlocal pos
        digits = re.match(r'\d+', name[pos:]).group()
        pos += len(digits)
        text = name[pos:pos + int(digits)]
        if len(text) != int(digits): raise ValueError
        pos += int(digits)
        return text

    def args():
        nonlocal pos
        pos += 1                                            # I
        out = []
        while name[pos] != 'E':
            if name[pos] == 'L':                            # literal: L <type> <value> E
                pos += 1; parse()
                end = name.index('E', pos)
                out.append(name[pos:end]); pos = end + 1
            else:
                out.append(parse())
        pos += 1
        return '<' + ', '.join(out) + '>'

    def substitution():
        nonlocal pos
        if name[pos:pos + 2] in ('St', 'Sa'):
            pos += 2
            return ('std', False) if name[pos - 1] == 't' else ('std::allocator', True)
        end = name.index('_', pos)
        code = name[pos + 1:end]
        pos = end + 1
        return subs[int(code, 36) + 1 if code else 0], True

    def named():
        """One possibly nested, possibly templated name."""
        nonlocal pos
        nested = name[pos] == 'N'
        if nested: pos += 1
        text, fresh = '', False
        while True:
            c = name[pos]
            if c == 'S':
                part, known = substitution()
                text = part if not text else text + '::' + part
                fresh = not known and text != 'std'
            elif c.isdigit():
                text = (text + '::' if text else '') + source(); fresh = True
            elif c == 'I':
                text += args(); fresh = True
            else:
                raise ValueError
            if fresh: subs.append(text)
            if nested:
                if name[pos] == 'E':
                    pos += 1
                    return text
            elif pos >= len(name) or not (name[pos] == 'I' or text == 'std' and name[pos].isdigit()):
                return text

    def parse():
        nonlocal pos
        c = name[pos]
        if c in BUILTIN:
            pos += 1
            return BUILTIN[c]
        if c in 'PRK':
            pos += 1
            inner = parse()
            if c == 'P' and inner.endswith(')') and '(' in inner:      # pointer to function
                head, tail = inner.split(' (', 1)
                text = f'{head} (*)({tail}'
            else:
                text = inner + {'P': '*', 'R': '&', 'K': ' const'}[c]
        elif c == 'F':
            pos += 1
            result = parse()
            params = []
            while name[pos] != 'E': params.append(parse())
            pos += 1
            text = f'{result} ({", ".join(p for p in params if p != "void")})'
        elif c == 'M':
            pos += 1
            owner = parse()
            text = f'{parse()} {owner}::*'
        else:
            return named()
        subs.append(text)
        return text

    try:
        text = parse()
        return text if pos == len(name) else name
    except (ValueError, IndexError, AttributeError, KeyError):
        return name


def scan(image: bytes, base: int = BASE, code_end: int = CODE_END) -> list[dict]:
    """Every RTTI class in a loaded ARM9 image, with bases and vtables, sorted by type_info."""
    count = len(image) // 4
    words = struct.unpack(f'<{count}I', image[:count * 4])
    end = base + len(image)

    def string(address):
        offset = address - base
        return image[offset:image.index(b'\0', offset)].decode('latin1')

    def find(value):
        return [base + 4 * i for i, word in enumerate(words) if word == value]

    # The three type_info classes describe themselves: name -> type_info -> vtable address point.
    kinds = {}
    for kind in KINDS:
        mangled = f'N10__cxxabiv1{len(kind)}{kind}E'.encode() + b'\0'
        at = image.find(mangled)
        if at < 0: raise ValueError(f'no {kind} name: this image has no Itanium RTTI')
        info = next(a - 4 for a in find(base + at))
        kinds[next(a + 4 for a in find(info) if words[(a - base) // 4 - 1] == 0)] = kind
    classes = {}
    for index, word in enumerate(words[:-1]):
        if word not in kinds or not code_end <= words[index + 1] < end: continue
        try: mangled = string(words[index + 1])
        except ValueError: continue
        if not re.match(r'[0-9NS]', mangled): continue
        bases = []
        if kinds[word] == KINDS[1]:
            bases = [(words[index + 2], 0)]
        elif kinds[word] == KINDS[2]:
            if words[index + 3] > 16: continue
            for k in range(words[index + 3]):
                bases.append((words[index + 4 + 2 * k], struct.unpack('<i', struct.pack('<I', words[index + 5 + 2 * k]))[0] >> 8))
        classes[base + 4 * index] = dict(name=demangle(mangled), mangled=mangled, typeinfo=base + 4 * index,
                                         bases=bases, vtables=[])
    code = lambda value: (base <= value < code_end or ITCM <= value < base) and value % 4 == 0
    starts = {}
    for index, word in enumerate(words[1:-1], 1):
        top = struct.unpack('<i', struct.pack('<I', words[index - 1]))[0]
        if word in classes and -0x1000 < top <= 0 and (code(words[index + 1]) or not words[index + 1]):
            starts[base + 4 * index + 4] = (word, -top)
    # A table ends at the next table, a type_info, or any address something else points at
    # (pointer-to-member tables often follow a vtable directly). Null slots are pure virtuals.
    referenced = {word for word in words if code_end <= word < end} - set(starts)
    for start, (info, offset) in sorted(starts.items()):
        slots, index = [], (start - base) // 4
        while index < count and (code(words[index]) or not words[index]):
            address = base + 4 * index
            if address != start and (address + 8 in starts or address in classes or address in referenced): break
            slots.append(words[index]); index += 1
        classes[info]['vtables'].append(dict(address=start, offset=offset, slots=slots))
    derived = {}
    for info, record in classes.items():
        for parent, offset in record['bases']: derived.setdefault(parent, []).append((info, offset))

    def settle(info, table):
        """Final slot count: only a class with subclasses may keep null slots, never more than they have."""
        if 'final' in table: return table['final']
        slots = table['slots']
        limits = [settle(child, other) for child, offset in derived.get(info, ())
                  for other in classes[child]['vtables'] if other['offset'] == offset + table['offset']]
        solid = next((i for i, slot in enumerate(slots) if not slot), len(slots))
        table['final'] = min([len(slots)] + limits) if limits else solid
        return table['final']

    for info, record in classes.items():
        for table in record['vtables']: settle(info, table)
    for record in classes.values():
        for table in record['vtables']: del table['slots'][table.pop('final'):]
    for record in classes.values():
        record['bases'] = [dict(name=classes[b]['name'], offset=o) for b, o in record['bases']]
    return [classes[key] for key in sorted(classes)]


def catalog(image: bytes) -> dict:
    hexed = lambda value: f'0x{value:08x}'
    return dict(
        schema_version=1,
        purpose='Classes, bases and vtables read from the clean CS5E ARM9 RTTI by tools/arm9_rtti.py. '
                'Generated: never edit by hand. Names for slots and fields live in engine_symbols.json.',
        arm9_sha256=hashlib.sha256(image).hexdigest(),
        classes=[dict(name=c['name'], mangled=c['mangled'], typeinfo=hexed(c['typeinfo']), bases=c['bases'],
                      vtables=[dict(address=hexed(v['address']), offset=v['offset'],
                                    slots=[hexed(s) for s in v['slots']]) for v in c['vtables']])
                 for c in scan(image)])


def dumps(data: dict) -> str:
    """Stable JSON with one class per line group: reviewable diffs, small file."""
    head = {k: v for k, v in data.items() if k != 'classes'}
    rows = ',\n'.join('  ' + json.dumps(c, separators=(',', ':')) for c in data['classes'])
    return json.dumps(head, indent=1)[:-2] + ',\n "classes": [\n' + rows + '\n ]\n}\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, default=CATALOG)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    from tools import arm9_hooks
    data = catalog(arm9_hooks.clean_arm9())
    args.out.write_text(dumps(data), encoding='utf-8', newline='\n')
    tables = sum(len(c['vtables']) for c in data['classes'])
    print(f'{len(data["classes"])} classes, {tables} vtables -> {args.out}')


if __name__ == '__main__':
    main()
