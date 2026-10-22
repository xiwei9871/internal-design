import json,math,runpy
from pathlib import Path
import shapely
from shapely.geometry import Polygon,MultiPoint,Point,LineString,box
from shapely.ops import unary_union
from shapely.affinity import rotate
OUT=Path(__file__).resolve().parent;L=json.loads((OUT/'LAYOUT_CONTRACT.json').read_text());P=L['opening'];S=L['shared']
B=runpy.run_path(str(OUT/'solid_backend.py'),run_name='helpers')
def section(w,z):
 w=dict(w);zs=[v[2] for v in w['vertices']];w['minz']=min(zs);w['maxz']=max(zs)
 return shapely.make_valid(B['cross_section'](w,z))
def shape(o):return MultiPoint([v[:2] for v in o['vertices']]).convex_hull
data={o:json.loads((OUT/f'{o}_ACTUAL_GEOMETRY.json').read_text()) for o in 'AB'}
wall={o:unary_union([section(w,1.25) for w in d['walls']]) for o,d in data.items()}
fixtures={k:box(*S[k]) for k in ['vanity','wc','wardrobe']};fixtures['shower']=Polygon(S['shower'])
report={'dimensions_source':'actual saved FreeCAD Shape bounds/vertices; actual fresh-open Blender mesh exports','options':{}}
plot={}
for opt,d in data.items():
 new=next(w for w in d['walls'] if w['name']=='R2_COMPLETE_PARTITION_WALLS')
 west_rect=box(*S['west_wall']);west_ok=all(section(new,z).buffer(.0001).covers(west_rect) for z in [.6,1.25,2.7,3.2])
 clear0,clear1=P['clear'];entry=box(clear0+.001,P['south_y']-.12,clear1-.001,P['north_y']+.002)
 air=entry.intersection(wall[opt]).area
 approach=box(clear0,3.65,clear1,P['south_y'])
 wardrobe_block=approach.intersection(fixtures['wardrobe']).area
 yellow=box(S['supplemental_wall'][0]+.001,S['supplemental_wall'][1]+.001,10.7999,S['supplemental_wall'][3]-.001)
 yellow_ok=all(section(new,z).buffer(.0001).covers(yellow) for z in [.6,1.25,2.7,3.2])
 header=box(P['gross'][0]+.001,P['south_y']+.001,P['gross'][1]-.001,P['north_y']-.001)
 head_ok=section(new,2.8).buffer(.0001).covers(header)
 frame=d['door_states']['1'];boundmatch={}
 for k,rect in [('vanity',S['vanity']),('wardrobe',S['wardrobe']),('wc',S['wc'])]:
  got=d['fixture_bounds'][k];actual=[got[0][0],got[0][1],got[1][0],got[1][1]]
  diff=max(abs(a-b)*1000 for a,b in zip(actual,rect));boundmatch[k]=dict(actual_bounds_mm=[round(v*1000,3) for v in actual],max_error_mm=diff)
 actualgroups_match=all(v['max_error_mm']<.02 for v in boundmatch.values())
 row=dict(west_full_rectangle_no_notch=west_ok,entry_solid_wall_overlap_mm2=air*1e6,wardrobe_entry_overlap_mm2=wardrobe_block*1e6,yellow_south_wall_complete=yellow_ok,full_header=head_ok,fixtures_match=actualgroups_match,fixture_bounds=boundmatch)
 if opt=='A':
  closed=shape(frame['R2_SLIDING_LEAF']);opened=shape(d['door_states']['100']['R2_SLIDING_LEAF'])
  sweep=closed.union(opened).convex_hull
  collisions={k:sweep.intersection(v).area*1e6 for k,v in fixtures.items()}
  actual_cavity=box(L['sliding']['pocket'][0],L['sliding']['cavity_y'][0],L['sliding']['pocket'][1],L['sliding']['cavity_y'][1])
  parked_fit=actual_cavity.covers(opened)
  rail=frame['R2_SLIDER_CONTINUOUS_RAIL']['bounds'];leafbounds=opened.bounds
  rail_connected=rail[0][0]<closed.bounds[0] and rail[1][0]>opened.bounds[2]
  row.update(parked_leaf_inside_pocket=parked_fit,full_travel_rail_connected=rail_connected,wall_motion_overlap_mm2=sweep.intersection(wall[opt]).area*1e6,fixture_motion_overlap_mm2=collisions,indoor_swing_area_m2=0,parked_leaf_bounds_mm=[round(v*1000,3) for v in leafbounds])
 else:
  closed=shape(frame['R2_HINGED_LEAF']);opened=shape(d['door_states']['100']['R2_HINGED_LEAF']);hinge=L['hinged']['hinge'];ang=L['hinged']['angle_degrees']
  movers={n:shape(v) for n,v in frame.items() if n.startswith(('R2_HINGED_LEAF','R2_HINGED_HANDLE'))}
  moving=unary_union(list(movers.values()));poses=[rotate(moving,ang*i/720,origin=hinge) for i in range(721)];sweep=unary_union(poses)
  max_wall=max(p.intersection(wall[opt]).area for p in poses)*1e6
  collisions={k:sweep.intersection(v).area*1e6 for k,v in fixtures.items()}
  row.update(angle_degrees=ang,angular_samples=721,wall_motion_overlap_mm2=max_wall,fixture_motion_overlap_mm2=collisions,indoor_swing_area_m2=sweep.area,
     fully_open_leaf_to_vanity_mm=opened.distance(fixtures['vanity'])*1000)
  # Check the actual stored open mesh agrees with the designed hinge motion.
  row['open_pose_geometry_error_mm2']=opened.symmetric_difference(rotate(closed,ang,origin=hinge)).area*1e6
 wc_front=box(S['wc'][0]-.8,(S['wc'][1]+S['wc'][3])/2-.3,S['wc'][0],(S['wc'][1]+S['wc'][3])/2+.3)
 comfort_front=box(S['wc'][0]-.8,(S['wc'][1]+S['wc'][3])/2-.4,S['wc'][0],(S['wc'][1]+S['wc'][3])/2+.4)
 row['wc_800deep_600wide_front_zone_door_overlap_mm2']=sweep.intersection(wc_front).area*1e6
 row['wc_800deep_600wide_front_zone_wall_overlap_mm2']=wc_front.intersection(wall[opt]).area*1e6
 row['wc_800deep_800wide_comfort_zone_outside_room_mm2']=comfort_front.difference(box(9.209,P['north_y'],11.3999,6.4502)).area*1e6
 row['geometry_gates_pass']=all([west_ok,air<1e-7,wardrobe_block<1e-7,yellow_ok,head_ok,actualgroups_match,row['wall_motion_overlap_mm2']<1,all(v<1 for v in row['fixture_motion_overlap_mm2'].values())])
 report['options'][opt]=row
 plot[opt]=dict(walls=wall[opt].intersection(box(8.95,3.65,11.65,6.75)).__geo_interface__,new_walls=section(new,1.25).__geo_interface__,closed=closed.__geo_interface__,opened=opened.__geo_interface__,sweep=sweep.__geo_interface__,wc_front=wc_front.__geo_interface__)
report['shared_fixtures_equal_AB']=data['A']['fixture_bounds']==data['B']['fixture_bounds']
report['shower_enclosure_bounds_mm']=[round(x*1000,3) for x in Polygon(S['shower']).bounds]
report['shower_net_plan_area_m2']=Polygon(S['shower']).intersection(box(9.209,4.8230625,11.3999,6.4502)).area
report['shower_chamfer_segment_mm']=math.dist(S['screen'][1],S['screen'][2])*1000
report['limitations']=['Approx729mm clear entrance is compact; confirm actual frame system before buying.',
 'Shower overall footprint is about842x785mm with a chamfer; it is smaller than the usual900x900 target and needs site/SKU confirmation.',
 'Saved WC footprint600x500mm is a layout envelope, not approval of a product or drain connection.',
 'Chamfer screen segment is only about418mm; the saved wire is a screen outline, not a confirmed shower clear opening. Shower entry mechanism remains to be designed.',
 'The800mm-deep x600mm-wide WC front zone is clear in both options. An optional800mm-wide comfort envelope clips the room south boundary by about38mm; product/site clearance remains to be checked.',
 'Pocket closure/maintenance/partition profiles, waterproofing and drainage are schematic.',
 'Old angled bedroom door retained from frozen base; latest photos establish separate wall placement, no inferred avoidance notch is made.']
(OUT/'CLEARANCE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'PLAN_GEOMETRY.json').write_text(json.dumps(plot))
print(json.dumps(report,ensure_ascii=False,indent=1))
