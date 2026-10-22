import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
model=Path('projects/c_type_home/design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend').resolve()
out=Path('projects/c_type_home/design/living_correction_v1')
def bounds(o):
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def rec(o):
 mats=[]
 for s in o.material_slots:
  m=s.material
  if m is None:
   mats.append(None); continue
  mats.append(dict(name=m.name,diffuse=list(m.diffuse_color),base=list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value) if m.use_nodes and m.node_tree.nodes.get('Principled BSDF') else None))
 return dict(name=o.name,type=o.type,bounds=bounds(o) if o.type=='MESH' else None,parent=o.parent.name if o.parent else None,collections=[c.name for c in o.users_collection],materials=mats,props={k:o[k] for k in o.keys() if k!='_RNA_UI'},hide_render=o.hide_render,hide_viewport=o.hide_viewport)
bpy.ops.wm.open_mainfile(filepath=str(model));bpy.context.view_layer.update()
allmesh=[rec(o) for o in bpy.data.objects if o.type=='MESH']
blue=[]
for o in allmesh:
 for m in o['materials']:
  if not m: continue
  c=m['diffuse']
  if c[2]>c[0]*1.3 and c[2]>c[1]*1.1 and c[2]>0.18: blue.append(o);break
terms=['door','D-','G-GB','GB-BALC','Rectangle','Circle','客','guest','BED']
related=[o for o in allmesh if any(t.lower() in o['name'].lower() for t in terms)]
result=dict(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),blue=blue,related=related)
(out/'BLUE_PANEL_INVENTORY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'blue_count':len(blue),'blue':[x['name'] for x in blue],'related_count':len(related)},ensure_ascii=False))
