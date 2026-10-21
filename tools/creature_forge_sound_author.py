"""Offline sound design from CC0 recordings; output pinned DS ADPCM assets.

Requires NumPy for source processing; the shipping build does not.
Foley sources/receipts live in work/creature-forge/foley; final samples are pinned
under reference/audio with provenance. Does not extract/reuse native game SFX.
"""
import sys,subprocess,json,wave,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from tools import creature_forge_audio as a,creature_forge_design as d,wos_tool as w
RATE=22050
SRC=ROOT/'reference/audio/creature-forge-sources';OUT=ROOT/'work/creature-forge/audio'
FFMPEG='C:/Users/enrik/OneDrive/Documents/FFMPEG/ffmpeg.exe'

def load(path):
    raw=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-f','f32le','-ac','1','-ar',str(RATE),'-'],capture_output=True,check=True).stdout
    v=np.frombuffer(raw,dtype='<f4').astype(float);v-=v.mean()
    return v/max(.01,np.max(np.abs(v)))

def pitch(v,ratio):return np.interp(np.arange(0,len(v)-1,ratio),np.arange(len(v)),v)
def filt(v,low=60,high=9000):
    frequencies=np.fft.rfftfreq(len(v),1/RATE)
    gain=(frequencies**2/(frequencies**2+low**2))/(1+(frequencies/high)**12)
    return np.fft.irfft(np.fft.rfft(v)*gain,n=len(v))
def mix(layers,dur):
    v=np.zeros(round(RATE*dur))
    for data,at,gain in layers:
        at=round(at*RATE);n=min(len(data),len(v)-at)
        if n>0:v[at:at+n]+=data[:n]*gain
    # Short room tail; different delay taps avoid one ringing oscillator.
    dry=v.copy()
    for delay,gain in ((.019,.14),(.047,.12),(.083,.08)):
        q=round(delay*RATE);v[q:]+=dry[:-q]*gain
    v=filt(v);v=np.tanh(v*1.2)
    fade=min(256,len(v)//8);v[:fade]*=np.linspace(0,1,fade);v[-fade:]*=np.linspace(1,0,fade)
    v*=.88/max(.01,np.max(np.abs(v)))
    return np.rint(v*32767).astype('<i2')

def main():
    OUT.mkdir(parents=True,exist_ok=True);a.DIR.mkdir(parents=True,exist_ok=True)
    src={}
    files={
      'growl':SRC/'monster-growl.mp3',
      'meat':SRC/'impact/Audio/impactSoft_heavy_001.ogg',
      'punch':SRC/'impact/Audio/impactPunch_heavy_003.ogg',
      'stone':SRC/'impact/Audio/impactMining_002.ogg',
      'steel':SRC/'impact/Audio/impactMetal_heavy_002.ogg',
      'bell':SRC/'impact/Audio/impactBell_heavy_000.ogg',
      'glass':SRC/'impact/Audio/impactGlass_heavy_002.ogg',
      'plate':SRC/'impact/Audio/impactPlate_heavy_003.ogg',
      'slime':SRC/'sci-fi/Audio/slime_001.ogg',
      'crunch':SRC/'sci-fi/Audio/explosionCrunch_001.ogg',
      'charge':SRC/'sci-fi/Audio/forceField_002.ogg',
      'arc':SRC/'sci-fi/Audio/laserLarge_002.ogg',
      'engine':SRC/'sci-fi/Audio/spaceEngineLow_002.ogg',
      'thrust':SRC/'sci-fi/Audio/thrusterFire_001.ogg'}
    for key,path in files.items():src[key]=load(path)
    rng=np.random.default_rng(0x2210);samples=[];allwav=[]
    def emit(name,pcm):
        raw=a.encode(pcm);filename=name+'.swavdata';(a.DIR/filename).write_bytes(raw)
        decoded=np.asarray(a.decode(raw[12:]),dtype=float)[:len(pcm)]
        snr=10*np.log10(np.sum(pcm.astype(float)**2)/max(1,np.sum((pcm.astype(float)-decoded)**2)))
        with wave.open(str(OUT/(name+'.wav')),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
        samples.append(dict(file=filename,sha256=w.sha256(raw),seconds=len(pcm)/RATE,rate=RATE,format='DS IMA-ADPCM',snr_db=round(float(snr),2),peak=int(np.max(np.abs(pcm)))))
        allwav.append(pcm)
    # Distinct materials/voices, independently cut and layered per species.
    materials=(('growl','slime',.78),('growl','steel',.52),('slime','charge',1.15),('plate','glass',1.35),('bell','steel',.66),('charge','arc',.85),('growl','bell',.48))
    for i,style in enumerate(d.STYLES):
        vocal,body,p=materials[i]
        for cat in range(5):
            dur=(.8,.65,1.25,.30,.55)[cat];ratio=p*(.8 if cat==2 else 1.25 if cat==3 else 1)
            core=pitch(src[vocal],ratio);offset=(i%3)*round(.11*RATE);core=core[offset:offset+round(dur*RATE)]
            if not len(core):core=pitch(src[vocal],ratio)[:round(dur*RATE)]
            env=np.linspace(1,.0,len(core))**(.8 if cat==2 else .4);core=core*env
            foley=pitch(src[body],p*(.8 if cat==2 else 1))
            layers=[(core,0,.65),(foley,.025,.27)]
            if cat==1:
                inhale=pitch(src['engine' if i in (4,5,6) else 'slime'],1.1+p*.4)[:round(.35*RATE)][::-1]
                inhale*=np.linspace(0,.7,len(inhale));layers=[(inhale,0,.4),(core,.10,.55),(foley,.04,.24)]
            elif cat==2:layers.extend(((pitch(src['meat'],.65),.02,.45),(pitch(src['crunch'],.7+p*.15),.10,.25)))
            elif cat==3:layers.extend(((pitch(src['punch'],1.1),0,.4),))
            emit(style+'-'+('alert','tell','death','hurt','idle')[cat],mix(layers,dur))
    for i,style in enumerate(d.STYLES):
        for j,move in enumerate(d.MOVES[style]):
            k=move.kind;p=materials[i][2]
            if k in ('quake','fugue','march','peal','crownfall'):
                q=.53+i*.025+j*.025
                layers=[(pitch(src['stone'],q),0,.7),(pitch(src['steel'],q+.03),.01,.4),(pitch(src['bell'],q+.08),.03,.35),(pitch(src['crunch'],q+.1),.04,.25)]
            elif k in ('beam','lance','verdict','seeds','twins','burst'):
                layers=[(pitch(src['arc'],.8+j*.13),0,.55),(pitch(src['charge'],.7+p*.3),.012,.3),(pitch(src['slime' if style=='spore' else 'glass'],p),.005,.35),(pitch(src['thrust'],.7),0,.2)]
            else:
                # Air blade precedes the contact crack by18ms, a brief layer
                # separation that remains readable on DS speakers.
                noise=filt(rng.normal(0,1,round(.2*RATE)),400,6000)*np.sin(np.linspace(0,np.pi,round(.2*RATE)))**2*.22
                layers=[(noise,0,.65),(pitch(src['punch'],p*.95),.018,.65),(pitch(src['plate' if i in (3,4,6) else 'meat'],p),.025,.4),(pitch(src['steel'],p*1.2),.03,.2)]
            emit(style+'-impact-'+str(j),mix(layers,.9 if k in ('quake','fugue','peal','crownfall') else .6))
    provenance=[dict(author='Kenney',license='CC0-1.0',url='https://kenney.nl/assets/impact-sounds'),dict(author='Kenney',license='CC0-1.0',url='https://kenney.nl/assets/sci-fi-sounds'),dict(author='john129pats',title='Hybrid Monster Growl',license='CC0-1.0',url='https://freesound.org/people/john129pats/sounds/146558/',download='https://cdn.freesound.org/previews/146/146558_831330-hq.mp3')]
    manifest=dict(schema_version=1,first=a.FIRST,samples=samples,provenance=provenance,sources={k:dict(file=str(v.relative_to(ROOT)),sha256=w.sha256(v.read_bytes())) for k,v in files.items()},processing='Layered, pitch-cut, filtered recordings; transient/room tail design; soft limiting; mono22050Hz DS IMA-ADPCM')
    w.write_json(a.DIR/'manifest.json',manifest)
    combined=np.concatenate([np.concatenate((v,np.zeros(RATE//4,dtype='<i2'))) for v in allwav[35:]])
    with wave.open(str(OUT/'attack-reel.wav'),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(combined.astype('<i2').tobytes())
    print(json.dumps(dict(samples=len(samples),bytes=sum((a.DIR/e['file']).stat().st_size for e in samples),minimum_snr=min(e['snr_db'] for e in samples))))
if __name__=='__main__':main()
