"""Authored full-body Rush poses on the canonical CS5E rig; no DCC required.

Game local coordinates: Y up, Z forward. Stored SCA rotation matrices transpose
to column-vector FK. Native length, scales/events/root gameplay remain separate.
Uses a native idle pose for bone lengths and hand/foot orientation, not attack
samples. Every major body chain is posed anew through the complete three clips.
"""
import math
from .sca import Sca, rotation_q12
from .sca_author import sample, repack_samples

IDENTITY=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
ROOT=((0.,0.,1.),(1.,0.,0.),(0.,1.,0.))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(v,s):return tuple(x*s for x in v)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(v):return math.sqrt(dot(v,v))
def unit(v):
    n=length(v)
    if n<1e-9:raise ValueError('Degenerate authoring vector')
    return mul(v,1/n)
def transpose(a):return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))
def mm(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def mv(a,v):return tuple(dot(row,v) for row in a)
def axis(axis,degrees):return tuple(tuple(x/4096 for x in rotation_q12(axis,degrees)[i*3:i*3+3]) for i in range(3))
def stored(a):return tuple(round(x*4096) for row in transpose(a) for x in row)
def decoded(values):return transpose(tuple(tuple(x/4096 for x in values[i*3:i*3+3]) for i in range(3)))
def quaternion(r):
    tr=sum(r[i][i] for i in range(3))
    if tr>0:
        s=math.sqrt(tr+1)*2;q=(s/4,(r[2][1]-r[1][2])/s,(r[0][2]-r[2][0])/s,(r[1][0]-r[0][1])/s)
    else:
        i=max(range(3),key=lambda i:r[i][i]);j=(i+1)%3;k=(j+1)%3
        s=math.sqrt(max(0.,1+r[i][i]-r[j][j]-r[k][k]))*2
        if s<1e-9:raise ValueError('Invalid authoring rotation')
        v=[0.,0.,0.,0.];v[0]=(r[k][j]-r[j][k])/s;v[i+1]=s/4;v[j+1]=(r[j][i]+r[i][j])/s;v[k+1]=(r[k][i]+r[i][k])/s;q=tuple(v)
    return unit(q)
def tween_rotation(a,b,t):
    if t<=0:return a
    if t>=1:return b
    q,r=quaternion(a),quaternion(b);cosine=dot(q,r)
    if cosine<0:r=mul(r,-1);cosine=-cosine
    if cosine>.9995:v=unit(add(mul(q,1-t),mul(r,t)))
    else:
        angle=math.acos(max(-1.,min(1.,cosine)));s=math.sin(angle)
        v=add(mul(q,math.sin((1-t)*angle)/s),mul(r,math.sin(t*angle)/s))
    w,x,y,z=v
    return ((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
            (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
            (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
def align(a,b):
    """Shortest rotation taking unit a onto b; no matrix-element tweening."""
    a,b=unit(a),unit(b);v=cross(a,b);c=max(-1.,min(1.,dot(a,b)))
    if c>1-1e-9:return IDENTITY
    if c< -1+1e-9:
        u=unit(cross(a,(1.,0.,0.) if abs(a[0])<.9 else (0.,1.,0.)))
        return tuple(tuple(2*u[i]*u[j]-(1 if i==j else 0) for j in range(3)) for i in range(3))
    k=((0.,-v[2],v[1]),(v[2],0.,-v[0]),(-v[1],v[0],0.));kk=mm(k,k)
    return tuple(tuple(IDENTITY[i][j]+k[i][j]+kk[i][j]/(1+c) for j in range(3)) for i in range(3))

def curve(keys,frame):
    """Smooth scalar/vector pose controls; exact endpoints, fixed sample count."""
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=frame<=b:
            t=(frame-a)/(b-a);t=t*t*(3-2*t)
            if isinstance(x,tuple):return add(mul(x,1-t),mul(y,t))
            return x*(1-t)+y*t
    return keys[0][1] if frame<keys[0][0] else keys[-1][1]

class Pose:
    def __init__(self,idle,parents):
        self.parents=parents
        self.r=[decoded(idle.rotation(j,0)) for j in range(37)]
        self.t=[tuple(v/4096 for v in sample(idle,j,0,'translation')) for j in range(37)]
    def fk(self):
        r=[];p=[]
        for j,parent in enumerate(self.parents):
            if parent is None:r.append(self.r[j]);p.append(self.t[j])
            else:r.append(mm(r[parent],self.r[j]));p.append(add(p[parent],mv(r[parent],self.t[j])))
        return r,p
    def world_rotation(self,joint,value):
        r,_=self.fk();parent=self.parents[joint]
        self.r[joint]=value if parent is None else mm(transpose(r[parent]),value)
    def aim(self,joint,child,target):
        r,p=self.fk();direction=mv(r[joint],self.t[child])
        self.world_rotation(joint,mm(align(direction,sub(target,p[joint])),r[joint]))
    def ik(self,upper,lower,end,target,pole):
        _,p=self.fk();start=p[upper];l1=length(self.t[lower]);l2=length(self.t[end])
        v=sub(target,start);d=max(abs(l1-l2)+.02,min(length(v),l1+l2-.02));direction=unit(v)
        target=add(start,mul(direction,d))
        projected=sub(sub(pole,start),mul(direction,dot(sub(pole,start),direction)))
        side=unit(projected);a=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0.,l1*l1-a*a))
        elbow=add(add(start,mul(direction,a)),mul(side,h))
        self.aim(upper,lower,elbow);self.aim(lower,end,target)
        return target

# Large screen-plane silhouettes: loaded straight, high cross, rising uppercut;
# a high knee into a fully extended kick; an oversized lunging overhand finish.
# Vector targets are in Y-up/Z-forward authoring space. The camera sees Y/Z;
# sweeping mostly across X foreshortens a limb instead of making a readable hit.
# One-sample strike transitions and brief impact holds retain native hit clocks.
GUARD_L=(1.0,6.75,1.2)
GUARD_R=(-1.0,6.95,.5)
FOOT_L=(.6,.78,1.8)
FOOT_R=(-.6,.78,-1.5)
CONTROLS={
 'entry':{
  'left':[(0,GUARD_L),(2,(1.3,6.5,-1.5)),(3,(1.3,6.5,-1.5)),(4,(.55,6.45,1.7)),
          (5,(.15,6.45,4.9)),(6,(.15,6.45,4.9)),(8,GUARD_L),(13,GUARD_L),
          (15,(1.35,4.85,-.5)),(16,(1.35,4.85,-.5)),(17,(.65,6.0,1.3)),
          (18,(.2,8.6,3.6)),(19,(.2,8.6,3.6)),(21,(.8,7.85,2.4)),(24,GUARD_L),(38,GUARD_L)],
  'right':[(0,GUARD_R),(8,GUARD_R),(10,(-1.3,7.0,-1.8)),(11,(-1.3,7.0,-1.8)),
           (12,(-.2,7.0,5.25)),(13,(-.2,7.0,5.25)),(15,GUARD_R),(38,GUARD_R)],
  'left_stretch':[(0,0.),(4,.4),(5,1.),(6,1.),(8,0.),(16,0.),(18,1.),(19,1.),(22,0.),(38,0.)],
  'right_stretch':[(0,0.),(11,0.),(12,1.),(13,1.),(15,0.),(38,0.)],
  'twist':[(0,0.),(3,-25.),(5,25.),(6,25.),(8,0.),(11,25.),(12,-30.),(13,-30.),
           (16,-20.),(18,30.),(19,30.),(24,0.),(38,0.)],
  'hip':[(0,0.),(3,-5.),(5,7.),(8,0.),(11,6.),(12,-8.),(15,0.),(18,8.),(24,0.),(38,0.)],
  'lean':[(0,8.),(3,-8.),(5,25.),(6,25.),(8,8.),(11,-5.),(12,28.),(13,28.),
          (16,0.),(18,12.),(19,12.),(24,8.),(38,8.)],
  'crouch':[(0,.3),(3,.7),(5,.35),(8,.3),(11,.65),(12,.3),(16,.85),(18,-.1),(19,-.1),(24,.3),(38,.3)],
  'drive':[(0,0.),(3,-.2),(5,.65),(6,.65),(8,0.),(11,-.2),(12,.8),(13,.8),
           (16,-.2),(18,.5),(19,.5),(24,0.),(38,0.)],
  'left_foot':[(0,FOOT_L),(5,(.6,.78,2.0)),(12,(.6,.78,2.05)),(18,(.6,.78,1.9)),(26,FOOT_L),(38,FOOT_L)],
  'right_foot':[(0,FOOT_R),(38,FOOT_R)]},
 'bridge':{
  'left':[(0,GUARD_L),(4,(1.0,7.1,1.8)),(7,GUARD_L),(9,(1.0,7.5,1.5)),(10,(1.0,7.5,1.5)),(11,GUARD_L)],
  'right':[(0,GUARD_R),(4,(-1.15,6.5,-.3)),(7,(-1.4,7.35,-1.2)),
           (9,(-1.3,7.0,-1.8)),(10,(-1.3,7.0,-1.8)),(11,GUARD_R)],
  'twist':[(0,0.),(2,-15.),(4,20.),(7,-10.),(9,30.),(10,30.),(11,0.)],
  'hip':[(0,0.),(4,5.),(7,-5.),(9,12.),(10,12.),(11,0.)],
  'lean':[(0,8.),(4,18.),(7,0.),(9,-12.),(10,-12.),(11,8.)],
  'crouch':[(0,.3),(4,.25),(7,.5),(9,.2),(10,.2),(11,.3)],
  'drive':[(0,0.),(4,.4),(7,.1),(9,.45),(10,.45),(11,0.)],
  'left_foot':[(0,FOOT_L),(11,FOOT_L)],
  'right_foot':[(0,FOOT_R),(2,(-.65,2.4,.2)),(4,(-.65,3.2,2.0)),(5,(-.65,3.2,2.0)),
                (7,(-.65,2.4,.5)),(8,(-.65,3.7,2.8)),(9,(-.65,4.8,5.8)),
                (10,(-.65,4.8,5.8)),(11,FOOT_R)],
  'leg_stretch':[(0,0.),(7,0.),(9,1.),(10,1.),(11,0.)],
  'knee_pole':[(0,(-.7,2.5,2.2)),(4,(-.7,5.8,3.5)),(7,(-.7,5.6,2.5)),
               (9,(-.7,4.9,3.5)),(10,(-.7,4.9,3.5)),(11,(-.7,2.5,2.2))]},
 'finish':{
  'left':[(0,GUARD_L),(3,(1.2,6.7,2.4)),(4,(1.2,6.7,2.4)),(6,(1.2,5.7,-1.4)),
          (7,(1.2,5.7,-1.4)),(10,(1.2,6.2,-.6)),(13,GUARD_L),(19,GUARD_L)],
  'right':[(0,GUARD_R),(3,(-1.2,8.6,-.65)),(4,(-1.2,8.6,-.65)),(5,(-.5,7.25,2.0)),
           (6,(-.1,5.8,6.0)),(7,(-.1,5.8,6.0)),(9,(-.3,5.9,4.5)),(12,GUARD_R),(19,GUARD_R)],
  'right_stretch':[(0,0.),(4,0.),(6,1.),(7,1.),(10,.3),(12,0.),(19,0.)],
  'twist':[(0,0.),(3,-35.),(4,-35.),(6,45.),(7,45.),(10,22.),(13,0.),(19,0.)],
  'hip':[(0,0.),(3,-8.),(4,-8.),(6,12.),(7,12.),(10,5.),(13,0.),(19,0.)],
  'lean':[(0,8.),(3,-10.),(4,-10.),(6,32.),(7,32.),(10,18.),(13,8.),(19,8.)],
  'crouch':[(0,.3),(3,.7),(4,.7),(6,.45),(7,.45),(10,.4),(13,.3),(19,.3)],
  'drive':[(0,0.),(3,-.3),(4,-.3),(6,1.),(7,1.),(10,.6),(13,0.),(19,0.)],
  'left_foot':[(0,FOOT_L),(6,(.6,.78,2.35)),(10,(.6,.78,2.35)),(14,FOOT_L),(19,FOOT_L)],
  'right_foot':[(0,FOOT_R),(19,FOOT_R)]}}

def authored_poses(idle,parents,variant,frames):
    if variant not in CONTROLS or frames!={'entry':39,'bridge':12,'finish':20}[variant]:
        raise ValueError('Unexpected Rush clip identity/duration')
    if len(parents)!=37 or idle.joint_count!=37:raise ValueError('Expected canonical player rig')
    neutral=Pose(idle,parents);neutral_r,neutral_positions=neutral.fk();rotations={j:[] for j in range(37)};translations={j:[] for j in range(37)}
    controls=CONTROLS[variant];diagnostics=[]
    for f in range(frames):
        values={name:curve(keys,f) for name,keys in controls.items()};p=Pose(idle,parents)
        twist=values.get('twist',0.);hip=values.get('hip',0.)
        lean=values['lean'];crouch=values['crouch'];drive=values['drive']
        p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.);p.t[1]=(0.,5.0-crouch,drive)
        p.r[1]=mm(mm(axis('y',hip),axis('x',lean)),ROOT)
        # ROOT maps local X to world up and local Z to world right. Twist
        # around X; Y would tip the chest sideways rather than turn shoulders.
        # Counter-pitch at the chest/neck keeps the gaze up during the punch.
        p.r[2]=axis('x',twist);p.r[3]=axis('z',-lean*.12);p.r[4]=axis('z',-lean*.55)
        p.r[5]=mm(axis('x',-twist*.7),axis('z',-lean*.2))
        # Two feet retain their original idle world orientation. IK plants both
        # ankles while hips/torso twist; the knee/kick phase deliberately lifts R.
        left=values['left_foot'];right=values['right_foot'];leg_gain=values.get('leg_stretch',0.)
        # Short contact-only translation stretch, not scale/inverse-scale edits.
        # The native limbs return to their exact lengths when the gain is zero.
        for j in (31,32):p.t[j]=mul(p.t[j],1+.08*leg_gain)
        for upper,lower,end,target,side in ((26,27,28,left,1),(30,31,32,right,-1)):
            pole=values.get('knee_pole',(side*.7,2.5,2.2)) if side==-1 else (side*.7,2.5,2.2)
            p.ik(upper,lower,end,target,pole)
            foot_r=neutral_r[end]
            if side==-1 and leg_gain:
                direction=mv(foot_r,p.t[33])
                foot_r=mm(align(direction,(0.,.45,1.)),foot_r)
                foot_r=tween_rotation(neutral_r[end],foot_r,leg_gain)
            p.world_rotation(end,foot_r)
        for upper,lower,end,side,hand in ((7,8,9,1,'left'),(17,18,19,-1,'right')):
            gain=values.get(hand+'_stretch',0.)
            stretch=.16 if variant=='finish' else .12
            for j in (lower,end):p.t[j]=mul(p.t[j],1+stretch*gain)
            target=values[hand]
            p.ik(upper,lower,end,target,(side*1.6,6.,-1.8))
            # The old frozen idle wrist could point the hand into screen depth.
            # Point the knuckles along the forearm, preserving native hand shape.
            _,positions=p.fk();forward=sub(positions[end],positions[lower])
            hand_r=neutral_r[end];local_forward=(-side,0.,0.)
            p.world_rotation(end,mm(align(mv(hand_r,local_forward),forward),hand_r))
        # End the full finisher at the actual native idle pose. Quaternion
        # blending keeps the baked matrices rigid while returning from guard.
        if variant=='finish' and f>=14:
            t=(f-14)/5;t=t*t*(3-2*t)
            for j in range(37):
                p.r[j]=tween_rotation(p.r[j],neutral.r[j],t)
                p.t[j]=add(mul(p.t[j],1-t),mul(neutral.t[j],t))
            if f<19:
                for upper,lower,end,target,side in ((26,27,28,left,1),(30,31,32,right,-1)):
                    planted=add(mul(target,1-t),mul(neutral_positions[end],t))
                    pole=add(mul((side*.7,2.5,2.2),1-t),mul(neutral_positions[lower],t))
                    p.ik(upper,lower,end,planted,pole);p.world_rotation(end,neutral_r[end])
        wr,wp=p.fk()
        for j in range(37):
            rotations[j].append(stored(p.r[j]));translations[j].append(tuple(round(v*4096) for v in p.t[j]))
        diagnostics.append({'sample':f,'root':p.t[1],'head':wp[5],
                            'left_shoulder':wp[7],'left_elbow':wp[8],'left_wrist':wp[9],
                            'right_shoulder':wp[17],'right_elbow':wp[18],'right_wrist':wp[19],
                            'left_hip':wp[26],'left_knee':wp[27],'left_ankle':wp[28],
                            'right_hip':wp[30],'right_knee':wp[31],'right_ankle':wp[32]})
    return rotations,translations,diagnostics

def author(raw,idle_raw,parents,variant):
    a=Sca.parse(raw);idle=Sca.parse(idle_raw)
    rotations,translations,diagnostics=authored_poses(idle,parents,variant,a.frame_count)
    result=repack_samples(raw,rotations=rotations,translations=translations)
    return result,diagnostics
