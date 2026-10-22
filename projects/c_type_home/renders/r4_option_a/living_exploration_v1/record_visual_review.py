"""Record bounded visual observations; source geometry still owns dimensions."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
DATA={}
def put(camera,variant,geometry,divergence,cats,ideas,notes,gn=''):
 DATA[f'living_{camera}_{variant}_v1']=dict(status='REVIEWED_CANDIDATE',geometry_preservation=geometry,design_divergence=divergence,difference_categories=cats,new_ideas=ideas,geometry_notes=gn,review_notes=notes,retry_count=0)
put('A1','faithful','PASS','LOW',[],['oatmeal_linen','light_sheer_strategy','curated_plant_density','bay_timber_finish'],'原两组座位、矩形双层茶几和边柜清楚，作为Faithful基准。')
put('A1','designer','PASS','HIGH',['furniture_silhouette','coffee_table_typology','rug_geometry','lighting_strategy','furniture_material_mix','side_furniture'],['exposed_ash_sofa_frame','oval_stone_coffee_table','rounded_large_rug','slender_floor_light','wood_stone_mix','large_textile_art'],'木平台框沙发、椭圆石桌、圆角地毯、线形灯和小边家具形成六类差异。')
put('A1','creative','PASS','HIGH',['seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy','coffee_table_typology','rug_geometry','furniture_material_mix'],['reading_chair_pair','lower_modular_sofa','nesting_timber_tables','organic_woven_rug','arched_reading_light','large_textile_art'],'原窗前双人沙发被轻阅读椅组合取代，弧灯与阅读角成为新焦点；主体墙窗和会客功能区保留。')
put('A2','faithful','WARNING','LOW',[],['projection_art_media','low_media_cabinet_finish','oatmeal_linen','curated_plant_density'],'未生成黑电视墙；后方普通直门、三阶与曲线平台可见。','原固定低media柜包络保持，AI柜内/腿部细分有再解释，不能以图确认固定柜加工拓扑。')
put('A2','designer','WARNING','HIGH',['furniture_silhouette','chair_design','coffee_table_typology','rug_geometry','lighting_strategy','furniture_material_mix'],['exposed_ash_sofa_frame','oval_stone_coffee_table','rounded_large_rug','slender_floor_light','wood_stone_mix','projection_art_media'],'木框软包、木制椅/躺椅、椭圆石桌、圆角毯、细灯和木石混搭一眼可辨；直门和台阶位置保留。','低media柜内部细节不可视为拓扑复核；非本轮修改源模型的依据。')
put('A2','creative','WARNING','HIGH',['seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy','coffee_table_typology','rug_geometry','furniture_material_mix'],['reading_chair_pair','lower_modular_sofa','nesting_timber_tables','organic_woven_rug','arched_reading_light','large_textile_art','projection_art_media'],'窗前座位区改轻椅，前景模块化软包与嵌套桌、弧灯、织物艺术相互配合，media侧保持轻艺术表达。','柜内部/面板解读仅为候选；未生成巨大黑电视，错层及直门总体保留。')
put('A3','faithful','PASS','LOW',[],['oatmeal_linen','curated_plant_density'],'原会客关系与矩形双层桌，织物细节适合作基准；未扩出不存在窗门。')
put('A3','designer','PASS','HIGH',['furniture_silhouette','coffee_table_typology','rug_geometry','furniture_material_mix','side_furniture'],['exposed_ash_sofa_frame','oval_stone_coffee_table','rounded_large_rug','wood_stone_mix'],'木底座与直木扶手、椭圆石桌、圆角大毯及木石混搭；边家具款式不同，差异超过四类。')
put('A3','creative','PASS','HIGH',['seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy','coffee_table_typology','rug_geometry','furniture_material_mix'],['reading_chair_pair','nesting_timber_tables','organic_woven_rug','arched_reading_light','large_textile_art'],'窗边阅读椅组合替代右沙发，弧灯、木桌系统和新的近景焦点/艺术组合形成明显新会客表达。')
put('A4','faithful','WARNING','LOW',[],['projection_art_media','low_media_cabinet_finish','oatmeal_linen'],'三阶、曲线平台、餐区玻璃开口和高低地坪仍对应；没有恢复旧斜门或前景门把手。','局部顶部暖光边缘/平台侧面木纹为AI表达，不能当新增灯槽或结构尺寸；低media柜细节仍需模型核对。')
put('A4','designer','WARNING','HIGH',['furniture_silhouette','chair_design','coffee_table_typology','rug_geometry','lighting_strategy','furniture_material_mix'],['exposed_ash_sofa_frame','oval_stone_coffee_table','rounded_large_rug','slender_floor_light','wood_stone_mix','projection_art_media'],'木框沙发、精细木椅/躺椅、椭圆桌、圆角毯及细灯；公共区开口和三阶关系可见。','平台石面及固定柜分格不能当作结构/加工批准。不得借材质变化抹平高低关系。')
put('A4','creative','WARNING','HIGH',['seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy','coffee_table_typology','rug_geometry','furniture_material_mix'],['reading_chair_pair','lower_modular_sofa','nesting_timber_tables','organic_woven_rug','arched_reading_light','large_textile_art','projection_art_media'],'原躺椅区域转为轻阅读座位，无原大躺椅体量；弧灯与大艺术焦点、木桌组合及有机毯构成六类以上差异。','部分椅/地毯靠近通道，实际家具净空仍需模型核对；平台边和柜分格只作视觉参考。')
put('A5','faithful','PASS','LOW',[],['bay_timber_finish','light_sheer_strategy','oatmeal_linen'],'原窗框与窗前座位、低平台关系保留；薄软垫是可撤软装，不是新台面高度。')
# These two are replaced with final post-retry observations after inspection.
put('A5','designer','FAIL','MEDIUM',['furniture_silhouette','curtain_treatment','furniture_material_mix'],['exposed_ash_sofa_frame','wood_stone_mix','light_sheer_strategy'],'初稿没有在原近景内证明四类差异，已触发一次重试。','初稿把完整茶几和更多地面带进近景，原裁切偏移。')
put('A5','creative','FAIL','HIGH',['seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy','coffee_table_typology','rug_geometry'],['lighter_window_seating','nesting_timber_tables','organic_woven_rug','arched_reading_light'],'初稿发散明显但座椅站在平台上，已触发一次重试。','新增扩大高地坪/平台承载椅子，改变飘窗与原相机近景，是主要几何错误。')
(OUT/'06_reports/VISUAL_REVIEW_DATA.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n')
print('INITIAL15_VISUAL_REVIEW_RECORDED_TWO_BOUNDED_RETRIES_PENDING')
