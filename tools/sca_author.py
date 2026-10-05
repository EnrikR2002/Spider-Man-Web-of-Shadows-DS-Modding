"""Sampled SCA authoring: export/import and independent rotation/translation tracks.

Frames/joints, scales, static pool, unknown header bytes and unselected data stay
native. New tracks are appended; constants/aliases can safely become independent.
This does not author hitboxes, movement physics, events, timing or purchase rules.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.sca import Sca,Pool,align4
from tools.animation_rig import AnimationRig
from tools import wos_tool as w


def sample(animation,joint,frame,channel):
    animation._check_frame(frame);track=animation.track(joint,channel)
    pool=animation.static_pool if track['static'] else animation.frames[frame]
    return getattr(pool,{'translation':'translations','rotation':'rotations','scale':'scales'}[channel])[track['index']]


def _keys(values,frames,width,bits):
    if not isinstance(values,(tuple,list)) or len(values)!=frames:
        raise ValueError('A sampled track must contain exactly the native frame count')
    result=[]
    for row in values:
        if (not isinstance(row,(tuple,list)) or len(row)!=width or
            any(type(v) is not int or not -(1<<(bits-1))<=v<(1<<(bits-1)) for v in row)):
            raise ValueError('Malformed or out-of-range sampled Q12 values')
        result.append(tuple(row))
    return tuple(result)


def repack_samples(raw,*,rotations=None,translations=None,independent_rotations=False):
    """Append independent sampled channels while retaining old pools and aliases.

    Zero changes returns exact original bytes. Explicit independent mode bakes
    every joint rotation, including unmodified static/shared tracks.
    Nonzero alignment bytes that would be discarded cause rejection.
    """
    a=Sca.parse(raw);requested={'translation':translations or {},'rotation':rotations or {}}
    selected={channel:{} for channel in requested}
    for channel,tracks in requested.items():
        for joint,values in tracks.items():
            a.track(joint,channel)
            keys=_keys(values,a.frame_count,9 if channel=='rotation' else 3,16 if channel=='rotation' else 32)
            before=tuple(sample(a,joint,f,channel) for f in range(a.frame_count))
            if keys!=before:selected[channel][joint]=keys
    if independent_rotations:
        for joint in range(a.joint_count):
            selected['rotation'].setdefault(joint,tuple(sample(a,joint,f,'rotation') for f in range(a.frame_count)))
    if not any(selected.values()):return bytes(raw)
    counts=list(a.counts);descriptors=[list(d) for d in a.descriptors]
    for channel,component,index in (('translation',0,3),('rotation',1,5)):
        for joint in sorted(selected[channel]):
            if counts[index]>=128:raise ValueError('New dynamic track exceeds 7-bit descriptor index')
            descriptors[joint][component]=counts[index]<<1;counts[index]+=1
    stride=align4(12*counts[3]+24*counts[4]+18*counts[5])
    padding_size=stride-(12*counts[3]+24*counts[4]+18*counts[5])
    frames=[]
    for f,pool in enumerate(a.frames):
        if any(pool.padding[padding_size:]):raise ValueError('Repacking would discard nonzero frame alignment bytes')
        padding=pool.padding[:padding_size]+bytes(max(0,padding_size-len(pool.padding)))
        t=pool.translations+tuple(selected['translation'][j][f] for j in sorted(selected['translation']))
        r=pool.rotations+tuple(selected['rotation'][j][f] for j in sorted(selected['rotation']))
        frames.append(Pool(t,pool.scales,r,padding).to_bytes())
    header=bytearray(a.header);struct.pack_into('<I',header,16,stride);header[20:26]=bytes(counts)
    result=(bytes(header)+b''.join(bytes(d) for d in descriptors)+a.descriptor_padding+
            a.static_pool.to_bytes()+b''.join(frames))
    b=Sca.parse(result)
    if b.to_bytes()!=result:raise ValueError('Repacked SCA failed structural round trip')
    for joint in range(a.joint_count):
        for channel in ('translation','rotation','scale'):
            for f in range(a.frame_count):
                expected=selected.get(channel,{}).get(joint)
                value=expected[f] if expected is not None else sample(a,joint,f,channel)
                if sample(b,joint,f,channel)!=value:raise ValueError('Repacked SCA changed an unexpected sampled value')
    return result


def export_samples(raw,rig=None):
    a=Sca.parse(raw)
    if rig is not None and len(rig.names)!=a.joint_count:raise ValueError('Model/animation joint count mismatch')
    return {'schema_version':1,'base_sha256':w.sha256(raw),'frame_count':a.frame_count,'joint_count':a.joint_count,
        'coordinate_contract':'Raw SCA stored local TRS, Q12. This is not Blender matrix_basis or world-space data.',
        'rig':rig.report() if rig else None,
        'tracks':[{'joint':j,**{channel+'_q12':[list(sample(a,j,f,channel)) for f in range(a.frame_count)]
                   for channel in ('translation','rotation','scale')}} for j in range(a.joint_count)]}


def import_samples(raw,data,*,independent_rotations=False):
    a=Sca.parse(raw)
    if (not isinstance(data,dict) or type(data.get('schema_version')) is not int or data.get('schema_version')!=1
        or type(data.get('frame_count')) is not int or type(data.get('joint_count')) is not int
        or data.get('base_sha256')!=w.sha256(raw)
        or data.get('frame_count')!=a.frame_count or data.get('joint_count')!=a.joint_count):
        raise ValueError('Sample document does not match its hash-identified native template')
    tracks=data.get('tracks');rotations={};translations={}
    if not isinstance(tracks,list) or len(tracks)!=a.joint_count:raise ValueError('Expected every native joint exactly once')
    for track in tracks:
        if not isinstance(track,dict):raise ValueError('Sampled joint record must be an object')
        joint=track['joint'];a.track(joint)
        if joint in rotations:raise ValueError('Duplicate sampled joint')
        rotations[joint]=_keys(track['rotation_q12'],a.frame_count,9,16)
        translations[joint]=_keys(track['translation_q12'],a.frame_count,3,32)
        scales=_keys(track['scale_q12'],a.frame_count,6,32)
        if scales!=tuple(sample(a,joint,f,'scale') for f in range(a.frame_count)):
            raise ValueError('Scale/inverse-scale authoring is not enabled; preserve native values')
    return repack_samples(raw,rotations=rotations,translations=translations,independent_rotations=independent_rotations)


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('export');p.add_argument('sca',type=Path);p.add_argument('--model',type=Path);p.add_argument('--out',type=Path,required=True)
    p=commands.add_parser('import');p.add_argument('sca',type=Path);p.add_argument('samples',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--independent-rotations',action='store_true')
    args=parser.parse_args()
    try:
        out=w.safe_output(args.out)
        if not (out.is_relative_to((w.PROJECT/'build').resolve()) or out.is_relative_to((w.PROJECT/'work').resolve())):
            raise ValueError('Authoring outputs must stay in private build/ or work/')
        if out==args.sca.resolve() or args.command=='import' and out==args.samples.resolve():raise ValueError('Keep authoring inputs separate from outputs')
        raw=args.sca.read_bytes()
        if args.command=='export':
            rig=AnimationRig.parse(args.model.read_bytes()) if args.model else None
            w.write_json(out,export_samples(raw,rig))
        else:
            data=json.loads(args.samples.read_text(encoding='utf-8'))
            result=import_samples(raw,data,independent_rotations=args.independent_rotations)
            w.atomic_write(out,result)
            print(f'SCA {len(raw)} -> {len(result)} bytes; SHA256 {w.sha256(result)}')
        print(out);return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print(f'error: {exc}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
