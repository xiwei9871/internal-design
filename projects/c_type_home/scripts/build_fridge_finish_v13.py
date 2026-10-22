import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';D.mkdir(exist_ok=True)
S=R/'design/mother_hunyuan_v12/WHOLE_HOUSE_MOTHER_HUNYUAN_V12.blend';O=D/'WHOLE_HOUSE_FRIDGE_FINISH_V13.blend';SHA='da6e5a80dec49831e9d856d0bab90113e87a5ae19316c162d869d7b65a280fd6';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==SHA and not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
wood=bpy.data.materials['V7_CATALOG_PALE_NATURAL_ASH'];metal=bpy.data.materials['V3_BRUSHED_STAINLESS'];before={o.name:[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [] for o in bpy.data.objects};changed=[]
for o in s.objects:
 if o.name.startswith('B11_K-FRIDGE-OVERHEAD_') and 'PULL' not in o.name:o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(wood);changed.append(o.name)
for n in ['B11_K-FRIDGE-OVERHEAD_PULL_0','B11_K-FRIDGE-OVERHEAD_PULL_1']:
 o=bpy.data.objects[n];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(metal)
bpy.ops.wm.save_as_mainfile(filepath=str(O))
def bounds(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
t=bounds(bpy.data.objects['R3_SHOWER_TRAY']);w=(t[1][0]-t[0][0])*1000;d=(t[1][1]-t[0][1])*1000
record={'source':str(S),'source_sha256':SHA,'output':str(O),'sha256':sha(O),'before':before,'changed_cabinet_objects':changed,'finish_material':wood.name,'pull_material':metal.name,'shower_audit':{'tray_outer_mm':[round(w,1),round(d,1)],'estimated_inner_clear_mm':[round(w-36,1),round(d-36,1)],'guidance':'Compact shower reference starts about 760-900mm per side; measured tray is tight but usable for basic standing use, not seated aging-in-place proof. Verify opening on site.'},'status':'HUMAN_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n');print('FRIDGE_FINISH_V13',record['sha256'],record['shower_audit'])

