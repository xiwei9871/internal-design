"""Bridge retained pull plates to the thinner glass, preserving their installation positions."""
import bpy,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dst=D/'WHOLE_HOUSE_PALE_ASH_DELIVERY_V7.blend';assert not dst.exists();assert hashlib.sha256(src.read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;bpy.context.view_layer.update();sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
col=bpy.data.collections['V7_FRAMED_GLASS_SLIDING_ASSEMBLY'];metal=bpy.data.materials['RENDER_BRUSHED_NICKEL'];P=Parts(col,metal,metal);created=[];records=[]
pane=bpy.data.objects[a['slider_frame_created'][0]];pv=[pane.matrix_world@v.co for v in pane.data.vertices];ymin=min(v.y for v in pv);ymax=max(v.y for v in pv)
for side in ['N','S']:
 pull=bpy.data.objects['R3_SLIDING_RECESSED_PULL_'+side];vs=[pull.matrix_world@v.co for v in pull.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)];x=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;cz=(lo[2]+hi[2])/2;plane=ymax if cy>pane.location.y else ymin
 for k,z in enumerate([cz-.055,cz+.055]):
  obj=P.rod('V7_GLASS_PULL_CLAMP_'+side+'_'+str(k),(x,plane,z),(x,cy,z),.0045,metal);created.append(obj.name);records.append({'name':obj.name,'glass_anchor_m':[x,plane,z],'pull_anchor_m':[x,cy,z],'construction':'inferred surface-mounted stand-off clamp; existing rail/pull positions retained, supplier drilling/tempering unresolved'})
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(dst));a['pre_pull_mount']={'path':str(src),'sha256':a['sha256']};a['output']=str(dst);a['sha256']=hashlib.sha256(dst.read_bytes()).hexdigest();a['slider_clamp_created']=created;a['slider_mounts']=records
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V7_DELIVERY',a['sha256'])
