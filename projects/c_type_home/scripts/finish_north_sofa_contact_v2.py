"""Measured38mm back/seat gap: restore resting contact and retain first candidate."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend'
if dest.exists():raise SystemExit('Preserved supported model exists')
bpy.ops.wm.open_mainfile(filepath=str(src))
for j in [0,1]:bpy.data.objects['HOUSE_V2_North_back_'+str(j)].location.z-=.036
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_north_contact']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['north_back_contact_correction_mm']=-36
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('NORTH_SUPPORTED',a['output_sha256'])
