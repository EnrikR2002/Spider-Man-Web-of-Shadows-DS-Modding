"""Append entity batches and event groups to CS5E OBJ records (room scripting).

Grounded in all 75 clean rooms (TECHNICAL "OBJ event commands and room scripting"):
- Section 0 entity batches are the record's *action groups* (AGs): record header
  byte +2 is the batch count and name category 2 holds one name per batch
  ('<AG_INIT>', 'EnemySpawners', 'Switch', ...). Category 0 names the entities
  in concatenated batch order, category 1 the event groups (EGs, header +3).
- Event commands reference an entity as (AG index 0-based, entity 1-based within
  that batch): every native 0x01 target is then a character or object.
- An *action* (handlers 0x02039DE0 delay, 0x02039F3C conditional) is 4 bytes:
  entity (AG 0-based, entity 1-based) to activate, AG to activate (1-based),
  EG to run (1-based); 0 = none. Delay 0x1C = u16 frames + one action;
  conditional 0x1D = u16 var, u16 frames, op, value, then-action, else-action.
  An appended AG's entities stay inert until activated. 0x03 takes the same
  entity/AG bytes and deactivates them (one-shot triggers remove themselves).
- 0x0F locks/unlocks a door entity; an object's byte +23 is the EG run when it
  is destroyed; a player-collide trigger runs the EG in its last byte.
Entities, AGs and EGs are only appended, so every existing index keeps its
meaning; `drop_commands` removes whole commands (no index moves). Results are
re-parsed; unknown bytes are preserved.
"""
from __future__ import annotations

import struct

from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

SET_VAR, INC_VAR, IF_VAR, DELAY, ANIMATE = 0x26, 0x25, 0x1D, 0x1C, 0x01
DEACTIVATE, DOOR = 0x03, 0x0F
TRIGGER_TYPE = 7
COMPARE = {'==': 0, '!=': 1, '<': 2, '<=': 3, '>': 4, '>=': 5}


def _slot(label):
    data = label.encode('ascii')
    if not data or len(data) > 31 or b'\0' in data: raise ValueError('Name must be 1..31 ASCII characters')
    return data + b'\0' + b' ' * max(0, 30 - len(data)) + (b'\0' if len(data) < 31 else b'')


def _byte(value, label):
    if type(value) is not int or not 0 <= value <= 255: raise ValueError(f'{label} must be a byte')
    return value


def _events_bytes(groups):
    count = 2 * len(groups) + sum(1 + len(g.commands) for g in groups)
    return Events(tuple(groups), bytes(-count % 4)).to_bytes()


def _replace(parsed, record, sections, header_bytes, names):
    """Rebuild one record (sections 0/1, header counts) and its name block."""
    rec = parsed.records[record]
    payload = [sections.get(i, s) for i, s in enumerate(rec.sections)]
    ends = [sum(map(len, payload[:i + 1])) for i in range(5)]
    if ends[-1] + 20 > 65535: raise ValueError('Object record exceeds u16 size')
    raw = bytearray(rec.raw[:20])
    struct.pack_into('<H', raw, 0, ends[-1] + 20)
    struct.pack_into('<5H', raw, 8, *ends)
    raw += b''.join(payload)
    for at, value in header_bytes.items(): raw[at] = _byte(value, 'Record count')
    records = [r.raw for r in parsed.records]
    records[record] = bytes(raw)
    blocks = [n.raw for n in parsed.names]
    blocks[record] = names
    header = bytearray(parsed.header)
    end = len(header) + sum(map(len, records))
    struct.pack_into('<2I', header, 4, end, end + len(parsed.between))
    result = bytes(header) + b''.join(records) + parsed.between + b''.join(blocks)
    RoomObjects.parse(result)
    return result


def _name_block(names, inserts):
    """Insert slots at the end of the given categories: {category: [labels]}."""
    slots, ends = list(names.slots), list(names.category_ends)
    for category in sorted(inserts, reverse=True):
        at = ends[category]
        slots[at:at] = [_slot(x) for x in inserts[category]]
        for c in range(category, 7): ends[c] += len(inserts[category])
    block = bytearray(names.raw[:20])
    struct.pack_into('<I', block, 0, 20 + 32 * len(slots))
    struct.pack_into('<7H', block, 6, *ends)
    return bytes(block) + b''.join(slots)


def counts(raw, record):
    """(entities per AG, event-group count) checked against the name categories."""
    parsed = RoomObjects.parse(raw)
    rec, names = parsed.records[record], parsed.names[record]
    batches = Entities.parse(rec.sections[0]).batches
    groups = len(Events.parse(rec.sections[1], rec.raw[3]).groups)
    ends = names.category_ends
    if (rec.raw[2] != len(batches) or ends[0] != sum(len(b.records) for b in batches)
            or ends[1] - ends[0] != groups or ends[2] - ends[1] != len(batches)):
        raise ValueError('Record names do not match its batches/event groups')
    return tuple(len(b.records) for b in batches), groups


def append_batch(raw, record, entities, name):
    """Append one AG holding [(entity bytes, name), ...]; returns (raw, AG index)."""
    parsed = RoomObjects.parse(raw)
    if type(record) is not int or not 0 <= record < len(parsed.records): raise ValueError('Record out of range')
    sizes, _ = counts(raw, record)
    rec = parsed.records[record]
    if not entities or len(entities) > 255 or len(sizes) >= 255: raise ValueError('Batch limits exceeded')
    lengths = [len(e) for e, _ in entities]
    if not all(0 < n < 256 for n in lengths): raise ValueError('Entity length must be 1..255')
    header_size = (4 + len(lengths) + 3) // 4 * 4
    body = b''.join(bytes(e) for e, _ in entities)
    batch = struct.pack('<HBB', header_size + len(body), header_size, len(lengths)) + bytes(lengths)
    batch += bytes(header_size - len(batch)) + body
    section0 = rec.sections[0] + batch
    old = Entities.parse(rec.sections[0]).records
    if Entities.parse(section0).records != old + tuple(bytes(e) for e, _ in entities):
        raise ValueError('Batch append failed')
    names = _name_block(parsed.names[record], {0: [n for _, n in entities], 2: [name]})
    result = _replace(parsed, record, {0: section0}, {2: len(sizes) + 1}, names)
    if counts(result, record)[0] != sizes + (len(entities),): raise ValueError('Batch append verification failed')
    return result, len(sizes)


def append_groups(raw, record, groups):
    """Append event groups [(EventGroup, name), ...]; returns (raw, first 1-based EG id)."""
    parsed = RoomObjects.parse(raw)
    sizes, count = counts(raw, record)
    rec = parsed.records[record]
    events = Events.parse(rec.sections[1], rec.raw[3])
    new = events.groups + tuple(g for g, _ in groups)
    if len(new) > 255: raise ValueError('Too many event groups')
    names = _name_block(parsed.names[record], {1: [n for _, n in groups]})
    result = _replace(parsed, record, {1: _events_bytes(new)}, {3: len(new)}, names)
    check = RoomObjects.parse(result).records[record]
    if Events.parse(check.sections[1], check.raw[3]).groups != new or counts(result, record) != (sizes, len(new)):
        raise ValueError('Group append verification failed')
    return result, count + 1


def names(raw, record):
    """(entity names per AG, EG names, AG names) of a record, checked by `counts`."""
    sizes, _ = counts(raw, record)
    block = RoomObjects.parse(raw).names[record]
    labels, ends = block.labels, block.category_ends
    entities, at = [], 0
    for size in sizes:
        entities.append(tuple(labels[at:at + size])); at += size
    return tuple(entities), tuple(labels[ends[0]:ends[1]]), tuple(labels[ends[1]:ends[2]])


def actions(command):
    """The 4-byte actions of a delay, conditional or deactivate command (else none)."""
    o = command.operand
    if command.opcode == DELAY: return (o[2:6],)
    if command.opcode == IF_VAR: return (o[6:10], o[10:14])
    if command.opcode == DEACTIVATE: return (o[0:4],)
    return ()


def targets(act):
    """AG indices (0-based) an action's entity and AG parts refer to."""
    a, entity, ag, _ = act
    return ({a} if entity else set()) | ({ag - 1} if ag else set())


def drop_commands(raw, record, drop):
    """Remove every command for which drop(group index, command) is true; returns (raw, removed)."""
    parsed = RoomObjects.parse(raw)
    rec = parsed.records[record]
    events = Events.parse(rec.sections[1], rec.raw[3])
    groups, removed = [], []
    for g, group in enumerate(events.groups):
        keep = []
        for command in group.commands:
            if drop(g, command): removed.append((g, command))
            else: keep.append(command)
        groups.append(EventGroup(tuple(keep)))
    if not removed: return raw, removed
    return parsed.replace_section(record, 1, _events_bytes(groups)), removed


def extend_group(raw, record, group, commands, *, prepend=False):
    """Add commands to an existing EG (0-based index); names and counts unchanged."""
    parsed = RoomObjects.parse(raw)
    rec = parsed.records[record]
    events = Events.parse(rec.sections[1], rec.raw[3])
    groups = list(events.groups)
    old = groups[group].commands
    groups[group] = EventGroup(tuple(commands) + old if prepend else old + tuple(commands))
    if len(groups[group].commands) > 255: raise ValueError('Too many event commands')
    return parsed.replace_section(record, 1, _events_bytes(groups))


# --- Command builders (operand layouts in TECHNICAL) -------------------------

def set_var(var, value):
    return Command(SET_VAR, struct.pack('<HBB', var, _byte(value, 'Value'), 0))


def action(ag=None, eg=0, entity=None):
    """4-byte action: activate `entity` (AG 0-based, entity 1-based), AG (0-based index), run EG (1-based).

    An out-of-range entity froze a room load in the lab; callers pass indices
    returned by append_batch/append_groups.
    """
    a, e = entity if entity else (0, 0)
    return bytes((_byte(a, 'AG'), _byte(e, 'Entity'), 0 if ag is None else _byte(ag + 1, 'AG'), _byte(eg, 'EG')))


def activate(ag=None, eg=0, frames=0, entity=None):
    """0x1C: after `frames`, run one action (see `action`)."""
    return Command(DELAY, struct.pack('<H', frames) + action(ag, eg, entity) + bytes(2))


def deactivate(ag=None, entity=None):
    """0x03: deactivate an AG (0-based index) or one entity (AG 0-based, entity 1-based)."""
    return Command(DEACTIVATE, action(ag, 0, entity))


def door(entity, locked):
    """0x0F: lock or unlock a door entity (AG 0-based, entity 1-based); native Lock_Grate/Door_Lock."""
    return Command(DOOR, bytes((_byte(entity[0], 'AG'), _byte(entity[1], 'Entity'), 1, 1 if locked else 0, 0, 1, 0, 0)))


def trigger(x, y, size, group, z=0):
    """Player-collide trigger entity (28 bytes, Q12 centre, box in units) running EG `group` (1-based).

    Same bytes as the native ambush/one-shot triggers of record 1 (word +16 = -1,
    mode 2 = touch); exits in record 0 use word 0 instead.
    """
    return struct.pack('<3i2I3H2B', x, y, z, TRIGGER_TYPE, 0xFFFFFFFF, size[0], size[1], 0x0A, 2, _byte(group, 'EG'))


def if_var(var, op, value, then=b'\0' * 4, otherwise=b'\0' * 4, frames=0):
    """0x1D: compare a game variable (unsigned) and run the then/else `action`."""
    return Command(IF_VAR, struct.pack('<HHBB', var, frames, COMPARE[op], _byte(value, 'Value'))
                   + bytes(then) + bytes(otherwise) + bytes(2))


def animate(ag, entity, anim, extra=0):
    """0x01: play animation `anim` on entity (AG 0-based, entity 1-based in the batch)."""
    return Command(ANIMATE, bytes((_byte(ag, 'AG'), _byte(entity, 'Entity'), _byte(anim, 'Animation'), extra)))
