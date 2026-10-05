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

# The first paid clip is a planted jab-cross-hook combination. The middle clip
# is a knee into a compact kick. The finisher is a loaded overhand cross. Motion
# stays in the upper body: a quiet base, close guard, and short weight shifts.
# Every control is sampled for the full native duration; peaks align with the
# measured contact clocks without the old side-to-side dance-like torso swing.
CONTROLS={
 'entry':{
  'left':[(0,0.),(3,0.),(4,.48),(5,1.),(7,.66),(9,0.),(15,0.),(17,.55),(18,1.),(20,.6),(22,0.),(38,0.)],
  'right':[(0,0.),(10,.35),(12,1.),(14,.62),(16,0.),(38,0.)],
  'hook':[(0,0.),(16,0.),(18,1.),(20,.55),(22,0.),(38,0.)],
  'cock':[(0,0.),(38,0.)],
  'twist':[(0,0.),(3,-3.),(5,8.),(8,1.),(10,-4.),(12,-10.),(15,-1.),(18,12.),(21,0.),(38,0.)],
  'hip':[(0,0.),(5,-2.),(8,0.),(12,3.),(15,0.),(18,-3.),(21,0.),(38,0.)],
  'lean':[(0,2.),(5,7.),(9,2.),(12,8.),(15,2.),(18,7.),(22,2.),(38,2.)],
  'crouch':[(0,.02),(5,.08),(9,.02),(12,.08),(18,.07),(22,.02),(38,.02)],
  'step':[(0,0.),(5,.08),(9,.02),(12,.12),(16,.04),(18,.12),(24,0.),(38,0.)]},
 'bridge':{
  'left':[(0,0.),(12,0.)],
  'right':[(0,0.),(12,0.)],
  'hook':[(0,0.),(12,0.)],
  'cock':[(0,0.),(12,0.)],
  'twist':[(0,0.),(2,-7.),(4,5.),(6,1.),(9,7.),(11,0.)],
  'hip':[(0,0.),(4,-2.),(6,0.),(9,2.),(11,0.)],
  'lean':[(0,2.),(4,8.),(6,3.),(9,6.),(11,2.)],
  'crouch':[(0,.02),(4,.08),(6,.03),(9,.06),(11,.02)],
  'knee':[(0,0.),(2,.58),(4,1.),(6,.72),(8,.35),(9,.78),(11,0.)],
  'step':[(0,0.),(4,.08),(6,.02),(9,.08),(11,0.)]},
 'finish':{
  'left':[(0,0.),(20,0.)],
  'right':[(0,0.),(4,0.),(5,.5),(6,1.),(8,.72),(10,.25),(12,0.),(20,0.)],
  'hook':[(0,0.),(20,0.)],
  'cock':[(0,0.),(1,.25),(3,1.),(4,.7),(6,0.),(20,0.)],
  'twist':[(0,0.),(2,-7.),(3,-11.),(6,15.),(9,7.),(12,0.),(20,0.)],
  'hip':[(0,0.),(3,-3.),(6,4.),(9,1.),(12,0.),(20,0.)],
  'lean':[(0,2.),(3,5.),(6,10.),(9,5.),(12,2.),(20,2.)],
  'crouch':[(0,.02),(3,.08),(6,.02),(9,.04),(12,.02),(20,.02)],
  'step':[(0,0.),(3,.02),(6,.12),(10,.04),(14,0.),(20,0.)]}}

def authored_poses(idle,parents,variant,frames):
    if variant not in CONTROLS or frames!={'entry':39,'bridge':12,'finish':20}[variant]:
        raise ValueError('Unexpected Rush clip identity/duration')
    if len(parents)!=37 or idle.joint_count!=37:raise ValueError('Expected canonical player rig')
    neutral=Pose(idle,parents);neutral_r,neutral_positions=neutral.fk();rotations={j:[] for j in range(37)};translations={j:[] for j in range(37)}
    controls=CONTROLS[variant];diagnostics=[]
    for f in range(frames):
        values={name:curve(keys,f) for name,keys in controls.items()};p=Pose(idle,parents)
        twist=values.get('twist',0.);hip=values.get('hip',0.)
        lean=values['lean'];crouch=values['crouch'];step=values.get('step',0.)
        p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.);p.t[1]=(0.,3.95-crouch,0.)
        p.r[1]=mm(mm(axis('y',hip),axis('x',lean)),ROOT)
        # ROOT maps local X to world up and local Z to world right. Twist
        # around X; Y would tip the chest sideways rather than turn shoulders.
        # Counter-pitch at the chest/neck keeps the gaze up during the punch.
        p.r[2]=axis('x',twist);p.r[3]=axis('z',-lean*.12);p.r[4]=axis('z',-lean*.6);p.r[5]=IDENTITY
        # Two feet retain their original idle world orientation. IK plants both
        # ankles while hips/torso twist; the knee/kick phase deliberately lifts R.
        left=(.46,.78,1.05+step*.3);right=(-.46,.78,-1.15+step*.45)
        knee=values.get('knee',0.)
        if knee:right=(-.46,.78+1.9*knee,-1.15+2.9*knee+step*.2)
        for upper,lower,end,target,side in ((26,27,28,left,1),(30,31,32,right,-1)):
            p.ik(upper,lower,end,target,(side*.9,2.,4.))
            p.world_rotation(end,neutral_r[end])
        arm_targets=[]
        for upper,lower,end,side,gain in ((7,8,9,1,values['left']),(17,18,19,-1,values['right'])):
            hook=values.get('hook',0.) if side==1 else 0.
            cock=values.get('cock',0.) if side==-1 else 0.
            target=(side*(.82-.42*max(gain,0.)+.20*cock)-1.35*hook,
                    5.65+.12*max(gain,0.)+.45*cock+.3*hook,
                    .55+2.65*max(gain,0.)-1.0*cock-.45*hook)
            p.ik(upper,lower,end,target,(side*1.15,4.9,-.8))
            # Keep palms oriented forward without native cartwheel wrist motion.
            p.world_rotation(end,neutral_r[end]);arm_targets.append(target)
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
                    pole=add(mul((side*.9,2.,4.),1-t),mul(neutral_positions[lower],t))
                    p.ik(upper,lower,end,planted,pole);p.world_rotation(end,neutral_r[end])
        wr,wp=p.fk()
        for j in range(37):
            rotations[j].append(stored(p.r[j]));translations[j].append(tuple(round(v*4096) for v in p.t[j]))
        diagnostics.append({'sample':f,'root':p.t[1],'left_wrist':wp[9],'right_wrist':wp[19],
                            'left_ankle':wp[28],'right_ankle':wp[32]})
    return rotations,translations,diagnostics

def author(raw,idle_raw,parents,variant):
    a=Sca.parse(raw);idle=Sca.parse(idle_raw)
    rotations,translations,diagnostics=authored_poses(idle,parents,variant,a.frame_count)
    result=repack_samples(raw,rotations=rotations,translations=translations)
    return result,diagnostics
