"""Add the user-confirmed kitchen divider only in a new R4-derived review snapshot.

X width is constrained by the utility cabinet and island connector. Y depth ends
at the island notch, NOT at the utility door front. Existing objects remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import bpy
import bmesh
from mathutils import Vector, Matrix
import math

R4_SHA='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
PIER_NAME='KITCHEN_DIVIDER_PIER_SITE_REVIEW'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bounds(obj):
    points=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
def object_state(obj):
    mesh=None
    if obj.type=='MESH':
        h=hashlib.sha256()
        for vertex in obj.data.vertices:h.update(struct.pack('<fff',*vertex.co))
        for face in obj.data.polygons:h.update(struct.pack('<'+str(len(face.vertices))+'I',*face.vertices))
        mesh=h.hexdigest()
    return {'mesh':mesh,'matrix':list(v for row in obj.matrix_world for v in row),'parent':obj.parent.name if obj.parent else None,
        'collections':sorted(c.name for c in obj.users_collection),'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport,'hidden':obj.hide_get(),
        'materials':[m.name if m else None for m in obj.data.materials] if obj.type=='MESH' else None,'properties':str(sorted(obj.items()))}

def run(source,output,project_root):
    source=Path(source).resolve();output=Path(output).resolve();project_root=Path(project_root).resolve()
    if sha(source)!=R4_SHA:raise RuntimeError('R4 SHA differs from frozen authority')
    if source==output or output.exists():raise RuntimeError('Review output must be new and separate from frozen source')
    frozen=[source,project_root/'design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend',project_root/'design/bedroom_door_r4/R4_DELIVERY_MANIFEST.json',project_root/'design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json']
    before={str(p):{'sha256':sha(p),'size':p.stat().st_size,'mtime_ns':str(p.stat().st_mtime_ns)} for p in frozen}
    kitchen_manifest=json.loads(frozen[-1].read_text());kitchen_model=frozen[1]
    if before[str(kitchen_model)]['sha256']!=kitchen_manifest['files_sha256'][str(kitchen_model)]:raise RuntimeError('Kitchen freeze hash mismatch')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    inherited={obj.name:object_state(obj) for obj in bpy.context.scene.objects}
    ac_root=bpy.data.objects['B11_K-UTILITY-WALL-AC']
    ac_body=bpy.data.objects['B11_K-UTILITY_AC_BODY']
    ac_bounds=bounds(ac_body);ac_center=Vector([(ac_bounds[0][i]+ac_bounds[1][i])/2 for i in range(3)])
    ac_members=[ac_root,*ac_root.children_recursive]
    ac_names={o.name for o in ac_members}
    ac_original_matrix=ac_root.matrix_world.copy()
    ac_root.matrix_world=Matrix.Translation(ac_center)@Matrix.Rotation(math.radians(60),4,'Z')@Matrix.Translation(-ac_center)@ac_original_matrix
    for obj in ac_members:obj['review_status']='HUMAN_REVIEW';obj['orientation_evidence']='USER_SITE_PHOTO_OBLIQUE_AC; +60deg model review yaw, not a measured installation angle'
    bpy.context.view_layer.update()
    base=bounds(bpy.data.objects['W_wall_md_0009'])
    connector=bounds(bpy.data.objects['B11_K-ISLAND_CONNECTOR_COUNTER'])
    utility_parts=[bpy.data.objects[n] for n in ['B11_K-UTILITY_L','B11_K-UTILITY_R','B11_K-UTILITY_TOP','B11_K-UTILITY_BASE']]
    utility_right=max(bounds(obj)[1][0] for obj in utility_parts)
    notch_parts=[bpy.data.objects['B11_K-ISLAND_ROUNDED_COUNTER']]
    notch_y=min(bounds(obj)[0][1] for obj in notch_parts)
    # Use the shared island/connector corner; thin panel tolerances stay below 0.1 mm.
    if abs(notch_y-connector[1][1])>.003:raise RuntimeError('Island notch and connector corner do not agree')
    notch_y=connector[1][1]
    lo=[utility_right,base[1][1],base[0][2]];hi=[connector[0][0],notch_y,base[1][2]]
    if any(hi[i]<=lo[i] for i in range(3)):raise RuntimeError('Nonpositive constrained pier extent')
    # Confirm the reported void before filling it: inherited visible wall shell only.
    shell=bpy.data.objects['R3_HOUSE_WALLS_D107_ROLLED_BACK'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    inv=shell.matrix_world.inverted();middle=[(lo[i]+hi[i])/2 for i in range(3)]
    origin=Vector((middle[0],middle[1],4))
    old_hit=shell.ray_cast(inv@origin,(inv.to_3x3()@Vector((0,0,-1))).normalized(),distance=6)[0]
    if old_hit:raise RuntimeError('Void test found existing active wall; avoid duplicate geometry')
    collection=bpy.data.collections.new('COL_KITCHEN_DIVIDER_SITE_REVIEW');bpy.context.scene.collection.children.link(collection)
    vertices=[(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh=bpy.data.meshes.new(PIER_NAME+'_Mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    pier=bpy.data.objects.new(PIER_NAME,mesh);collection.objects.link(pier)
    material=bpy.data.materials.new('SITE_REVIEW_WALL_WHITE');material.diffuse_color=(.82,.82,.79,1);mesh.materials.append(material)
    pier['review_status']='HUMAN_REVIEW';pier['structural_role']='UNKNOWN; site-confirmed wall/pier presence, not engineering classification'
    pier['width_basis']='Utility cabinet right extent to island connector left plane'
    pier['depth_basis']='Existing CAD pier front to island notch/connector north corner; not utility front'
    pier['height_basis']='Inherited lower ceiling +2800mm';pier['fabrication_release']=False
    bpy.context.view_layer.update()
    if any(object_state(bpy.data.objects[name])!=state for name,state in inherited.items() if name not in ac_names):raise RuntimeError('Inherited object outside authorized AC pose changed')
    for name in ac_names:
        if name in inherited and object_state(bpy.data.objects[name])['mesh']!=inherited[name]['mesh']:raise RuntimeError('AC geometry/size changed')
    bm=bmesh.new();bm.from_mesh(mesh);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=False);bm.free()
    if boundary or nonmanifold or volume<=0:raise RuntimeError('Pier solid topology failed')
    probes=[]
    for fx,fy in [(.2,.2),(.5,.5),(.8,.8)]:
        point=(lo[0]+fx*(hi[0]-lo[0]),lo[1]+fy*(hi[1]-lo[1]),4)
        hit,location,normal,index=pier.ray_cast(Vector(point),Vector((0,0,-1)),distance=6)
        if not hit or abs(location.z-hi[2])>1e-5:raise RuntimeError('Added pier top ray failed')
        probes.append({'xy':list(point[:2]),'top_z':location.z})
    # Axis-aligned volume overlap must be absent for every protected utility/island part.
    overlaps=[];schematic_device_overlaps=[]
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or not obj.name.startswith(('B11_K-UTILITY_','B11_K-ISLAND_')):continue
        b=bounds(obj);depths=[max(0,min(hi[i],b[1][i])-max(lo[i],b[0][i])) for i in range(3)]
        if all(v>1e-5 for v in depths):
            record={'object':obj.name,'axis_overlap_m':depths}
            (schematic_device_overlaps if 'UTILITY_AC_' in obj.name else overlaps).append(record)
    if overlaps:raise RuntimeError('Protected cabinet/island intersection: '+str(overlaps))
    output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(output))
    for path,meta in before.items():
        p=Path(path)
        if sha(p)!=meta['sha256'] or str(p.stat().st_mtime_ns)!=meta['mtime_ns']:raise RuntimeError('Frozen source changed: '+path)
    report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':R4_SHA,'corrected_source':str(output),'corrected_sha256':sha(output),'native_id':PIER_NAME,
        'bounds_m':[lo,hi],'added_dimensions_mm':[(hi[i]-lo[i])*1000 for i in range(3)],'total_depth_from_existing_back_mm':(hi[1]-base[0][1])*1000,
        'dimension_authority':'Inherited model anchors plus user-confirmed alignment; exact site fabrication dimensions require measurement.',
        'source_void_before':True,'top_probes':probes,'closed_solid':True,'volume_m3':volume,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,
        'inherited_object_count':len(inherited),'inherited_objects_unchanged_except_ac_pose':True,'authorized_ac_pose_names':sorted(ac_names),'ac_yaw_degrees_review':60,'ac_center_m':list(ac_center),'protected_cabinet_aabb_overlaps':overlaps,'frozen_files_unchanged':before,
        'schematic_ac_intersections':schematic_device_overlaps,'ac_policy':'User requested oblique site-photo installation; fixed-center +60deg review yaw, mesh dimensions unchanged. Exact angle/SKU requires site review.',
        'width_rule':'CABINET_BOUNDARY_TO_ISLAND_CONNECTOR','depth_rule':'ISLAND_NOTCH_NOT_CABINET_FRONT'}
    (output.parent/(output.stem+'_QA.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (output.parent/(output.stem+'_INHERITED_STATES.json')).write_text(json.dumps(inherited,ensure_ascii=False,default=str)+'\n')
    print(json.dumps({k:report[k] for k in ['status','bounds_m','added_dimensions_mm','inherited_objects_unchanged_except_ac_pose','ac_yaw_degrees_review','corrected_sha256']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',required=True);parser.add_argument('--project-root',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    run(args.source,args.output,args.project_root)
