import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];BASE=ROOT/'design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2.blend';BASE_MANIFEST=ROOT/'design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_MANIFEST.json'
ROOM={'x0':9.05,'y0':4.65,'x1':11.30,'y1':6.30,'z0':.45,'z1':3.25};OPEN={'x0':10.10,'x1':10.95,'z0':.45,'z1':2.55,'south_y':4.45};FIXTURES={'basin':[9.4195,4.7501,10.4195,5.2501],'wc':[9.6934,5.7707,10.1934,6.3707],'wet':[10.4738,4.7499,11.297,6.297]};OPTIONS={'A':{'name':'OPTION_A_SLIDING','file':OUT/'OPTION_A_SLIDING.blend','title':'南侧推拉门'},'B':{'name':'OPTION_B_INWARD_SWING','file':OUT/'OPTION_B_INWARD_SWING.blend','title':'南侧内开平开门'}}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def snapshot():return {o.name:(o.type,list(o.location),list(o.rotation_euler),list(o.scale),o.hide_render,o.hide_viewport) for o in bpy.data.objects}
def material(name,color):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.6;return m
def box(name,lo,hi,mat,col):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)]);o=bpy.context.object;o.name=name;o.dimensions=[hi[i]-lo[i] for i in range(3)];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat);o.color=mat.diffuse_color;o['secondary_bath_option']=True;o['review_status']='HUMAN_REVIEW';return o
def collection(name):c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);return c
def overlaps(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
def make_partition(opt,col,wall,frame,panel):
 box('OPTION_'+opt+'_SOUTH_WALL_LEFT',[ROOM['x0'],OPEN['south_y'],ROOM['z0']],[OPEN['x0'],ROOM['y0'],ROOM['z1']],wall,col);box('OPTION_'+opt+'_SOUTH_WALL_RIGHT',[OPEN['x1'],OPEN['south_y'],ROOM['z0']],[ROOM['x1'],ROOM['y0'],ROOM['z1']],wall,col);box('OPTION_'+opt+'_SOUTH_WALL_HEADER',[OPEN['x0'],OPEN['south_y'],OPEN['z1']],[OPEN['x1'],ROOM['y0'],ROOM['z1']],wall,col)
 for tag,lo,hi in [('CASING_L',[OPEN['x0']-.05,OPEN['south_y']-.01,ROOM['z0']-.01],[OPEN['x0'],ROOM['y0']+.01,OPEN['z1']+.075]),('CASING_R',[OPEN['x1'],OPEN['south_y']-.01,ROOM['z0']-.01],[OPEN['x1']+.05,ROOM['y0']+.01,OPEN['z1']+.075]),('CASING_TOP',[OPEN['x0']-.05,OPEN['south_y']-.01,OPEN['z1']],[OPEN['x1']+.05,ROOM['y0']+.01,OPEN['z1']+.075])]:box('OPTION_'+opt+'_'+tag,lo,hi,frame,col)
 if opt=='A':
  leaf=box('OPTION_A_SLIDING_LEAF',[9.20,4.34,.45],[10.05,4.39,2.55],panel,col);track=box('OPTION_A_SLIDING_TOP_TRACK',[10.10,4.36,2.58],[10.95,4.42,2.64],frame,col);box('OPTION_A_SLIDING_STOP',[9.15,4.34,.45],[9.20,4.39,2.55],frame,col);return {'type':'SLIDING','leaf_bounds':[[9.20,4.34,.45],[10.05,4.39,2.55]],'parking':[9.20,10.05,4.34,4.39],'track_bounds':[[10.10,4.36,2.58],[10.95,4.42,2.64]],'clearance_conflict':False}
 leaf=box('OPTION_B_INWARD_LEAF',[10.925,4.45,.45],[10.975,5.30,2.55],panel,col);box('OPTION_B_HINGE_SIDE',[10.915,4.44,.45],[10.985,4.49,2.55],frame,col);sweep=[10.925,4.45,10.975,5.30];conflict=any(overlaps(sweep,v) for v in FIXTURES.values());return {'type':'INWARD_HINGED','leaf_bounds':[[10.925,4.45,.45],[10.975,5.30,2.55]],'hinge':[10.95,4.45,.45],'sweep':sweep,'clearance_conflict':conflict,'conflicting_fixtures':[k for k,v in FIXTURES.items() if overlaps(sweep,v)]}
def add_cameras(col,opt):
 views=[('ENTRY','南侧入口',[10.55,3.2,1.6],[10.55,5.55,1.55],28),('INTERIOR','卫生间内部',[9.25,5.45,1.5],[10.45,5.2,1.45],26)];out=[]
 for id,name,pos,target,lens in views:
  data=bpy.data.cameras.new(f'{opt}_{id}_CAM');o=bpy.data.objects.new(data.name,data);col.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;out.append({'id':id,'name':name,'camera':o.name,'pos':pos,'target':target,'lens':lens})
 data=bpy.data.cameras.new(f'{opt}_TOP_CAM');o=bpy.data.objects.new(data.name,data);col.objects.link(o);o.location=(10.2,5.45,8);o.rotation_euler=(Vector((10.2,5.45,.45))-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=3.2;out.append({'id':'TOP','name':'洁具与门型俯视','camera':o.name,'pos':[10.2,5.45,8],'target':[10.2,5.45,.45],'projection':'ORTHO','scale':3.2});return out
def build(opt):
 base_hash=json.loads(BASE_MANIFEST.read_text())['model_sha256'];assert sha(BASE)==base_hash;assert not OPTIONS[opt]['file'].exists();bpy.ops.wm.open_mainfile(filepath=str(BASE));before=snapshot();col=collection(f'SECONDARY_BATH_{opt}');wall=material('OPTION_WALL',(.84,.85,.83));frame=material('OPTION_FRAME',(.48,.42,.31));panel=material('OPTION_DOOR_PANEL',(.34,.37,.40));root=bpy.data.objects.new(f'{OPTIONS[opt]["name"]}_ROOT',None);col.objects.link(root);root['base_sha256']=base_hash;root['black_wall_policy']='PRESERVE';root['white_wall_policy']='OPTION_ONLY';door=make_partition(opt,col,wall,frame,panel);box('OPTION_'+opt+'_FLOOR',[ROOM['x0'],ROOM['y0'],ROOM['z0']],[ROOM['x1'],ROOM['y1'],ROOM['z0']+.035],material('OPTION_FLOOR',(.58,.58,.54)),col);views=add_cameras(col,opt);bpy.context.scene.camera=bpy.data.objects[views[0]['camera']];bpy.context.scene['secondary_bath_option']=opt;bpy.context.scene['base_geometry_frozen']=True;after=snapshot()
 for n,s in before.items():assert after[n]==s,n
 bpy.ops.wm.save_as_mainfile(filepath=str(OPTIONS[opt]['file']));manifest={'status':'HUMAN_REVIEW','option':opt,'title':OPTIONS[opt]['title'],'model':str(OPTIONS[opt]['file']),'model_sha256':sha(OPTIONS[opt]['file']),'base_model':str(BASE),'base_sha256':base_hash,'room_bounds_mm':[9050,4650,11300,6300],'south_door_width_mm':850,'south_door_head_mm':2550,'shared_fixture_bounds':FIXTURES,'door':door,'views':views,'base_source_unchanged':True,'black_walls_changed':0,'white_wall_option_partition':True,'site_measurements_required':['southern corridor width','actual wall thickness','door parking/hinge clearance','drain and sanitary SKU']};write(f'OPTION_{opt}_MANIFEST.json',manifest);print(json.dumps({'build':'PASS','option':opt,'model':str(OPTIONS[opt]['file']),'door':door},ensure_ascii=False))
def verify(opt):
 m=json.loads((OUT/f'OPTION_{opt}_MANIFEST.json').read_text());assert sha(m['model'])==m['model_sha256'];assert sha(BASE)==m['base_sha256'];bpy.ops.wm.open_mainfile(filepath=m['model']);assert bpy.context.scene['base_geometry_frozen'];print(json.dumps({'verify':'PASS','option':opt,'fresh_open_objects':len(bpy.data.objects),'base_sha_match':sha(BASE)==m['base_sha256'],'clearance_conflict':m['door'].get('clearance_conflict')},ensure_ascii=False))
def render(opt):
 m=json.loads((OUT/f'OPTION_{opt}_MANIFEST.json').read_text());bpy.ops.wm.open_mainfile(filepath=m['model']);out=OUT/'renders';out.mkdir(exist_ok=True);rows=[]
 for v in m['views']:
  s=bpy.context.scene;s.camera=bpy.data.objects[v['camera']];s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';s.world.color=(.90,.92,.94);s.display.render_aa='32';s.view_settings.view_transform='Standard';s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
  for o in bpy.data.objects:
   if o.type=='MESH':
    keep=any(c.name==f'SECONDARY_BATH_{opt}' for c in o.users_collection) or any(k in o.name for k in ['B11_Rectangle036','B11_Rectangle037','B11_Rectangle038'])
    if not keep:o.hide_render=True
  path=out/f'OPTION_{opt}_{v["id"]}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'option':opt,'view':v['id'],'path':str(path),'sha256':sha(path),'resolution':[1600,1200],'source_saved':False,'local_review_view':True})
 write(f'OPTION_{opt}_RENDER_MANIFEST.json',rows);print(json.dumps({'render':'PASS','option':opt,'views':3,'images':'FILESYSTEM_ONLY'}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','verify','render']);p.add_argument('option',choices=['A','B']);a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];args=p.parse_args(a);{'build':build,'verify':verify,'render':render}[args.mode](args.option)
