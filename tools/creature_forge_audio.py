"""Pinned layered foley bank and Nintendo DS IMA-ADPCM, no runtime synthesis."""
import json,struct
from pathlib import Path
from tools import sdat,wos_tool as w
ROOT=Path(__file__).resolve().parents[1]
FIRST=653
DIR=ROOT/'reference/audio/creature-forge-v1'
STEP=(7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767)
INDEX=(-1,-1,-1,-1,2,4,6,8)

def decode(data):
    value,index=struct.unpack_from('<hH',data);index=min(88,index&127);out=[value]
    for byte in data[4:]:
        for code in (byte&15,byte>>4):
            delta=((code&7)*2+1)*STEP[index]//8
            value=max(-32767,min(32767,value+(-delta if code&8 else delta)))
            index=max(0,min(88,index+INDEX[code&7]));out.append(value)
    return out

def encode(samples,rate=22050):
    values=[max(-32767,min(32767,int(v))) for v in samples]
    if not values:raise ValueError('Empty sound')
    # Start with a quiet predictor and let the adaptive step settle naturally.
    value=values[0];index=0;out=bytearray(struct.pack('<hH',value,index));nibbles=[]
    for target in values[1:]:
        difference=target-value;sign=8 if difference<0 else 0
        q=min(range(8),key=lambda i:abs(abs(difference)-((i*2+1)*STEP[index]//8)))
        code=sign|q;delta=((q*2+1)*STEP[index])//8
        value=max(-32767,min(32767,value+(-delta if sign else delta)));index=max(0,min(88,index+INDEX[q]));nibbles.append(code)
    nibbles.extend([0]*(-len(nibbles)%8))
    out.extend(a|(b<<4) for a,b in zip(nibbles[::2],nibbles[1::2]))
    return struct.pack('<BBHHHI',2,0,rate,round(16756991/rate),0,len(out)//4)+out

def sound_data(raw):
    manifest=json.loads((DIR/'manifest.json').read_text());waves=[]
    for e in manifest['samples']:
        data=(DIR/e['file']).read_bytes()
        if w.sha256(data)!=e['sha256']:raise ValueError('Pinned authored sound differs: '+e['file'])
        waves.append(data)
    a=sdat.Sdat.parse(raw);ids=(a.file_id(1,0),a.file_id(2,20),a.file_id(3,0));seq,bank,wave=(a.blob(i) for i in ids)
    if (w.u32(seq,0x1c),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Expected exact0.21 sound tables')
    notes=[struct.pack('<HH6B',FIRST+i,0,60,127,127,127,127,64) for i in range(len(waves))]
    seqs=[(306,bytes((0x81,0x80|((FIRST+i)>>7),(FIRST+i)&127,60,110,0,0xff))) for i in range(len(waves))]
    return a.replace({ids[0]:sdat.append_sequences(seq,seqs),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})
