import bpy,json,hashlib,runpy,sys,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(OUT));from room_plan import ROOMS
P=json.loads((OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();SRC=Path(P['source_path']);BRANCH=Path(P['working_copy'])
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='state_helpers')
def states():return {n:{k:v for k,v in s.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,s in H['snapshot']().items()}
def render_room(id):
 assert json.loads((OUT/'00_manifest/WHOLE_HOUSE_API_PREFLIGHT.json').read_text())['status']=='PASS';assert sha(SRC)==P['sha256'];room=next(r for r in ROOMS if r['id']==id);dest=OUT/room['folder']
 for p in ['reference','faithful','designer','creative','bonus','contact_sheet','prompts','reports']:(dest/p).mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();before=states()
 def mat(n,c):m=bpy.data.materials.new(n);m.diffuse_color=c;return m
 mats={k:mat('WH_CLAY_'+k,v) for k,v in {'ARCH':(.88,.88,.86,1),'FURN':(.71,.73,.71,1),'FLOOR':(.76,.77,.74,1),'FRAME':(.27,.32,.33,1),'GLASS':(.83,.90,.92,.16)}.items()}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','COL_B11_REVIEW_MARKERS'] for c in o.users_collection):o.hide_render=True;continue
  if o.name.endswith('XY_ONLY_HELPER'):o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,m in enumerate(list(o.data.materials)):
   name=o.name.upper();mn=m.name.upper() if m else ''
   if 'GLASS' in mn or 'GLASS' in name:new=mats['GLASS']
   elif 'FRAME' in mn or 'METAL' in mn or any(k in name for k in ['JAMB','RAIL','MULLION','TRACK']):new=mats['FRAME']
   elif name.startswith(('FLOOR_','SITE_GROUND')) or 'UPPER_FLOOR' in name:new=mats['FLOOR']
   elif 'WALL' in mn or 'CEILING' in name or name.startswith(('R3_HOUSE_WALL','V5_CORNER_PATCH','R4_DOOR_WEST','R4_DOOR_COMPLETE','R4_WEST_PARTITION')):new=mats['ARCH']
   else:new=mats['FURN']
   o.data.materials[i]=new
 col=bpy.data.collections.new('WH_'+id+'_CAMERAS');bpy.context.scene.collection.children.link(col);rows=[]
 for cam in room['cameras']:
  d=bpy.data.cameras.new('WH_'+id+'_'+cam['id']);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=cam['pos'];o.rotation_euler=(Vector(cam['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=cam['lens'];d.sensor_width=36;d.clip_start=.025;d.clip_end=100;rows.append(dict(**cam,camera_object=o.name,room=id,reference=str(dest/'reference'/(id+'_'+cam['id']+'_reference.png'))))
 after=states()
 for n,s in before.items():assert after[n]==s,n
 s=bpy.context.scene;s.camera=bpy.data.objects[rows[0]['camera_object']];s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
 branch=dest/'reference'/('R4_'+id+'_REFERENCE.blend');bpy.ops.wm.save_as_mainfile(filepath=str(branch))
 def variance(path):
  image=bpy.data.images.load(path,check_existing=False);pix=image.pixels[:];sample=[float(pix[i]) for i in range(0,len(pix),max(4,(len(pix)//10000)//4*4))];mean=sum(sample)/len(sample);sd=math.sqrt(sum((p-mean)**2 for p in sample)/len(sample));bpy.data.images.remove(image);return sd
 for r in rows:
  s.camera=bpy.data.objects[r['camera_object']];s.render.filepath=r['reference'];bpy.ops.render.render(write_still=True);sd=variance(r['reference']);r['initial_pos']=r['pos'].copy();r['automatic_camera_adjustments']=[]
  if sd<.025:
   original=r['pos'].copy();target=r['target'];candidates=[[original[i]+(target[i]-original[i])*t if i<2 else original[i] for i in range(3)] for t in [.25,.5,.7]]
   candidates.extend([cam['pos'].copy() for cam in room['cameras'] if cam['id']!=r['id']])
   for pos in candidates:
    s.camera.location=pos;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();bpy.ops.render.render(write_still=True);sd=variance(r['reference']);r['automatic_camera_adjustments'].append(dict(pos=pos,pixel_sd=sd,reason='near-uniform wall/occlusion correction; source architecture unchanged'))
    if sd>=.025:r['pos']=pos;break
  r['pixel_sd']=sd;r['reference_camera_QA']='PASS_STRUCTURE_VISIBLE' if sd>=.025 else 'WARNING_NEAR_UNIFORM_FRAME';r['reference_sha256']=sha(r['reference']);r['source_sha256']=P['sha256'];r['architecture_modified']=False
 bpy.ops.wm.save_as_mainfile(filepath=str(branch))
 assert sha(SRC)==P['sha256'];(dest/'reports/CAMERA_REGISTER.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(dest/'reports/REFERENCE_QA.json').write_text(json.dumps(dict(status='PASS_GEOMETRY_AND_SOURCE_LOCK',source=P['source_path'],sha256=P['sha256'],locked_objects=len(before),cycles=False,room=id,camera_count=len(rows)),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(reference='PASS',room=id,cameras=len(rows)),ensure_ascii=False))
if __name__=='__main__':render_room(sys.argv[sys.argv.index('--')+1])
