"""Frozen CC0-recording-based machinery/room cues, appended after Forge's bank."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import sdat,wos_tool as w,creature_forge_audio as codec
DIR=ROOT/'reference/audio/chapter-spectacle-v1'
FIRST=710
NAMES=('station-air','harbor-air','pump-start','storm-tell','storm-release','hoist-tell','hoist-impact','motor-open','harbor-release')
IDS={n:FIRST+i for i,n in enumerate(NAMES)}

def sound_data(raw):
    manifest=json.loads((DIR/'manifest.json').read_text());waves=[]
    for row in manifest['samples']:
        data=(DIR/row['file']).read_bytes()
        if w.sha256(data)!=row['sha256']:raise ValueError('Spectacle sound differs from frozen asset')
        waves.append(data)
    archive=sdat.Sdat.parse(raw);ids=(archive.file_id(1,0),archive.file_id(2,20),archive.file_id(3,0));seq,bank,wave=(archive.blob(i) for i in ids)
    if (w.u32(seq,0x1c),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Expected immutable0.22 audio parent')
    notes=[struct.pack('<HH6B',FIRST+i,0,60,127,127,127,127,64) for i in range(len(waves))]
    sequences=[(306,bytes((0x81,0x80|((FIRST+i)>>7),(FIRST+i)&127,60,110,0,0xff))) for i in range(len(waves))]
    return archive.replace({ids[0]:sdat.append_sequences(seq,sequences),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})

def author():
    """Offline only; deterministic processing, no oscillators or game samples."""
    import numpy as np,wave
    from tools import creature_forge_sound_author as a
    DIR.mkdir(parents=True,exist_ok=True);out=ROOT/'work/chapter-spectacle/audio';out.mkdir(parents=True,exist_ok=True)
    files={
        'engine':a.SRC/'sci-fi/Audio/spaceEngineLow_002.ogg',
        'field':a.SRC/'sci-fi/Audio/forceField_002.ogg',
        'thrust':a.SRC/'sci-fi/Audio/thrusterFire_001.ogg',
        'crunch':a.SRC/'sci-fi/Audio/explosionCrunch_001.ogg',
        'steel':a.SRC/'impact/Audio/impactMetal_heavy_002.ogg',
        'bell':a.SRC/'impact/Audio/impactBell_heavy_000.ogg',
        'plate':a.SRC/'impact/Audio/impactPlate_heavy_003.ogg',
        'stone':a.SRC/'impact/Audio/impactMining_002.ogg'}
    src={n:a.load(p) for n,p in files.items()}
    def layer(key,pitch,at,gain,low=45,high=7000):return (a.filt(a.pitch(src[key],pitch),low,high),at,gain)
    recipes={
        'station-air':(1.8,.14,[layer('engine',.72,0,.7,70,1700),layer('field',.6,.28,.16,200,2400)]),
        'harbor-air':(1.8,.12,[layer('engine',.43,0,.65,110,1000),layer('plate',.42,.38,.12,70,1000)]),
        'pump-start':(2.1,.68,[layer('steel',.72,0,.8),layer('engine',.7,.05,.5),layer('engine',1.05,.38,.45),layer('thrust',.8,.62,.5)]),
        'storm-tell':(.7,.64,[layer('bell',1.5,0,.55),layer('field',1.45,.03,.35)]),
        'storm-release':(2.2,.66,[layer('crunch',.63,0,.75),layer('field',.52,.08,.42),layer('bell',.52,.3,.24)]),
        'hoist-tell':(.65,.7,[layer('plate',.85,0,.6),layer('bell',.82,.16,.45)]),
        'hoist-impact':(.9,.75,[layer('steel',.61,0,.7),layer('stone',.72,0,.65),layer('plate',.65,.04,.3)]),
        'motor-open':(.85,.58,[layer('steel',1.3,0,.3),layer('thrust',1.2,.02,.5),layer('field',1.15,.12,.3)]),
        'harbor-release':(2.4,.72,[layer('steel',.55,0,.5),layer('crunch',.56,.03,.55),layer('engine',.36,.2,.3),layer('plate',.48,.65,.22)])}
    rows=[]
    for name in NAMES:
        duration,gain,layers=recipes[name];pcm=np.rint(a.mix(layers,duration).astype(float)*gain).astype('<i2')
        raw=codec.encode(pcm);file=name+'.swavdata';(DIR/file).write_bytes(raw)
        decoded=np.asarray(codec.decode(raw[12:])[:len(pcm)],dtype=float)
        snr=10*np.log10(np.sum(pcm.astype(float)**2)/max(1,np.sum((pcm.astype(float)-decoded)**2)))
        with wave.open(str(out/(name+'.wav')),'wb') as stream:stream.setparams((1,2,22050,0,'NONE','not compressed'));stream.writeframes(pcm.tobytes())
        rows.append(dict(name=name,id=IDS[name],file=file,sha256=w.sha256(raw),samples=len(pcm),peak=int(np.max(np.abs(pcm.astype(int)))),snr_db=round(float(snr),2)))
    provenance=json.loads((a.SRC/'provenance.json').read_text())
    w.write_json(DIR/'manifest.json',dict(schema_version=1,first=FIRST,format='mono22050Hz DS IMA-ADPCM',samples=rows,
        source_receipt='reference/audio/creature-forge-sources/provenance.json',sources={n:dict(path=str(p.relative_to(ROOT)),sha256=w.sha256(p.read_bytes())) for n,p in files.items()},
        processing='Layered/pitched/filtered recordings; deterministic room tails; ambience14/12% and events58..75% of author mix peak; no native game samples.'))
    print(json.dumps(dict(samples=len(rows),output=str(DIR))))

if __name__=='__main__':author()
