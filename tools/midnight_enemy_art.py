"""Native-scale creature mass and coherent articulated silhouettes."""
from tools import creature_forge_art as art,chapter_spectacle_art as prior
from tools.rush_choreography import add,sub,mul,unit,cross


class Sculpt(prior.ReadableSculpt):
    def __init__(self,template,pose):
        super().__init__(template,pose);self.style=getattr(pose,'rebuild_style',None)

    def panel(self,j,c,size,tile,bevel=.18):
        if self.style=='warden' and j in (8,15):
            size=(.9,1.4,.95) if j==8 else (.65,1.1,.65)
        return super().panel(j,c,size,tile,bevel)

    def limb(self,j,a,b,r,tile):
        # Forearms/haunches must read as anatomy at256px, not green wire.
        return art.Sculpt.limb(self,j,a,b,r*1.7,tile)

    def loft(self,j,a,b,radii,tile,sides=6):
        if j in (1,2,3):radii=tuple((t,rx*1.22,ry*1.24) for t,rx,ry in radii)
        return art.Sculpt.loft(self,j,a,b,radii,tile,sides)

    def blade(self,j,a,b,width,tile=2,curve=(0,0,0)):
        # Two broad striking blades remain legible; decorative spikes shrink
        # so the torso and working joints carry the silhouette.
        if j in (1,3,5,12):
            b=tuple(x+(y-x)*.72 for x,y in zip(a,b));width*=1.05
        if width<.45:return art.Sculpt.blade(self,j,a,b,width,tile,curve)
        # Closed ridged blades have a back and a bevel. The old one-sided fans
        # could disappear when a wrist/petal turned through an attack.
        middle=add(add(a,mul(sub(b,a),.62)),curve);direction=unit(sub(b,a))
        u=unit(cross(direction,(0,1,0) if abs(direction[1])<.85 else (0,0,1)));v=cross(u,direction)
        ring=[add(a,mul(u,-width)),add(middle,mul(u,-width*.65)),b,add(middle,mul(u,width*.65)),add(a,mul(u,width))]
        front=add(middle,mul(v,width*.3));back=add(middle,mul(v,-width*.18))
        for i in range(len(ring)):
            a0,b0=ring[i],ring[(i+1)%len(ring)]
            self.face(j,tile,(a0,b0,front,front));self.face(j,tile,(b0,a0,back,back))
