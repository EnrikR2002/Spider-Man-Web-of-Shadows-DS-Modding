"""Disposable-RAM room-registration probe, not a published chapter loader.

Use the kit's unused 1 KiB reservation for an extended lookup and five cloned
descriptors. Preserve native index 75 (invalid sentinel). No heap allocation,
position changes, native descriptors, ROM writes, or persistent writes.
"""
import struct

from tools import room_catalog, tasm_kit as kit

BASE = kit.KIT_STATE + 0x400
LIMIT = kit.TARGET + kit.RESERVE
FIRST = 76
ROOM_NAMES = ('ML_Platform', 'ML_Refuge', 'ML_Service', 'ML_Switching', 'ML_Gallery')
LOOKUP_LITERAL = 0x02084AC8
TEST_ENTRY = 0x020ED7B4
TEST_MODE = 0x020ED7DC
TEST_CONTEXT = 0x020ED7AC


def probe_image(arm9, names, resources=None, mode=2, test_context=True):
    if type(mode) is not int or mode not in (0,1,2): raise ValueError('Unsupported research entry record')
    if type(test_context) is not bool: raise ValueError('Test context must be boolean')
    rooms = room_catalog.parse(arm9, names)
    source = next(e for e in rooms if e.name == 'Test_Combat01')
    descriptors = BASE + (FIRST + len(ROOM_NAMES)) * 4
    labels = descriptors + len(ROOM_NAMES) * room_catalog.SIZE
    lookup = [e.address for e in rooms] + [0]
    data, strings = bytearray(), bytearray()
    for i, name in enumerate(ROOM_NAMES):
        raw = bytearray(source.raw)
        struct.pack_into('<I', raw, 0, labels + len(strings))
        strings.extend(name.encode('ascii') + b'\0')
        data.extend(raw)
        lookup.append(descriptors + i * room_catalog.SIZE)
    if resources:
        # A single authored shell demonstrates the resource-loading contract;
        # the other four descriptors remain native clones in this experiment.
        required = {'texture': '.nsbtx', 'bsp': '.bsp', 'objects': '.obj', 'model': '.nsbmd'}
        if set(resources) != set(required): raise ValueError('Incomplete room resource mapping')
        for kind, suffix in required.items():
            index = resources[kind]
            if type(index) is not int or not 0 <= index < len(names) or not names[index].endswith(suffix):
                raise ValueError('Invalid room resource index/type')
        for offset, key in ((4, 'texture'), (8, 'bsp'), (12, 'objects')):
            struct.pack_into('<I', data, offset, resources[key])
        model_pointer = labels + len(strings)
        strings.extend(bytes(-model_pointer % 4))
        model_pointer = labels + len(strings)
        strings.extend(struct.pack('<I', resources['model']))
        struct.pack_into('<I', data, 32, model_pointer)
    image = struct.pack(f'<{len(lookup)}I', *lookup) + data + strings
    image += bytes(-len(image) % 4)
    if BASE + len(image) > LIMIT: raise ValueError('Room probe exceeds unused kit reservation')
    for address, expected in ((LOOKUP_LITERAL, room_catalog.LOOKUP), (TEST_ENTRY, 0xE3A02046)):
        if struct.unpack_from('<I', arm9, address - 0x02000000)[0] != expected:
            raise ValueError('Native room lookup/test entry changed')
    patches = [
        {'addr': BASE, 'hex': image.hex(), 'expect': bytes(len(image)).hex()},
        {'addr': LOOKUP_LITERAL, 'hex': struct.pack('<I', BASE).hex(), 'expect': struct.pack('<I', room_catalog.LOOKUP).hex()},
        {'addr': TEST_ENTRY, 'hex': struct.pack('<I', 0xE3A02000 | FIRST).hex(), 'expect': struct.pack('<I', 0xE3A02046).hex()}
    ]
    if mode != 2:
        if struct.unpack_from('<I',arm9,TEST_MODE-0x02000000)[0] != 0xE3A02002:
            raise ValueError('Native test mode instruction changed')
        patches.append({'addr':TEST_MODE,'hex':struct.pack('<I',0xE3A02000 | mode).hex(),
                        'expect':struct.pack('<I',0xE3A02002).hex()})
    if not test_context:
        if struct.unpack_from('<I',arm9,TEST_CONTEXT-0x02000000)[0] != 0xE3A01001:
            raise ValueError('Native test-context instruction changed')
        patches.append({'addr':TEST_CONTEXT,'hex':struct.pack('<I',0xE3A01000).hex(),
                        'expect':struct.pack('<I',0xE3A01001).hex()})
    return patches
