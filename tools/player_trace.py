"""Read-only player probes for the hash-identified CS5E ARM9, not a RAM editor.

RTTI identifies the Spidey vtables. Field labels reflect paired observations;
only resource IDs/state changes and the attack-clock correlation are established.
"""
import struct

ARM9_SHA256 = 'e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc'
BASE = 0x02000000
VTABLES = (0x0212e3f0, 0x0212e40c, 0x0212e510)


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
    return {'actor_address': BASE+actor, 'motion_address': BASE+motion, **values}
