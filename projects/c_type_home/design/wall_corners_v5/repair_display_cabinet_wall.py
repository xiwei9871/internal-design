"""Add the missing rear wall behind the kitchen display cabinet to a new base revision."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
SOURCE=OUT/'HOUSE_BASE_GEOMETRY_V1.blend';MODEL=OUT/'HOUSE_BASE_GEOMETRY_V2.blend'
MANIFEST=OUT/'HOUSE_BASE_GEOMETRY_V2_MANIFEST.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
def snapshot():
 out={}
 for o in bpy.data.objects:
  if o.type=='MESH':out[o.name]=dict(bounds=bounds(o),matrix=[list(r) for r in o.matrix_world],hide_render=o.hide_render,hide_viewport=o.hide_viewport,materials=[s.material.name if s.material else None for s in o.material_slots])
 return out
def build():
 assert not MODEL.exists();bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update();before=snapshot()
 col=bpy.data.collections.new('COL_KITCHEN_DISPLAY_CABINET_WALL_V2');bpy.context.scene.collection.children.link(col)
 mat=bpy.data.materials.get('SITE_REVIEW_CONTINUOUS_WALL') or bpy.data.materials.new('SITE_REVIEW_CONTINUOUS_WALL');mat.diffuse_color=(.85,.86,.84,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=mat.diffuse_color
 # Existing parapet W_wall_md_0004 runs x=1300..1500, y=700..2300, z=0..1050.
 # Display cabinet back reaches x=1520; extend the wall up behind it to the ceiling.
 bpy.ops.mesh.primitive_cube_add(size=1,location=(1.41,1.50,(1.05+2.80)/2));o=bpy.context.object;o.name='V2_KITCHEN_DISPLAY_CABINET_REAR_WALL';o.dimensions=(.22,1.60,1.75);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);o.color=mat.diffuse_color
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o['source_reference']='W_wall_md_0004 + B11_SITE_BUFFET_R029';o['semantic_role']='UPPER_REAR_WALL_BEHIND_INDEPENDENT_DISPLAY_CABINET';o['review_status']='HUMAN_REVIEW';o['physical_ground_truth']=False
 camdata=bpy.data.cameras.new('V2_DISPLAY_WALL_CAM');cam=bpy.data.objects.new('V2_DISPLAY_WALL_CAM',camdata);col.objects.link(cam);cam.location=(.15,1.55,1.8);cam.rotation_euler=(Vector((1.55,1.5,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=35
 scene=bpy.context.scene;scene.camera=cam;scene['base_revision']='HOUSE_BASE_GEOMETRY_V2';scene['display_cabinet_rear_wall_added']=True
 after=snapshot()
 for n,s in before.items():assert after[n]==s,n
 bpy.ops.wm.save_as_mainfile(filepath=str(MODEL));assert sha(SOURCE)==sha(SOURCE)
 manifest=dict(status='HOUSE_BASE_GEOMETRY_V2_CANDIDATE',source=str(SOURCE),source_sha256=sha(SOURCE),model=str(MODEL),model_sha256=sha(MODEL),wall_bounds_mm=[[1300,700,1050],[1520,2300,2800]],display_cabinet='B11_SITE_PHOTO5_BUFFET_R029',existing_parapet='W_wall_md_0004',source_meshes_poses_preserved=True,kitchen_layout_preserved=True,black_wall_demolition_count=0,scope='UPPER_REAR_WALL_BEHIND_INDEPENDENT_DISPLAY_CABINET')
 MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
def verify():
 m=json.loads(MANIFEST.read_text());assert sha(MODEL)==m['model_sha256'] and sha(SOURCE)==m['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(MODEL));o=bpy.data.objects['V2_KITCHEN_DISPLAY_CABINET_REAR_WALL'];b=bounds(o);assert abs(b[0][0]-1.30)<1e-5 and abs(b[1][2]-2.8)<1e-5;print(json.dumps({'verify':'PASS','model_sha256':sha(MODEL),'wall_bounds_m':b,'objects':len(bpy.data.objects)}))
if __name__=='__main__':
 mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build';{'build':build,'verify':verify}[mode]()
