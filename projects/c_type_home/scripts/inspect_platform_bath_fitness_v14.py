import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';D.mkdir(exist_ok=True);S=R/'design/fridge_finish_v13/WHOLE_HOUSE_FRIDGE_FINISH_DELIVERY_V13.blend';assert hashlib.sha256(S.read_bytes()).hexdigest()=='cfabc7215452f4c2e9ddba3b7ab7c2f063c14c460ba773b1fc340ee0745f31c7';bpy.ops.wm.open_mainfile(filepath=str(S))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
 if o.type not in {'MESH','CURVE','EMPTY'} or o.hide_render:continue
 name=o.name
 targeted=name.startswith(('WAVE_','STEP_','R3_SHOWER','R3_VANITY','R3_WC','CBM_SECONDARY','HOUSE_V1_STUDY_GAP_ART','LD_WINDOW_CHAISE','V3_CHAISE','HOUSE_V1_WINDOW','V4_Curtain')) or name in ['VIEW_WALL_W_wall_md_0006','VIEW_WALL_W_wall_md_0033','VIEW_WALL_R3_WEST_PARTITION','VIEW_WALL_R3_SOUTH_POCKET_PARTITION','HUNYUAN_V3_LIVING_L_SOFA']
 if o.type=='MESH':
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
  if not vs:continue
  lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
  # Bounded exact local inspection only around selected bath/study/fitness walls.
  near=(lo[0]<7.8 and hi[0]>2.85 and lo[1]<13.9 and hi[1]>10.5) or (lo[0]<16.5 and hi[0]>15.3 and lo[1]<9.7 and hi[1]>7.7) or (lo[0]<11.7 and hi[0]>9.1 and lo[1]<6.7 and hi[1]>4.45)
  if not targeted and not near:continue
 else:
  if not targeted:continue
  lo=hi=None
 data={'name':name,'type':o.type,'bounds':[lo,hi] if lo else None,'location':list(o.location),'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []}
 if o.type=='CURVE':data['splines']=[{'type':sp.type,'points':[list(p.co) for p in sp.points],'bezier':[list(p.co) for p in sp.bezier_points]} for sp in o.data.splines];data['bevel_depth']=o.data.bevel_depth
 rows.append(data)
(D/'INSPECTION.json').write_text(json.dumps(rows,indent=2));print('V14_BOUNDED_INSPECTION',len(rows))
for x in rows:
 if x['name'].startswith(('WAVE_','R3_SHOWER','R3_VANITY','R3_WC','CBM_SECONDARY','HOUSE_V1_STUDY_GAP_ART','LD_WINDOW_CHAISE')):print(x['name'],x['bounds'],x.get('splines',[]),x['parent'])

