"""Current design registry inventory for rendering, not CAD rediscovery."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1/00_MANIFEST'
R=ROOT/'design/console_bath_mirrors_review';reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update();rows=[]
for b in reg['bindings']:
 o=bpy.data.objects[b['native_id']];vs=[o.matrix_world@v.co for v in o.data.vertices]
 if not vs:continue
 a=[min(v[i] for v in vs) for i in range(3)];c=[max(v[i] for v in vs) for i in range(3)]
 rows.append({'name':o.name,'entity_id':b['entity_id'],'semantic_type':b['semantic_type'],'room_id':b['room_id'],
 'bounds':[a,c],'collections':[x.name for x in o.users_collection],'parent':o.parent.name if o.parent else None,'materials':[m.name if m else None for m in o.data.materials],
 'visible':not(o.hide_render or o.hide_viewport),'mesh_vertices':len(vs)})
hidden=[{'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection]} for o in bpy.context.scene.objects if any(x in o.name.upper() for x in ['CEILING','ROOF','CAMERA','LIGHT'])]
devices=[]
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.get_devices();devices=[{'name':d.name,'type':d.type} for d in p.devices]
except Exception as e:devices=[{'error':str(e)}]
d={'source':reg['source_locator'],'sha256':reg['source_sha256'],'rows':rows,'existing_presentation_objects':hidden,'devices':devices,
 'bounds_frame':'c_type_world','render_discovery_only':True}
(OUT/'CURRENT_MODEL_RENDER_INVENTORY.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('RENDER_INVENTORY',len(rows),'devices',devices)
for r in rows:
 if r['name'].startswith(('B11_Rectangle','FLOOR_','STEP_','READING','NORTH_WINDOW')):print(r['name'],[[round(x,3) for x in v] for v in r['bounds']])
print('PRESENTATION_OBJECTS',json.dumps(hidden))
