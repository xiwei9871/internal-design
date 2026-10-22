"""Fresh-reopen source/derivative geometry and evaluated envelope checks."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/living_dining_detail_v1';BASE=ROOT/'design/sunroom_stepped_storage_v1/SUNROOM_STEPPED_STORAGE_V1.blend'
registry=json.loads((BASE.parent/'spatial-canvas.bindings.full.json').read_text());names=[b['native_id'] for b in registry['bindings']]
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),tuple(v for row in o.matrix_world for v in row)
bpy.ops.wm.open_mainfile(filepath=str(BASE));original={n:fingerprint(bpy.data.objects[n]) for n in names}
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_DETAIL_V1.blend'))
for n in names:bpy.data.objects[n].hide_set(False);bpy.data.objects[n].hide_viewport=False
bpy.context.view_layer.update()
for n,f in original.items():assert fingerprint(bpy.data.objects[n])==f,n
deps=bpy.context.evaluated_depsgraph_get()
def bounds(objects):
 pts=[]
 for o in objects:
  if o.type not in ['MESH','CURVE']:continue
  e=o.evaluated_get(deps);me=e.to_mesh();pts.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
checks={}
for n,wanted in [('COFFEE_TABLE',[[5.025,9.49,0],[5.575,10.49,.4]]),('RACETRACK_DINING_TABLE',[[3.027625,3.064406,0],[4.627625,3.864406,.75]]),('L_SOFA',[[3.4,7.95,0],[5.2,11.25,.7]]),('WINDOW_CHAISE',[[4.671625,11.05522,0],[6.371625,11.95522,.8]])]:
 actual=bounds(bpy.data.objects['LD_'+n].children);within=all(actual[0][i]>=wanted[0][i]-.003 and actual[1][i]<=wanted[1][i]+.003 for i in range(3));checks[n]={'bounds_m':actual,'source_envelope_m':wanted,'within_source_envelope_3mm':within};assert within,(n,actual)
for i in range(4):
 n='LD_DINING_CHAIR_%d'%i;b=bounds(bpy.data.objects[n].children);assert max(b[1][j]-b[0][j] for j in [0,1])<=.401
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
report={'status':'PASS','fresh_reopen':True,'unchanged_source_meshes_and_matrices':len(names),'evaluated_envelopes':checks,'four_chairs_within_400mm_xy':True,'missing_images':missing,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'safety_and_manufacturing_certification':False}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('LD_VERIFY_PASS',len(names))
