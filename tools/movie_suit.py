#!/usr/bin/env python3
"""Hash-bounded 128x128 I8 suit experiment, retaining geometry and animation."""
from __future__ import annotations
import math
import argparse
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w
from tools.nitro_texture import TextureArchive, dictionary, preview
from tools.suit_uv_inspect import uv_body_map, render

DEST = mod.ROOT / 'build/movie-suit-clean'
SIZE = 128


def resize_i8(raw, indices, palette, size=128):
    if w.sha256(raw)!='461b2a00b617a4987e84338a63d7242ce54052c9537d85b8308719aa980c5206':
        raise ValueError('Expected clean hash-identified red suit texture')
    a = TextureArchive.parse(raw)
    if (len(raw), a.palette_start, a.palette_size) != (4772, 4260, 512) or len(a.textures) != 1:
        raise ValueError('Expected bounded 64x64 suit archive')
    t = a.textures[0]
    if (t['offset'], t['size'], t['format'], t['width'], t['height']) != (164,4096,4,64,64):
        raise ValueError('Unsupported suit texture layout')
    if size not in (64,128) or len(indices)!=size*size or len(palette)!=512:
        raise ValueError('Invalid replacement texture dimensions')
    if size==64:
        return raw[:164]+indices+palette
    delta=size*size-4096
    out=bytearray(raw[:164]+indices+palette)
    struct.pack_into('<I',out,8,len(out))
    struct.pack_into('<I',out,24,len(out)-20)
    struct.pack_into('<H',out,20+0x0c,size*size//8)
    # Empty compressed pools track the old end of the ordinary pixel pool.
    for off in (0x24,0x28,0x38):
        struct.pack_into('<I',out,20+off,w.u32(raw,20+off)+delta)
    # Texture dictionary data entry starts at 0x64 for this exact profile.
    params=w.u32(raw,0x64)
    struct.pack_into('<I',out,0x64,(params & ~((7<<20)|(7<<23))) | 4<<20 | 4<<23)
    parsed=TextureArchive.parse(bytes(out))
    if parsed.textures[0]['width']!=size or parsed.palette_start!=164+size*size:
        raise ValueError('Resized texture validation failed')
    return bytes(out)


def uv_offsets(raw):
    if raw[:4]!=b'BMD0': raise ValueError('Expected NSBMD')
    block=w.u32(raw,16)
    models=dictionary(raw,block+8,4)
    if len(models)!=1 or models[0][0]!='spd': raise ValueError('Expected player model')
    model=block+struct.unpack('<I',models[0][1])[0]
    mats=model+w.u32(raw,model+8)
    entries=dictionary(raw,mats+4,4)
    if len(entries)!=1: raise ValueError('Expected one player material')
    material=mats+struct.unpack('<I',entries[0][1])[0]
    if (w.u16(raw,material+32),w.u16(raw,material+34))!=(64,64):
        raise ValueError('Expected clean 64x64 material dimensions')
    shapes=model+w.u32(raw,model+12)
    offsets=[]
    counts={0:0,0x14:1,0x1b:3,0x20:1,0x21:1,0x22:1,0x23:2,
            0x24:1,0x25:1,0x26:1,0x27:1,0x28:1,0x40:1,0x41:0}
    for _,entry in dictionary(raw,shapes,4):
        shape=shapes+struct.unpack('<I',entry)[0]
        if w.u16(raw,shape+2)!=16: raise ValueError('Unsupported shape header')
        pos=shape+w.u32(raw,shape+8); end=pos+w.u32(raw,shape+12)
        w.check_range(raw,pos,end-pos,'shape commands')
        while pos<end:
            commands=raw[pos:pos+4]; pos+=4
            for opcode in commands:
                if opcode not in counts: raise ValueError(f'Unsupported GPU opcode {opcode:x}')
                if opcode==0x22: offsets.append(pos)
                pos+=counts[opcode]*4
                if pos>end: raise ValueError('GPU packet exceeds shape')
    return material,offsets


def scale_model(raw, factor=2):
    if w.sha256(raw)!='ca645169617bb0af052786380823542b9c96de19916bd3440699baf33dfdd0d4':
        raise ValueError('Expected clean hash-identified red suit model')
    if factor not in (1,2): raise ValueError('Only bounded 1x/2x scaling supported')
    material,offsets=uv_offsets(raw)
    out=bytearray(raw)
    for off in offsets:
        u,v=struct.unpack_from('<hh',raw,off)
        if not all(-32768<=x*factor<=32767 for x in (u,v)):
            raise ValueError('UV fixed-point overflow')
        struct.pack_into('<hh',out,off,u*factor,v*factor)
    struct.pack_into('<HH',out,material+32,64*factor,64*factor)
    return bytes(out)


def segment_distance(x,y,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)


def artwork(raw, style='clean', body=None):
    if style not in ('clean', 'legacy'):
        raise ValueError('Unknown suit art style')
    a=TextureArchive.parse(raw); t=a.textures[0]
    source=raw[t['offset']:t['offset']+4096]
    body=uv_body_map(SIZE) if body is None else body
    if len(body)!=SIZE*SIZE:
        raise ValueError('Body map must match texture dimensions')
    colors=[]
    for py in range(SIZE):
        for px in range(SIZE):
            i=source[(py//2)*64+px//2]
            old=w.u16(raw,a.palette_start+i*2)
            r,g,b=(old>>s&31 for s in (0,5,10))
            p=body[py*SIZE+px]
            if p is None:
                colors.append((r,g,b)); continue
            x,y,z=p; ax=abs(x)
            # Body-space paint establishes consistent front/side panel boundaries.
            head=y>8.55
            torso=ax<1.25 and 5.45<y<8.6
            red=head or (torso and (y>7.85 or ax<(.32+.16*(y-5.45)))) or y<2.85
            # Lower arms and hands retain red; upper arms become predominantly blue.
            if ax>3.05 and y>6: red=True
            # The clean pass uses solid panels. Original texel luminance contains
            # webbing/emblem noise, so carrying it forward recreates dark speckles.
            lum=(r*3+g*6+b)/10
            shade=.60+.40*min(1,lum/19)
            base=(27,4,7) if red else (3,10,25)
            color=((24,3,4) if red else (2,7,19)) if style=='clean' else tuple(round(v*shade) for v in base)
            # Retain the earlier experiment exactly when explicitly requested.
            if style=='legacy' and not red and (px+py)%4==0:
                color=tuple(min(31,v+1) for v in color)
            if style=='legacy' and red:
                if head:
                    angle=math.atan2(x,max(.10,abs(z)))
                    web=abs(math.sin(angle*9))<.14 or abs(math.sin((y-8.5)*13))<.16
                else:
                    web=abs(math.sin(x*12+z*4))<.13 or abs(math.sin(y*12))<.15
                if web: color=(max(4,color[0]//3),2,3)
            # Reuse known eye islands, not an arbitrary head-space rectangle.
            if head and min(r,g,b)>21:
                color=(1,1,1) if style=='clean' else (29,21,6)
            # Long-legged spider emblem on front AND back (side test remains necessary).
            if torso and abs(z)>.25:
                black=(ax<.065 and 7.15<y<7.8)
                for sign in (-1,1):
                    for start, bend, end in [((.04,7.70),(.45,7.9),(.62,8.1)),
                                             ((.06,7.58),(.50,7.65),(.63,7.9)),
                                             ((.06,7.45),(.36,7.25),(.38,6.1)),
                                             ((.04,7.35),(.20,7.1),(.23,5.95))]:
                        start=(start[0]*sign,start[1]); bend=(bend[0]*sign,bend[1]); end=(end[0]*sign,end[1])
                        black |= min(segment_distance(x,y,start,bend),segment_distance(x,y,bend,end))<.035
                if black: color=(2,2,3)
            colors.append(color)
    # Fixed RGB555 palette, deterministically nearest-quantized (no dependency).
    palette_colors=sorted(set(colors))
    if len(palette_colors)>256:
        # Stable frequency selection: favor dominant colors, keeping emblem and lenses.
        from collections import Counter
        frequency=Counter(colors)
        palette_colors=sorted(frequency,key=lambda c:(-frequency[c],c))[:256]
    lookup={c:min(range(len(palette_colors)),key=lambda j:sum((c[k]-palette_colors[j][k])**2 for k in range(3))) for c in set(colors)}
    indices=bytes(lookup[c] for c in colors)
    palette=b''.join(struct.pack('<H',r|g<<5|b<<10) for r,g,b in palette_colors)
    palette+=bytes(512-len(palette))
    return indices,palette


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=('clean','legacy'), default='clean')
    parser.add_argument('--out', help='Private experiment folder inside build/')
    parser.add_argument('--combined', action='store_true')
    args=parser.parse_args()
    dest=w.safe_output(mod.project_path(args.out)) if args.out else (
        DEST if args.style=='clean' else mod.ROOT/'build/movie-suit-128')
    if not dest.is_relative_to((mod.ROOT/'build').resolve()):
        raise ValueError('Suit experiment outputs must stay in build/')
    _,glob,manifest=mod.load_clean()
    assets={e['name']:glob[e['offset']:e['offset']+e['size']] for e in manifest['entries'] if e['name'] in ('spd.nsbmd','spd.nsbtx')}
    raw=assets['spd.nsbtx']; a=TextureArchive.parse(raw)
    pixels=raw[164:4260]
    up=bytes(pixels[(y//2)*64+x//2] for y in range(128) for x in range(128))
    palette=raw[a.palette_start:a.palette_start+512]
    painted,pal=artwork(raw,args.style)
    model=scale_model(assets['spd.nsbmd'])
    for label,indices,colors in [('control',up,palette),('painted',painted,pal)]:
        overlay={'spd.nsbtx':resize_i8(raw,indices,colors),'spd.nsbmd':model}
        folder=dest/label/'mods'; folder.mkdir(parents=True,exist_ok=True)
        for name,data in overlay.items():
            path=folder/name
            if path.exists() and path.read_bytes()!=data: raise ValueError(f'Existing edit differs: {path}')
            w.atomic_write(path,data)
        preview(overlay['spd.nsbtx'],dest/label/'texture.png',4)
        rgb=bytearray()
        for i in indices:
            color=w.u16(colors,i*2)
            rgb.extend((color>>s&31)*255//31 for s in (0,5,10))
        render(rgb,128,dest/label/'front-preview.png')
    w.write_json(dest/'experiment.json',{'texture_size':128,'texture_memory_bytes':16384,
                 'baseline_texture_memory_bytes':4096,'uv_commands':len(uv_offsets(assets['spd.nsbmd'])[1]),
                 'model_vertices_changed':False,'unknown_texture_dictionary_word':'preserved',
                 'art':('Solid movie-inspired panels, black lenses, elongated emblem; no fine webbing'
                        if args.style=='clean' else 'Legacy procedural panels/webbing/gold lenses'),
                 'style':args.style,
                 'exporter_zip_sha256':'2baa745de84f299086713b3f52392d3d5d5b100279d4c0fc745e9556722c32db'})
    if args.combined:
        folder=dest/'combined/mods'; folder.mkdir(parents=True,exist_ok=True)
        sources=[dest/'painted/mods'/n for n in ('spd.nsbmd','spd.nsbtx')]
        sources += [mod.ROOT/'build/qol-suits-menu/mods'/n for n in
                    ('spdB.nsbtx','American.strings','English.strings','MissionMiniMapIcon.pal')]
        payload={p.name:p.read_bytes() for p in sources}
        for p in folder.iterdir():
            if not p.is_file() or p.name not in payload or p.read_bytes()!=payload[p.name]:
                raise ValueError(f'Existing combined overlay differs: {p}')
        for name,data in payload.items(): w.atomic_write(folder/name,data)
    print(f'Generated control and {args.style} experiments: {dest}')


if __name__=='__main__': main()
