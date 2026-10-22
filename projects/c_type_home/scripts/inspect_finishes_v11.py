import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/finishes_v11';D.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'design/reading_wall_v10/WHOLE_HOUSE_READING_CLEANUP_V10.blend'))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
a=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render:continue
 if any(k in o.name.upper() for k in ['FLOOR','TILE','WALL','STEP_','CLEAT','READING_DISPLAY','READING_5015','BASEBOARD','SKIRT']):
  vs=[o.matrix_world@Vector(v) for v in o.bound_box]
  a.append({'name':o.name,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'materials':[m.name if m else None for m in o.data.materials],'polygons':len(o.data.polygons)})
(D/'INSPECTION.json').write_text(json.dumps(a,indent=2))
ms={m for x in a for m in x['materials'] if m};ma=[]
for n in sorted(ms):
 m=bpy.data.materials[n];ma.append({'name':n,'diffuse_color':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,'inputs':{p.name:list(p.default_value) if hasattr(p.default_value,'__len__') and not isinstance(p.default_value,str) else p.default_value for p in n.inputs if hasattr(p,'default_value') and p.type in ['VALUE','RGBA','VECTOR']}} for n in m.node_tree.nodes] if m.use_nodes else []})
(D/'MATERIALS.json').write_text(json.dumps(ma,indent=2))
print('FINISH_INSPECT',len(a),'objects',len(ma),'materials')
