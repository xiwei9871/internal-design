"""Adapt the existing project's framed-glazing assembly to the retained door envelope."""
import bpy,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dst=D/'WHOLE_HOUSE_PALE_ASH_FRAMED_V7.blend';assert not dst.exists()
assert hashlib.sha256(src.read_bytes()).hexdigest()==a['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
old=bpy.data.objects['R3_SLIDING_LEAF'];bpy.context.view_layer.update();vs=[old.matrix_world@v.co for v in old.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)];w=hi[0]-lo[0];th=hi[1]-lo[1];h=hi[2]-lo[2];cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;cz=(lo[2]+hi[2])/2
old.hide_render=True;old.hide_viewport=True;old.hide_set(True)
sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
col=bpy.data.collections.new('V7_FRAMED_GLASS_SLIDING_ASSEMBLY');s.collection.children.link(col)
metal=bpy.data.materials['RENDER_BRUSHED_NICKEL'];glass=bpy.data.materials['V7_SLIDING_CLEAR_GLASS'];P=Parts(col,metal,metal);created=[]
# Existing house framed glazing workflow: slender metal frame + real thin pane.
# Retain the previous 40mm outer leaf envelope; 10mm pane/25mm frame are inferred custom construction, not an ordered SKU.
t=.025
for name,c,size,mat in [('SLIDER_GLASS_PANE',(cx,cy,cz),(w-2*t,.010,h-2*t),glass),('SLIDER_FRAME_LEFT',(lo[0]+t/2,cy,cz),(t,th,h),metal),('SLIDER_FRAME_RIGHT',(hi[0]-t/2,cy,cz),(t,th,h),metal),('SLIDER_FRAME_TOP',(cx,cy,hi[2]-t/2),(w-2*t,th,t),metal),('SLIDER_FRAME_BOTTOM',(cx,cy,lo[2]+t/2),(w-2*t,th,t),metal)]:
 o=P.box('V7_'+name,c,size,mat,r=.001);created.append(o.name)
# Existing hanger/rail and pull installation positions remain; glazing production and safety-glass specification require final supplier data.
s.view_layers['OVERVIEW_CEILING_HIDDEN'].use=False;s.view_layers['INTERIOR_CLOSED_CEILING'].use=True;bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']
bpy.ops.wm.save_as_mainfile(filepath=str(dst));a['pre_framed_slider']={'path':str(src),'sha256':a['sha256']};a['output']=str(dst);a['sha256']=hashlib.sha256(dst.read_bytes()).hexdigest();a['slider_hidden_source']='R3_SLIDING_LEAF';a['slider_frame_created']=created;a['slider_construction']={'outer_bounds_m':[lo,hi],'glass_thickness_mm':10,'frame_face_width_mm':25,'frame_depth_mm':th*1000,'construction':'project-established framed glazing; custom inferred assembly, no purchased SKU or safety certification'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V7_FRAMED_SLIDER',a['sha256'],created)
