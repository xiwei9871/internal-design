"""Owner catalog metric correction; keep rawGLB and uniform import candidates."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_HUNYUAN_METRIC_V3.blend'
if dest.exists():raise SystemExit('Preserved metric candidate exists')
bpy.ops.wm.open_mainfile(filepath=str(src));records=[]
def bounds(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices];return [Vector((min(p[i] for p in vs) for i in range(3))),Vector((max(p[i] for p in vs) for i in range(3)))]
bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];lo,hi=bounds(bed);size=hi-lo;target=Vector((2.13,1.91,1.07));factor=Vector(target[i]/size[i] for i in range(3));head=11.267;cy=2.087;floor=.45
bed.data=bed.data.copy()
for v in bed.data.vertices:
 p=bed.matrix_world@v.co;v.co=Vector((head-2.13+(p.x-lo.x)*factor.x,cy-.955+(p.y-lo.y)*factor.y,floor+(p.z-lo.z)*factor.z))
records.append({'asset':bed.name,'target_l_w_h_mm':[2130,1910,1070],'axis_factors_relative_to_uniform_import':list(factor),'status':'ownerauthorizedcatalog calibration ofgeneratedshape,not manufacturergeometry','catalog':'2011-1.8'})
sofa=bpy.data.objects['HUNYUAN_V3_LIVING_L_SOFA'];lo,hi=bounds(sofa);size=hi-lo;sofa.data=sofa.data.copy()
# Whole source has roughlythree equallywidth bag bays; southchaise one third.
# Piecewise mapping fixescatalog800widechaise+2100widedouble and900depth
# standard module+1450depthchaise without uniformlyflattening all softbags.
long_break=1/3;depth_break=.61;rear=3.404;south=8.0
def piece(t,b,targetbreak):return t/b*targetbreak if t<=b else targetbreak+(t-b)/(1-b)*(1-targetbreak)
for v in sofa.data.vertices:
 p=sofa.matrix_world@v.co;u=(p.y-lo.y)/size.y;depth=(p.x-lo.x)/size.x
 v.co=Vector((rear+1.45*piece(depth,depth_break,.9/1.45),south+2.9*piece(u,long_break,.8/2.9),(p.z-lo.z)/size.z*.9))
records.append({'asset':sofa.name,'target_overall_depth_long_height_mm':[1450,2900,900],'double_module_mm':[2100,900,900],'chaise_depth_width_height_mm':[1450,800,900],'mapping':'catalogboundarypiecewise; sourcebays inferred fromgenerated threebaglayout; internalfoam/jointsnot manufacturerexact','south_chaise_retained':True})
console=bpy.data.objects['HUNYUAN_V3_COUPLE_TV_CONSOLE'];lo,hi=bounds(console);size=hi-lo;scale=1.2/size.y;console.data=console.data.copy()
for v in console.data.vertices:
 p=console.matrix_world@v.co;v.co=Vector((8.02+(p.x-lo.x)*scale,2.087-.6+(p.y-lo.y)*scale,.45+(p.z-lo.z)*scale))
records.append({'asset':console.name,'target_long_mm':1200,'uniform_factor_relative_to_import':scale,'depth_mm':size.x*scale*1000,'total_height_with_decor_mm':size.z*scale*1000,'decor':'ownerGLBincludescatalogprops; not separately chosenproducts'})
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pre_metric_candidate']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['metric_calibration']=records
for rec in a['assets']:
 o=bpy.data.objects[rec['object']];lo,hi=bounds(o);rec['final_bounds_m']=[list(lo),list(hi)];rec['final_dims_m']=list(hi-lo)
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('OWNER_METRIC_V3',a['output_sha256'],[(r['role'],r['final_dims_m']) for r in a['assets']])
