import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/"design/secondary_mirror_v15";D.mkdir(exist_ok=True)
S=R/"design/platform_bath_fitness_v14/WHOLE_HOUSE_PLATFORM_BATH_FITNESS_FINAL_V14.blend";O=D/"WHOLE_HOUSE_SECONDARY_MIRROR_V15.blend"
SHA="0ef86d31de4ab8afb4befcb6ac639054c955e970f85bd4007f04dc3252055144"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==SHA and not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
 h=hashlib.sha256()
 if o.type=="MESH":
  for v in o.data.vertices:h.update(struct.pack("<fff",*v.co))
  for f in o.data.polygons:h.update(struct.pack("<"+"I"*len(f.vertices),*f.vertices))
 return h.hexdigest()
before={o.name:{"mesh":mh(o),"matrix":[list(r) for r in o.matrix_world],"render":o.hide_render,"mats":[m.name if m else None for m in o.data.materials] if hasattr(o.data,"materials") else []} for o in bpy.data.objects}
for n in ["CBM_SECONDARY_MIRROR","CBM_SECONDARY_MIRROR_FRAME"]:
 o=bpy.data.objects[n];o.location.x-=.2
hidden=[]
for n in ["CBM_secondary_BOTTLE_0","CBM_secondary_BOTTLE_1","HOUSE_V1_secondary_bath_soap_body","HOUSE_V1_secondary_bath_soap_neck","HOUSE_V1_secondary_bath_towel"]:
 o=bpy.data.objects.get(n)
 if o:o.hide_render=True;o.hide_viewport=True;o.hide_set(True);hidden.append(n)
# The 217mm strip between vanity edge x10.228 and shower west fixed pane x10.444 is a clearance/service gap, not an independent slab. Preserve it; removing it would remove a wall/finish zone without increasing the shower tray.
bpy.context.window.view_layer=s.view_layers["OVERVIEW_CEILING_HIDDEN"];bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={"source":str(S),"source_sha256":SHA,"output":str(O),"sha256":sha(O),"before":before,"mirror_translation_west_mm":200,"moved_objects":["CBM_SECONDARY_MIRROR","CBM_SECONDARY_MIRROR_FRAME"],"upper_storage_unchanged":True,"hidden_accessories":hidden,"vanity_east_x_m":10.228,"shower_west_pane_x_m":10.444,"clearance_strip_mm":216,"clearance_strip_status":"existing service/finish gap; preserved, not an independent object","source_preserved":True,"status":"HUMAN_REVIEW"}
(D/"BUILD_AUDIT.json").write_text(json.dumps(a,indent=2)+"\n")
for f in json.loads((R/"design/whole_house_model_v1/PRESERVATION.json").read_text())["files"]:assert sha(f["path"])==f["sha256"]
print("V15_BUILT",a["sha256"],a["hidden_accessories"])
