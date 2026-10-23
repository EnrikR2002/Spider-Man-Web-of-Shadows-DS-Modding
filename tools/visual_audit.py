"""Read-only native texture census; output is private, no textures exported."""
import argparse
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w
from tools.nitro_texture import TextureArchive

def audit(mods='mods'):
    rom,glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']}
    from tools.oscorp_resources import EXTRA_NAMES
    from tools.tasm_kit import EXTRA_NAMES as KIT_NAMES
    overlay=mod.overlay_files(mod.project_path(mods),list(entries),added_names=(*EXTRA_NAMES,*KIT_NAMES))
    rows=[];dims=Counter();formats=Counter()
    for name,e in entries.items():
        if not name.endswith('.nsbtx'):continue
        clean=glob[e['offset']:e['offset']+e['size']];raw=overlay.get(name,clean)
        archive=TextureArchive.parse(raw)
        if archive.to_bytes()!=raw:raise ValueError('Texture no-op round trip failed')
        for texture in archive.textures:
            dims[f"{texture['width']}x{texture['height']}"]+=1;formats[str(texture['format'])]+=1
        rows.append({'asset':name,'bytes':len(raw),'clean_bytes':len(clean),
            'changed':raw!=clean,'texture_count':len(archive.textures),
            'pixel_pool_bytes':sum(t['size'] for t in archive.textures),
            'palette_pool_bytes':archive.palette_size,
            'textures':list(archive.textures),'sha256':w.sha256(raw)})
    return {'original_rom_sha256':w.sha256(rom),'archive_count':len(rows),
            'texture_count':sum(dims.values()),'dimensions':dict(sorted(dims.items())),
            'formats':dict(sorted(formats.items())),
            'largest_pixel_pools':sorted(rows,key=lambda x:x['pixel_pool_bytes'],reverse=True)[:15],
            'player':next(r for r in rows if r['asset']=='spd.nsbtx'),
            'archives':rows,'limitation':'Storage census; simultaneous residency, room ownership and VRAM peaks are not inferred.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mods',default='mods');p.add_argument('--out',default='work/performance/visual-audit.json');a=p.parse_args()
    report=audit(a.mods);w.write_json(mod.project_path(a.out),report)
    print({k:report[k] for k in ('archive_count','texture_count','dimensions','formats')})
    print('Player:',report['player']['textures']);return 0
if __name__=='__main__':raise SystemExit(main())
