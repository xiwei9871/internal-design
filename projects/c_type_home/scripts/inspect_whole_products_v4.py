"""Isolated finished-product front/back/side previews, retaining authored objects."""
import bpy,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4';DEST=OUT/'whole_product_views_v3';DEST.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LIVING_DINING_PRODUCT_REBUILD_V4.blend'))
scene=bpy.context.scene
for c in bpy.data.collections:c.hide_render=False
for o in scene.objects:o.hide_render=True
def view(n,eye,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01;return o
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True;scene.display.shading.background_type='WORLD';scene.world.color=(.24,.24,.24)
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
records=[]
products=[
('SOFA','V4_LIVING_SOFA_COMPLETE',(4.0,9.6,.37),[('front',(7.7,8.2,2.1)),('back',(1.0,10.4,1.7)),('side',(5.1,5.8,1.7))]),
('CHAIR','V4_DINING_CHAIR_1_COMPLETE',(4.227625,3.924406,.43),[('front',(4.95,2.85,1.14)),('back',(3.55,5.1,1.12)),('side',(5.7,4.0,1.07))])]
for id,g,target,views in products:
 items=bpy.data.objects[g].children_recursive
 for o in items:o.hide_render=False
 for label,eye in views:
  scene.camera=view(id+'_'+label,eye,target,25 if id=='SOFA' else 32);p=DEST/(id+'_'+label+'.png');scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'product':id,'view':label,'path':str(p)})
 for o in items:o.hide_render=True
(DEST/'evidence.json').write_text(json.dumps({'method':'isolated full product front/back/side geometry inspection','views':records},indent=2)+'\n');print('WHOLE_PRODUCT_VIEWS_READY',len(records))
