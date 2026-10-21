"""Dark symbiote shell with articulated conductive veins."""
from tools.midnight_encore_art import Conductor
from tools.rush_choreography import add
from tools.creature_forge_design import arms


class Electrical(Conductor):
    def face(self,j,tile,verts,uv=((0,0),(0,1),(1,1),(1,0))):
        if tile in (5,6,12):tile=3
        return super().face(j,tile,verts,uv)
    def finish(self):
        for u,l,e in arms('brt'):
            self.limb(u,add(self.p[u],(0,.15,.35)),add(self.p[l],(0,.15,.35)),.075,9)
            self.limb(l,add(self.p[l],(0,.15,.35)),add(self.p[e],(0,.15,.35)),.08,9)
        return super().finish()
