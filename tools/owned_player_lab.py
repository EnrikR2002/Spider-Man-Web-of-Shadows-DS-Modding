"""Restore measured current purchases/XP/initial HP in disposable lab RAM only."""
import argparse,ctypes as ct,json,os,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import kit_lab as k,wos_tool as w


def install(path=None):
    path=path or os.environ.get('WOS_CHAPTER_PLAYER_PROFILE')
    if not path:return None
    path=Path(path).resolve();root=Path(__file__).resolve().parents[1]
    if not path.is_relative_to((root/'work').resolve()):raise ValueError('Measured player profile must stay in work/')
    data=json.loads(path.read_text());source=Path(data['source_save']);words=data['ability_words']
    if w.sha256(source.read_bytes())!=data['source_sha256'] or len(words)!=3:raise ValueError('Measured player profile source changed')
    from tools import playtest
    if w.sha256(playtest.current_save().read_bytes())!=data['source_sha256']:raise ValueError('Actual battery changed; remeasure current player profile')
    if getattr(k.set_bits,'_owned_profile',None)==str(path):return data
    def exact(lib,bits,clear,bits2=0):
        ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
        if not 0<=stats<len(ram)-0x98:raise ValueError('Native stats pointer is invalid')
        ct.memmove(ptr+stats+12,struct.pack('<3I',*words),12)
        ct.memmove(ptr+stats+0x44,struct.pack('<I',data['xp']),4)
        ct.memmove(ptr+stats+0x84,struct.pack('<I',data['initial_hp']),4)
    exact._owned_profile=str(path);k.set_bits=exact
    return data


def measure(rom,out):
    from tools import emulator_smoke as e,playtest
    rom=Path(rom);out=Path(out).resolve()
    if not out.is_relative_to((ROOT/'work').resolve()):raise ValueError('Measured profile must stay in work/')
    out.mkdir(parents=True,exist_ok=True);actual=playtest.current_save();before=actual.read_bytes();copy=out/'current-player-copy.dsv';copy.write_bytes(before)
    script=[dict(start=t,end=t+6,buttons=[b]) for t,b in ((720,'A'),(840,'A'),(960,'A'),(1080,'Down'),(1140,'A'),(1500,'B'),(1620,'A'))]
    cap=e.run(rom.resolve(),3560,{820,1380,3500},save_path=copy,script=script,label='owned-profile-'+w.sha256(before)[:8],ram_captures={3500},core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    ram=(cap/'ram-03500.bin').read_bytes();stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
    if not 0<=stats<len(ram)-0x98:raise ValueError('Continue did not reach valid native stats')
    profile=dict(source_save=str(copy),source_sha256=w.sha256(before),rom_sha256=w.sha256(rom.read_bytes()),ability_words=list(struct.unpack_from('<3I',ram,stats+12)),xp=w.u32(ram,stats+0x44),initial_hp=w.u32(ram,stats+0x84),room=w.u32(ram,stats),captures=str(cap),limits='Fresh normal Continue from latest actual DSV copy; no training/purchase/warp fixtures in this observation.')
    if actual.read_bytes()!=before or copy.read_bytes()!=before:raise ValueError('Source battery changed during normal Continue')
    path=out/'owned-player-profile.json';w.write_json(path,profile);print(json.dumps(dict(profile=str(path),rom_sha256=profile['rom_sha256'],room=profile['room'])));return path


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('measure',));p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();measure(a.rom,a.out)
