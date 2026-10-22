"""Final bounded presentation repair; source architecture and product shapes stay fixed."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'design/whole_house_model_v1/assembly'
a=json.loads((RUN/'BUILD_AUDIT.json').read_text())
src=Path(a['output']);dest=RUN/'WHOLE_HOUSE_REVIEW_V1.blend'
if dest.exists():raise SystemExit('Preserved review exists; choose a new version.')
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
fix=[]
# Verified white discs are the V3 south-window area light: camera visibility
# alone was false, while transmission/glossy were true. Retain diffuse energy.
o=bpy.data.objects['V3_KITCHEN_DAYLIGHT_THROUGH_SOUTH_WINDOW']
fix.append({'object':o.name,'before':{'glossy':o.visible_glossy,'transmission':o.visible_transmission},'energy_unchanged':o.data.energy})
o.visible_glossy=False;o.visible_transmission=False
# Original source preview powers were ~6-7 render watts and the enclosed halls
# and baths were unreadably dark. These are look-development values, not a
# claim about electrical wattage, lux or the installed fixture specification.
lights=[]
for n,p in [('LIGHT_hallway_2900K',55),('LIGHT_master_bath_2900K',65),('LIGHT_secondary_bath_2900K',55),('LIGHT_guest_bath_2900K',55)]:
 o=bpy.data.objects[n];lights.append({'object':n,'before':o.data.energy,'after':p,'status':'render lighting only; no photometric certification'});o.data.energy=p
# On the opposing wall the source bookcase overlaps the console top by30mm.
# Wall-hang the complete unchanged assembly55mm higher. Two wall cleats are
# explicit custom construction, NOT manufacturer load-certified hardware.
reading=[]
for o in s.objects:
 if o.name.startswith(('READING_5015_','READING_DISPLAY_','READING_BOOK_')):
  o.location.z+=.055;reading.append(o.name)
col=bpy.data.collections['WHOLE_HOUSE_ACTUAL_FINISH_V1'] if 'WHOLE_HOUSE_ACTUAL_FINISH_V1' in bpy.data.collections else s.collection
wood=bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'].data.materials[0]
for z in [.58,.735]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(7.72,8.60,z));o=bpy.context.object;o.name='HOUSE_V1_READING_WALL_CLEAT_'+str(z);o.dimensions=(.06,.72,.05);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(wood);o['construction']='wall-fixed custom support; anchors/load/substrate require site detailing';a['created_objects'].append(o.name)
a['created_count']+=2
# Additional review angles supplement the75 untouched registered cameras.
def cam(n,eye,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01
cam('HOUSE_V1_LIVING_SOFA_DETAIL',(6.43,10.58,1.52),(4.72,10.11,.57),42)
cam('HOUSE_V1_DINING_WHOLE',(5.48,5.44,1.62),(3.90,3.52,1.15),25)
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
a['pre_presentation_repair']={'path':str(src),'sha256':a['output_sha256']}
a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
a['presentation_repairs']={'light_visibility':fix,'practical_light_energy':lights,'reading_wall_hung_rise_m':.055,'reading_wall_mount_objects':reading,'installation_review':'wall substrate, anchors and book loading pending; console unchanged'}
a['room_changes']['reading_transition']='original820x320 assembly on opposite art wall, wall-hung bottom505mm,25mm console-top clearance; source shape unchanged, mounting capacity pending'
(RUN/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
print('FINAL_PRESENTATION',a['output_sha256'])
