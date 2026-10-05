"""Serial same-core experiment with read-only batteries and reproducible inputs.

Reports host wall time, framebuffer checks and a semantic RAM snapshot. This is
not a DeSmuME FPS or Nintendo DS timing benchmark. No emulator state is loaded.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import statistics
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import emulator_smoke as e,wos_tool as w,player_trace,upgrade_trace

MODES={'serial':{b'melonds_threaded_renderer':b'disabled'},
       'threaded':{b'melonds_threaded_renderer':b'enabled'}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path);parser.add_argument('--save',type=Path,required=True)
    parser.add_argument('--script',type=Path,required=True);parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--frames',type=int,default=5000);parser.add_argument('--start',type=int,default=3000)
    parser.add_argument('--out',type=Path,default=w.PROJECT/'work/performance/benchmark.json')
    parser.add_argument('--worker',choices=MODES);parser.add_argument('--label')
    args=parser.parse_args()
    if not 1<=args.rounds<=10 or not 0<=args.start<args.frames<=10000:raise ValueError('Invalid bounded benchmark range')
    before=args.save.read_bytes()
    if args.worker:
        dest=e.run(args.rom,args.frames,{args.frames-1},save_path=args.save,
            script=json.loads(args.script.read_text()),label=args.label,
            ram_captures={args.frames-1},core_options=MODES[args.worker],timing_start=args.start)
        print(dest);return 0
    digest=w.sha256(args.rom.read_bytes());root=w.PROJECT/'build/boot-tests'/(args.rom.stem+'-'+digest[:8])
    runs=[]
    # Alternate order to reduce warm-up/order bias; never run emulator instances in parallel.
    for round in range(args.rounds):
        for mode in (('serial','threaded') if round%2==0 else ('threaded','serial')):
            label=f'benchmark-{mode}-{round}'
            path=root/label;log=w.safe_output(path/'worker.log');log.parent.mkdir(parents=True,exist_ok=True)
            with log.open('w',encoding='utf-8') as output:
                subprocess.run([sys.executable,str(Path(__file__).resolve()),str(args.rom),'--save',str(args.save),
                    '--script',str(args.script),'--frames',str(args.frames),'--start',str(args.start),
                    '--worker',mode,'--label',label],stdout=output,stderr=subprocess.STDOUT,check=True)
            timing=json.loads((path/'frame-timing.json').read_text());boot=json.loads((path/'boot.json').read_text())
            ram=(path/f'ram-{args.frames-1:05d}.bin').read_bytes()
            digest_arm=upgrade_trace.verify_rom(args.rom.read_bytes())
            observation=player_trace.sample(ram);ownership=upgrade_trace.snapshot(ram,arm9_sha256=digest_arm)
            runs.append({'mode':mode,'round':round,'evidence':path.relative_to(w.PROJECT).as_posix(),
                'timing':{k:v for k,v in timing.items() if k!='frame_ms'},
                'screenshot_sha256':boot['screenshots'][0]['png_sha256'],
                'player':observation,'ownership':ownership})
            print(mode,round,'median',round_value(timing['median_ms']),flush=True)
    if args.save.read_bytes()!=before:raise ValueError('Source battery changed; results are not comparable')
    summary={mode:{key:statistics.median(r['timing'][key] for r in runs if r['mode']==mode)
                for key in ('mean_ms','median_ms','p95_ms','p99_ms')} for mode in MODES}
    result={'rom_sha256':digest,'battery_sha256':w.sha256(before),'script':str(args.script),'runs':runs,'summary':summary,
        'final_framebuffers_equal':len({r['screenshot_sha256'] for r in runs})==1,
        'final_player_observations_equal':all(r['player']==runs[0]['player'] for r in runs),
        'final_ownership_equal':all(r['ownership']==runs[0]['ownership'] for r in runs),
        'limitation':'Host timing of pinned melonDS DS software core; no DeSmuME or dense-AI FPS claim.'}
    w.write_json(args.out,result);print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2));return 0

def round_value(value):return f'{value:.3f} ms'
if __name__=='__main__':raise SystemExit(main())
