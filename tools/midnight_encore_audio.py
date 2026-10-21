"""Dry creature foley with role-based headroom, frozen for deterministic builds.

New57-sample bank; the0.24 sound bank and its provenance stay immutable.
Offline authoring uses the bundled NumPy runtime and verified CC0 recordings.
"""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIRST=776
DIR=ROOT/'reference/audio/midnight-encore-v1'


def sound_data(raw):
    from tools import sdat,wos_tool as w
    manifest=json.loads((DIR/'manifest.json').read_text());waves=[]
    for entry in manifest['samples']:
        wave=(DIR/entry['file']).read_bytes()
        if w.sha256(wave)!=entry['sha256']:raise ValueError('Frozen encore audio changed')
        waves.append(wave)
    a=sdat.Sdat.parse(raw);ids=(a.file_id(1,0),a.file_id(2,20),a.file_id(3,0));seq,bank,wave=(a.blob(i) for i in ids)
    if (w.u32(seq,0x1c),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Expected exact0.24 audio count')
    notes=[struct.pack('<HH6B',FIRST+i,0,60,127,127,127,127,64) for i in range(len(waves))]
    sequences=[(306,bytes((0x81,0x80|((FIRST+i)>>7),(FIRST+i)&127,60,115,0,0xff))) for i in range(len(waves))]
    return a.replace({ids[0]:sdat.append_sequences(seq,sequences),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})


def author():
    import numpy as np,wave
    from tools import creature_forge_sound_author as src,creature_forge_audio as codec,wos_tool as w
    from tools import creature_forge_design as d,midnight_encore_motion as motion
    rate=src.RATE;out=ROOT/'work/midnight-epic/audio';out.mkdir(parents=True,exist_ok=True);DIR.mkdir(parents=True,exist_ok=True)
    paths=dict(growl=src.SRC/'monster-growl.mp3',slime=src.SRC/'sci-fi/Audio/slime_001.ogg',
        soft=src.SRC/'impact/Audio/impactSoft_heavy_001.ogg',punch=src.SRC/'impact/Audio/impactPunch_heavy_003.ogg',
        metal=src.SRC/'impact/Audio/impactMetal_heavy_002.ogg',plate=src.SRC/'impact/Audio/impactPlate_heavy_003.ogg',
        stone=src.SRC/'impact/Audio/impactMining_002.ogg',glass=src.SRC/'impact/Audio/impactGlass_heavy_002.ogg',
        crunch=src.SRC/'sci-fi/Audio/explosionCrunch_001.ogg',air=src.SRC/'sci-fi/Audio/thrusterFire_001.ogg',
        arc=src.SRC/'sci-fi/Audio/laserLarge_002.ogg')
    samples={k:src.load(v) for k,v in paths.items()};rng=np.random.default_rng(250018)
    def cut(name,pitch=1,dur=.3,start=0):
        v=src.pitch(samples[name],pitch);v=v[round(start*rate):round((start+dur)*rate)].copy()
        if len(v):
            fade=min(96,len(v)//8);v[:fade]*=np.linspace(0,1,fade);v[-fade:]*=np.linspace(1,0,fade)
        return v
    def mix(layers,dur,level):
        v=np.zeros(round(dur*rate))
        for signal,at,gain in layers:
            at=round(at*rate);n=min(len(signal),len(v)-at)
            if n>0:v[at:at+n]+=signal[:n]*gain
        v=src.filt(v,100,7200)
        # No blanket echo or equal-volume normalization. Footsteps, warning
        # breaths and damaging impacts occupy deliberately different levels.
        v=np.tanh(v*1.3)*level
        fade=min(140,len(v)//8);v[:fade]*=np.linspace(0,1,fade);v[-fade:]*=np.linspace(1,0,fade)
        return np.rint(v*32767).astype('<i2')
    rows=[];reel=[]
    def emit(name,pcm,role):
        raw=codec.encode(pcm);filename=name+'.swavdata';(DIR/filename).write_bytes(raw)
        decoded=np.array(codec.decode(raw[12:]),dtype=float)[:len(pcm)]
        snr=10*np.log10(max(1,np.sum(pcm.astype(float)**2))/max(1,np.sum((pcm.astype(float)-decoded)**2)))
        rows.append(dict(file=filename,sha256=w.sha256(raw),seconds=len(pcm)/rate,rate=rate,format='DS IMA-ADPCM',
            peak=int(np.max(np.abs(pcm))),rms=round(float(np.sqrt(np.mean(pcm.astype(float)**2))),2),snr_db=round(float(snr),2),role=role))
        with wave.open(str(out/(name+'.wav')),'wb') as f:f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
        reel.append(pcm)
    profile=(('slime',.93),('stone',.73),('slime',1.13),('plate',1.45),('metal',.79),('glass',1.2),('metal',.67))
    for i,style in enumerate(d.STYLES):
        material,pitch=profile[i]
        for category,label in enumerate(('alert','tell','death','hurt','step')):
            dur=(.43,.19,.85,.19,.10)[category];layers=[]
            if category==4:
                layers=[(cut('soft',1.2,.09),0,.7),(cut(material,1.45,.08),0,.16)]
                level=.19
            else:
                # Keep vocal detail in the midrange; drastic downward pitch
                # plus bells made the old bank muddy and metallic in the mix.
                g=cut('growl',pitch*(1.15 if category==3 else .87 if category==2 else 1),dur,start=.025*(i%3))
                if style in ('skitter','eye'):
                    t=np.arange(len(g))/rate;g*=.4+.6*np.maximum(0,np.sin(t*2*np.pi*(24 if style=='skitter' else 11)))**2
                if len(g):g*=np.linspace(1,.12,len(g))**.7
                layers=[(g,0,.62),(cut(material,pitch,dur),.008,.12)]
                if category==2:layers.extend(((cut('soft',.7,.45),.12,.7),(cut('crunch',.8,.35),.10,.16)))
                level=(.48,.34,.64,.37)[category]
            emit(style+'-'+label,mix(layers,dur,level),label)
    for i,style in enumerate(d.STYLES):
        material,pitch=profile[i]
        for j,move in enumerate(motion.MOVES[style]):
            heavy=move.kind in ('quake','peal','march','fugue','crownfall');ranged=move.kind in ('seeds','twins','beam','lance','verdict','burst')
            dur=.31 if heavy else .21 if ranged else .17
            n=round(rate*.075);t=np.arange(n)/rate
            swish=src.filt(rng.normal(0,.28,n),800,6500)*np.sin(np.linspace(0,np.pi,n))**1.2
            if heavy:
                layers=[(cut('soft',.78,.28),0,.9),(cut('stone',.83,.25),.006,.52),(cut('crunch',.95,.22),.012,.18),(cut(material,1.1,.15),.008,.1)]
            elif ranged:
                layers=[(cut('air',1.65+j*.12,.14),0,.45),(cut('arc',1.5+j*.12,.13),0,.22),(cut('glass',1.55,.10),.01,.14)]
                if style=='spore':layers.append((cut('slime',1.2,.18),0,.6))
            else:
                layers=[(swish,0,.4),(cut('punch',1.05+j*.12,.14),.004,.72),(cut(material,1.25+j*.09,.11),.007,.17)]
            emit(style+'-strike-'+str(j),mix(layers,dur,.72 if style=='conductor' else .62),'strike')
    prior=json.loads((ROOT/'reference/audio/midnight-creatures-v2/manifest.json').read_text())
    w.write_json(DIR/'manifest.json',dict(schema_version=1,first=FIRST,samples=rows,provenance=prior['provenance'],
        sources={k:dict(file=str(v.relative_to(ROOT)),sha256=w.sha256(v.read_bytes())) for k,v in paths.items()},
        processing='Dry short organic/material layers; no blanket delay or peak normalization; quiet steps, separate warnings, midrange vocal detail, transient-driven impacts; fixed role headroom.'))
    with wave.open(str(out/'reel.wav'),'wb') as f:
        f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(np.concatenate([np.concatenate((v,np.zeros(rate//5,dtype='<i2'))) for v in reel]).astype('<i2').tobytes())
    print(json.dumps(dict(samples=len(rows),first=FIRST,manifest=str(DIR))))


if __name__=='__main__':sys.path.insert(0,str(ROOT));author()
