import bpy,json,uuid,sys
from pathlib import Path
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import sha,object_state

project=Path('/Users/xiwei/interior_design/projects/c_type_home')
root=project/'design/living_furniture_review_20261006'
source=root/'OPTION_A_R4_LIVING_FURNITURE_REVIEW.blend'
out=root/'OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend'
assert sha(source)=='c371efb418964fcb575ac92d18f18e1a027b6c2e683a78e93647046fc254d72b'
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
geom=json.loads((root/'WAVE_STEP_GEOMETRY.json').read_text())

def make_mesh(name,data,material=None):
    me=bpy.data.meshes.new(name+'_MESH'); me.from_pydata(data['vertices'],[],data['faces']); me.update()
    ob=bpy.data.objects.get(name)
    if ob is None: ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
    else:
        old=ob.data; ob.data=me
        if old and old.users==0: bpy.data.meshes.remove(old)
    if material:
        me.materials.append(material)
    return ob

wood=bpy.data.materials.get('R4_WAVE_STEP_PALE_WOOD') or bpy.data.materials.new('R4_WAVE_STEP_PALE_WOOD')
wood.diffuse_color=(0.62,0.48,0.32,1); wood.use_nodes=True
wood.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(0.62,0.48,0.32,1)
wood.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.72
for name,objdata in geom['objects'].items():
    make_mesh(name,objdata,wood if name.startswith(('STEP_','WAVE_STEP_')) else None)

for o in bpy.context.scene.objects:
    if o.name=='FASCIA_PLATFORM_CURVE' or o.name.startswith('B11_STEP_') or o.name.startswith('B11_LEISURE_CURVE_TRIM_'):
        o.hide_viewport=True; o.hide_render=True; o.hide_set(True)

glass=bpy.data.materials.get('R4_NORTH_BALCONY_GLASS') or bpy.data.materials.new('R4_NORTH_BALCONY_GLASS')
glass.diffuse_color=(0.52,0.78,0.86,0.30); glass.use_nodes=True
bs=glass.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(0.30,0.68,0.82,1); bs.inputs['Roughness'].default_value=.12; bs.inputs['Alpha'].default_value=.30
try: glass.surface_render_method='DITHERED'
except Exception: pass

def cube_mesh(lo,hi):
    x0,y0,z0=lo; x1,y1,z1=hi
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return {'vertices':v,'faces':f}

# Clear glass is inset into the aluminum frame on all four sides. The east bay
# runs all the way to the south post and the north corner post.
glass_parts=[('NORTH_BALCONY_GLASS_NORTH_A',(8.25,13.649,1.10),(10.48,13.661,2.74)),('NORTH_BALCONY_GLASS_NORTH_B',(10.57,13.649,1.10),(12.84,13.661,2.74)),('NORTH_BALCONY_GLASS_EAST',(12.969,11.17,1.10),(12.981,13.58,2.74))]
for name,lo,hi in glass_parts: make_mesh(name,cube_mesh(lo,hi),glass)

# Continuous thermally-broken aluminum frame: sill, head, end posts, corner post,
# and intermediate mullion. These are review geometry only and keep each glass bay
# separately selectable so the enclosure is not represented as two floating panes.
alum=bpy.data.materials.get('R4_NORTH_BALCONY_ALUMINUM') or bpy.data.materials.new('R4_NORTH_BALCONY_ALUMINUM')
alum.diffuse_color=(0.08,0.09,0.10,1); alum.use_nodes=True
ab=alum.node_tree.nodes.get('Principled BSDF'); ab.inputs['Base Color'].default_value=(0.08,0.09,0.10,1); ab.inputs['Roughness'].default_value=.28; ab.inputs['Metallic'].default_value=.82
frame_parts=[
 ('NORTH_BALCONY_FRAME_NORTH_SILL',(8.16,13.60,1.02),(12.92,13.71,1.10)),
 ('NORTH_BALCONY_FRAME_NORTH_HEAD',(8.16,13.60,2.74),(12.92,13.71,2.82)),
 ('NORTH_BALCONY_FRAME_NORTH_LEFT_POST',(8.16,13.60,1.02),(8.25,13.71,2.82)),
 ('NORTH_BALCONY_FRAME_NORTH_MULLION',(10.48,13.60,1.02),(10.57,13.71,2.82)),
 ('NORTH_BALCONY_FRAME_NORTH_RIGHT_POST',(12.84,13.60,1.02),(12.93,13.71,2.82)),
 ('NORTH_BALCONY_FRAME_EAST_SILL',(12.92,11.08,1.02),(13.03,13.67,1.10)),
 ('NORTH_BALCONY_FRAME_EAST_HEAD',(12.92,11.08,2.74),(13.03,13.67,2.82)),
 ('NORTH_BALCONY_FRAME_EAST_POST_SOUTH',(12.92,11.08,1.02),(13.03,11.17,2.82)),
 ('NORTH_BALCONY_FRAME_EAST_CORNER_POST',(12.92,13.58,1.02),(13.03,13.67,2.82)),
]
for name,lo,hi in frame_parts: make_mesh(name,cube_mesh(lo,hi),alum)

registry=json.loads((root/'spatial-canvas.bindings.json').read_text())
# Retired stair/platform trim is retained in the review .blend for provenance but
# intentionally omitted from the derived interaction proxy to avoid duplicate hits.
retired={'FASCIA_PLATFORM_CURVE'}
retired.update(o.name for o in bpy.context.scene.objects if o.name.startswith('B11_STEP_') or o.name.startswith('B11_LEISURE_CURVE_TRIM_'))
registry['bindings']=[b for b in registry['bindings'] if b['native_id'] not in retired]
existing={x['native_id'] for x in registry['bindings']}
for name,_lo,_hi in glass_parts:
    if name not in existing:
        registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:north-balcony-glass:v1:'+name).hex,'adapter':'blender','native_id':name,'semantic_type':'window','room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
if 'WAVE_STEP_3_ARRIVAL' not in existing:
    registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:wave-step:v1:WAVE_STEP_3_ARRIVAL').hex,'adapter':'blender','native_id':'WAVE_STEP_3_ARRIVAL','semantic_type':'stair','room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
for name,_lo,_hi in frame_parts:
    if name not in existing:
        registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:north-balcony-aluminum:v1:'+name).hex,'adapter':'blender','native_id':name,'semantic_type':'window_frame','room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
registry['registry_revision']='12-living-wave35-aluminum-fit-review'; registry['source_resource_id']='c_type_r4_living_wave35_aluminum_review'; registry['source_revision']='r4-living-wave35-aluminum-review-2'; registry['source_locator']=str(out); registry['source_authority']='frozen'
bpy.ops.wm.save_as_mainfile(filepath=str(out)); registry['source_sha256']=sha(out)
(root/'spatial-canvas.bindings.aluminum-fit-2.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(out))
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name in {'FLOOR_LOWER','R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','STEP_0','STEP_1','STEP_2','FASCIA_PLATFORM_CURVE'} or name.startswith('B11_STEP_') or name.startswith('B11_LEISURE_CURVE_TRIM_'): continue
    assert now==state,name
assert sha(source)=='c371efb418964fcb575ac92d18f18e1a027b6c2e683a78e93647046fc254d72b'
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':sha(source),'output':str(out),'output_sha256':sha(out),'stair':{'risers':4,'rise_m':geom['rise_m'],'tread_run_m':geom['tread_run_m'],'overall_retraction_m':geom['overall_retraction_m'],'lower_edge_retraction_m':geom['lower_edge_retraction_m'],'reclaimed_lower_floor_m2':geom['reclaimed_lower_floor_m2'],'arrival_full_height':True},'north_balcony_glass':{'objects':[x[0] for x in glass_parts],'aluminum_frame_objects':[x[0] for x in frame_parts],'base_wall_native_ids':['VIEW_WALL_DOOR_V2_NBALC_SOLID_ABOVE_DOOR','VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0061','VIEW_WALL_W_wall_md_0062'],'opaque_walls_unchanged':True,'glass_and_frame_are_derived_review_only':True},'frozen_source_unchanged':True,'fresh_reopen_verified':True}
(root/'ALUMINUM_FIT_REVIEW_2_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(report,ensure_ascii=False))
