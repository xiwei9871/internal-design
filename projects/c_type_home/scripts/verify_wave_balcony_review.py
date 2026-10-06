import bpy,json,sys,math,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
bpy.ops.wm.open_mainfile(filepath=str(r/'OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend'))
def coords(o):return [tuple(o.matrix_world@v.co) for v in o.data.vertices]
def bb(o):
    c=coords(o);return [[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]]
def bvh(o):return BVHTree.FromPolygons(coords(o),[list(p.vertices) for p in o.data.polygons],all_triangles=False,epsilon=1e-7)
steps=[bpy.data.objects[n] for n in ['STEP_0','STEP_1','STEP_2','WAVE_STEP_3_ARRIVAL']]
trees={o.name:bvh(o) for o in steps};hits=[]
for wall in bpy.context.scene.objects:
    if wall.type!='MESH' or not wall.visible_get() or not wall.name.startswith('VIEW_WALL_'):continue
    lo,hi=bb(wall)
    if hi[0]<5.6 or lo[0]>8.5 or hi[1]<4.7 or lo[1]>7.8:continue
    wt=bvh(wall)
    for o in steps:
        if lo[2]>=bb(o)[1][2]-1e-6:continue
        pairs=wt.overlap(trees[o.name])
        if pairs:hits.append({'wall':wall.name,'step':o.name,'pairs':len(pairs),'bounds':[lo,hi]})
# Pane size must exactly match the frame opening, including the formerly missing180mm.
openings={'NORTH_BALCONY_GLASS_EAST':(1,11.17,13.58),'NORTH_BALCONY_GLASS_NORTH_A':(0,8.25,10.48),'NORTH_BALCONY_GLASS_NORTH_B':(0,10.57,12.84)}
panes=[]
for n,(axis,a,b) in openings.items():
    lo,hi=bb(bpy.data.objects[n])
    assert abs(lo[axis]-a)<1e-5 and abs(hi[axis]-b)<1e-5
    assert abs(lo[2]-1.10)<1e-5 and abs(hi[2]-2.74)<1e-5
    panes.append({'name':n,'bounds':[lo,hi],'clear_width_m':b-a,'clear_height_m':1.64})
(r/'FIT2_CONTACT_QA.json').write_text(json.dumps({'wall_stair_surface_contacts':hits,'panes':panes},indent=2))
assert not hits,hits
print(json.dumps({'wall_stair_surface_contacts':hits,'panes':panes}))
# Same numeric source camera for the balcony fit evidence, transformed into glTFY-up.
manifest=json.loads((r/'proxy_aluminum_fit_2/interaction_proxy.manifest.json').read_text())
view=json.loads((r/'living_furniture_compare.view-preset.json').read_text())
from mathutils import Quaternion
eye=Vector((16.1,16.3,3.6));target=Vector((12.3,13.1,1.9))
sq=(target-eye).to_track_quat('-Z','Y');pq=Quaternion((1,0,0),-math.pi/2)@sq
view.update(preset_id='balcony_frame_fit_2',source_resource_id=manifest['source_resource_id'],source_revision=manifest['source_revision'],source_sha256=manifest['source_sha256'],source_locator=manifest['source_resource'],bindings=manifest['extensions']['spatial_canvas.blender']['bindings'],position=[eye.x,eye.z,-eye.y],quaternion=[pq.x,pq.y,pq.z,pq.w],orbit_target=[target.x,target.z,-target.y],hidden_entity_ids=[],ghost_entity_ids=[],preview_uri='balcony_frame_fit_2.png')
view['source_camera'].update(position=list(eye),quaternion=[sq.x,sq.y,sq.z,sq.w])
(r/'balcony_frame_fit_2.view-preset.json').write_text(json.dumps(view,indent=2))
geometry=json.loads((r/'WAVE_STEP_GEOMETRY.json').read_text())
assert geometry['tread_run_m']==.35 and geometry['overall_retraction_m']==1.0
for k in range(4):
    for a,b in zip(geometry['front_lines'][k],geometry['front_lines'][k+1]):
        assert abs(b[0]-a[0]-.35)<1e-8
topology={}
for o in steps:
    bm=bmesh.new();bm.from_mesh(o.data)
    topology[o.name]={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)}
    assert not topology[o.name]['nonmanifold_edges'],o.name
    bm.free()
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert hashlib.sha256(frozen.read_bytes()).hexdigest()=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
# Reopen derived GLB in a clean scene and verify actual materials/identity.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(r/'proxy_aluminum_fit_2/interaction_proxy.glb'))
exported={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(exported)==987
for row in panes:
    got=bb(exported[row['name']])
    assert all(abs(got[j][i]-row['bounds'][j][i])<1e-4 for j in range(2) for i in range(3))
    mat=exported[row['name']].data.materials[0]
    assert abs(mat.diffuse_color[3]-.32)<1e-5
for name,o in exported.items():
    if name.startswith('NORTH_BALCONY_FRAME_'):assert max(o.data.materials[0].diffuse_color[:3])<.1
(r/'FIT2_FINAL_QA.json').write_text(json.dumps({'revision':manifest['source_revision'],'source_sha256':manifest['source_sha256'],'panes':panes,'no_wall_stair_surface_crossings':not hits,'tread_m':.35,'additional_retreat_m':.5,'total_retreat_m':1.0,'step_topology':topology,'fresh_glb_entities':len(exported),'glass_alpha':.32,'frozen_r4_unchanged':True},indent=2))
print('FIT2_FINAL_QA_PASS')
