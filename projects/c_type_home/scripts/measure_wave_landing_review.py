"""Measure the packet-selected landing approach; dimensioned model plan, not a site survey."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union,nearest_points
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
rows=json.loads((r/'LANDING_WALL_LOCAL_GEOMETRY.json').read_text());objs={x['name']:x for x in rows}
geom=json.loads((r/'WAVE_STEP_GEOMETRY.json').read_text())
wall=objs['VIEW_WALL_R3_WEST_PARTITION']['bounds']
obstacle=box(wall[0][0],wall[0][1],wall[1][0],wall[1][1])
clip=box(0,6.50725,20,7.799)
edge=LineString(geom['front_lines'][3]).intersection(clip)
edge4=LineString(geom['front_lines'][4]).intersection(clip)
a,b=nearest_points(edge4,obstacle);c,d=nearest_points(edge,obstacle)
south=objs['VIEW_WALL_W_wall_md_0050']['bounds'][1][1]
north=objs['VIEW_WALL_W_wall_md_0051']['bounds'][0][1]
casing=objs['V4_D-GUEST-BATH_CASING_B_FRONT']['bounds'][0][1]
report={'source_revision':'r4-living-wave35-aluminum-review-2','measurement_scope':'Local upper landing beside last stair,leading toward guest bathroom,around packet source hit8.62835,6.70418,.45','wall_face_to_wall_face_m':north-south,'minimum_door_approach_clear_depth_m':casing-south,'flat_landing_excluding_arrival_tread_throat_m':edge4.distance(obstacle),'same_level_area_including_arrival_tread_throat_m':edge.distance(obstacle),'flat_throat_endpoints_source_xy':[list(a.coords)[0],list(b.coords)[0]],'width_definition':'Shortest diagonal clearance between fourth-band rear edge and west-partition corner; including fourth tread uses exposed last-riser edge. The pointed stair/wall terminal itself is not a traversable route and is excluded.','door_state':'Current door mesh behind wall plane; opening sweep is not validated.','design_assessment':'1175mm door approach is usable for one-person circulation but below1200mm accessibility reference and offers little margin;944mm independent flat landing is constrained and below project1100mm preferred route target. Do not certify compliance or claim door swing clearance.','standard_reference':'GB55019-2021 2.2.2 only as accessibility comparison, not automatically governing this internal private stair.'}
(r/'LANDING_WIDTH_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(9,8))
for k,line in enumerate(geom['front_lines'][:-1]):
 poly=Polygon(line+list(reversed(geom['front_lines'][k+1])));xs,ys=poly.exterior.xy
 ax.fill(xs,ys,color=['#eedac1','#dfc19b','#cca477','#bc8f62'][k],edgecolor='#6d553d',lw=1)
for row in rows:
 if not row['name'].startswith(('VIEW_WALL_','V4_D-GUEST-BATH_CASING')):continue
 lo,hi=row['bounds']
 if lo[2]>2.5:continue
 ax.fill([lo[0],hi[0],hi[0],lo[0]],[lo[1],lo[1],hi[1],hi[1]],color='#707778',alpha=.85)
def dimension(p,q,label):
 ax.annotate('',xy=q,xytext=p,arrowprops={'arrowstyle':'<->','color':'#b52b30','lw':2})
 mx=(p[0]+q[0])/2;my=(p[1]+q[1])/2
 ax.text(mx+.06,my+.05,label,color='#b52b30',fontsize=11,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
dimension(list(a.coords)[0],list(b.coords)[0],'944 mm (flat landing only)')
dimension([9.64,south],[9.64,casing],'1175 mm (incl. casing)')
ax.scatter([8.6283507],[6.7041757],s=55,color='#176d8e')
ax.annotate('Packet hit / upper floor',(8.6283507,6.7041757),(8.55,7.14),arrowprops={'arrowstyle':'->'},fontsize=10)
ax.text(8.89,7.98,'Guest bathroom door',fontsize=10)
ax.text(6.1,5.4,'4 x 350 mm treads',rotation=90,fontsize=11)
ax.set_xlim(5.4,10);ax.set_ylim(4.5,8.25);ax.set_aspect('equal');ax.grid(alpha=.18)
ax.set_xlabel('Source X (m)');ax.set_ylabel('Source Y (m)')
ax.set_title('Review2: model landing clearances (not site measurements)')
fig.tight_layout();fig.savefig(r/'LANDING_WIDTH_DIMENSIONED.png',dpi=160)
print(json.dumps(report,ensure_ascii=False))
