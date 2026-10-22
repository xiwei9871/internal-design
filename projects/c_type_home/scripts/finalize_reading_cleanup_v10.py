"""Restore previously approved duplicate-bench hide in the relocated reading candidate."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/reading_wall_v10';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_READING_CLEANUP_V10.blend';assert not dest.exists();assert hashlib.sha256(src.read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;o=bpy.data.objects['READING_3205A_PADDED_BENCH'];bpy.context.view_layer.update();vs=[o.matrix_world@v.co for v in o.data.vertices];bounds=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
o.hide_render=True;o.hide_viewport=True
for layer in s.view_layers:o.hide_set(True,view_layer=layer)
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_duplicate_cleanup']={'path':str(src),'sha256':a['sha256']};a['output']=str(dest);a['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['hidden_duplicate_bench']={'name':o.name,'bounds_m':bounds,'reason':'Previously hidden in living_dining_detail_v1 because overlaps living low cabinet; inherited whole-house visibility regression. User explicitly flagged extra item. Geometry retained.'};a['circulation_sections']=json.loads((D/'CIRCULATION_SECTIONS.json').read_text());a.pop('corridor_clear_width_assuming_opposite_edge_x8_0_mm',None);a['corridor_note']='Use actual top-step mesh cross sections at five y positions; smallest horizontal cabinet-to-step gap1693mm, not the misleading AABB estimate.'
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('READING_CLEANUP_V10',a['sha256'],bounds)
