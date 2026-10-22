# blender -b V15_WORK_STEP_FIX_CANDIDATE.blend -P step_wave_p0_fix_floor.py -- <out_dir>
# P0.1: FLOOR_LOWER 错层交界旧弧边界 → 顶点吸附到 STEP_0 确认西缘.
# 顶点级编辑(不动拓扑): 窗口内每个越过曲线西侧的顶点(任意z)吸附到曲线;
# 西壁边界点(退缩段)反向拉到曲线. 仅动 FLOOR_LOWER; 原网格先备份 JSON.
import bpy, bmesh, json, sys, collections
from mathutils import Vector

argv = sys.argv[sys.argv.index('--')+1:]
OUT = argv[0] if argv else '/tmp'

FL = bpy.data.objects['FLOOR_LOWER']; ST = bpy.data.objects['STEP_0']
flmw = FL.matrix_world; stmw = ST.matrix_world
me = FL.data

# ---------- 1) 原网格备份 ----------
backup = {'verts':[list(v.co) for v in me.vertices],
          'polygons':[list(p.vertices) for p in me.polygons],
          'matrix_world':[list(r) for r in flmw]}
json.dump(backup, open(OUT+'/floor_lower_orig_backup.json','w'))

# ---------- 2) STEP_0 西缘曲线 ----------
zst = max((stmw@v.co).z for v in ST.data.vertices)
bk = collections.defaultdict(list)
for v in ST.data.vertices:
    w = stmw@v.co
    if abs(w.z-zst)<0.01 and 4.6<=w.y<=8.15: bk[round(w.y/0.02)*0.02].append(w.x)
step_curve = sorted([(min(xs),y) for y,xs in bk.items()], key=lambda t:t[1])
print('step west edge pts:', len(step_curve), step_curve[0], step_curve[-1])
def xstep(y):
    if y<=step_curve[0][1]: return step_curve[0][0]
    if y>=step_curve[-1][1]: return step_curve[-1][0]
    for i in range(len(step_curve)-1):
        (x0,y0),(x1,y1)=step_curve[i],step_curve[i+1]
        if y0<=y<=y1:
            return x0+(x1-x0)*(y-y0)/(y1-y0)

# ---------- 3) 修复前西缘采样(顶面最西顶点/50mm) ----------
def west_edge_sample():
    t=collections.defaultdict(list)
    for v in me.vertices:
        w=flmw@v.co
        if abs(w.z)<0.005 and 4.5<=w.y<=8.05 and 5.3<=w.x<=7.5:
            t[round(w.y/0.05)*0.05].append(w.x)
    return {y:min(xs) for y,xs in t.items()}
orig_edge = west_edge_sample()

# ---------- 4) 顶点吸附 ----------
# 西壁边界点 = 关联到 world -x 法向面片的点(退缩段拉回用)
bm = bmesh.new(); bm.from_mesh(me)
nmat = flmw.to_3x3()
west_verts=set()
for f in bm.faces:
    n=(nmat @ f.normal).normalized()
    if n.x < -0.5:
        for v in f.verts:
            w=flmw@v.co
            if 4.5<=w.y<=8.05 and 5.3<=w.x<=7.5: west_verts.add(v.index)
moved_west=0; moved_snap=0; moved=[]
for v in me.vertices:
    w=flmw@v.co
    if not (4.55<=w.y<=8.05 and 5.3<=w.x<=7.5): continue
    tgt=xstep(w.y); nx=None
    if w.x < tgt-0.001: nx=tgt; moved_snap+=1          # 凸出: 东移
    elif v.index in west_verts and w.x > tgt+0.001: nx=tgt; moved_west+=1  # 退缩: 西拉
    if nx is not None:
        nw=Vector((nx,w.y,w.z)); v.co = flmw.inverted() @ nw
        moved.append((round(w.x,3),round(nx,3),round(w.y,3),round(w.z,3)))
me.update(); bm.free()
print(f'moved protrusion={moved_snap} recession={moved_west} total={len(moved)}')

# ---------- 5) 清理退化面 ----------
bm = bmesh.new(); bm.from_mesh(me)
degen=[f for f in bm.faces if f.calc_area()<1e-9]
if degen: bmesh.ops.delete(bm, geom=degen, context='FACES_ONLY')
bm.to_mesh(me); me.update()
nonman=sum(1 for e in bm.edges if not e.is_manifold)
dg=len(degen); bm.free()
mesh_valid = me.validate(verbose=False, clean_customdata=False)
new_edge = west_edge_sample()

# ---------- 6) 差异报告 ----------
diffs=[]
for y,fx in sorted(new_edge.items()):
    if y in orig_edge: diffs.append((y, orig_edge[y], fx, (orig_edge[y]-fx)*1000))
ymax=max(diffs,key=lambda t:abs(t[3])) if diffs else None
area_mm2=sum(abs(o-f)*50*1e6 for _,o,f,_ in diffs)/1e6  # 50mm带宽×|Δx|
report={'moved_protrusion':moved_snap,'moved_recession':moved_west,
        'degenerate_removed':dg,'nonmanifold':nonman,'validate_errors':mesh_valid,
        'verts':len(me.vertices),'faces':len(me.polygons),
        'max_deviation_mm':round(ymax[3],1) if ymax else 0,
        'max_dev_at_y':ymax[0] if ymax else None,
        'affected_area_mm2':round(area_mm2),
        'edge_samples':[(y,round(o,3),round(f,3),round(d,1)) for y,o,f,d in diffs]}
json.dump(report, open(OUT+'/floor_fix_report.json','w'), indent=1)
json.dump({'moved':moved}, open(OUT+'/floor_moved_verts.json','w'))
print(json.dumps(report,indent=1))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('saved candidate:', bpy.data.filepath)
