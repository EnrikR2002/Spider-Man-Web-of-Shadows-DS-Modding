"""A serrated, articulated storm crown and long working forearm blades."""
from tools import midnight_enemy_art as prior
from tools.rush_choreography import add


class Conductor(prior.Sculpt):
    def panel(self,j,c,size,tile,bevel=.18):
        if j==4 and size[1]>.9:
            # Tapered mask with an angular brow instead of a square doll head.
            return self.loft(j,add(c,(0,-1.2,0)),add(c,(0,1.25,0)),
                ((0,.22,.4),(.3,.62,.7),(.72,1.,.62),(1,.58,.35)),6,6)
        return super().panel(j,c,size,tile,bevel)

    def finish(self):
        from tools.creature_forge_design import arms
        for side,(u,l,e) in zip((1,-1),arms('brt')):
            # Raking edges belong to the actual forearm/wrist chains. The
            # articulated mantle and claws now carry the spinning silhouette.
            a=add(self.p[l],(side*.35,0,.1))
            self.blade(l,a,add(self.p[e],(side*.8,.1,3.9)),.92,13,(side*.5,.6,.5))
            a=add(self.p[e],(side*.2,.25,1.0))
            self.blade(e,a,add(a,(side*.6,.5,3.5)),.58,9,(0,-.6,.6))
            shoulder=u-1;a=add(self.p[u],(side*.2,.6,-.6))
            self.blade(shoulder,a,add(a,(side*2.2,2.2,-2.1)),.65,6)
        return super().finish()
