"""Roof-only release of defeated NormalEnemy costs from native spawner lists.

Route a non-null, zero-HP NormalEnemy weak reference through the native null
reference cleanup. The list removes its own node; the enemy actor is neither
destroyed nor modified here. Live enemies and every other room retain native
handling. Both native paths preserve the cumulative spawn cost correctly.
"""
import struct

BASE=0x02000000
SITE,OLD=0x0204C2C8,0x1A00001C
LIVE,DEAD=0x0204C340,0x0204C2CC
STATS,NORMAL=0x02145C5C,0x021301D0
ROOM=93

def branch(site,target,condition=14):
    offset=target-site-8
    if offset%4 or not -(1<<25)<=offset<(1<<25):raise ValueError('ARM branch out of range')
    return condition<<28|0x0A000000|((offset>>2)&0xffffff)

def adapter(arm9,at):
    if struct.unpack_from('<I',arm9,SITE-BASE)[0]!=OLD:raise ValueError('Native spawner site changed')
    # r1 already holds actor = non-null weak reference - 4. r0 must survive
    # for native live handling. r2/r3 are scratch in both following paths.
    words=[0xE59F2038,0xE5922000,0xE3520000,0,       # stats pointer / null guard
           0xE5923000,0xE3530000|ROOM,0,             # current room guard
           0xE5913000,0xE59F201C,0xE1530002,0,       # NormalEnemy vtable guard
           0xE5913044,0xE3530000,0,                 # HP <= 0
           0,0,STATS,NORMAL]
    keep=at+14*4;dead=at+15*4
    words[3]=branch(at+3*4,keep,0)
    words[6]=branch(at+6*4,keep,1)
    words[10]=branch(at+10*4,keep,1)
    words[13]=branch(at+13*4,dead,13)               # signed <=
    words[14]=branch(keep,LIVE)
    words[15]=branch(dead,DEAD)
    return struct.pack('<18I',*words),(SITE,OLD,branch(SITE,at,1))
