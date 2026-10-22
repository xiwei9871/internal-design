"""Import owner-generated whole furniture, preserve shape/UV and source house."""
import bpy,json,hashlib,math,struct,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';reg=json.loads((D/'IMPORT_REGISTER.json').read_text());S=R/'design/whole_house_model_v2/WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend';O=D/'WHOLE_HOUSE_HUNYUAN_CANDIDATE_V3.blend'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='5a8bf58aaea0978147db40e1c7c68d57c27be6f9b254c9a6191ca7ef32c11801'
if O.exists():raise SystemExit('Preserved candidate exists')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;col=bpy.data.collections.new('OWNER_HUNYUAN_WHOLE_ASSETS_V3');s.collection.children.link(col)
def hashmesh(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
initial={o.name:{'type':o.type,'geometry':hashmesh(o.data) if o.type=='MESH' else None,'matrix':[list(row) for row in o.matrix_world],'hide_render':o.hide_render} for o in s.objects};hidden=[];records=[]
def hide(n):
 o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True;o.hide_set(True);hidden.append(n)
for o in list(s.objects):
 n=o.name
 if n.startswith('HOUSE_V2_COUPLE_') and not n.startswith(('HOUSE_V2_COUPLE_0_','HOUSE_V2_COUPLE_1_')):hide(n)
 if n.startswith(('V4_Sofa_','HOUSE_V1_SOFA_')) or n=='CBM_COUPLE_CONSOLE_TOP' or n.startswith(('CBM_COUPLE_CONSOLE_DRAWER','CBM_COUPLE_CONSOLE_PEDESTAL','CBM_COUPLE_CONSOLE_PORTAL','CBM_CONSOLE_')):hide(n)
def imported(index,role,scale_axis,target_size,rotation,center,floor,mirror=False):
 info=reg['assets'][index];path=Path(info['copy']);assert hashlib.sha256(path.read_bytes()).hexdigest()==info['sha256'];before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));objects=[o for o in bpy.data.objects if o not in before];meshes=[o for o in objects if o.type=='MESH'];assert len(meshes)==1
 o=meshes[0];world=o.matrix_world.copy();o.data=o.data.copy();o.data.transform(world);o.matrix_world=Matrix.Identity(4);o.parent=None;lo=[min(v.co[i] for v in o.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in o.data.vertices) for i in range(3)];dims=[hi[i]-lo[i] for i in range(3)];scale=target_size/dims[scale_axis];normal=Matrix.Rotation(rotation,4,'Z')@Matrix.Diagonal(((-1 if mirror else 1)*scale,scale,scale,1))
 for v in o.data.vertices:v.co=normal@Vector((v.co.x-(lo[0]+hi[0])/2,v.co.y-(lo[1]+hi[1])/2,v.co.z-lo[2]))+Vector((center[0],center[1],floor))
 if mirror:o.data.flip_normals()
 o.data.update();o.name='HUNYUAN_V3_'+role
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 for m in o.data.materials:m.name='HUNYUAN_V3_'+role+'_PBR';m['source']='owner generated, embedded textures retained; not scanned/specimen calibration'
 for other in objects:
  if other!=o and other.type=='EMPTY':bpy.data.objects.remove(other,do_unlink=True)
 outlo=[min(v.co[i] for v in o.data.vertices) for i in range(3)];outhi=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
 o['source_glb_sha256']=info['sha256'];o['uniform_scale']=scale;o['scale_reference']=f'owner-house target {target_size}m axis{scale_axis}; AI units not product specs';o['whole_horizontal_mirror']=mirror
 rec={'object':o.name,'role':role,'source_glb':str(path),'source_sha256':info['sha256'],'input_dims_m':dims,'uniform_scale':scale,'rotation_z_degrees':rotation*180/math.pi,'whole_mirror':mirror,'output_bounds_m':[outlo,outhi],'output_dims_m':[outhi[i]-outlo[i] for i in range(3)],'triangles':len(o.data.polygons),'material':o.data.materials[0].name,'uv_layers':len(o.data.uv_layers),'new_geometry_hash':hashmesh(o.data)};records.append(rec);return o
# Bed full width1930, uniform preserves generated depth/height; catalog2090
# length is fit reference, cannot silently stretch mesh independently.
bed=imported(0,'COUPLE_BED',0,1.93,-math.pi/2,(10.22,2.087),.45)
# Whole mirroredL retains source south chaise and continuous one-product form.
sofa=imported(2,'LIVING_L_SOFA',0,3.30,math.pi/2,(4.199,9.60),0,True)
# Console source aspect2m yields~532deep, source reserve400deep. Wall-side
# begins8.02; report interior projection+~132mm, no architecture movement.
console=imported(1,'COUPLE_TV_CONSOLE',0,2.0,math.pi/2,(8.02+(.309116/1.162776*2)/2,2.087),.45)
def camera(n,eye,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01
camera('HUNYUAN_V3_BED_REVERSE',(9.20,3.85,1.92),(10.23,2.08,1.05),30)
camera('HUNYUAN_V3_CONSOLE',(10.01,3.48,1.69),(8.30,2.15,1.03),32)
camera('HUNYUAN_V3_SOFA_WHOLE',(6.26,8.58,1.64),(4.23,9.75,.49),32)
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and Path(bpy.path.abspath(im.filepath)).exists():im.pack()
s.camera=bpy.data.objects['CAM_couple_bedroom_VIEW_01'];s['hunyuan_assets_v3']='whole owner-generated bed,sofa,console; shape aspect preserved; not measured SKU';bpy.ops.wm.save_as_mainfile(filepath=str(O))
report={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output':str(O),'output_sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'original_states':initial,'hidden_replaced':hidden,'assets':records,'guest_room':'unchanged V2, entry collision unresolved by owner instruction','source_writeback':False,'image2_requests':0,'license':'owner-supplied for project use; no public asset redistribution inferred','warnings':['texture colors/roughness are generated not measured','TVconsole includes supplied decorative objects','uniformscale dimensions differ from catalog; do not procure from these dimensions','Hunyuan mesh boundaries may include UVseams; hiddenfaces not real manufacturing evidence']}
(D/'BUILD_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('HUNYUAN_HOUSE_CANDIDATE',report['output_sha256'],[{k:r[k] for k in ['role','uniform_scale','output_dims_m']} for r in records])
