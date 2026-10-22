"""Bounded user-authorized furniture successor and full interaction export."""
import bpy,json,hashlib,struct,uuid,sys,math
from pathlib import Path
from argparse import Namespace
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];R=ROOT/"design/sunroom_stepped_storage_v1";OLD=ROOT/"design/console_bath_mirrors_review";OUT=R/"proxy_full";OUT.mkdir(parents=True,exist_ok=True)
REV="sunroom-stepped-storage-review-1";DEST=R/"SUNROOM_STEPPED_STORAGE_V1.blend"
assert not DEST.exists(),"Never overwrite a previous candidate"
reg=json.loads((OLD/"spatial-canvas.bindings.full.json").read_text());SRC=Path(reg["source_locator"])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
truths=json.loads((ROOT/"renders/whole_house_final_study_v1/production_batch_v1/00_MANIFEST/AUTHORITY_HASH_CHECK.json").read_text())
assert all(sha(a["path"])==a["sha256"] for a in truths)
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
def state(o):
 h=hashlib.sha256()
 if o.type=="MESH":
  for v in o.data.vertices:h.update(struct.pack("<fff",*v.co))
  for p in o.data.polygons:h.update(struct.pack("<"+"I"*len(p.vertices),*p.vertices))
 return [h.hexdigest(),[float(x) for row in o.matrix_world for x in row],o.hide_render,o.hide_viewport,o.hide_get(),[m.name if m else None for m in o.data.materials] if o.type=="MESH" else []]
before={o.name:state(o) for o in bpy.context.scene.objects}
names=["SUNROOM_SOFA_REAR_HIGH_CABINET","SUNROOM_INTEGRATED_UNDERSIDE"]+["SUNROOM_INTEGRATED_UPPER_DOOR_"+str(i) for i in [2,3,4]]+["SUNROOM_INTEGRATED_UPPER_PULL_"+str(i) for i in [2,3,4]]
print("BEFORE_SELECTED",json.dumps([{n:before[n]} for n in names]))
retired=["SUNROOM_INTEGRATED_UPPER_PULL_"+str(i) for i in [2,3,4]]
for n in retired:o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
col=bpy.data.collections.new("COL_SUNROOM_STEPPED_REVIEW");bpy.context.scene.collection.children.link(col)
wood=bpy.data.materials.new("STEPPED_PALE_ASH");wood.diffuse_color=(.69,.56,.40,1);wood.use_nodes=True;wood.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=wood.diffuse_color
new=[];changed=set(names)
def box(n,a,b):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)]);o=bpy.context.object;o.name=n;o.scale=[b[i]-a[i] for i in range(3)];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(wood)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);return o
def joined(n,parts,existing=False):
 bpy.ops.object.select_all(action="DESELECT")
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object
 if existing:
  dst=bpy.data.objects[n];dst.data=tmp.data.copy();dst.matrix_world=tmp.matrix_world.copy();bpy.data.objects.remove(tmp,do_unlink=True);return dst
 tmp.name=n;tmp["authority"]="DERIVED_DESIGN_MODEL";new.append(tmp);return tmp
x0,x1=8.765,10.32;y0=11.135;t=.018;back=.012;inside=(x1-x0-4*t)/3
# Uppercase below is actual hard bottom2100; no trimprojects below it.
parts=[box("tmp_upper_bottom",(x0,y0,2.1),(x1,y0+.6,2.118)),box("tmp_upper_top",(x0,y0,2.582),(x1,y0+.6,2.6)),box("tmp_upper_back",(x0+t,y0,2.118),(x1-t,y0+back,2.582))]
for x in [x0,x1-t]:parts.append(box("tmp_upper_side",(x,y0,2.118),(x+t,y0+.6,2.582)))
for i in [1,2]:
 x=x0+t+i*inside+(i-1)*t;parts.append(box("tmp_upper_divider",(x,y0+back,2.118),(x+t,y0+.6,2.582)))
joined("SUNROOM_SOFA_REAR_HIGH_CABINET",parts,True)
# Shallow open underside bottom starts1800, preserves legacy ID.
o=box("tmp_open_base",(x0,y0,1.8),(x1,y0+.35,1.818));joined("SUNROOM_INTEGRATED_UNDERSIDE",[o],True)
parts=[box("tmp_open_top",(x0,y0,2.082),(x1,y0+.35,2.1)),box("tmp_open_back",(x0+t,y0,1.818),(x1-t,y0+back,2.082))]
for x in [x0,x1-t]:parts.append(box("tmp_open_side",(x,y0,1.818),(x+t,y0+.35,2.082)))
for i in [1,2]:
 x=x0+t+i*inside+(i-1)*t;parts.append(box("tmp_open_divider",(x,y0+back,1.818),(x+t,y0+.35,2.082)))
joined("SUNROOM_STEPPED_OPEN_CARCASS",parts)
for i in range(3):
 a=x0+i*(x1-x0)/3+.003;b=x0+(i+1)*(x1-x0)/3-.003
 joined("SUNROOM_INTEGRATED_UPPER_DOOR_"+str(i+2),[box("tmp_door",(a,y0+.600,2.103),(b,y0+.618,2.597))],True)
 # Recessedunderside grip represented bythinnotchcolorededge inside door bottom, noprojectinghandle.
 o=box("SUNROOM_STEPPED_RECESSED_GRIP_"+str(i),(a+.07,y0+.603,2.103),(b-.07,y0+.615,2.109));new.append(o)
bpy.context.view_layer.update()
unrelated=[n for n,s in before.items() if n not in changed and state(bpy.data.objects[n])!=s];assert not unrelated,unrelated
assert all(sha(a["path"])==a["sha256"] for a in truths)
reg["bindings"]=[b for b in reg["bindings"] if b["native_id"] not in retired]
for o in new:reg["bindings"].append({"entity_id":"ent_"+uuid.uuid5(uuid.NAMESPACE_URL,"c_type_home:steppedstorage:"+o.name).hex,"adapter":"blender","native_id":o.name,"semantic_type":"cabinet" if "CARCASS" in o.name else "cabinet_handle","room_id":"unassigned","authority_level":"HUMAN_DESIGN_GUIDE"})
reg.update(registry_revision=REV,source_resource_id="c_type_sunroom_stepped",source_revision=REV,source_locator=str(DEST))
bpy.ops.wm.save_as_mainfile(filepath=str(DEST));reg["source_sha256"]=sha(DEST);(R/"spatial-canvas.bindings.full.json").write_text(json.dumps(reg,ensure_ascii=False,indent=2))
def bounds(n):
 o=bpy.data.objects[n];vs=[o.matrix_world@v.co for v in o.data.vertices];return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
a,b=bounds("SUNROOM_SOFA_REAR_HIGH_CABINET");assert abs(a[2]-2.1)<1e-5 and abs(b[2]-2.6)<1e-5 and abs(b[1]-a[1]-.6)<1e-5
la,lb=bounds("SUNROOM_INTEGRATED_UNDERSIDE");assert abs(la[2]-1.8)<1e-5 and abs(lb[1]-la[1]-.35)<1e-5
report={"status":"HUMAN_REVIEW","source_sha256":sha(SRC),"candidate_sha256":sha(DEST),"source":str(SRC),"candidate":str(DEST),"changed_native_ids":sorted(changed),"retired_native_ids":retired,"new_native_ids":[o.name for o in new],"unrelated_geometry_unchanged":True,"frozen_hashes_unchanged":True,"lower_external_mm":[1555,350,300],"lower_bay_clear_mm":[inside*1000,338,264],"upper_external_mm":[1555,600,500],"upper_bay_clear_mm":[inside*1000,588,464],"lowest_hard_edges_mm":[1800,2100],"doorfront_depth_mm":618,"user_height_mm":1750,"static_verticaldifference_mm":50,"dynamic_head_clearance_verified":False,"dooropening_review":"threehingedfronts, actualhardware/open motion pending; nohead-safe assertion","no_source_writeback":True}
(R/"MODEL_REVIEW.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Exact unchanged exportadapter; zoningflat with sourceflat furniture, transparentbalconyglass.
sys.path.insert(0,"/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/adapters/blender");import export_proxy
ordinary=export_proxy.assign_flat_colors
def presentation(mesh,entity,cache,owned,counts,mode,source):
 n=entity["native_object_id"]
 if n.startswith(("SUNROOM_","STUDY_","BW1_","CBM_","READING_","WAVE_","STEP_","B11_Rectangle039","B11_Rectangle040")):return ordinary(mesh,entity,cache,owned,counts,"source-flat",source)
 if n.startswith("NORTH_BALCONY_GLASS_"):
  key="balconyglass"
  if key not in cache:
   m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(.45,.70,.78,.32);p=m.node_tree.nodes.get("Principled BSDF");p.inputs["Base Color"].default_value=m.diffuse_color;p.inputs["Alpha"].default_value=.32;m.surface_render_method="DITHERED";cache[key]=m;owned.append(m)
  mesh.materials.clear();mesh.materials.append(cache[key])
  for f in mesh.polygons:f.material_index=0
  counts[key]=counts.get(key,0)+1;return
 return ordinary(mesh,entity,cache,owned,counts,mode,source)
export_proxy.assign_flat_colors=presentation
m=export_proxy.export_proxy(Namespace(output=str(OUT),bindings=str(R/"spatial-canvas.bindings.full.json"),scope="full",room_id=None,global_ids=None,collection=None,color_mode="zoning-flat",source_resource_id=reg["source_resource_id"],source_revision=REV))
m["extensions"]["spatial_canvas.review"]={"status":"HUMAN_REVIEW","source_design_authority":"DERIVED_DESIGN_MODEL","lower_open_mm":[1800,2100,350],"upper_closed_mm":[2100,2600,600],"dynamic_head_clearance_verified":False}
(OUT/"interaction_proxy.manifest.json").write_text(json.dumps(m,indent=2))
old=json.loads((OLD/"proxy_full/interaction_proxy.manifest.json").read_text());repl={old[k]:m[k] for k in ["source_resource_id","resource_id","source_revision","source_sha256","source_resource"]}
def relink(v):
 if isinstance(v,str):return repl.get(v,v)
 if isinstance(v,list):return [relink(x) for x in v]
 if isinstance(v,dict):return {k:relink(x) for k,x in v.items()}
 return v
for name in ["spatial-canvas.project.json","spatial-canvas.spaces.json","spatial-canvas.relationships.json"]:
 data=relink(json.loads((OLD/"proxy_full"/name).read_text()))
 if name.endswith("relationships.json"):
  known={b["entity_id"]:b for b in reg["bindings"]};data["nodes"]=[n for n in data["nodes"] if n["kind"]!="entity" or n["node_id"] in known];ids={n["node_id"] for n in data["nodes"]};changedids={b["entity_id"] for b in reg["bindings"] if b["native_id"] in changed}
  data["edges"]=[e for e in data["edges"] if e["from"] in ids and e["to"] in ids and not(e["from"] in changedids or e["to"] in changedids)]
  for gid,b in known.items():
   if gid not in ids:data["nodes"].append({"node_id":gid,"kind":"entity","name":b["native_id"],"native_id":b["native_id"],"resource_id":m["source_resource_id"],"revision":REV,"sha256":m["source_sha256"]})
  for src in data["sources"]:
   if src["resource_id"]=="spaces_c_type_r4":src.update(sha256=sha(OUT/"spatial-canvas.spaces.json"),locator=str(OUT/"spatial-canvas.spaces.json"))
 (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
eye=(11.55,12.93,1.6);target=(9.42,11.43,1.65);q=(Vector(target)-Vector(eye)).to_track_quat("-Z","Y");pq=Quaternion((2**-.5,-2**-.5,0,0))@q
preset=json.loads((OLD/"proxy_full/guest.view-preset.json").read_text());preset=relink(preset);preset.update(preset_id="north_stepped_storage_review",position=[eye[0],eye[2],-eye[1]],quaternion=[pq.x,pq.y,pq.z,pq.w],orbit_target=[target[0],target[2],-target[1]],fov_degrees=58,source_camera={"position":eye,"quaternion":[q.x,q.y,q.z,q.w],"frame_id":"c_type_world","unit":"meter","up_axis":"Z"},bindings=m["extensions"]["spatial_canvas.blender"]["bindings"]);preset.pop("preview_uri",None);(OUT/"north.view-preset.json").write_text(json.dumps(preset,indent=2))
# Freshglbimport gate, thenreload candidate for lowcostdecision views.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/"interaction_proxy.glb"));entities={o.get("native_object_id"):o for o in bpy.context.scene.objects if o.get("global_id")};assert len(entities)==len(reg["bindings"]);assert all(entities[b["native_id"]]["global_id"]==b["entity_id"] for b in reg["bindings"]);assert not set(retired)&set(entities)
(OUT/"EXPORT_EVIDENCE.json").write_text(json.dumps({"status":"PASS","entities":len(entities),"stable_ids_match":True,"fresh_import":True,"source_unchanged":sha(SRC)==report["source_sha256"]},indent=2))
bpy.ops.wm.open_mainfile(filepath=str(DEST));scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH";scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.display.shading.color_type="MATERIAL";scene.display.shading.light="STUDIO";scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True;scene.render.threads_mode="FIXED";scene.render.threads=2
keep={b["native_id"] for b in reg["bindings"] if b["native_id"].startswith(("SUNROOM_","B11_Rectangle040","B11_Rectangle039","NORTH_BALCONY_"))};keep.add("FLOOR_LOWER")
for o in scene.objects:
 if o.type=="MESH":o.hide_render=o.name not in keep
camdata=bpy.data.cameras.new("CAM_STORAGE_REVIEW");cam=bpy.data.objects.new("CAM_STORAGE_REVIEW",camdata);scene.collection.objects.link(cam);scene.camera=cam
for name,e,tg,lens in [("REVIEW_NORTH",eye,target,25),("REVIEW_SIDE",(10.82,12.25,1.95),(9.15,11.45,1.6),28)]:
 cam.location=e;cam.rotation_euler=(Vector(tg)-Vector(e)).to_track_quat("-Z","Y").to_euler();camdata.lens=lens;scene.render.filepath=str(R/(name+".png"));bpy.ops.render.render(write_still=True)
assert all(sha(a["path"])==a["sha256"] for a in truths)
print("STEPPED_STORAGE_PASS",len(reg["bindings"]),str(DEST))
