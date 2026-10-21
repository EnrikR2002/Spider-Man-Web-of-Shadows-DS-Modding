"""Frozen creature voices and movement/strike foley, appended after0.23 audio.

Offline authoring uses the already licensed CC0 recordings. Shipping only reads
verified ADPCM assets; it does not require NumPy or an audio workstation.
"""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIRST=719
DIR=ROOT/'reference/audio/midnight-creatures-v2'


def sound_data(raw):
    from tools import sdat,wos_tool as w
    manifest=json.loads((DIR/'manifest.json').read_text(encoding='utf-8'));waves=[]
    for entry in manifest['samples']:
        data=(DIR/entry['file']).read_bytes()
        if w.sha256(data)!=entry['sha256']:raise ValueError('Frozen creature audio changed')
        waves.append(data)
    a=sdat.Sdat.parse(raw);ids=(a.file_id(1,0),a.file_id(2,20),a.file_id(3,0));seq,bank,wave=(a.blob(i) for i in ids)
    if (w.u32(seq,0x1c),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Expected exact0.23.0 audio')
    notes=[struct.pack('<HH6B',FIRST+i,0,60,127,127,127,127,64) for i in range(len(waves))]
    seqs=[(306,bytes((0x81,0x80|((FIRST+i)>>7),(FIRST+i)&127,60,115,0,0xff))) for i in range(len(waves))]
    return a.replace({ids[0]:sdat.append_sequences(seq,seqs),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})


def author():
    import numpy as np,wave
    from tools import creature_forge_sound_author as source,creature_forge_audio as codec,wos_tool as w
    from tools import creature_forge_design as design,midnight_enemy_motion as motion
    rate=source.RATE;out=ROOT/'work/midnight-rebuild/audio';out.mkdir(parents=True,exist_ok=True);DIR.mkdir(parents=True,exist_ok=True)
    src=source.SRC
    files=dict(growl=src/'monster-growl.mp3',slime=src/'sci-fi/Audio/slime_001.ogg',
        metal=src/'impact/Audio/impactMetal_heavy_002.ogg',bell=src/'impact/Audio/impactBell_heavy_000.ogg',
        glass=src/'impact/Audio/impactGlass_heavy_002.ogg',plate=src/'impact/Audio/impactPlate_heavy_003.ogg',
        punch=src/'impact/Audio/impactPunch_heavy_003.ogg',stone=src/'impact/Audio/impactMining_002.ogg',
        arc=src/'sci-fi/Audio/laserLarge_002.ogg',charge=src/'sci-fi/Audio/forceField_002.ogg',
        crunch=src/'sci-fi/Audio/explosionCrunch_001.ogg',thrust=src/'sci-fi/Audio/thrusterFire_001.ogg')
    sounds={k:source.load(v) for k,v in files.items()};rng=np.random.default_rng(0x241018);entries=[];reel=[]
    # Different vocal resonances and attack materials. All seven include a real
    # creature voice, rather than substituting a stock plate/bell for a vocal.
    profiles=(('slime',.82),('metal',.49),('slime',1.18),('plate',1.85),('bell',.56),('charge',1.35),('bell',.43))
    def layer(name,pitch=1,cut=None):
        data=source.pitch(sounds[name],pitch)
        return data[:round(cut*rate)] if cut else data
    def voice(style,index,category,dur):
        body,pitch=profiles[index];g=layer('growl',pitch*(1.25 if category==3 else .78 if category==2 else 1))
        if style=='skitter':
            # Tight dry double/triple chirps with an organic rasp underneath.
            n=min(len(g),round(dur*rate));g=g[:n]
            t=np.arange(n)/rate;g*=.32+.68*np.maximum(0,np.sin(t*2*np.pi*19))**3
        elif style=='eye':
            g=g[::-1].copy();t=np.arange(len(g))/rate;g*=.7+.3*np.sin(t*2*np.pi*37)
        elif style=='spore':
            n=min(len(g),round(dur*rate));g=g[:n];g*=.55+.45*np.sin(np.arange(n)/rate*math_tau*13)**2
        if len(g):g*=np.linspace(1,.1,len(g))**.55
        layers=[(source.filt(g,90,5800),0,.78),(layer(body,pitch*.9),.012,.23)]
        if category==1:
            inhale=layer('charge' if index in (4,5,6) else 'slime',1.8,.09)[::-1].copy()
            inhale*=np.linspace(0,.8,len(inhale));layers.append((inhale,0,.2))
        if category==2:layers.extend(((layer('crunch',pitch),.07,.25),(layer('metal' if index in (1,4,6) else 'slime',pitch),.15,.22)))
        if category==3:layers.append((layer('punch',1.2),0,.18))
        return layers
    def emit(name,pcm):
        raw=codec.encode(pcm);filename=name+'.swavdata';(DIR/filename).write_bytes(raw)
        decoded=np.asarray(codec.decode(raw[12:]),dtype=float)[:len(pcm)]
        snr=10*np.log10(np.sum(pcm.astype(float)**2)/max(1,np.sum((pcm.astype(float)-decoded)**2)))
        entries.append(dict(file=filename,sha256=w.sha256(raw),seconds=len(pcm)/rate,rate=rate,format='DS IMA-ADPCM',peak=int(np.max(np.abs(pcm))),snr_db=round(float(snr),2)))
        with wave.open(str(out/(name+'.wav')),'wb') as stream:stream.setparams((1,2,rate,0,'NONE','not compressed'));stream.writeframes(pcm.tobytes())
        reel.append(pcm)
    math_tau=6.283185307179586
    for i,style in enumerate(design.STYLES):
        body,pitch=profiles[i]
        for category,label in enumerate(('alert','tell','death','hurt','step')):
            dur=(.48,.26 if style=='skitter' else .38 if style!='conductor' else .48,1.05,.23,.18)[category]
            if category==4:layers=[(layer(body,pitch*1.25,.16),0,.5),(layer('slime' if i in (0,2) else 'plate',1.7,.12),.025,.23)]
            else:layers=voice(style,i,category,dur)
            emit(style+'-'+label,source.mix(layers,dur))
    for i,style in enumerate(design.STYLES):
        body,pitch=profiles[i]
        for j,move in enumerate(motion.MOVES[style]):
            dur=.48 if move.kind in ('quake','peal','fugue','crownfall') else .27
            n=round(rate*.12);noise=source.filt(rng.normal(0,1,n),450,6500)*np.sin(np.linspace(0,np.pi,n))**1.7
            if move.kind in ('seeds','twins','beam','lance','verdict','burst'):
                layers=[(layer('arc',1.2+j*.17),0,.5),(layer('charge',pitch),.01,.3),(layer('glass',1.5),.02,.14)]
                if style=='spore':layers.append((layer('slime',.8),0,.55))
            elif move.kind in ('quake','peal','march','fugue','crownfall'):
                layers=[(layer('stone',.7),0,.6),(layer(body,.6+j*.1),.012,.45),(layer('crunch',.8),.02,.2)]
            else:layers=[(noise,0,.2),(layer('plate' if style=='skitter' else body,pitch*(1+j*.14)),.015,.6),(layer('punch',.85+j*.15),.018,.35)]
            emit(style+'-strike-'+str(j),source.mix(layers,dur))
    old_manifest=json.loads((codec.DIR/'manifest.json').read_text(encoding='utf-8'))
    w.write_json(DIR/'manifest.json',dict(schema_version=1,first=FIRST,samples=entries,provenance=old_manifest['provenance'],
        sources={k:dict(file=str(v.relative_to(ROOT)),sha256=w.sha256(v.read_bytes())) for k,v in files.items()},
        processing='Short organic vocal identities, material-specific foley, continuous chirp/formant envelopes, filtered CC0 recording layers; short tells matched to new animation cadence.'))
    with wave.open(str(out/'voices-and-strikes.wav'),'wb') as stream:
        stream.setparams((1,2,rate,0,'NONE','not compressed'));stream.writeframes(np.concatenate([np.concatenate((r,np.zeros(rate//5,dtype='<i2'))) for r in reel]).astype('<i2').tobytes())
    print(json.dumps(dict(samples=len(entries),first=FIRST,manifest=str(DIR/'manifest.json'))))


if __name__=='__main__':
    sys.path.insert(0,str(ROOT));author()
