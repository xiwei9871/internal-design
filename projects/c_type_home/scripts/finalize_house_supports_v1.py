"""Place household styling on verified source supports; keep earlier candidates."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'design/whole_house_model_v1/assembly';a=json.loads((RUN/'BUILD_AUDIT.json').read_text());SOURCE=Path(a['output']);DEST=RUN/'WHOLE_HOUSE_FINAL_CANDIDATE_V1.blend'
if DEST.exists():raise SystemExit('Final candidate already exists; do not overwrite.')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));targets={'HOUSE_V1_Utility_storage_bin':((1.78,1.38,1.10),'B11_SITE_BUFFET_COUNTER'),'HOUSE_V1_Utility_folded_linen':((1.78,1.85,1.10),'B11_SITE_BUFFET_COUNTER'),'HOUSE_V1_Entry_ceramic':((3.085,4.93,1.00),'B11_Rectangle031_TOP')}
records=[]
for prefix,(target,support) in targets.items():
 obs=[o for o in bpy.data.objects if o.name.startswith(prefix)];bpy.context.view_layer.update();pts=[]
 for o in obs:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();pts.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];delta=Vector((target[0]-(lo[0]+hi[0])/2,target[1]-(lo[1]+hi[1])/2,target[2]-lo[2]))
 for o in obs:o.location+=delta;o['support_source_object']=support
 records.append({'objects':[o.name for o in obs],'source_support':support,'bottom_elevation_m':target[2],'center_xy':target[:2]})
bpy.ops.wm.save_as_mainfile(filepath=str(DEST));a['pre_support_finish_source']=str(SOURCE);a['output']=str(DEST);a['output_sha256']=hashlib.sha256(DEST.read_bytes()).hexdigest();a['explicit_prop_supports']=records;(RUN/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('HOUSE_FINAL_CANDIDATE',a['output_sha256'])
