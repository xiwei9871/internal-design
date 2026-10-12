"""Bounded geometry-contact finish repair, preserving first assembled candidate."""
import bpy,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'design/whole_house_model_v1/assembly';a=json.loads((RUN/'BUILD_AUDIT.json').read_text());SOURCE=Path(a['output']);DEST=RUN/'WHOLE_HOUSE_ASSEMBLED_DELIVERY_V1.blend'
if DEST.exists():raise SystemExit('Preserved delivery exists; do not overwrite.')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
changes=[]
# Three custom-built bags touch at less0.2mm because pilot overall width includes
# curve rounding. Give complete rear-cover/attached sewing paths3mm seam clearance
# across original module centres. No wood-frame relocation or height change.
for o in list(scene.objects):
 if o.name.startswith('HOUSE_V1_SOFA_') and 'BACK_COMPLETE_COVER' in o.name:
  if o.type=='MESH':
   o.data=o.data.copy()
   for v in o.data.vertices:v.co.x*=.997
  elif o.type=='CURVE':
   o.data=o.data.copy()
   for spline in o.data.splines:
    for p in spline.points:p.co.x*=.997
  changes.append(o.name)
# Put styling physically on actual source countertops, not at guessed coordinates.
def move(prefix,delta):
 for o in scene.objects:
  if o.name.startswith('HOUSE_V1_'+prefix):o.location+=Vector(delta)
move('Utility_storage_bin',(-.52,.22,-.06))
move('Utility_folded_linen',(-.56,.13,-.036))
move('Entry_ceramic',(-.45,0,-.007))
# Additional review cameras are separate from75 approved views: relocated reading
# shelf and changed master vanity must be shown from visible sides.
def camera(name,eye,target,lens):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01
camera('HOUSE_V1_READING_OPPOSITE_WALL',(5.84,8.28,1.72),(7.55,8.6,1.28),34)
camera('HOUSE_V1_MASTER_CABINET',(13.78,5.16,1.54),(13.8,6.0,1.01),28)
camera('HOUSE_V1_MOTHER_CREATIVE_BED',(12.05,3.65,1.98),(14.12,2.18,1.11),28)
bpy.ops.wm.save_as_mainfile(filepath=str(DEST));a['first_assembly_source']=str(SOURCE);a['first_assembly_sha256']=a['output_sha256'];a['output']=str(DEST);a['output_sha256']=hashlib.sha256(DEST.read_bytes()).hexdigest();a['bounded_contact_repairs']={'complete_back_cover_width_factor':.997,'bag_clearance_mm':3,'changed_back_objects':changes,'styling_supports':'utility and entry props placed on actual existing counters','review_cameras_added':3};(RUN/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('ASSEMBLY_DELIVERY',a['output_sha256'])
