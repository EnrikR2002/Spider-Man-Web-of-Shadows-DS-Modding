"""Native room exits, spawn points and authored doorways in CS5E OBJ envelopes.

Grounded in all 75 clean rooms (TECHNICAL "Native doors, spawns and flags"):
- Envelope header byte +13 is the spawn count, u16 +14 its byte size (20 each).
  Spawn: i32 x, y, z (Q12), u16 angle (0x4000 faces right, 0xC000 left),
  unknown bytes +14..+17, u8 id at +18 (door operands name this id), unknown +19.
- Event opcode 0x12 (handler 0x02039A4C) queues a room change through
  0x020D6B88: operand bytes (room, OBJ record selector, spawn id, 0).
- A type-7 trigger entity (28 bytes) fires the event group named by its last
  byte, 1-based within its own record; the byte before it is a trigger mode
  (2 on every native exit). +20/+22 are u16 box sizes; other bytes are copied
  from a native exit trigger and remain unknown.
Only appending is supported, so existing entity, group and spawn indices keep
their meaning. Every result is re-parsed; unknown bytes are preserved.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct

from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events, OPERAND_WIDTHS
from tools.room_objects import RoomObjects

GO_TO_ROOM = 0x12
TRIGGER_TYPE = 7
FACING = {'right': 0x4000, 'left': 0xC000}


@dataclass(frozen=True)
class Spawn:
    x: int
    y: int
    z: int
    angle: int
    spawn_id: int
    raw: bytes


@dataclass(frozen=True)
class Exit:
    record: int
    group: int
    room: int
    selector: int
    spawn: int


def spawns(raw):
    raw = bytes(raw)
    count, size = raw[13], struct.unpack_from('<H', raw, 14)[0]
    if size != 20 * count: raise ValueError('Unexpected spawn table size')
    out = []
    for i in range(count):
        rec = raw[16 + 20 * i:36 + 20 * i]
        x, y, z, angle = struct.unpack_from('<3iH', rec)
        out.append(Spawn(x, y, z, angle, rec[18], rec))
    return tuple(out)


def exits(raw):
    room = RoomObjects.parse(raw)
    out = []
    for r, record in enumerate(room.records):
        for g, group in enumerate(Events.parse(record.sections[1], record.raw[3]).groups):
            for command in group.commands:
                if command.opcode == GO_TO_ROOM:
                    out.append(Exit(r, g, *command.operand[:3]))
    return tuple(out)


OPPOSITE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}


def door_kind(raw, group):
    """'up', 'down', 'left' or 'right': trigger centre relative to its nearest spawn.

    A spawn sits beside each door (the arrival point for the way back), so the
    trigger's offset from it says which way Spidey leaves. Agrees with 169 of
    175 native door pairs; the rest are diagonal shafts.
    """
    record = RoomObjects.parse(raw).records[0]
    trigger = next((e for e in Entities.parse(record.sections[0]).records if len(e) == 28
                    and struct.unpack_from('<I', e, 12)[0] == TRIGGER_TYPE and e[27] == group + 1), None)
    if trigger is None: raise ValueError('No exit trigger for that group')
    tx, ty = struct.unpack_from('<2i', trigger)
    table = spawns(raw)
    if not table: raise ValueError('Room has no spawns')
    near = min(table, key=lambda s: (s.x - tx) ** 2 + (s.y - ty) ** 2)
    dx, dy = tx - near.x, ty - near.y
    if abs(dy) > abs(dx) and abs(dy) > 6 * 4096: return 'up' if dy > 0 else 'down'
    return 'right' if dx > 0 else 'left'


def _byte(value, label):
    if type(value) is not int or not 0 <= value <= 255: raise ValueError(f'{label} must be a byte')
    return value


def _slot(label):
    data = label.encode('ascii')
    if not data or len(data) > 31 or b'\0' in data: raise ValueError('Name must be 1..31 ASCII characters')
    return data + b'\0' + b' ' * max(0, 30 - len(data)) + (b'\0' if len(data) < 31 else b'')


def _assemble(room, records, names, header=None):
    header = bytearray(room.header if header is None else header)
    end = len(header) + sum(map(len, records))
    struct.pack_into('<2I', header, 4, end, end + len(room.between))
    result = bytes(header) + b''.join(records) + room.between + b''.join(names)
    RoomObjects.parse(result)
    return result


def retarget(raw, changes):
    """Rewrite go-to-room operands: {(record, group): (room, selector, spawn)}."""
    room = RoomObjects.parse(raw)
    by_record = {}
    for (r, g), target in changes.items():
        by_record.setdefault(r, {})[g] = tuple(_byte(v, 'Exit operand') for v in target)
    records = [x.raw for x in room.records]
    for r, groups in by_record.items():
        if type(r) is not int or not 0 <= r < len(records): raise ValueError('Record index out of range')
        record = room.records[r]
        events = Events.parse(record.sections[1], record.raw[3])
        new_groups = list(events.groups)
        for g, target in groups.items():
            if type(g) is not int or not 0 <= g < len(new_groups): raise ValueError('Group index out of range')
            hits = [i for i, c in enumerate(new_groups[g].commands) if c.opcode == GO_TO_ROOM]
            if len(hits) != 1: raise ValueError('Group must contain exactly one go-to-room command')
            commands = list(new_groups[g].commands)
            old = commands[hits[0]].operand
            commands[hits[0]] = Command(GO_TO_ROOM, bytes(target) + old[3:])
            new_groups[g] = EventGroup(tuple(commands))
        records[r] = record.replace_section(1, Events(tuple(new_groups), events.padding).to_bytes())
    return _assemble(room, records, [n.raw for n in room.names])


def add_spawn(raw, spawn_id, xyz, facing):
    """Append a spawn cloned from the first native one (unknown bytes kept)."""
    room = RoomObjects.parse(raw)
    table = spawns(raw)
    if not table: raise ValueError('Room has no spawn template')
    if _byte(spawn_id, 'Spawn id') in {s.spawn_id for s in table}: raise ValueError('Duplicate spawn id')
    if len(table) >= 255: raise ValueError('Too many spawns')
    record = bytearray(table[0].raw)
    struct.pack_into('<3iH', record, 0, *xyz, FACING[facing])
    record[18] = spawn_id
    header = bytearray(room.header[:16 + 20 * len(table)] + bytes(record))
    header[13] = len(table) + 1
    struct.pack_into('<H', header, 14, 20 * (len(table) + 1))
    result = _assemble(room, [r.raw for r in room.records], [n.raw for n in room.names], header)
    if spawns(result)[:-1] != table: raise ValueError('Existing spawns changed')
    return result


def append_entity(raw, record, entity, name):
    """Append one entity to a record's last batch and its name to category 0.

    Existing entity indices (and so every event reference) keep their meaning.
    """
    parsed = RoomObjects.parse(raw)
    if type(record) is not int or not 0 <= record < len(parsed.records): raise ValueError('Record out of range')
    rec, names = parsed.records[record], parsed.names[record]
    entities = Entities.parse(rec.sections[0])
    if names.category_ends[0] != len(entities.records): raise ValueError('Entity names do not match entities')
    if not entities.batches: raise ValueError('Record has no entity batch to extend')
    last = entities.batches[-1]
    lengths = [len(r) for r in last.records] + [len(entity)]
    if len(lengths) > 255 or not 0 < len(entity) < 256: raise ValueError('Entity batch limits exceeded')
    header_size = (4 + len(lengths) + 3) // 4 * 4
    body = b''.join(last.records) + bytes(entity)
    batch = struct.pack('<HBB', header_size + len(body), header_size, len(lengths)) + bytes(lengths)
    batch += bytes(header_size - len(batch)) + body
    section0 = b''.join(b.header + b''.join(b.records) for b in entities.batches[:-1]) + batch
    if Entities.parse(section0).records != entities.records + (bytes(entity),): raise ValueError('Entity append failed')
    records = [r.raw for r in parsed.records]
    records[record] = rec.replace_section(0, section0)
    slots = list(names.slots)
    slots.insert(names.category_ends[0], _slot(name))
    block = bytearray(names.raw[:20])
    struct.pack_into('<I', block, 0, 20 + 32 * len(slots))
    struct.pack_into('<7H', block, 6, *(e + 1 for e in names.category_ends))
    block += b''.join(slots)
    blocks = [n.raw for n in parsed.names]
    blocks[record] = bytes(block)
    return _assemble(parsed, records, blocks)


def add_exit(raw, *, center, size, room, selector, spawn, trigger_name, group_name):
    """Append a player-collide trigger and a go-to-room group to record 0.

    The trigger is a copy of the room's first native exit trigger with a new
    centre (x, y, z) Q12, box size (w, h) and group reference.
    """
    parsed = RoomObjects.parse(raw)
    record, names = parsed.records[0], parsed.names[0]
    entities = Entities.parse(record.sections[0])
    events = Events.parse(record.sections[1], record.raw[3])
    if names.category_ends[0] != len(entities.records) or names.category_ends[1] - names.category_ends[0] != len(events.groups):
        raise ValueError('Record 0 names do not match entities/event groups')
    exit_groups = {g for g, group in enumerate(events.groups)
                   if any(c.opcode == GO_TO_ROOM for c in group.commands)}
    template = next((e for e in entities.records if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == TRIGGER_TYPE
                     and e[26] == 2 and e[27] - 1 in exit_groups), None)
    if template is None: raise ValueError('Room has no native exit trigger to copy')
    if len(events.groups) >= 254: raise ValueError('Too many event groups')
    trigger = bytearray(template)
    struct.pack_into('<3i', trigger, 0, *center)
    struct.pack_into('<2H', trigger, 20, *size)
    trigger[27] = len(events.groups) + 1
    # Entities: extend the final batch; its header grows only at 4-byte steps.
    last = entities.batches[-1]
    lengths = [len(r) for r in last.records] + [len(trigger)]
    if len(lengths) > 255: raise ValueError('Too many entities in batch')
    header_size = (4 + len(lengths) + 3) // 4 * 4
    body = b''.join(last.records) + bytes(trigger)
    batch = struct.pack('<HBB', header_size + len(body), header_size, len(lengths)) + bytes(lengths)
    batch += bytes(header_size - len(batch)) + body
    section0 = b''.join(b.header + b''.join(b.records) for b in entities.batches[:-1]) + batch
    if Entities.parse(section0).records != entities.records + (bytes(trigger),):
        raise ValueError('Entity append verification failed')
    # Events: new trailing group; header padding is recomputed with zeros.
    operand = bytes([_byte(room, 'Room'), _byte(selector, 'Selector'), _byte(spawn, 'Spawn'), 0])
    assert len(operand) == OPERAND_WIDTHS[GO_TO_ROOM]
    groups = events.groups + (EventGroup((Command(GO_TO_ROOM, operand),)),)
    header_bytes = 2 * len(groups) + sum(1 + len(g.commands) for g in groups)
    section1 = Events(groups, bytes(-header_bytes % 4)).to_bytes()
    sections = list(record.sections)
    sections[0], sections[1] = section0, section1
    ends, total = [], 0
    for s in sections:
        total += len(s)
        ends.append(total)
    if total + 20 > 65535: raise ValueError('Object record exceeds u16 size')
    rec_header = bytearray(record.raw[:20])
    struct.pack_into('<H', rec_header, 0, total + 20)
    rec_header[3] = len(groups)
    struct.pack_into('<5H', rec_header, 8, *ends)
    new_record = bytes(rec_header) + b''.join(sections)
    # Names: trigger at the end of category 0, group at the end of category 1.
    slots = list(names.slots)
    c0, c1 = names.category_ends[0], names.category_ends[1]
    slots.insert(c1, _slot(group_name))
    slots.insert(c0, _slot(trigger_name))
    new_ends = (c0 + 1, *(e + 2 for e in names.category_ends[1:]))
    block = bytearray(names.raw[:20])
    struct.pack_into('<I', block, 0, 20 + 32 * len(slots))
    struct.pack_into('<7H', block, 6, *new_ends)
    block += b''.join(slots)
    result = _assemble(parsed, [new_record] + [r.raw for r in parsed.records[1:]],
                       [bytes(block)] + [n.raw for n in parsed.names[1:]])
    check = RoomObjects.parse(result)
    if check.names[0].category_ends != new_ends or Events.parse(check.records[0].sections[1], check.records[0].raw[3]).groups != groups:
        raise ValueError('Exit append verification failed')
    return result
