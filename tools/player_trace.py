"""Read-only player probes for the hash-identified CS5E ARM9, not a RAM editor.

RTTI identifies the Spidey vtables. Field labels reflect paired observations;
only resource IDs/state changes and the attack-clock correlation are established.
"""
import struct

ARM9_SHA256 = 'e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc'
BASE = 0x02000000
VTABLES = (0x0212e3f0, 0x0212e40c, 0x0212e510)
COMBO_MODEL_POINTER = 0x02145c44
CONTROLLER_VTABLE = 0x021352a4


def sample_combo(ram: bytes):
    """Read the clean ARM9's combo model; labels await paired hit confirmation."""
    if len(ram) != 4 * 1024 * 1024: raise ValueError('Expected 4 MiB DS main RAM')
    address = struct.unpack_from('<I', ram, COMBO_MODEL_POINTER - BASE)[0]
    if not address: return None
    offset = address - BASE
    if not 0 <= offset <= len(ram) - 0x20: raise ValueError('Combo model outside main RAM')
    return {'address': address, **{name: struct.unpack_from('<i', ram, offset + field)[0]
            for name, field in (('level_candidate', 0), ('gauge_fixed_candidate', 4),
                                ('grace_candidate', 0x10), ('decay_candidate', 0x14))},
            'active_candidate': ram[offset + 0x18], 'credit_marker_candidate': ram[offset + 0x19]}


def sample(ram: bytes):
    if len(ram) != 4 * 1024 * 1024: raise ValueError('Expected 4 MiB DS main RAM')
    candidates, start = [], 0
    needle = struct.pack('<I', VTABLES[0])
    while (start := ram.find(needle, start)) >= 0:
        if start + 0x34 <= len(ram) and (struct.unpack_from('<I', ram, start+8)[0],
                struct.unpack_from('<I', ram, start+20)[0]) == VTABLES[1:]:
            candidates.append(start)
        start += 4
    if len(candidates) != 1: raise ValueError(f'Expected one live Spidey layout, found {len(candidates)}')
    actor = candidates[0]
    motion = struct.unpack_from('<I', ram, actor+0x30)[0] - BASE
    if not 0 <= motion <= len(ram) - 0x300: raise ValueError('Player motion pointer outside main RAM')
    values = {name: struct.unpack_from('<I', ram, motion+offset)[0] for name, offset in (
        ('last_gab_id', 0x16c), ('event_clock_candidate', 0x178), ('gmb_id', 0x230),
        ('gmb_length_candidate', 0x23c), ('action_id_candidate', 0x254))}
    # The position getter 0x02074CD0 sums the base and local offsets. Do not
    # confuse the +88/+8C/+90 vector (geometry dimensions) with position.
    position = [struct.unpack_from('<i', ram, motion+base)[0] +
                struct.unpack_from('<i', ram, motion+local)[0]
                for base, local in ((0x7c, 0x160), (0x80, 0x164))]
    facing = struct.unpack_from('<I', ram, motion+0x180)[0]
    controller_address = struct.unpack_from('<I', ram, motion+0x1f8)[0]
    controller = None
    if controller_address:
        offset = controller_address - BASE
        if controller_address % 4 or not 0 <= offset <= len(ram) - 0x48:
            raise ValueError('Player controller pointer outside aligned main RAM')
        vtable = struct.unpack_from('<I', ram, offset)[0]
        owner = struct.unpack_from('<I', ram, offset+0x44)[0]
        if vtable != CONTROLLER_VTABLE or owner != BASE+actor:
            raise ValueError('Player controller vtable/owner mismatch')
        controller = {'address': controller_address,
                      'state_id_candidate': struct.unpack_from('<I', ram, offset+0x14)[0]}
    return {'actor_address': BASE+actor, 'motion_address': BASE+motion, **values,
            'position_q12_candidate': position, 'facing_candidate': facing,
            'controller': controller,
            'motion_flags_candidate': struct.unpack_from('<I', ram, motion+0x2fc)[0],
            'combo': sample_combo(ram)}
