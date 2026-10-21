"""Repair owned waveform rendering without replacing any native sound row."""
import struct,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sdat,wos_tool as w,creature_forge_audio as codec
FIRST=776;COUNT=57
DIR=ROOT/'reference/audio/midnight-voltage-v1'


def linear_bank(raw,gain=1):
    archive=sdat.Sdat.parse(raw);file=archive.file_id(3,0);wave=archive.blob(file)
    size=w.u32(wave,8);count=w.u32(wave,0x38)
    if count!=FIRST+COUNT:raise ValueError('Expected exact0.25 wave archive')
    start=w.u32(wave,0x3c+FIRST*4);out=bytearray(wave[:start])
    for index in range(FIRST,count):
        offset=w.u32(wave,0x3c+index*4);end=w.u32(wave,0x3c+(index+1)*4) if index+1<count else size
        source=wave[offset:end];rate=w.u16(source,2)
        if source[0]!=2:raise ValueError('Expected owned ADPCM wave')
        values=codec.decode(source[12:]);values=[max(-30000,min(30000,round(v*gain))) for v in values]
        pcm=struct.pack('<'+'h'*len(values),*values);pcm+=bytes(-len(pcm)%4)
        payload=struct.pack('<BBHHHI',1,0,rate,round(16756991/rate),0,len(pcm)//4)+pcm
        struct.pack_into('<I',out,0x3c+index*4,len(out));out.extend(payload)
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0x14,len(out)-0x10)
    return archive.replace({file:bytes(out)+wave[size:]})


def sound_data(raw,*,muted=False):
    """Replace only the57 owned rows; native/player/music payloads stay exact."""
    archive=sdat.Sdat.parse(raw);wid=archive.file_id(3,0);sid=archive.file_id(1,0)
    wave=archive.blob(wid);seq=bytearray(archive.blob(sid));manifest=json.loads((DIR/'manifest.json').read_text())
    if (w.u32(wave,0x38),w.u32(seq,0x1c))!=(FIRST+COUNT,)*2:raise ValueError('Expected exact0.25 owned rows')
    size=w.u32(wave,8);out=bytearray(wave[:w.u32(wave,0x3c+FIRST*4)])
    for index,entry in enumerate(manifest['samples'],FIRST):
        payload=(DIR/entry['file']).read_bytes()
        if w.sha256(payload)!=entry['sha256']:raise ValueError('Frozen audible sample changed')
        if muted:payload=payload[:12]+bytes(len(payload)-12)
        struct.pack_into('<I',out,0x3c+index*4,len(out));out.extend(payload)
        at=0x20+index*12;seq[at+6]=127
        seq[at+7]=110 if entry['role']=='step' else 124
        seq[at+8]=110 if entry['role']=='step' else 126
        events=w.u32(seq,0x18)+w.u32(seq,at)
        if seq[events]!=0x81 or seq[events+3]!=60:raise ValueError('Owned one-shot sequence differs')
        seq[events+4]=127
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0x14,len(out)-0x10)
    return archive.replace({wid:bytes(out)+wave[size:],sid:bytes(seq)})


def author():
    import numpy as np,wave as wav
    source=ROOT/'reference/audio/midnight-encore-v1';manifest=json.loads((source/'manifest.json').read_text());rows=[]
    DIR.mkdir(exist_ok=True,parents=True);out=ROOT/'work/midnight-voltage/audio';out.mkdir(parents=True,exist_ok=True)
    targets=dict(alert=5700,tell=6100,death=6500,hurt=5100,step=1400,strike=7600)
    for entry in manifest['samples']:
        data=(source/entry['file']).read_bytes()
        if w.sha256(data)!=entry['sha256']:raise ValueError('Immutable0.25 source changed')
        v=np.asarray(codec.decode(data[12:]),dtype=float);role=entry['role'];before=float(np.sqrt(np.mean(v*v)))
        v*=targets[role]/max(1,before)
        v=np.tanh(v/26000)*26000
        v*=min(1.6,targets[role]/max(1,float(np.sqrt(np.mean(v*v)))))
        v=np.clip(np.rint(v),-30000,30000).astype('<i2');pcm=v.tobytes()+bytes(-len(v.tobytes())%4);rate=w.u16(data,2)
        payload=struct.pack('<BBHHHI',1,0,rate,int(16756991/rate),0,len(pcm)//4)+pcm
        (DIR/entry['file']).write_bytes(payload)
        with wav.open(str(out/(Path(entry['file']).stem+'.wav')),'wb') as f:f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(pcm)
        rows.append(dict(file=entry['file'],sha256=w.sha256(payload),role=role,format='PCM16',rate=rate,source_rms=round(before,2),
            rms=round(float(np.sqrt(np.mean(v.astype(float)**2))),2),peak=int(np.max(np.abs(v.astype(float)))),source_sha256=entry['sha256']))
    w.write_json(DIR/'manifest.json',dict(schema_version=1,first=FIRST,samples=rows,provenance=manifest['provenance'],
        processing='Own0.25 sources, role-based RMS matching to native effects, gentle peak control, PCM16, higher hostile-cue priority; no native row changes.'))
    print(json.dumps(dict(samples=len(rows),manifest=str(DIR/'manifest.json'))))


if __name__=='__main__':author()
