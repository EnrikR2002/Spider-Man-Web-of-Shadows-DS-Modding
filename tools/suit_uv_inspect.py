"""Private deterministic UV evidence from apicula's COLLADA export."""
from pathlib import Path
import xml.etree.ElementTree as ET
from tools import wos_tool as w
from tools.nitro_texture import png_rgb
import math

ROOT = Path(__file__).resolve().parents[1]


def barycentric(p, a, b, c):
    det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(det) < 1e-8: return None
    u=((b[1]-c[1])*(p[0]-c[0])+(c[0]-b[0])*(p[1]-c[1]))/det
    v=((c[1]-a[1])*(p[0]-c[0])+(a[0]-c[0])*(p[1]-c[1]))/det
    return (u,v,1-u-v) if min(u,v,1-u-v)>=-1e-6 else None


def uv_body_map(size):
    positions, coords, faces = load_mesh()
    samples = [None] * (size*size)
    for face in faces:
        pts=[(coords[t][0]*size,(1-coords[t][1])*size) for _,t in face]
        for y in range(max(0,math.floor(min(p[1] for p in pts))),min(size,math.ceil(max(p[1] for p in pts)))):
            for x in range(max(0,math.floor(min(p[0] for p in pts))),min(size,math.ceil(max(p[0] for p in pts)))):
                weights=barycentric((x+.5,y+.5),*pts)
                if weights:
                    samples[y*size+x]=tuple(sum(weights[j]*positions[face[j][0]][k] for j in range(3)) for k in range(3))
    return samples


def render(rgb, texture_size, path):
    positions, coords, faces = load_mesh()
    width,height=512,640
    output=bytearray([24]*width*height*3); depths=[-1e6]*(width*height)
    for face in faces:
        pts=[(width/2+positions[v][0]*45,height-65-positions[v][1]*52) for v,_ in face]
        for y in range(max(0,math.floor(min(p[1] for p in pts))),min(height,math.ceil(max(p[1] for p in pts)))):
            for x in range(max(0,math.floor(min(p[0] for p in pts))),min(width,math.ceil(max(p[0] for p in pts)))):
                weights=barycentric((x+.5,y+.5),*pts)
                if not weights: continue
                z=sum(weights[j]*positions[face[j][0]][2] for j in range(3))
                pos=y*width+x
                if z<=depths[pos]: continue
                depths[pos]=z
                u=sum(weights[j]*coords[face[j][1]][0] for j in range(3))
                v=sum(weights[j]*coords[face[j][1]][1] for j in range(3))
                off=(min(texture_size-1,int((1-v)*texture_size))*texture_size+min(texture_size-1,int(u*texture_size)))*3
                output[pos*3:pos*3+3]=rgb[off:off+3]
    w.atomic_write(path,png_rgb(width,height,output))


def load_mesh():
    r = ET.parse(ROOT / 'build/suit-model-inspect/spd.dae')
    ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
    sources = {s.get('id'): list(map(float, s.find('c:float_array', ns).text.split()))
               for s in r.findall('.//c:source', ns) if s.find('c:float_array', ns) is not None}
    p = sources['positions']; uv = sources['texcoords']
    positions = [tuple(p[i:i+3]) for i in range(0, len(p), 3)]
    coords = [tuple(uv[i:i+2]) for i in range(0, len(uv), 2)]
    poly = r.find('.//c:polylist', ns)
    inputs = poly.findall('c:input', ns)
    stride = max(int(x.get('offset')) for x in inputs) + 1
    print('Inputs', [x.attrib for x in inputs])
    vi = next(int(x.get('offset')) for x in inputs if x.get('semantic') == 'VERTEX')
    ti = next((int(x.get('offset')) for x in inputs if x.get('semantic') == 'TEXCOORD'), vi)
    indices = list(map(int, poly.find('c:p', ns).text.split()))
    counts = list(map(int, poly.find('c:vcount', ns).text.split()))
    faces = []; at = 0
    for count in counts:
        face = [(indices[at + j * stride + vi], indices[at + j * stride + ti]) for j in range(count)]
        faces.extend((face[0], face[j], face[j+1]) for j in range(1, count-1))
        at += count * stride
    return positions, coords, faces


def main():
    positions, coords, faces = load_mesh()
    print('Position bounds', [(min(p[k] for p in positions), max(p[k] for p in positions)) for k in range(3)])
    print('UV bounds', [(min(p[k] for p in coords), max(p[k] for p in coords)) for k in range(2)])
    size = 512
    rgb = bytearray([32] * size * size * 3)
    for face in faces:
        pts = [(int(coords[t][0]*size), int((1-coords[t][1])*size)) for _, t in face]
        for a,b in zip(pts,pts[1:]+pts[:1]):
            steps=max(abs(a[0]-b[0]),abs(a[1]-b[1]),1)
            for i in range(steps+1):
                x=round(a[0]+(b[0]-a[0])*i/steps); y=round(a[1]+(b[1]-a[1])*i/steps)
                if 0<=x<size and 0<=y<size:
                    off=(y*size+x)*3; rgb[off:off+3]=b'\xff\xff\xff'
    w.atomic_write(ROOT/'build/suit-model-inspect/uv-wire.png',png_rgb(size,size,rgb))
    # UV vertices with body positions are private research evidence.
    w.write_json(ROOT/'build/suit-model-inspect/uv-positions.json',
                 [{'xyz':positions[v],'uv':coords[t]} for face in faces for v,t in face])


if __name__ == '__main__': main()