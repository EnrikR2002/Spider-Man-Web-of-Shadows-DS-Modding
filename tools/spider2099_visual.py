"""Guarded cosmetic display-list selection on the native shared player model.

Both native forms load spd.nsbmd. Keep its original Red list and append the Black
sculpt list, selected immediately before native model draw. No actor, motion,
animation, purchase or kit state is changed; no live pointer is cached.
"""
import struct

from tools import wos_tool as w,tasm_kit as kit,midnight_voltage,crane_row
from tools.chapter_renewal_combat import asm
from tools.model_geometry import ModelGeometry
from tools.animation_rig import AnimationRig
from tools.nitro_texture import dictionary,TextureArchive

PARENT='2ebdf894ae723ce6ead2cfbe15a4b11151243f639958bdeea18e9149bdabf088'
MAGIC=b'S2099DL1'
TRAILER_SIZE=64
HOOK_EXEC=0x01FF87C0
ORIGINAL_WORD=0xE1A00005  # mov r0,r5; native model wrapper immediately before draw
MODEL_VTABLE=0x021284B4
STATS_POINTER=0x02145C5C


def material(raw):
    g=ModelGeometry.parse(raw);base=g.model+w.u32(raw,g.model+8)
    rows=dictionary(raw,base+4,4)
    if len(rows)!=1:raise ValueError('Expected one shared player material')
    return base+w.u32(rows[0][1],0)


def _magnification(texture,width,height):
    extra=TextureArchive.parse(texture).textures[0]['unknown_u32']
    return (round((extra&2047)*4096/width),round(((extra>>11)&2047)*4096/height))


def shared_model(red,black,red_texture,black_texture):
    r,b=ModelGeometry.parse(red),ModelGeometry.parse(black)
    rr,br=AnimationRig.parse(red),AnimationRig.parse(black)
    if (rr.names,rr.parents,rr.node_records)!=(br.names,br.parents,br.node_records):
        raise ValueError('Dual appearance cannot change the shared native rig')
    if len(r.shapes)!=1 or len(b.shapes)!=1:raise ValueError('Expected one native player shape')
    out=bytearray(red);black_at=len(out);stream=black[b.shapes[0].start:b.shapes[0].start+b.shapes[0].length]
    out.extend(stream);trailer_at=len(out);mat=material(red);black_mat=material(black)
    red_dims=struct.unpack_from('<2H',red,mat+32);black_dims=struct.unpack_from('<2H',black,black_mat+32)
    size=len(out)+TRAILER_SIZE-r.model
    words=(*struct.unpack('<2I',MAGIC),r.shapes[0].header-r.model,mat-r.model,
        w.u32(red,r.shapes[0].header+8),r.shapes[0].length,
        black_at-r.shapes[0].header,len(stream),red_dims[0]|red_dims[1]<<16,
        black_dims[0]|black_dims[1]<<16,*_magnification(red_texture,*red_dims),
        *_magnification(black_texture,*black_dims),size,0x50333031)
    out.extend(struct.pack('<16I',*words))
    for at,value in ((8,len(out)),(r.block+4,len(out)-r.block),(r.model,len(out)-r.model)):
        struct.pack_into('<I',out,at,value)
    # Counts and box cover either list; only the selected list is submitted.
    counts=tuple(max(x,y) for x,y in zip(struct.unpack_from('<4H',red,r.model+36),struct.unpack_from('<4H',black,b.model+36)))
    struct.pack_into('<4H',out,r.model+36,*counts)
    if red[r.model+56:r.model+64]!=black[b.model+56:b.model+64]:raise ValueError('Box scale changed')
    rb,bb=(struct.unpack_from('<6h',raw,g.model+44) for raw,g in ((red,r),(black,b)))
    lo=[min(rb[i],bb[i]) for i in range(3)];hi=[max(rb[i]+rb[i+3],bb[i]+bb[i+3]) for i in range(3)]
    struct.pack_into('<6h',out,r.model+44,*lo,*(hi[i]-lo[i] for i in range(3)))
    g=ModelGeometry.parse(out)
    if out[g.shapes[0].start:g.shapes[0].start+g.shapes[0].length]!=red[r.shapes[0].start:r.shapes[0].start+r.shapes[0].length]:
        raise ValueError('Default Red GPU list changed')
    return bytes(out),{'model_size':size,'metadata_offset':trailer_at-r.model,'shape_offset':words[2],
        'material_offset':words[3],'red_stream_bytes':words[5],'black_stream_bytes':words[7],
        'red_dimensions':list(red_dims),'black_dimensions':list(black_dims),
        'red_magnification':list(words[10:12]),'black_magnification':list(words[12:14]),
        'default_red_list_exact':True,'one_list_per_draw':True,'trailer':list(words)}


def selected_model(raw,form):
    """Offline equivalent of the draw selector for artifact/pose review."""
    if form not in (0,1):raise ValueError('Expected native Red/Black form')
    g=ModelGeometry.parse(raw);words=struct.unpack_from('<16I',raw,len(raw)-TRAILER_SIZE)
    if raw[-TRAILER_SIZE:-TRAILER_SIZE+8]!=MAGIC:raise ValueError('Missing shared-model tag')
    out=bytearray(raw);shape=g.model+words[2];mat=g.model+words[3]
    struct.pack_into('<2I',out,shape+8,*words[4+form*2:6+form*2])
    struct.pack_into('<I',out,mat+32,words[8+form])
    struct.pack_into('<2I',out,mat+36,*words[10+form*2:12+form*2])
    return bytes(out)


def selector_source(at,metadata):
    magic0,magic1=struct.unpack('<2I',MAGIC)
    return f'''
        push {{r0-r12,lr}}
        mrs r12,cpsr
        push {{r3,r12}}
        mov r0,r5
        bl select_visual
        pop {{r3,r12}}
        msr cpsr_f,r12
        pop {{r0-r12,lr}}
        mov r0,r5
        b #0x{HOOK_EXEC+4:x}
    select_visual:
        push {{r4-r8,lr}}
        ldr r1,ram_low
        cmp r0,r1
        blo done
        ldr r2,wrapper_high
        cmp r0,r2
        bhi done
        tst r0,#3
        bne done
        ldr r1,[r0]
        ldr r2,model_vtable
        cmp r1,r2
        bne done
        ldr r4,[r0,#0x14]
        ldr r1,ram_low
        cmp r4,r1
        blo done
        ldr r2,model_high
        cmp r4,r2
        bhi done
        tst r4,#3
        bne done
        ldr r1,[r4]
        ldr r2,model_size
        cmp r1,r2
        bne done
        ldr r1,metadata_offset
        add r6,r4,r1
        ldr r1,[r6]
        ldr r2,magic_a
        cmp r1,r2
        bne done
        ldr r1,[r6,#4]
        ldr r2,magic_b
        cmp r1,r2
        bne done
        ldr r1,[r6,#56]
        ldr r2,model_size
        cmp r1,r2
        bne done
        ldr r1,[r6,#60]
        ldr r2,tail_magic
        cmp r1,r2
        bne done
        ldr r1,stats_cell
        ldr r1,[r1]
        ldr r2,ram_low
        cmp r1,r2
        blo done
        ldr r2,stats_high
        cmp r1,r2
        bhi done
        tst r1,#3
        bne done
        ldrb r7,[r1,#0x53]
        cmp r7,#1
        bhi done
        ldr r1,[r6,#8]
        ldr r2,shape_offset
        cmp r1,r2
        bne done
        ldr r1,[r6,#12]
        ldr r2,material_offset
        cmp r1,r2
        bne done
        ldr r1,[r6,#8]
        add r5,r4,r1
        add r8,r6,#16
        add r8,r8,r7,lsl #3
        ldr r1,[r8]
        ldr r2,[r8,#4]
        cmp r2,#4
        blo done
        tst r2,#3
        bne done
        add r3,r5,r1
        cmp r3,r4
        blo done
        tst r3,#3
        bne done
        add r0,r3,r2
        cmp r0,r3
        blo done
        cmp r0,r6
        bhi done
        str r1,[r5,#8]
        str r2,[r5,#12]
        ldr r1,[r6,#12]
        add r5,r4,r1
        add r8,r6,#32
        ldr r1,[r8,r7,lsl #2]
        str r1,[r5,#32]
        add r8,r6,#40
        add r8,r8,r7,lsl #3
        ldr r1,[r8]
        ldr r2,[r8,#4]
        str r1,[r5,#36]
        str r2,[r5,#40]
    done:
        pop {{r4-r8,pc}}
    ram_low: .word 0x02004000
    wrapper_high: .word 0x023ffe00
    model_high: .word 0x{0x02400000-metadata['model_size']:x}
    stats_high: .word 0x023fff00
    model_vtable: .word 0x{MODEL_VTABLE:x}
    model_size: .word {metadata['model_size']}
    metadata_offset: .word {metadata['metadata_offset']}
    shape_offset: .word {metadata['shape_offset']}
    material_offset: .word {metadata['material_offset']}
    magic_a: .word 0x{magic0:x}
    magic_b: .word 0x{magic1:x}
    tail_magic: .word 0x50333031
    stats_cell: .word 0x{STATS_POINTER:x}
    '''


class Runtime(midnight_voltage.Runtime):
    def __init__(self,rom):
        if w.sha256(rom)!=PARENT:raise ValueError('Visual selector requires exact v0.30.0')
        self.rom=rom;self.header=w.parse_header(rom);h=self.header
        self.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];self.new=bytearray(self.arm)
        self.end=len(self.arm)-36;self.start=kit.TARGET+self.end-kit.SOURCE;self.data=bytearray()

    def install(self,metadata):
        # First autoload segment is ITCM. Derive its physical ROM source offset.
        table=w.u32(self.arm,kit.TABLE_POINTERS)-kit.BASE
        destination,size,_=struct.unpack_from('<3I',self.arm,table)
        if destination!=0x01ff8000 or not destination<=HOOK_EXEC<destination+size:
            raise ValueError('Unexpected native ITCM mapping')
        source=w.u32(self.arm,0xb6c)-kit.BASE+HOOK_EXEC-destination
        if w.u32(self.arm,source)!=ORIGINAL_WORD:raise ValueError('Native pre-draw hook changed')
        at=self.alloc();code=asm(selector_source(at,metadata),at);self.data.extend(code)
        struct.pack_into('<I',self.new,source,crane_row.branch(HOOK_EXEC,at))
        return {'execution_hook':HOOK_EXEC,'arm9_hook_source_offset':source,'code_address':at,
            'code_bytes':len(code),'code_sha256':w.sha256(code),
            'abi':'All registers and CPSR flags preserved, then native mov r0,r5 replayed.',
            'guards':'Live wrapper bounds/vtable, fresh MDL bounds/size, private footer tag and offsets, bounded native stats/form. No cached RAM pointer.',
            'writes':'Selected shape display-list pointer/length and material dimensions/magnification only.',
            'player_kit_32k_unchanged':True}
