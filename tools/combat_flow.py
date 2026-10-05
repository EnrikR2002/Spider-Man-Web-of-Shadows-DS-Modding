"""Guarded combat-flow revision of the purchased Sling/compact-HUD composition."""
from pathlib import Path
import argparse
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import tasm_sling_strike as s, combat_hud as h, wos_tool as w
from tools.combat_feedback import branch

SOURCE_OFFSET=0x1439A0
ARM9_SHA256='b43630d4f0bf0ea3530a6330f7c80482d6ba1f70ba194a447eb93e8a738d77ea'
CODE_SHA256='0a53f65237b0c7f1b523c5b31694b9d09d9bf29559300275c898b628d314c2ea'
VAULT_OFFSET=0xC9268
OLD_VAULT=(0xE1A00004,0xEBFFD7BC,0xE3A01025,0xE3A00B03,0xEAFFFFF7)
NEW_VAULT=(0xE3A01025,0xE3A00B03,0xE58D14BC,0xE58D04B8,0xEA000014)
TEXT_EDITS={191:'In mid-air, press \ue602 near an enemy.\nKick past them, then face back.',
            188:'Grapple with \ue602, then press up.\nLaunch together, follow with \ue602.'}

def code_bytes():
 raw=bytes.fromhex(Path(__file__).with_suffix('.hex').read_text(encoding='utf-8'))
 if len(raw)!=0x3600 or w.sha256(raw)!=CODE_SHA256: raise ValueError('Combat-flow code differs from validated source')
 return raw

def apply_rom(rom):
 header=w.parse_header(rom);start=header['arm9_offset'];size=header['arm9_size']
 raw=rom[start:start+size]
 if w.sha256(raw)!=s.ARM9_SHA256: raise ValueError('Combat flow requires the exact purchased Sling composition')
 if struct.unpack_from('<5I',raw,VAULT_OFFSET)!=OLD_VAULT: raise ValueError('Historical Vault hook differs')
 if w.u32(raw,0x73A68)!=branch(0x02073A68,0x02150B20): raise ValueError('Historical observer hook differs')
 if w.u32(raw,0xC9314)!=0xE28D0F8A: raise ValueError('Native target-dispatch return differs')
 changed=bytearray(rom)
 struct.pack_into('<I',changed,start+0x73A68,branch(0x02073A68,0x02151920))
 code=code_bytes(); changed[start+SOURCE_OFFSET:start+SOURCE_OFFSET+len(code)]=code
 struct.pack_into('<5I',changed,start+VAULT_OFFSET,*NEW_VAULT)
 hook=branch(0x020C9314,0x02151520);struct.pack_into('<I',changed,start+0xC9314,hook)
 if w.sha256(changed[start:start+size])!=ARM9_SHA256: raise ValueError('Unexpected combat-flow ARM9')
 return bytes(changed),[{'field':'authored_combat_flow_extension','offset':SOURCE_OFFSET,'size':len(code),'sha256':CODE_SHA256},
  {'field':'cheap_enemy_snapshot_filter','arm9_offset':0x73A68,'old':branch(0x02073A68,0x02150B20),'new':branch(0x02073A68,0x02151920)},
  {'field':'vault_confirmed_matched_launch','arm9_offset':0xC9314,'old':0xE28D0F8A,'new':hook},
  {'field':'vault_native_target_dispatch_before_hop','arm9_offset':VAULT_OFFSET,'old':list(OLD_VAULT),'new':list(NEW_VAULT)}]

def sample(ram):
 data=h.sample(ram);at=h.STATE-h.BASE
 data['render_work']=dict(zip(('draw_passes','idle_skips','cleared_cells','projections'),struct.unpack_from('<4I',ram,at+0x6B0)))
 data['pending_rectangles']=w.u32(ram,at+0x6A0)
 data['sling_pass']=list(struct.unpack_from('<6i',ram,at+0x680))
 return data

def generate(base_mods='mods',output='build/combat-flow'):
 import mod
 from tools import combat_profile as cp, combat_readability as q
 root=w.safe_output(mod.project_path(output))
 if not root.is_relative_to((mod.ROOT/'build').resolve()): raise ValueError('Candidates belong in build/')
 rom,glob,manifest=mod.load_clean();names=[e['name'] for e in manifest['entries']]
 overlays=mod.overlay_files(mod.project_path(base_mods),names)
 current=cp.load_recipe(mod.ROOT/'reference/gameplay_profile.json',overlays)
 if current not in ('tasm-sling-strike','tasm-combat-flow'):
  raise ValueError('Historical combat-flow generator cannot replace a newer gameplay composition')
 q.compose(glob,manifest,overlays,TEXT_EDITS)
 for name,data in overlays.items():w.atomic_write(root/'mods'/name,data,(mod.DEFAULT_ROM,))
 w.write_json(root/'gameplay_profile.json',{'schema_version':1,'profile':'tasm-combat-flow',
  'required_overlays':{name:w.sha256(data) for name,data in overlays.items()}})
 result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile='tasm-combat-flow')
 path=root/'CombatFlow.nds';w.atomic_write(path,result,(mod.DEFAULT_ROM,));w.write_json(path.with_suffix('.build.json'),log)
 return path

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mods',default='mods');parser.add_argument('--out',default='build/combat-flow');args=parser.parse_args()
 try: print(generate(args.mods,args.out))
 except (ValueError,OSError) as exc: print(f'error: {exc}',file=sys.stderr);return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
