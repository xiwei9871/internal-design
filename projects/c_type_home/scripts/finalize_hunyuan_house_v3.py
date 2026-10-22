"""Restore owner-selected bedside cabinets caught by broad prefix replacement."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_HUNYUAN_REVIEW_V3.blend'
if dest.exists():raise SystemExit('Preserved review exists')
bpy.ops.wm.open_mainfile(filepath=str(src));restored=[]
for n in a['hidden_replaced']:
 if n.startswith(('HOUSE_V2_COUPLE_0_','HOUSE_V2_COUPLE_1_')):
  o=bpy.data.objects[n];o.hide_render=False;o.hide_viewport=False;o.hide_set(False);restored.append(n)
a['hidden_replaced']=[n for n in a['hidden_replaced'] if n not in restored]
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['first_candidate']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['bedside_restored']=restored
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('HUNYUAN_REVIEW',a['output_sha256'],len(restored))
