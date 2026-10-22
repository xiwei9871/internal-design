import bpy,bmesh,json,sys,math,time,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];option=sys.argv[sys.argv.index('--')+1];file=OUT/('LEISURE_COMPARE_OPTION_'+option+'.blend');bpy.ops.wm.open_mainfile(filepath=str(file));s=bpy.context.scene;qa=json.loads((OUT/'reports'/('OPTION_'+option+'_BUILD_QA.json')).read_text());allbase={o.name:dict(hide_render=o.hide_render,hide_viewport=o.hide_viewport,hide_get=o.hide_get()) for o in bpy.data.objects};data_backup={};results=[]
for c in qa['cameras']:
 # All cuts are in-memory visualization state; never saved into either option model.
 for n,v in allbase.items():o=bpy.data.objects[n];o.hide_render=v['hide_render'];o.hide_viewport=v['hide_viewport'];o.hide_set(v['hide_get'])
 for n,me in data_backup.items():bpy.data.objects[n].data=me
 data_backup={};s.camera=bpy.data.objects[c['camera']]
 if c['id'] in ['PLAN','AXON','SECTION']:
  for o in bpy.data.objects:
   if o.type!='MESH' or o.hide_render:continue
   if 'CEILING' in o.name.upper() or '03_EXISTING_CEILING' in [co.name for co in o.users_collection]:o.hide_render=True;continue
   if c['id']=='AXON' and ('WALL' in o.name.upper() or 'CORNER_PATCH' in o.name.upper()):
    old=o.data;data_backup[o.name]=old;o.data=old.copy();bm=bmesh.new();bm.from_mesh(o.data);world=o.matrix_world;inv=world.inverted();p=inv@Vector([0,0,1.15]);normal=(world.to_3x3().transposed()@Vector([0,0,1])).normalized();bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=normal,clear_outer=True,clear_inner=False,dist=1e-6);bm.to_mesh(o.data);bm.free()
 if c['id']=='SECTION':
  # Section Y=5.55, look north; furniture/background removed for a readable cut.
  for o in bpy.data.objects:
   if o.type!='MESH' or o.hide_render:continue
   if any(co.name in ['COL_B11_CORE_FURNITURE','COL_B11_APPLIANCES','COL_B11_BATHROOMS','COL_B11_KITCHEN','COL_B11_SPLIT_FINISHING'] for co in o.users_collection) or o.name.startswith(('B11_','R3_WARDROBE')):o.hide_render=True;continue
   # Retain just the cut floors and original walls so foreground wall doesn't seal camera.
   old=o.data;data_backup[o.name]=old;o.data=old.copy();bm=bmesh.new();bm.from_mesh(o.data);w=o.matrix_world;inv=w.inverted();p=inv@Vector([0,5.55,0]);normal=(w.to_3x3().transposed()@Vector([0,1,0])).normalized();bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=normal,clear_inner=True,clear_outer=False,dist=1e-6);bm.to_mesh(o.data);bm.free()
  # Camera clipping includes upper walls but no invented geometry; markers added later on image.
 s.render.resolution_x=1800;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.filepath=str(OUT/'renders/raw'/('LEISURE_OPTION_'+option+'_'+c['id']+'.png'));t=time.monotonic();bpy.ops.render.render(write_still=True);seconds=round(time.monotonic()-t,2);results.append(dict(option=option,view=c['id'],raw=s.render.filepath,camera=c,seconds=seconds,cut_render_only=c['cut'],saved_back=False));print('RENDER_DONE '+option+' '+c['id']+' '+str(seconds)+'s',flush=True)
(OUT/'reports'/('OPTION_'+option+'_RENDERS.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print('OPTION_RENDER_PASS '+option)
