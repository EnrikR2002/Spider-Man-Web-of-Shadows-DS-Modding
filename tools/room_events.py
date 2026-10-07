"""Lossless CS5E OBJ event-group framing, grounded in the native ARM9 tables.

Operand widths are known; most opcode/operand meanings remain unknown. Entity
references are relative to the event's runtime bank, not necessarily OBJ record 0.
Repacking does not automatically repair names, entity references or event links.
"""
from dataclasses import dataclass
import struct


# 0x02119CCC, consumed by 0x0203134C; dispatch records at 0x021199F8.
OPERAND_WIDTHS = (4,4,4,4,4,24,4,32,4,4,8,4,12,4,4,8,16,4,4,4,
                  4,8,4,4,4,4,0,4,8,16,12,16,0,4,4,4,4,4,4)


@dataclass(frozen=True)
class Command:
    opcode: int
    operand: bytes


@dataclass(frozen=True)
class EventGroup:
    commands: tuple[Command, ...]


@dataclass(frozen=True)
class Events:
    groups: tuple[EventGroup, ...]
    padding: bytes

    @classmethod
    def parse(cls, raw, count):
        raw = bytes(raw)
        if type(count) is not int or not 0 <= count <= 255:
            raise ValueError('Event-group count must be a byte')
        if count == 0:
            if raw: raise ValueError('Data without event groups')
            return cls((), b'')
        if len(raw) < count * 2: raise ValueError('Truncated event offsets')
        offsets = struct.unpack_from('<' + str(count) + 'H', raw)
        at, types = 2 * count, []
        for _ in range(count):
            if at >= len(raw): raise ValueError('Truncated event command header')
            end = at + 1 + raw[at]
            if end > len(raw): raise ValueError('Truncated event opcodes')
            opcodes = tuple(raw[at + 1:end])
            if any(op >= len(OPERAND_WIDTHS) for op in opcodes):
                raise ValueError('Unknown opcode outside native width table')
            types.append(opcodes)
            at = end
        aligned = (at + 3) // 4 * 4
        if aligned > len(raw): raise ValueError('Truncated event header padding')
        padding, expected, groups = raw[at:aligned], aligned, []
        for index, (offset, opcodes) in enumerate(zip(offsets, types)):
            if offset != expected: raise ValueError('Noncontiguous event operands')
            commands = []
            for opcode in opcodes:
                end = offset + OPERAND_WIDTHS[opcode]
                if end > len(raw): raise ValueError('Truncated event operand')
                commands.append(Command(opcode, raw[offset:end]))
                offset = end
            expected = offsets[index + 1] if index + 1 < count else len(raw)
            if offset != expected: raise ValueError('Event operand widths disagree with bounds')
            groups.append(EventGroup(tuple(commands)))
        return cls(tuple(groups), padding)

    def to_bytes(self):
        """Byte-exact reconstruction, including the native header padding."""
        count = len(self.groups)
        if count > 255: raise ValueError('Too many event groups')
        if not count:
            if self.padding: raise ValueError('Padding without groups')
            return b''
        header, operands, offsets = bytearray(), bytearray(), []
        for group in self.groups:
            if len(group.commands) > 255: raise ValueError('Too many event commands')
            header.append(len(group.commands))
            for command in group.commands:
                if type(command.opcode) is not int or not 0 <= command.opcode < len(OPERAND_WIDTHS):
                    raise ValueError('Opcode outside native width table')
                if len(command.operand) != OPERAND_WIDTHS[command.opcode]:
                    raise ValueError('Wrong operand width')
                header.append(command.opcode)
        needed = -(2 * count + len(header)) % 4
        if len(self.padding) != needed: raise ValueError('Padding disagrees with event header')
        header.extend(self.padding)
        start = 2 * count + len(header)
        for group in self.groups:
            offsets.append(start + len(operands))
            for command in group.commands: operands.extend(command.operand)
        if start + len(operands) > 65535: raise ValueError('Event section exceeds u16 bounds')
        return struct.pack('<' + str(count) + 'H', *offsets) + header + operands

    def omit_commands(self, group_index, command_indices=()):
        """Explicit structural edit; callers must qualify all remaining links."""
        if type(group_index) is not int or not 0 <= group_index < len(self.groups):
            raise ValueError('Event group index out of range')
        indices = set(command_indices)
        old = self.groups[group_index]
        if any(type(i) is not int or not 0 <= i < len(old.commands) for i in indices):
            raise ValueError('Event command index out of range')
        if not indices: return self.to_bytes()
        groups = list(self.groups)
        groups[group_index] = EventGroup(tuple(c for i,c in enumerate(old.commands) if i not in indices))
        header_size = 2 * len(groups) + sum(1 + len(g.commands) for g in groups)
        needed = -header_size % 4
        padding = self.padding[:needed] + bytes(max(0,needed-len(self.padding)))
        result = Events(tuple(groups), padding).to_bytes()
        self.parse(result, len(groups))
        return result
