"""One lookup for the game engine: what an address, class, symbol, field or hook is.

Joins four sources so nobody has to re-derive them from prose:
  reference/engine_classes.json  classes and vtables from RTTI (tools/arm9_rtti.py)
  reference/engine_hooks.json    native words the mod changed (tools/arm9_hooks.py)
  reference/engine_symbols.json  curated names, struct fields and enums (edit this one)
  docs/TECHNICAL.md + tools/     every line that mentions the address

  engine_map.py ADDR             everything known about a CS5E address
  engine_map.py find TEXT        search symbols, classes, fields and enum values
  engine_map.py class NAME       bases, subclasses and named vtable slots (--slots: all)
  engine_map.py struct [NAME]    curated field layout;  enum [NAME]  curated values
  engine_map.py table [NAME]     a native table (state handlers, transition lists) row by row
  engine_map.py hooks [TEXT]     changed native sites (filter: address, version, title)
  engine_map.py refs VALUE       code that loads a literal (address, number or Glob file name)
  engine_map.py dis ADDR [N]     annotated disassembly (--rom ROM reads a modded image)
  engine_map.py objects RAM      live heap objects by class in a kit_lab --ram dump
  engine_map.py ptmf ADDR [N]    a member-pointer table as an entries list for the curated file
  engine_map.py check            validate the curated file against the catalogs and ROM

ADDR, find, class, struct, enum, table and hooks work in a fresh clone. Callers,
callees, digests, refs, dis and objects need the clean ROM in original/; dis
also needs capstone in work/research-libs. Addresses are clean USA CS5E. See
TECHNICAL "Engine map".
"""
from __future__ import annotations

import argparse
import bisect
import csv
import functools
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import arm9_hooks, arm9_rtti  # noqa: E402

BASE, CODE_END, ITCM = arm9_rtti.BASE, arm9_rtti.CODE_END, arm9_rtti.ITCM
REFERENCE = ROOT / 'reference'
KINDS = ('function', 'site', 'data', 'ram')       # site: an address inside a function
ABILITY_SLOT = 0x184                              # Spidey vtable+0x184: HasAbility(bit)
QUEUE = {0x020CFF0C: 'peeks', 0x020CFFE8: 'peeks', 0x020CFC34: 'consumes'}   # input-command queue calls
CONFIDENCE = ('high', 'medium', 'low')
ADDRESS = re.compile(r'0x0[12][0-9A-Fa-f]{6}\b')


def number(text: str) -> int:
    return int(text, 16) if re.fullmatch(r'(0x)?[0-9A-Fa-f]{6,8}', text) else int(text, 0)


@functools.cache
def load(name: str) -> dict:
    return json.loads((REFERENCE / f'engine_{name}.json').read_text(encoding='utf-8'))


@functools.cache
def classes() -> dict[str, dict]:
    return {record['name']: record for record in load('classes')['classes']}


@functools.cache
def subclasses() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for record in classes().values():
        for base in record['bases']: out.setdefault(base['name'], []).append(record['name'])
    return out


def table_at(name: str, offset: int):
    return next((t for t in classes()[name]['vtables'] if t['offset'] == offset), None)


def origin(name: str, offset: int, slot: int) -> tuple[str, int]:
    """(class, sub-object offset) of the topmost base whose table declares this slot."""
    for base in classes()[name]['bases']:
        inner = offset - base['offset']
        table = table_at(base['name'], inner) if inner >= 0 else None
        if table and slot < len(table['slots']): return origin(base['name'], inner, slot)
    return name, offset


def implementer(name: str, offset: int, slot: int) -> str:
    """The topmost base that already has this function in this slot."""
    function = table_at(name, offset)['slots'][slot]
    for base in classes()[name]['bases']:
        inner = offset - base['offset']
        table = table_at(base['name'], inner) if inner >= 0 else None
        if table and slot < len(table['slots']) and table['slots'][slot] == function:
            return implementer(base['name'], inner, slot)
    return name


def primary(name: str, offset: int, slot: int) -> int:
    """Byte offset of a slot from the class's first vtable: the number native code indexes with.

    A class's tables are contiguous, and a subclass's new virtuals are appended to the last one
    but called through the first vptr, so Spidey's ability query is `[[actor]+0x184]`.
    """
    tables = classes()[name]['vtables']
    return int(table_at(name, offset)['address'], 16) - int(tables[0]['address'], 16) + slot * 4


def locate(name: str, offset: int):
    """(sub-object offset, slot index) for a primary byte offset, or None."""
    for table in classes().get(name, {}).get('vtables', ()):
        slot, odd = divmod(offset - primary(name, table['offset'], 0), 4)
        if not odd and 0 <= slot < len(table['slots']): return table['offset'], slot
    return None


@functools.cache
def slot_names() -> dict[tuple[str, int, int], dict]:
    return {(row['class'], *locate(row['class'], number(row['slot']))): row
            for row in load('symbols')['vslots'] if locate(row['class'], number(row['slot']))}


def slot_label(name: str, offset: int, slot: int) -> str:
    """Class::Name for a vtable slot, using the curated name of the declaring class when one exists."""
    root, inner = origin(name, offset, slot)
    row = slot_names().get((root, inner, slot))
    return f'{implementer(name, offset, slot)}::{row["name"] if row else f"{root}_v{primary(root, inner, slot):X}"}'


@functools.cache
def virtuals() -> dict[int, list[tuple[str, int, int]]]:
    """function address -> [(class, sub-object offset, slot index)] for every vtable slot."""
    out: dict[int, list] = {}
    for record in classes().values():
        for table in record['vtables']:
            for slot, value in enumerate(table['slots']):
                if int(value, 16): out.setdefault(int(value, 16), []).append((record['name'], table['offset'], slot))
    return out


@functools.cache
def vtables() -> dict[int, tuple[str, dict]]:
    return {int(t['address'], 16): (r['name'], t) for r in classes().values() for t in r['vtables']}


@functools.cache
def symbols() -> dict[int, dict]:
    return {int(row['address'], 16): row for row in load('symbols')['symbols']}


def enum_name(enum: str | None, value: int) -> str:
    """Number plus the identifier of an enum value (the text before the colon)."""
    text = load('symbols')['enums'].get(enum or '', {}).get('values', {}).get(str(value))
    return f'{value} {text.split(":")[0]}' if text else str(value)


@functools.cache
def table_functions() -> dict[int, list[tuple[dict, int]]]:
    """function address -> [(table, index)] for every function a curated table points at."""
    out: dict[int, list] = {}
    for table in load('symbols')['tables']:
        for index, entry in enumerate(table['entries']):
            if isinstance(entry, str) and entry.startswith('0x'): out.setdefault(int(entry, 16), []).append((table, index))
    return out


def table_label(address: int) -> str:
    """Class::Label_<indices> from the first table that lists a function."""
    table = table_functions()[address][0][0]
    indices = [i for t, i in table_functions()[address] if t is table]
    if not table.get('index'): return f'{table["class"]}::{table["label"]}{indices[0]:02d}'
    names = '_'.join(str(i) for i in indices[:4]) + ('_etc' if len(indices) > 4 else '')
    tail = enum_name(table['index'], indices[0]).split(' ', 1)
    return f'{table["class"]}::{table["label"]}_{names}' + (f'_{tail[1]}' if len(tail) > 1 and len(indices) == 1 else '')


def name_of(address: int) -> str | None:
    """Best short name: curated symbol, table handler, the implementing class's vtable slot, else a vtable."""
    if address in symbols(): return symbols()[address]['name']
    if address in table_functions(): return table_label(address)
    if address in virtuals():
        owners = sorted({slot_label(*use) for use in virtuals()[address]})
        return owners[0] if len(owners) == 1 else f'{owners[0]} (+{len(owners) - 1} more)'
    if address in vtables():
        name, table = vtables()[address]
        return f'vtable {name}' + (f' (+{table["offset"]})' if table['offset'] else '')
    return None


def block_of(address: int):
    """(start, end, version) of the extension block holding an address."""
    extension = load('hooks')['extension']
    return next((b for b in extension['blocks'] if int(b[0], 16) <= address < int(b[1], 16)), None)


def release_title(version: str) -> str:
    return dict(load('hooks')['releases']).get(version, '')


# ---------------------------------------------------------------- mentions in prose and tools
@functools.cache
def mentions() -> dict[int, list[tuple[str, int, str, str]]]:
    """address -> [(file, line, heading, text)] over the technical docs and tools/."""
    out: dict[int, list] = {}
    paths = [ROOT / 'docs/TECHNICAL.md', ROOT / 'docs/OG_GAMEPLAY.md', ROOT / 'docs/DEVELOPMENT.md']
    paths += sorted((ROOT / 'tools').glob('*.py')) + sorted((ROOT / 'tools').glob('*.s'))
    for path in paths:
        heading = ''
        for index, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if path.suffix == '.md' and line.startswith('#'): heading = line.lstrip('# ').strip()
            for match in ADDRESS.finditer(line):
                out.setdefault(int(match.group(), 16), []).append(
                    (path.relative_to(ROOT).as_posix(), index, heading, line.strip()))
    return out


# ---------------------------------------------------------------- static index of the clean ARM9
class Static:
    """Function entries, direct calls and literal loads of the clean ARM9 (ARM code only)."""

    def __init__(self, image: bytes):
        self.image = image
        code = (CODE_END - BASE) // 4
        self.words = struct.unpack(f'<{code}I', image[:code * 4])
        self.calls: dict[int, list[int]] = {}
        self.loads: dict[int, list[int]] = {}
        for index, word in enumerate(self.words):
            address = BASE + 4 * index
            if word >> 28 != 0xF and (word >> 24) & 0xF == 0xB:
                self.calls.setdefault(arm9_hooks.branch_target(address, word), []).append(address)
            elif word & 0x0F7F0000 == 0x051F0000:                      # ldr rX, [pc, #+-imm]
                pool = address + 8 + (word & 0xFFF) * (1 if word & 0x800000 else -1)
                if BASE <= pool < CODE_END:
                    self.loads.setdefault(self.words[(pool - BASE) // 4], []).append(address)
        entries = set(self.calls) | set(virtuals()) | set(table_functions())
        entries |= {a for a, s in symbols().items() if s['kind'] == 'function'}
        # Functions reached only through pointers (member-pointer and callback tables): a stored
        # address counts when it lands on a push prologue. Matches 95% of the EUR decomp's bounds.
        for (value,) in struct.iter_unpack('<I', image[:len(image) // 4 * 4]):
            if BASE <= value < CODE_END and not value % 4 and self.words[(value - BASE) // 4] >> 16 in (0xE92D, 0xE52D):
                entries.add(value)
        self.entries = sorted(a for a in entries if BASE <= a < CODE_END)

    def function(self, address: int) -> int | None:
        """Nearest known entry at or before a code address (uncalled static functions are not known)."""
        index = bisect.bisect_right(self.entries, address) - 1
        return self.entries[index] if index >= 0 and BASE <= address < CODE_END else None

    def end(self, entry: int) -> int:
        index = bisect.bisect_right(self.entries, entry)
        return self.entries[index] if index < len(self.entries) else CODE_END

    def callees(self, entry: int) -> list[int]:
        out = []
        for address in range(entry, self.end(entry), 4):
            word = self.words[(address - BASE) // 4]
            if word >> 28 != 0xF and (word >> 24) & 0xF == 0xB:
                target = arm9_hooks.branch_target(address, word)
                if target not in out: out.append(target)
        return out

    def thunk(self, address: int) -> int | None:
        """Target of a this-adjusting thunk: ldr ip,[pc,#4]; add rX,rX,ip; b target; .word adjust."""
        if not BASE <= address < CODE_END - 12: return None
        first, add, jump = self.words[(address - BASE) // 4:(address - BASE) // 4 + 3]
        if first != 0xE59FC004 or add & 0xFFF00FFF != 0xE080000C or jump >> 24 != 0xEA: return None
        return arm9_hooks.branch_target(address + 8, jump)

    def digest(self, entry: int) -> dict:
        """Constants a function returns, queue commands it reads and ability bits it tests.

        Pattern matching on the compiler's idioms, not data flow: confirm in `dis` before relying on it.
        """
        words = self.words[(entry - BASE) // 4:(self.end(entry) - BASE) // 4]
        immediate = lambda w: ((w & 0xFF) >> 2 * (w >> 8 & 15) | (w & 0xFF) << 32 - 2 * (w >> 8 & 15)) & 0xFFFFFFFF
        is_mov = lambda w, reg: w & 0x0FEF0000 == 0x03A00000 and (w >> 12) & 15 == reg

        def back(i, reg, span):
            return next((immediate(words[j]) for j in range(i - 1, max(i - span, -1), -1) if is_mov(words[j], reg)), None)

        out = dict(returns=set(), peeks=set(), consumes=set(), abilities=set())
        for i, w in enumerate(words):
            target = arm9_hooks.branch_target(entry + 4 * i, w)
            if is_mov(w, 0) and any(x & 0x0FFF8000 == 0x08BD8000 for x in words[i + 1:i + 4]):
                out['returns'].add(immediate(w))
            if w & 0x0FF00FFF == 0x05900000 | ABILITY_SLOT and (w >> 16) & 15 != 13:   # not a stack slot
                bit = back(i, 1, 6)
                if bit is not None: out['abilities'].add(bit)
            if w >> 28 != 0xF and (w >> 24) & 0xF == 0xB and target in QUEUE:
                # The command is passed by reference: mov rX,#cmd ... str rX,[sp,#n] ... bl
                stored = next((words[j] for j in range(i - 1, max(i - 8, -1), -1) if words[j] & 0x0FFF0000 == 0x058D0000), None)
                command = back(i, (stored >> 12) & 15, 24) if stored is not None else None
                if command is not None: out[QUEUE[target]].add(command)
        return out


def digest_text(entry: int, returns: str | None = None) -> str:
    """One line for a function's digest; `returns` names the enum of its return values."""
    found = static().digest(entry)
    parts = []
    if found['peeks'] or found['consumes']:
        parts.append('input ' + ', '.join(enum_name('QueueCommand', c) for c in sorted(found['peeks'] | found['consumes'])))
    if found['abilities']: parts.append('ability bits ' + ','.join(str(b) for b in sorted(found['abilities'])))
    if found['returns']: parts.append('returns ' + ', '.join(enum_name(returns, v) for v in sorted(found['returns'])))
    named = [symbols()[c]['name'] for c in static().callees(entry) if c in symbols() and c not in QUEUE]
    if named: parts.append('calls ' + ', '.join(named[:4]))
    return '; '.join(parts)


@functools.cache
def static() -> Static | None:
    """The static index, or None in a workspace without the clean ROM."""
    try: return Static(arm9_hooks.clean_arm9())
    except FileNotFoundError: return None


def label(address: int) -> str:
    """0xADDR plus a name, or the entry it sits in."""
    text = f'0x{address:08x}'
    name = name_of(address)
    if not name and static() and BASE <= address < CODE_END:
        entry = static().function(address)
        if entry is not None and entry != address:
            name = f'{name_of(entry) or f"0x{entry:08x}"}+0x{address - entry:x}'
    block = block_of(address)
    if not name and block:
        # Inside our extension: offset from the nearest curated symbol of the same block, if any.
        near = max((a for a in symbols() if int(block[0], 16) <= a <= address and address - a < 0x100), default=None)
        name = (f'{symbols()[near]["name"]}+0x{address - near:x} ' if near is not None else '') + f'(mod v{block[2]})'
    return f'{text} {name}' if name else text


# ---------------------------------------------------------------- commands
def describe(address: int, limit: int = 12) -> str:
    out = [label(address)]
    row = symbols().get(address)
    if row:
        out.append(f'  {row["kind"]}, {row["confidence"]} confidence' + (f': {row["note"]}' if row.get('note') else ''))
        if row.get('doc'): out.append(f'  read: TECHNICAL "{row["doc"]}"')
    for use in virtuals().get(address, [])[:limit]:
        name, offset, slot = use
        part = f' (sub-object +{offset}, slot +0x{slot * 4:X} there)' if offset else ''
        out.append(f'  virtual: {name} vtable+0x{primary(*use):X}{part} = {slot_label(*use)}')
    if len(virtuals().get(address, [])) > limit: out.append(f'  ... in {len(virtuals()[address])} vtable slots')
    for table, slot in table_functions().get(address, [])[:limit]:
        out.append(f'  listed in {table["name"]} ({table["address"]}) [{enum_name(table.get("index"), slot)}]')
    holder = next((t for t in load('symbols')['tables'] if int(t['address'], 16) <= address
                   < int(t['address'], 16) + stride(t) * len(t['entries'])), None)
    if holder:
        slot = (address - int(holder['address'], 16)) // stride(holder)
        out.append(f'  {holder["name"]}[{enum_name(holder.get("index"), slot)}] = {holder["entries"][slot] or "none"}: '
                   f'engine_map.py table {holder["name"]}')
    if address in vtables():
        name, table = vtables()[address]
        out.append(f'  vtable of {name}, {len(table["slots"])} slots: engine_map.py class {name}')
    inside = next(((start, name, table) for start, (name, table) in vtables().items()
                   if start < address < start + 4 * len(table['slots'])), None)
    if inside:
        start, name, table = inside
        slot = (address - start) // 4
        out.append(f'  {name} vtable+0x{primary(name, table["offset"], slot):X} (slot +0x{slot * 4:X} of table {table["address"]}): '
                   f'{slot_label(name, table["offset"], slot)} = {table["slots"][slot]}')
    hooks = load('hooks')
    for site in hooks['sites']:
        if int(site['address'], 16) == address:
            chain = ' > '.join(f'{v} {w}' for v, w in site['history'])
            goes = f' -> {label(int(site["target"], 16))}' if 'target' in site else ''
            out.append(f'  CHANGED by the mod (v{hooks["release"]}): clean {site["clean"]}, now {site["current"]}{goes}')
            out.append(f'    history: {chain}')
    block = block_of(address)
    if block: out.append(f'  mod extension block {block[0]}-{block[1]}, last written by v{block[2]} {release_title(block[2])}')
    index = static()
    if index and index.thunk(address):
        out.append(f'  thunk: adjusts this, then jumps to {label(index.thunk(address))}')
    if index and BASE <= address < CODE_END:
        entry = index.function(address)
        if entry is not None:
            inner = [s for s in hooks['sites'] if entry <= int(s['address'], 16) < index.end(entry) and int(s['address'], 16) != address]
            if entry != address: out.append(f'  inside {label(entry)} (next entry {index.end(entry):#010x})')
            if inner: out.append('  mod-changed sites in this function: ' + ', '.join(s['address'] for s in inner))
            if entry == address:
                returns = next((t.get('returns') for t, _ in table_functions().get(address, []) if t.get('returns')), None)
                if digest_text(address, returns): out.append(f'  static digest: {digest_text(address, returns)}')
                callers = sorted({index.function(site) for site in index.calls.get(address, [])})
                out.append(f'  direct callers ({len(callers)}): ' + ', '.join(label(c) for c in callers[:limit])
                           + (' ...' if len(callers) > limit else ''))
                callees = index.callees(address)
                out.append(f'  calls ({len(callees)}): ' + ', '.join(label(c) for c in callees[:limit])
                           + (' ...' if len(callees) > limit else ''))
    if index and index.loads.get(address):
        sites = index.loads[address]
        out.append(f'  loaded as a literal by ({len(sites)}): ' + ', '.join(label(s) for s in sites[:limit])
                   + (' ...' if len(sites) > limit else ''))
    seen = mentions().get(address, [])
    for path, line, heading, text in seen[:limit]:
        where = f'{path}:{line}' + (f' [{heading}]' if heading else '')
        out.append(f'  {where}: {text[:150]}')
    if len(seen) > limit: out.append(f'  ... {len(seen)} mentions; search for {address:#010x} (any case)')
    if len(out) == 1: out.append('  nothing recorded: disassemble it, then add what you verify to reference/engine_symbols.json')
    return '\n'.join(out)


def find(text: str) -> str:
    needle, out = text.lower(), []
    for address, row in sorted(symbols().items()):
        if needle in row['name'].lower() or needle in row.get('note', '').lower():
            out.append(f'{row["kind"]:8} 0x{address:08x} {row["name"]}: {row.get("note", "")[:100]}')
    for name, record in classes().items():
        if needle in name.lower() and len(name) < 80:
            out.append(f'class    {record["vtables"][0]["address"] if record["vtables"] else "(no vtable)":10} {name}')
    for row in load('symbols')['vslots']:
        if needle in row['name'].lower() or needle in row.get('note', '').lower():
            out.append(f'vslot    {row["class"]} vtable+0x{number(row["slot"]):X} {row["name"]}: {row.get("note", "")[:100]}')
    for name, record in load('symbols')['structs'].items():
        if needle in name.lower(): out.append(f'struct   {name}: {record.get("note", "")[:100]}')
        for offset, kind, field, note in record['fields']:
            if needle in field.lower() or needle in note.lower():
                out.append(f'field    {name}+{offset} {field} ({kind}): {note[:100]}')
    for table in load('symbols')['tables']:
        if needle in table['name'].lower(): out.append(f'table    {table["address"]} {table["name"]}: {table.get("note", "")[:100]}')
    for address in table_functions():
        if address not in symbols() and needle in table_label(address).lower(): out.append(f'function 0x{address:08x} {table_label(address)}')
    for name, record in load('symbols')['enums'].items():
        if needle in name.lower(): out.append(f'enum     {name}: {record.get("note", "")[:100]}')
        for value, meaning in record['values'].items():
            if needle in meaning.lower(): out.append(f'value    {name} {value} = {meaning[:110]}')
    return '\n'.join(out) or f'no symbol, class, field or enum value matches {text!r}'


def show_class(name: str, every: bool = False) -> str:
    matches = [n for n in classes() if n == name] or [n for n in classes() if name.lower() in n.lower()]
    if len(matches) != 1:
        return '\n'.join(matches[:60]) if matches else f'no class matches {name!r}'
    record = classes()[matches[0]]
    out = [f'{record["name"]}  (type_info {record["typeinfo"]})']
    chain, current = [], record
    while current['bases']:
        chain.append(' + '.join(f'{b["name"]}@{b["offset"]}' for b in current['bases']))
        current = classes()[current['bases'][0]['name']]
    if chain: out.append('  bases: ' + '  <-  '.join(chain))
    if subclasses().get(record['name']): out.append('  subclasses: ' + ', '.join(sorted(subclasses()[record['name']])))
    if record['name'] in load('symbols')['structs']: out.append(f'  fields: engine_map.py struct {record["name"]}')
    for table in record['vtables']:
        root = origin(record['name'], table['offset'], 0)[0] if table['slots'] else record['name']
        out.append(f'  vtable {table["address"]} sub-object +{table["offset"]} ({root} part), {len(table["slots"])} slots'
                   f' at vtable+0x{primary(record["name"], table["offset"], 0):X}')
        for slot, value in enumerate(table['slots']):
            declared, inner = origin(record['name'], table['offset'], slot)
            named = slot_names().get((declared, inner, slot))
            mine = implementer(record['name'], table['offset'], slot) == record['name']
            if every or named or (mine and declared != record['name']) or int(value, 16) in symbols():
                text = slot_label(record['name'], table['offset'], slot) if int(value, 16) else 'pure virtual'
                curated = symbols().get(int(value, 16))
                out.append(f'    +0x{primary(record["name"], table["offset"], slot):03X} {value} {text}'
                           + (' [overrides here]' if mine and declared != record['name'] else '')
                           + (f'  = {curated["name"]}' if curated and curated["name"] not in text else '')
                           + (f'  -> thunk to {label(static().thunk(int(value, 16)))}' if static() and static().thunk(int(value, 16)) else '')
                           + (f'  ; {named["note"]}' if named and named.get('note') else ''))
    out.append('  Offsets count from the first vtable, as native code indexes them: [[object]+0xNNN].')
    if not every: out.append('  (named and overridden slots only; --slots lists all)')
    return '\n'.join(out)


def show_table(kind: str, name: str | None) -> str:
    tables = load('symbols')[kind]
    if not name: return '\n'.join(f'{key}: {value.get("note", "")}' for key, value in tables.items())
    key = next((k for k in tables if k.lower() == name.lower()), None)
    if not key: return f'no {kind[:-1]} {name!r}; known: ' + ', '.join(tables)
    record = tables[key]
    out = [f'{key}: {record.get("note", "")}'] + ([f'  read: TECHNICAL "{record["doc"]}"'] if record.get('doc') else [])
    if kind == 'structs':
        out += [f'  +{offset:6} {kind_:5} {field:24} {note}' for offset, kind_, field, note in record['fields']]
    else:
        out += [f'  {value:>6} {meaning}' for value, meaning in record['values'].items()]
    return '\n'.join(out)


def member_pointer(image: bytes, address: int) -> str:
    """One {function or vtable offset, adjust} pair as the curated files spell it; '' for null."""
    value, adjust = struct.unpack_from('<2I', image, address - BASE)
    return '' if not value else f'vtable+0x{value:X}' if adjust & 1 else f'0x{value:08x}'


def member_pointers(address: int, count: int | None, step: int = 8) -> str:
    """The entries of a member-pointer table: N of them, or up to the null terminator of a list."""
    image, out = arm9_hooks.clean_arm9(), []
    while count is None or len(out) < count:
        out.append(member_pointer(image, address + step * len(out)))
        if count is None and not out[-1]: return json.dumps(out[:-1])
    return json.dumps(out)


def stride(table: dict) -> int:
    """Bytes per row: a member pointer is 8, a u32 is 4; "stride" overrides for wider records."""
    return table.get('stride', 8 if table['layout'] == 'ptmf' else 4)


def show_native_table(name: str | None) -> str:
    tables = load('symbols')['tables']
    if not name:
        return '\n'.join(f'{t["address"]} {t["name"]} ({len(t["entries"])} x {t["layout"]}): {t.get("note", "")[:90]}' for t in tables)
    table = next((t for t in tables if t['name'].lower() == name.lower()), None) \
        or next((t for t in tables if name.lower() in t['name'].lower()), None)
    if not table: return f'no table {name!r}; known: ' + ', '.join(t['name'] for t in tables)
    out = [f'{table["name"]} at {table["address"]}: {table.get("note", "")}']
    if table.get('doc'): out.append(f'  read: TECHNICAL "{table["doc"]}"')
    hooked = {int(site['address'], 16) for site in load('hooks')['sites']}
    for index, entry in enumerate(table['entries']):
        key = enum_name(table.get('index'), index)
        if isinstance(entry, int): text = enum_name(table.get('values'), entry)
        elif not entry: text = '-'
        elif not entry.startswith('0x'): text = entry
        else:
            address = int(entry, 16)
            text = label(address)
            if static():
                extra = digest_text(address, table.get('returns'))
                mods = [a for a in hooked if address <= a < static().end(address)]
                text += (f'  | {extra}' if extra else '') + (f'  | mod-changed: {", ".join(f"{a:#010x}" for a in sorted(mods))}' if mods else '')
        out.append(f'  [{key}] {text}')
    return '\n'.join(out)


def show_hooks(text: str | None) -> str:
    hooks, out = load('hooks'), []
    needle = (text or '').lower()
    versions = {v for v, title in hooks['releases'] if needle and needle in title.lower()}
    for site in hooks['sites']:
        touched = {v for v, _ in site['history']}
        if needle and not (needle in site['address'] or needle.lstrip('v') in touched or touched & versions): continue
        goes = f' -> {site["target"]} (v{site["owner"]} block)' if 'target' in site else ''
        out.append(f'{site["address"]} {site["region"]:6} {label(int(site["address"], 16))[11:] or "-"}: '
                   f'clean {site["clean"]} now {site["current"]}{goes}; changed in {", ".join(v for v, _ in site["history"])}')
    out.append(f'{len(out)} changed native sites in v{hooks["release"]}; extension {hooks["extension"]["target"]}-{hooks["extension"]["end"]}')
    return '\n'.join(out)


def refs(text: str) -> str:
    index = static()
    if not index: return 'needs the clean ROM in original/'
    try: value = number(text)
    except ValueError:
        with open(REFERENCE / 'glob_manifest.csv', newline='', encoding='utf-8') as handle:
            value = next((int(row['index']) for row in csv.DictReader(handle) if row['name'].lower() == text.lower()), None)
        if value is None: return f'{text!r} is neither a number nor a Glob file name'
    sites = index.loads.get(value, [])
    hint = [] if sites else ['  none: small numbers are usually mov immediates, and resource ids also sit in XBD tables']
    return '\n'.join([f'{len(sites)} literal loads of {value:#x}'] + [f'  {label(site)}' for site in sites] + hint)


def disassemble(address: int, count: int, rom: Path | None) -> str:
    sys.path.insert(0, str(ROOT / 'work/research-libs'))
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    image = arm9_hooks.arm9_of(rom) if rom else arm9_hooks.clean_arm9()
    offset = arm9_hooks.offset_of(image, address)
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    engine.skipdata = True
    changed = {int(site['address'], 16): site for site in load('hooks')['sites']}
    out = []
    for ins in engine.disasm(image[offset:offset + 4 * count], address):
        word = struct.unpack_from('<I', image, arm9_hooks.offset_of(image, ins.address))[0]
        note = ''
        target = arm9_hooks.branch_target(ins.address, word)
        if target is not None and ins.mnemonic.startswith('b'): note = label(target)[11:]
        elif word & 0x0F7F0000 == 0x051F0000:
            pool = ins.address + 8 + (word & 0xFFF) * (1 if word & 0x800000 else -1)
            value = struct.unpack_from('<I', image, arm9_hooks.offset_of(image, pool))[0]
            note = f'={value:#x} {label(value)[11:]}'.rstrip()
        if ins.address in changed:
            site = changed[ins.address]
            note += f'  [mod: clean {site["clean"]}, v{load("hooks")["release"]} {site["current"]}]'
        mark = name_of(ins.address)
        if mark: out.append(f'{mark}:')
        out.append(f'  {ins.address:08x}: {word:08x}  {ins.mnemonic:8s} {ins.op_str}' + (f'   ; {note.strip()}' if note.strip() else ''))
    return '\n'.join(out)


def objects(ram: bytes) -> str:
    """Count live heap blocks whose first word is a known vtable (objects made with new)."""
    from tools import heap_report
    u32 = lambda address: struct.unpack_from('<I', ram, address - BASE)[0]
    found: dict[str, list[tuple[int, int, int]]] = {}
    for heap in range(heap_report.COUNT):
        head = u32(u32(heap_report.TABLE + heap * heap_report.ENTRY) + 0x2C)
        while head:
            size, head_next = u32(head + 4), u32(head + 12)
            payload = head + heap_report.HEADER
            hit = next((vtables()[u32(payload + skip)] for skip in (0, 4, 8) if u32(payload + skip) in vtables()), None)
            if hit and not hit[1]['offset']: found.setdefault(hit[0], []).append((payload, size, heap))
            head = head_next
    out = [f'{"class":32} count heap sizes / first addresses']
    for name, rows in sorted(found.items(), key=lambda item: (-len(item[1]), item[0])):
        sizes = ','.join(f'0x{s:X}' for s in sorted({size for _, size, _ in rows})[:4])
        out.append(f'{name[:32]:32} {len(rows):5} {rows[0][2]:4} {sizes}  ' + ' '.join(f'0x{a:08x}' for a, _, _ in rows[:3]))
    return '\n'.join(out)


def check() -> list[str]:
    """Problems in the curated file; an empty list means it agrees with the catalogs (and ROM)."""
    data, problems, seen = load('symbols'), [], set()
    headings = {line.lstrip('# ').strip() for line in (ROOT / 'docs/TECHNICAL.md').read_text(encoding='utf-8').splitlines()
                if line.startswith('#')}
    def doc(row, what):
        if row.get('doc') and row['doc'] not in headings: problems.append(f'{what}: no TECHNICAL heading "{row["doc"]}"')
    extension = load('hooks')['extension']
    for row in data['symbols']:
        what = f'symbol {row.get("address")} {row.get("name")}'
        address = int(row['address'], 16)
        if address in seen: problems.append(f'{what}: duplicate address')
        seen.add(address)
        if row['kind'] not in KINDS or row['confidence'] not in CONFIDENCE: problems.append(f'{what}: bad kind/confidence')
        code = BASE <= address < CODE_END or ITCM <= address < BASE
        if row['kind'] in ('function', 'site') and (not code or address % 4): problems.append(f'{what}: not a code address')
        if row['kind'] == 'data' and not CODE_END <= address < int(extension['target'], 16): problems.append(f'{what}: not in the native data image')
        if row['kind'] == 'ram' and not int(extension['target'], 16) <= address < 0x02400000 and not 0x027E0000 <= address < 0x02800000:
            problems.append(f'{what}: not a RAM address')
        if row['kind'] == 'function' and static() and BASE <= address < CODE_END and address not in static().calls \
                and address not in virtuals() and static().words[(address - BASE) // 4] >> 16 not in (0xE92D, 0xE52D) \
                and not row.get('unreferenced'):
            problems.append(f'{what}: no direct call, vtable slot or push prologue; use kind "site" or set "unreferenced"')
        doc(row, what)
    for row in data['vslots']:
        what = f'vslot {row["class"]}+{row["slot"]}'
        where = locate(row['class'], number(row['slot']))
        if not where: problems.append(f'{what}: no such slot')
        elif origin(row['class'], *where)[0] != row['class']:
            root, inner = origin(row['class'], *where)
            problems.append(f'{what}: declared by {root} at vtable+0x{primary(root, inner, where[1]):X}; name it there')
    for name, record in data['structs'].items():
        offsets = [number(field[0]) for field in record['fields']]
        if offsets != sorted(set(offsets)): problems.append(f'struct {name}: offsets must ascend without repeats')
        if any(len(field) != 4 for field in record['fields']): problems.append(f'struct {name}: fields are [offset, type, name, note]')
        doc(record, f'struct {name}')
    for name, record in data['enums'].items():
        doc(record, f'enum {name}')
    for table in data['tables']:
        what = f'table {table["name"]}'
        doc(table, what)
        for key in ('index', 'values', 'returns'):
            if table.get(key) and table[key] not in data['enums']: problems.append(f'{what}: no enum {table[key]}')
        if table['layout'] == 'ptmf' and static():        # a member pointer is {function or vtable offset, adjust}
            for index, entry in enumerate(table['entries']):
                stored = member_pointer(static().image, int(table['address'], 16) + stride(table) * index)
                if stored != entry: problems.append(f'{what}[{index}]: ARM9 has {stored or "none"}, file has {entry or "none"}')
    if static():
        if hashlib.sha256(static().image).hexdigest() != load('classes')['arm9_sha256']:
            problems.append('engine_classes.json was not generated from the clean ROM: run tools/arm9_rtti.py')
    if arm9_hooks.STABLE.is_file() and hashlib.sha256(arm9_hooks.arm9_of(arm9_hooks.STABLE)).hexdigest() != load('hooks')['arm9_sha256']:
        problems.append('engine_hooks.json does not describe the stable ROM: run tools/arm9_hooks.py after publishing')
    return problems


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.stdout.reconfigure(encoding='utf-8')
    if argv and re.fullmatch(r'(0x)?[0-9A-Fa-f]{7,8}', argv[0]): argv.insert(0, 'addr')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('addr').add_argument('address', type=number)
    sub.add_parser('find').add_argument('text')
    s = sub.add_parser('class'); s.add_argument('name'); s.add_argument('--slots', action='store_true')
    sub.add_parser('struct').add_argument('name', nargs='?')
    sub.add_parser('enum').add_argument('name', nargs='?')
    sub.add_parser('table').add_argument('name', nargs='?')
    sub.add_parser('hooks').add_argument('text', nargs='?')
    sub.add_parser('refs').add_argument('value')
    s = sub.add_parser('dis'); s.add_argument('address', type=number); s.add_argument('count', nargs='?', type=int, default=40)
    s.add_argument('--rom', type=Path)
    sub.add_parser('objects').add_argument('ram', type=Path)
    s = sub.add_parser('ptmf'); s.add_argument('address', type=number); s.add_argument('count', nargs='?', type=int)
    s.add_argument('--stride', type=int, default=8, help='bytes per record when the member pointer is its first field')
    sub.add_parser('check')
    args = parser.parse_args(argv)
    if args.command == 'addr': print(describe(args.address))
    elif args.command == 'find': print(find(args.text))
    elif args.command == 'class': print(show_class(args.name, args.slots))
    elif args.command in ('struct', 'enum'): print(show_table(args.command + 's', args.name))
    elif args.command == 'table': print(show_native_table(args.name))
    elif args.command == 'hooks': print(show_hooks(args.text))
    elif args.command == 'refs': print(refs(args.value))
    elif args.command == 'dis': print(disassemble(args.address, args.count, args.rom))
    elif args.command == 'objects': print(objects(args.ram.read_bytes()))
    elif args.command == 'ptmf': print(member_pointers(args.address, args.count, args.stride))
    else:
        problems = check()
        print('\n'.join(problems) or 'engine map consistent')
        return 1 if problems else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
