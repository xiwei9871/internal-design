"""Natural wood study: long tea table, bookcase behind it, wet/boiling side counter."""
import bpy,math,json
from mathutils import Vector
def build(h,col,offset_north=0):
 box=h['box'];mat=h['mat'];cylinder=h['cylinder'];empty=h['empty'];bevel=h['bevel'];mesh=h['objmesh']
 wood=mat('R3_STUDY_WOOD',(.47,.335,.235));stone=mat('R3_TEA_WORKTOP',(.22,.25,.245));metal=mat('R3_TEA_METAL',(.12,.15,.15));sinkmat=mat('R3_TEA_SINK',(.42,.49,.48));paper=mat('R3_BOOK_PAPER',(.76,.72,.62));clay=mat('R3_TEA_PORCELAIN',(.73,.68,.57))
 legacy=[];booknames=[];tablenames=[]
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.name.startswith(('B11_Rectangle024','B11_Rectangle026','B11_Rectangle027','B11_Circle008')):
   vs=[list(o.matrix_world@v.co) for v in o.data.vertices]
   if o.name.startswith('B11_Rectangle026'):
    for p in vs:p[1]+=offset_north
   new=mesh('R3_STUDY_'+o.name,vs,[list(p.vertices) for p in o.data.polygons],wood,col)
   for p,q in zip(new.data.polygons,o.data.polygons):p.use_smooth=q.use_smooth
   if o.name.startswith('B11_Rectangle024'):booknames.append(new.name)
   if o.name.startswith('B11_Rectangle026'):tablenames.append(new.name)
 for o in list(bpy.data.objects):
  if o.name.startswith(('B11_Rectangle024','B11_Rectangle025','B11_Rectangle026','B11_Rectangle027','B11_Circle007','B11_Circle008','B11_Rectangle043','B11_Rectangle044')) or o.name in ['FN_书柜','FN_矮书柜','FN_茶台','FN_主人椅','FN_条凳','FN_凳子','FN_打印机','FN_nas']:
   o.hide_viewport=True;o.hide_render=True;o.hide_set(True);legacy.append(o.name)
 # Replace the pending direction pink chair block with a readable wood chair
 # at the same400x400 footprint; the host faces west toward the tea table.
 qx,qy=15.21725,8.26059375
 bevel(box('R3_STUDY_HOST_SEAT',[qx,qy,.873],[qx+.4,qy+.4,.90],wood,col))
 for dx,dy in [(.025,.025),(.35,.025),(.025,.35),(.35,.35)]:box('R3_STUDY_HOST_LEG_'+str(dx)+'_'+str(dy),[qx+dx,qy+dy,.45],[qx+dx+.025,qy+dy+.025,.88],wood,col)
 for yy in [qy+.025,qy+.35]:box('R3_STUDY_HOST_BACK_POST_'+str(yy),[qx+.372,yy,.88],[qx+.4,yy+.025,1.30],wood,col)
 box('R3_STUDY_HOST_BACK_RAIL',[qx+.37,qy+.02,1.267],[qx+.4,qy+.38,1.30],wood,col)
 for i in range(5):box('R3_STUDY_HOST_BACK_SLAT_'+str(i),[qx+.378,qy+.067+i*.055,.93],[qx+.392,qy+.083+i*.055,1.28],wood,col)
 # Keep the long table's approved2200x800 footprint and750mm height.
 # A shallow apron echoes the reference's vertical wood rhythm without
 # blocking seated knee room or inventing full-height pedestal panels.
 for side,x in [('WEST',14.281625),('EAST',15.061625)]:
  for i in range(53):
   y=7.41+offset_north+i*.04
   box('R3_TEA_APRON_'+side+'_'+str(i),[x-.008,y,1.12],[x+.008,y+.020,1.18],wood,col)
 # Dedicated tea-service counter replaces the old open low bookcase.
 x0,y0,x1,y1=14.097375,6.642625,15.697375,7.092625;z0=.45;zt=1.35;t=.018
 carcass=[]
 for n,a,b in [('L',[x0,y0,.53],[x0+t,y1,zt-.04]),('R',[x1-t,y0,.53],[x1,y1,zt-.04]),('BACK',[x0,y0,.53],[x1,y0+t,zt-.04]),('BASE',[x0,y0,.53],[x1,y1,.548]),('PLINTH',[x0,y0+.03,z0],[x1,y1-.03,.53])]:carcass.append(box('R3_TEA_COUNTER_'+n,a,b,wood,col).name)
 for i in range(3):
  a=x0+i*(x1-x0)/3;b=x0+(i+1)*(x1-x0)/3
  carcass.append(bevel(box('R3_TEA_COUNTER_FRONT_'+str(i),[a+.002,y1-.018,.55],[b-.002,y1,zt-.042],wood,col)).name)
  box('R3_TEA_COUNTER_PULL_'+str(i),[(a+b)/2-.035,y1,1.19],[(a+b)/2+.035,y1+.014,1.197],metal,col)
 # Counter top is physically open at the sink, rather than a solid slab
 # behind a proxy bowl. Wet zone west; dry heating zone east.
 sx0,sy0,sx1,sy1=14.277375,6.722625,14.627375,7.002625
 for n,a,b in [('WEST',[x0,y0,zt-.04],[sx0,y1,zt]),('EAST',[sx1,y0,zt-.04],[x1,y1,zt]),('REAR',[sx0,y0,zt-.04],[sx1,sy0,zt]),('FRONT',[sx0,sy1,zt-.04],[sx1,y1,zt])]:carcass.append(box('R3_TEA_WORKTOP_'+n,a,b,stone,col).name)
 for n,a,b in [('BOTTOM',[sx0,sy0,1.18],[sx1,sy1,1.184]),('L',[sx0,sy0,1.18],[sx0+.004,sy1,zt]),('R',[sx1-.004,sy0,1.18],[sx1,sy1,zt]),('BACK',[sx0,sy0,1.18],[sx1,sy0+.004,zt]),('FRONT',[sx0,sy1-.004,1.18],[sx1,sy1,zt])]:box('R3_TEA_SINK_'+n,a,b,sinkmat,col)
 def tube(n,pts,r,m):
  d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=8;d.bevel_depth=r;d.bevel_resolution=3
  sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
  for p,v in zip(sp.points,pts):p.co=(*v,1)
  o=bpy.data.objects.new(n,d);col.objects.link(o);d.materials.append(m);return o
 fx,fy=14.46,6.682625
 cylinder('R3_TEA_FAUCET_BASE',(fx,fy,1.373),.025,.046,metal,col)
 tube('R3_TEA_FAUCET',[(fx,fy,1.37),(fx,fy,1.57),(fx,fy+.025,1.61),(fx,fy+.12,1.61),(fx,fy+.165,1.58),(fx,fy+.165,1.55)],.012,metal)
 box('R3_TEA_FAUCET_HANDLE',[fx+.026,fy-.006,1.42],[fx+.065,fy+.006,1.431],metal,col)
 cx,cy=(sx0+sx1)/2,(sy0+sy1)/2
 cylinder('R3_TEA_SINK_DRAIN',(cx,cy,1.184),.021,.008,metal,col)
 tube('R3_TEA_DRAIN_TRAP',[(cx,cy,1.18),(cx,cy,.98),(cx,cy-.055,.92),(cx,cy-.115,.92),(cx,cy-.16,.97),(cx,6.643,.97)],.018,sinkmat)
 tube('R3_TEA_COLD_FEED',[(fx,fy,1.35),(fx,fy,1.02),(fx,6.643,1.02)],.006,sinkmat)
 for n,p in [('COLD_INLET',(fx,6.643,1.02)),('DRAIN_OUTLET',(cx,6.643,.97)),('DRY_POWER',(15.33,6.602,1.48))]:
  o=empty('R3_TEA_'+n+'_TO_VERIFY',col);o.location=p;o['site_connection_status']='SCHEMATIC_POINT_TO_VERIFY';o['room']='STUDY_TEA_SERVICE'
 box('R3_TEA_INDUCTION_PLATE',[15.105,6.725,zt],[15.455,7.025,zt+.015],metal,col)
 for i in range(3):cylinder('R3_TEA_BOILER_BUTTON_'+str(i),(15.18+i*.035,7.005,zt+.018),.005,.004,clay,col)
 kx,ky=15.28,6.865
 cylinder('R3_TEA_KETTLE',(kx,ky,zt+.105),.09,.17,clay,col)
 cylinder('R3_TEA_KETTLE_LID',(kx,ky,zt+.195),.078,.018,metal,col)
 cylinder('R3_TEA_KETTLE_KNOB',(kx,ky,zt+.215),.017,.022,wood,col)
 tube('R3_TEA_KETTLE_SPOUT',[(kx-.07,ky,zt+.10),(kx-.13,ky,zt+.14),(kx-.16,ky,zt+.18)],.020,clay)
 handle=[(kx+.03,ky-.105,zt+.07),(kx+.13,ky-.105,zt+.09),(kx+.145,ky-.105,zt+.15),(kx+.08,ky-.105,zt+.185)]
 tube('R3_TEA_KETTLE_HANDLE',handle,.009,metal)
 # Add sparse books to existing open shelves; preserve all shelf geometry.
 sh=bpy.data.objects['B11_Rectangle024_SHELF_2'];bookbase=max((sh.matrix_world@v.co).z for v in sh.data.vertices)+.001
 for bay in [1,3,5,7]:
  yy=6.69+bay*.462
  for i in range(4):
   box('R3_STUDY_BOOK_'+str(bay)+'_'+str(i),[15.76,yy+i*.047,bookbase],[15.99,yy+i*.047+.032,bookbase+.23+(i%2)*.045],paper if i%2 else wood,col)
 record=dict(status='FUNCTION_AND_STYLE_REVIEW',reference_style='Natural wood long tea table + open bookcase behind host + low tea service counter, per user reference',
  bookcase=dict(source='Rectangle024',bounds_mm=[15735.875,6642.59375,16185.875,10842.59375],height_mm=2000,objects=booknames),
  tea_table=dict(source='Rectangle026',bounds_mm=[14271.625,7389.71875+offset_north*1000,15071.625,9589.71875+offset_north*1000],height_mm=750,objects=tablenames,shift_north_mm=offset_north*1000),
  tea_counter=dict(replaces='Rectangle025 LOW_BOOKCASE',bounds_mm=[14097.375,6642.625,15697.375,7092.625],height_mm=900,body_objects=carcass,sink_mm=[350,280],boiler_zone_mm=[350,300],water_and_drain='MODELED_SERVICE_POINTS_SITE_CONNECTION_PENDING'),
  table_counter_gap_mm=297.09375+offset_north*1000,
  operation_note='User explicitly chose to keep FreeCAD positions on2026-10-02. The297mm table/counter gap remains and is not represented as a comfortable standing service aisle; future real-use dimensions require review.',
  inactive_original_objects=legacy,materials='Simple natural-wood review colors, not a final photoreal material specification')
 return legacy,record
