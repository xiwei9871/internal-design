import json
from pathlib import Path
from shapely.geometry import shape,box,mapping
OUT=Path(__file__).resolve().parents[1]
def calculate():
 d=json.loads((OUT/'reports/SOURCE_FLOOR_FOOTPRINTS.json').read_text());U=shape(d['upper_footprint']);F=U.intersection(box(5.6999,4.6999,7.2,6.6001));core=F.union(box(6.7,F.bounds[3],7.8,7.2));clip=box(5.05,4.72,7.80,7.75);tier2=core.buffer(.30,join_style='round',quad_segs=32).intersection(clip).difference(U);tier1=core.buffer(.60,join_style='round',quad_segs=32).intersection(clip).difference(U);addon=core.difference(U);retain=U.difference(F);bsteps=[box(6.3,5.0,6.6,6.2),box(6.6,5.0,6.9,6.2),box(6.9,5.0,7.2,6.2)]
 metrics=dict(original_fan_area_m2=F.area,original_stairs_area_m2=.72,A_added_transition_area_m2=tier1.union(addon).area,A_upper_extension_m2=addon.area,A_lower_tread_area_m2=tier1.difference(tier2).area,A_upper_tread_area_m2=tier2.difference(addon).area,B_new_stair_area_m2=1.08,B_net_lower_recovered_area_m2=F.area+.72-1.08,B_original_fan_recovery_before_stairs_m2=F.area)
 q=dict(source_sha256=d['source_sha256'],fan=mapping(F),upper=mapping(U),A_core=mapping(core),A_tier_300=mapping(tier2),A_tier_150=mapping(tier1),A_addon=mapping(addon),A_full_upper=mapping(U.union(core)),B_retained_upper=mapping(retain),B_steps=[mapping(x) for x in bsteps],metrics=metrics,local_change_zone=[5.05,4.7,7.8,7.8],stairs_A=dict(rise_mm=150,going_mm=300,risers=3,geometry='two continuous offset curved treads plus upper platform'),stairs_B=dict(rise_mm=150,going_mm=300,risers=3,width_mm=1200,top_connection=[7.2,5.0,7.2,6.2]),ramp=dict(rise_mm=450,ratio='1:12',run_mm=5400,width_mm=1100,landing_mm=1525,total_envelope_mm=8450,adopted=False))
 (OUT/'reports/OPTION_GEOMETRY.json').write_text(json.dumps(q,ensure_ascii=False)+'\n');return q
if __name__=='__main__':print(calculate()['metrics'])
