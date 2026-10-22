import bpy,json
from pathlib import Path
from mathutils import Vector
src='/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006/OPTION_A_R4_LIVING_WAVE35_ALUMINUM_REVIEW.blend'
bpy.ops.wm.open_mainfile(filepath=src)
def bbox(o):
    c=[o.matrix_world@Vector(p) for p in o.bound_box];return [min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]
def overlap(a,b):return all(min(a[1][i],b[1][i])-max(a[0][i],b[0][i])>1e-6 for i in range(3))
steps=['STEP_0','STEP_1','STEP_2','WAVE_STEP_3_ARRIVAL'];step_rows=[]
for n in steps:
    o=bpy.data.objects[n];lo,hi=bbox(o);step_rows.append({'name':n,'min':lo,'max':hi,'run_x':hi[0]-lo[0],'height':hi[2]-lo[2]})
walls=['VIEW_WALL_LIVING_FIX_GUEST_BATH_FULL_WALL','VIEW_WALL_LIVING_FIX_GUEST_BATH_NORTH_JUNCTION'];wall_rows=[]
for n in walls:
    if bpy.data.objects.get(n):wall_rows.append({'name':n,'bounds':bbox(bpy.data.objects[n]),'step_collisions':[s['name'] for s in step_rows if overlap((s['min'],s['max']),bbox(bpy.data.objects[n]))]})
report={'status':'HUMAN_REVIEW','steps':step_rows,'wall_collision_audit':wall_rows,'frame_objects':[n.name for n in bpy.data.objects if n.name.startswith('NORTH_BALCONY_FRAME_')],'glass_objects':[n.name for n in bpy.data.objects if n.name.startswith('NORTH_BALCONY_GLASS_')]}
Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006/WAVE35_ALUMINUM_GEOMETRY_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
