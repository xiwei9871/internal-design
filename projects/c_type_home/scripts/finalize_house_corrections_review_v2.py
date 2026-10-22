"""Bounded supplemental-camera correction, no architecture or registered-camera edit."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_CORRECTED_REVIEW_V2.blend'
if dest.exists():raise SystemExit('Preserved output exists')
bpy.ops.wm.open_mainfile(filepath=str(src));o=next(o for o in bpy.data.objects if o.name.startswith('HOUSE_V2_NORTH_SOFA') and o.type=='CAMERA');o.location=(9.60,12.66,1.14);o.rotation_euler=(Vector((9.60,11.45,.55))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=37
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_camera_review']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('REVIEW_V2',a['output_sha256'])
