"""Sculpt the Ballast research model in Blender; invoked by crane_blender.py."""
import bpy,sys
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for vert in mesh.data.vertices:
    group=max(vert.groups,key=lambda x:x.weight,default=None)
    if group is None:raise ValueError('Unweighted vertex')
    name=mesh.vertex_groups[group.group].name.split(':')[-1]
    pivot=arm.matrix_world@arm.data.bones[mesh.vertex_groups[group.group].name].head_local
    d=mesh.matrix_world@vert.co-pivot
    if name=='Chest_M':
        d.y*=1.27;d.z*=1.10;d.x*=1.10
    elif name=='Neck_L':d.y*=1.22;d.z*=1.10;d.x*=1.15
    elif name.startswith('Shoulder_'):d.y*=1.20;d.z*=1.12
    elif name.startswith('Elbow_'):d.y*=1.10;d.z*=1.06
    elif name.startswith('Wrist_'):d.y*=1.22;d.z*=1.14
    vert.co=mesh.matrix_world.inverted()@(pivot+d)
mesh.data.update()
verts=[];faces=[];weights=[];uvs=[]
def face(bone,points,xy):
    start=len(verts);verts.extend(points);faces.append(tuple(range(start,start+len(points))));weights.extend([bone]*len(points));uvs.append(xy)
def slab(bone,side,x0,x1,yz,xy):
    outer=[(side*x1,y,z) for y,z in yz]; inner=[(side*x0,y,z) for y,z in yz]
    if side<0:outer.reverse();inner.reverse()
    face(bone,outer,xy)
    for i in range(4):face(bone,(inner[i],inner[(i+1)%4],outer[(i+1)%4],outer[i]),xy)
def panel(bone,side,x,yz,xy):
    p=[(side*x,y,z) for y,z in yz]
    if side<0:p.reverse()
    face(bone,p,xy)
for side,suffix in ((1,'L'),(-1,'R')):
    panel('brt:Chest_M',side,3.55,[(-1.55,7.15),(-1.55,8.65),(-.8,8.90),(-.8,7.4)],(11,39))
    shoulder='brt:Shoulder_'+suffix
    slab(shoulder,side,2.45,3.12,[(.08,9.55),(.12,10.45),(.78,11.2),(1.48,10.05)],(8,24))
    panel(shoulder,side,3.14,[(.18,10.03),(.22,10.32),(.83,10.72),(.77,10.41)],(11,39))
    front=[(side*2.0,-1.25,9.7),(side*2.4,-1.25,10.95),(side*4.1,-1.25,10.65),(side*4.45,-1.25,9.75)]
    if side<0:front.reverse()
    face(shoulder,front,(8,24))
    wrist='brt:Wrist_'+suffix
    panel(wrist,side,6.90,[(-1.18,7.15),(-1.2,8.0),(-.25,8.35),(.05,7.3)],(8,24))
    panel(wrist,side,6.92,[(-1.1,7.65),(-1.1,7.92),(-.32,8.21),(-.32,7.95)],(11,39))
new=bpy.data.meshes.new('Ballast forged armor');new.from_pydata(verts,[],faces);new.update();uv=new.uv_layers.new(name=mesh.data.uv_layers.active.name)
for poly,coord in zip(new.polygons,uvs):
    if coord == (8,24):
        x0,y0=1,17
        corners=[(x0,y0),(x0+14,y0),(x0+14,y0+14),(x0,y0+14)]
        for li,(x,y) in zip(poly.loop_indices,corners):uv.data[li].uv=((x+.5)/64,1-(y+.5)/64)
    else:
        for li in poly.loop_indices:uv.data[li].uv=((coord[0]+.5)/64,1-(coord[1]+.5)/64)
obj=bpy.data.objects.new('Ballast forged armor',new);bpy.context.collection.objects.link(obj);obj.data.materials.append(mesh.data.materials[0])
for bone in sorted(set(weights)):
    g=obj.vertex_groups.new(name=bone);g.add([i for i,n in enumerate(weights) if n==bone],1.0,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB')
