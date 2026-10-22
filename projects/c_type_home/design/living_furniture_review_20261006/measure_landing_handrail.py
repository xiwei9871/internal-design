import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
r=Path(__file__).parent
source=r/'OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='78d64077368b1a4952f44ed4877464e0cde51ffceeee40b2ae40727ebfc85d30'
bpy.ops.wm.open_mainfile(filepath=str(source))
names=['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','VIEW_WALL_W_wall_md_0044','VIEW_WALL_V4_D-GUEST-BATH_COMPLETE_HOST_WALL','VIEW_WALL_W_wall_md_0051','STEP_0','STEP_1','STEP_2','WAVE_STEP_3_ARRIVAL']
names+=['V4_D-GUEST-BATH_CASING_A_FRONT','V4_D-GUEST-BATH_CASING_B_FRONT','V4_D-GUEST-BATH_LEAF_0','V4_D-GUEST-BATH_HANDLE_LEVER']
index=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
for part in index['parts']:
 lo,hi=part['world_bounds']
 if hi[0]>=6.5 and lo[0]<=10.0 and hi[1]>=4.7 and lo[1]<=8.01 and lo[2]<2.5:
  if part['native_id'] not in names:names.append(part['native_id'])
rows=[]
for n in names:
 o=bpy.data.objects.get(n)
 if o is None:continue
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 faces=[[list(pts[i]) for i in p.vertices] for p in o.data.polygons]
 rows.append({'name':n,'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'faces':faces})
(r/'LANDING_WALL_LOCAL_GEOMETRY.json').write_text(json.dumps(rows,indent=2))
print(json.dumps([{k:v for k,v in row.items() if k!='faces'} for row in rows]))
