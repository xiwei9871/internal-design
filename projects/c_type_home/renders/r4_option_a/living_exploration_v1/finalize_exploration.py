import json,hashlib,statistics
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
link=lambda title,p:f'[{title}]({Path(p).resolve()})'
P=json.loads((OUT/'R4_LIVING_PREFLIGHT.json').read_text());C=json.loads((OUT/'00_reference/R4_CAMERA_REGISTER.json').read_text());J=json.loads((OUT/'05_prompts/LIVING_JOBS.json').read_text());R=json.loads((OUT/'06_reports/GENERATION_RESULTS.json').read_text());S=json.loads((OUT/'06_reports/GENERATION_SUMMARY.json').read_text());V=json.loads((OUT/'06_reports/VISUAL_REVIEW_DATA.json').read_text());QA=json.loads((OUT/'06_reports/REFERENCE_GEOMETRY_QA.json').read_text())
assert sha(P['source_path'])==P['SHA256'];assert sha(P['working_copy'])==QA['branch_sha256'];assert len(C)==5
images=[]
for j in J:
 r=next(r for r in R if r['image_id']==j['image_id']);review=V[j['image_id']];exists=Path(j['output']).exists();size=None
 if exists:
  im=Image.open(j['output']);im.load();size=list(im.size);assert im.format=='PNG';assert im.size==(1536,1024)
 gate='NOT_REQUIRED'
 if j['variant']!='faithful':
  required=4 if j['variant']=='designer' else 6;cats=review['difference_categories'];mandatory={'seating_composition','furniture_silhouette','lighting_strategy','focal_art_strategy'}
  gate='PASS' if len(cats)>=required and (j['variant']!='creative' or mandatory.issubset(cats)) else 'WARNING_AFTER_ONE_RETRY'
 row=dict(**j,status=review['status'] if exists else 'GENERATION_FAILED',geometry_preservation=review['geometry_preservation'],design_divergence=review['design_divergence'],new_ideas=review['new_ideas'],difference_categories=review['difference_categories'],divergence_gate=gate,geometry_notes=review['geometry_notes'],review_notes=review['review_notes'],retry_count=review.get('retry_count',0),attempts=review.get('attempts',[]),actual_size=size,initial_generation_seconds=r['seconds'],source_reference_sha256=sha(j['source_reference']),image_sha256=sha(j['output']) if exists else None)
 if review.get('effective_prompt_file'):row['prompt_file']=review['effective_prompt_file']
 images.append(row)
manifest=dict(status='LIVING_AI_EXPLORATION_HUMAN_REVIEW',source_model=P['source_path'],source_sha256=P['SHA256'],working_reference=P['working_copy'],source_objects=P['object_count'],source_collections=P['collection_count'],camera_register=str(OUT/'00_reference/R4_CAMERA_REGISTER.json'),reference_geometry_QA='PASS_UNCHANGED_R4',requested_matrix=15,successful_generation=sum(r['actual_size'] is not None for r in images),failed_generation=sum(r['actual_size'] is None for r in images),geometry_warning_count=sum(r['geometry_preservation']=='WARNING' for r in images),geometry_failure_count=sum(r['geometry_preservation']=='FAIL' for r in images),divergence_warning_count=sum(r['divergence_gate']=='WARNING_AFTER_ONE_RETRY' for r in images),no_selected_DNA=True,no_cross_view_consistency_required_yet=True,no_ranking_or_winner=True,images=images)
(OUT/'06_reports/LIVING_AI_MANIFEST_V1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Curated extraction records observations and trade-offs, not ranked choices.
IDEA_SPECS=[
 ('furniture','exposed_ash_sofa_frame','裸露白蜡木框架和薄木扶手，将沙发软包与木作语言统一。','MEDIUM',False),
 ('furniture','oval_stone_coffee_table','浅暖石面椭圆茶几搭低木底座，用软硬材质区分会客中心。','MEDIUM',False),
 ('furniture','nesting_timber_tables','大小错落的有机木桌组合，可把活动桌系统替代单一长方桌。','LOW',False),
 ('furniture','reading_chair_pair','以两张轻木框阅读/休闲椅代替一张窗前双人沙发；需要核对全屋座位能力及门口净空。','MEDIUM',False),
 ('furniture','lower_modular_sofa','主座位采用更低、更圆润的模块式软包和浅木框，原会客区保持。','MEDIUM',False),
 ('furniture','lighter_window_seating','窗边改为一张轻量阅读椅，保留低飘窗平台与通道，减少窗前体量。','LOW',False),
 ('material','wood_stone_mix','浅白蜡木和克制浅暖石材的组合，比全木或全米色更有层次。','LOW',False),
 ('material','oatmeal_linen','燕麦/米灰织物强调耐看和触感，与浅木暖白形成柔和对比。','LOW',False),
 ('textile','rounded_large_rug','圆角/椭圆大地毯统一座位区域，与矩形建筑形成适度对比。','LOW',False),
 ('textile','organic_woven_rug','天然纤维有机曲线地毯、同类圆桌，形成阅读会客组合焦点。','LOW',False),
 ('textile','light_sheer_strategy','透光自然织物与卷帘/轻帘结合，避免厚窗帘压暗窗边。','MEDIUM',False),
 ('lighting','slender_floor_light','纤细线形立灯与低眩光台灯形成阅读和会客辅助光层。','LOW',False),
 ('lighting','arched_reading_light','弧形阅读灯作为空间焦点，取代依赖堆装饰的视觉层次；需核对灯杆与通道。','LOW',False),
 ('art','large_textile_art','低饱和大幅织物/抽象艺术建立焦点，保持墙面轻量和住宅感。','LOW',False),
 ('wall','projection_art_media','把原media墙表达为暖白投影/艺术整合，降低大黑电视的存在感；设备距离和使用工况另行核对。','MEDIUM',False),
 ('storage','low_media_cabinet_finish','保留原低media柜包络，探索浅木表面与轻艺术功能；AI柜内分格不是加工依据。','LOW',False),
 ('decor','curated_plant_density','少量体量明确的植物/花器搭配，而不是把所有角落塞满小摆件。','LOW',False),
 ('material','bay_timber_finish','仅将原飘窗平台表面表达为浅木，禁止加深、加高或做新固定高柜。','MEDIUM',False),
]
ideas=[]
for category,code,desc,complexity,geometry in IDEA_SPECS:
 sources=[r['image_id'] for r in images if code in r['new_ideas']]
 if not sources:continue
 ideas.append(dict(idea_id='IDEA_'+str(len(ideas)+1).zfill(2),source_image=sources[0],source_images=sources,category=category,description=desc,implementation_complexity=complexity,geometry_change_required=geometry,selection_status='UNSELECTED_HUMAN_DISCUSSION'))
(OUT/'06_reports/LIVING_AI_IDEA_REGISTER_V1.json').write_text(json.dumps(dict(status='UNRANKED_IDEA_LIBRARY',ideas=ideas),ensure_ascii=False,indent=2)+'\n')
ideamd=['# LIVING AI IDEA REGISTER V1','', '本表从候选图提取讨论想法，未选winner，未回写模型。geometry_change_required=false表示不需要改变本次硬锁建筑；实际家具净空和施工连接仍需核对。','', '| idea_id | 来源图片 | 类别 | 想法 | 复杂度 | 建筑几何变化 |','|---|---|---|---|---|---|']
for i in ideas:
 sources='、'.join(link(s,next(r['output'] for r in images if r['image_id']==s)) for s in i['source_images']);ideamd.append('| '+i['idea_id']+' | '+sources+' | '+i['category']+' | '+i['description']+' | '+i['implementation_complexity']+' | '+str(i['geometry_change_required']).lower()+' |')
(OUT/'06_reports/LIVING_AI_IDEA_REGISTER_V1.md').write_text('\n'.join(ideamd)+'\n')
index=['# R4客厅AI图像索引','', '| 机位 | FAITHFUL | DESIGNER | CREATIVE |','|---|---|---|---|']
for c in C:
 row=[c['id']+' '+c['name']]
 for v in ['faithful','designer','creative']:
  r=next(r for r in images if r['camera_id']==c['id'] and r['variant']==v);row.append(link(v.upper(),r['output'])+' · '+r['geometry_preservation']+' / '+r['divergence_gate'])
 index.append('| '+' | '.join(row)+' |')
index.extend(['','标记：geometry_preservation为视觉结构检查；divergence_gate为同机位相对Faithful的分类差异门槛。WARNING图保留用于讨论，但不可当几何/差异合格图。',''])
(OUT/'06_reports/LIVING_IMAGE_INDEX.md').write_text('\n'.join(index))
report=['# R4 OPTION A — LIVING ROOM FULL AI DESIGN EXPLORATION V1','', '**LIVING_AI_EXPLORATION = HUMAN_REVIEW**。五个机位、三类方向全部执行；没有排名、没有选winner、没有做Selected DNA或跨视角一致性渲染。','',
 link('全部15张总览',OUT/'04_contact_sheets/LIVING_ALL_15_CONTACT_SHEET.png'),' · '+link('图像索引',OUT/'06_reports/LIVING_IMAGE_INDEX.md'),' · '+link('Manifest',OUT/'06_reports/LIVING_AI_MANIFEST_V1.json'),'',
 '## R4源与preflight','',f'唯一源：{link("OPTION_A_SLIDING_R4.blend",P["source_path"])}；SHA256 `{P["SHA256"]}`。源对象{P["object_count"]}，源collections {P["collection_count"]}，Blender可打开。独立工作副本 {link("R4_LIVING_AI_REFERENCE_V1.blend",P["working_copy"])}。所有参考直接从R4派生，未引用R3底图、未mergeR3对象、未重建厨房；源哈希结束一致。源几何和姿态锁校验通过，正常直门和连续+450mm门口地坪承接R4。','',
 '先仅导出A1并做真实API最小测试，约'+str(S['minimal_test_seconds'])+'秒返回PNG；成功后才导出剩余参考并运行批次。A1 test被复用为正式A1 faithful，不额外算第16张。',
 'Blender只用Workbench clay，无PBR、Cycles或最终灯光开发。1536×1024，gpt-image-2 high，最大并发3；正式剩余批次约'+str(S['batch_seconds'])+'秒。每张耗时、接口日志与审核重试记录位于06_reports，key不进入项目或prompt。','',
 '## 相机与生成矩阵','', '| 机位 | 位置m / 目标m | 焦距与视高 | Faithful / Designer / Creative |','|---|---|---|---|']
for c in C:report.append('| '+c['id']+' '+c['name']+' | '+str(c['pos'])+' / '+str(c['target'])+' | '+str(c['lens'])+'mm / '+str(c['eye_height'])+'m | 3张 |')
report.extend(['',f'生成成功{manifest["successful_generation"]}/15；接口失败{manifest["failed_generation"]}。几何WARNING {manifest["geometry_warning_count"]}，几何FAIL {manifest["geometry_failure_count"]}；差异重试后WARNING {manifest["divergence_warning_count"]}。','',
 '## 逐图审核与差异','', '逐张小型代理对照同机位clay，检查建筑/窗框/飘窗/错层、通道和家具尺度。相同机位方向对比用实际可见的类别记录；不是依靠像素相似度宣称精确几何。AI图片始终是候选，毫米尺寸及未被相机拍到的净空以模型为准。Designer至少4类，Creative至少6类且包括座位组合、轮廓、照明和焦点策略。一处主要失败最多重试一次，仍不足则WARNING保留，没有无休止循环。','',
 '| 图片 | 几何 | 差异 | 可见分类数量 | 重试 | 说明 |','|---|---|---|---|---|---|'])
for r in images:report.append('| '+link(r['image_id'],r['output'])+' | '+r['geometry_preservation']+' | '+r['design_divergence']+' / '+r['divergence_gate']+' | '+str(len(r['difference_categories']))+' | '+str(r['retry_count'])+' | '+r['review_notes']+' '+r['geometry_notes']+' |')
report.extend(['','## 灵感库与下一阶段','',f'提取{len(ideas)}类可讨论想法，来源、复杂度和是否需改建筑分别记录于 {link("Idea Register",OUT/"06_reports/LIVING_AI_IDEA_REGISTER_V1.md")} 和对应JSON。它们是未排序候选；未将任何家具、灯具或画回写R4。',
 '本批Designer/Creative各视角允许独立家具灵感。跨角度不一致是本阶段的允许范围，不为了“同一家具”压制发散。人选之后才建立LIVING_SELECTED_DNA并做多视角一致性。','',
 '## 交付路径','',link('Faithful五视角',OUT/'04_contact_sheets/LIVING_FAITHFUL_5VIEW.png'),' · '+link('Designer五视角',OUT/'04_contact_sheets/LIVING_DESIGNER_5VIEW.png'),' · '+link('Creative五视角',OUT/'04_contact_sheets/LIVING_CREATIVE_5VIEW.png'),'',link('R4五机位白模',OUT/'04_contact_sheets/LIVING_R4_CAMERA_REFERENCE_SHEET.png'),' · '+link('Prompt Pack R4 V1',OUT/'05_prompts/LIVING_PROMPT_PACK_R4_V1.md'),'',
 '所有prompt由MASTER_ARCH_LOCK + MASTER_STYLE_DNA + CAMERA_PROMPT + VARIANT_PROMPT + DIVERGENCE_REQUIREMENT代码拼装。prompt_rules.py更新共享规则即可统一所有机位；重试附加指令单独留档。全部大图/联系图/代理保存到磁盘，聊天只返回路径和摘要。','',
 '本轮停止，等待HUMAN REVIEW；不启动全屋、其他机位、PBR或Selected DNA。'])
(OUT/'06_reports/LIVING_AI_EXPLORATION_REPORT_V1.md').write_text('\n'.join(report)+'\n')
files=[Path(r['output']) for r in images if r['actual_size']]+[OUT/'06_reports/LIVING_AI_MANIFEST_V1.json',OUT/'06_reports/LIVING_AI_IDEA_REGISTER_V1.md',OUT/'06_reports/LIVING_AI_IDEA_REGISTER_V1.json',OUT/'06_reports/LIVING_AI_EXPLORATION_REPORT_V1.md',OUT/'05_prompts/LIVING_PROMPT_PACK_R4_V1.md',OUT/'R4_LIVING_PREFLIGHT.json']+list((OUT/'04_contact_sheets').glob('*.png'))
(OUT/'06_reports/DELIVERY_INTEGRITY.json').write_text(json.dumps(dict(status='STOPPED_HUMAN_REVIEW',source_sha256=P['SHA256'],files_sha256={str(f):sha(f) for f in files},no_selection=True,no_other_rooms=True),ensure_ascii=False,indent=2)+'\n')
(OUT/'06_reports/work_state.md').write_text('COMPLETE15 matrix; user-directed bounded review retries finished. STOP atHUMAN_REVIEW. No winner/DNA selection or further room/camera work authorized by this task. See manifest warnings and idea register. R4 source hash preserved; only independent clay branch edited.\n')
print(json.dumps(dict(delivery='HUMAN_REVIEW',generated=manifest['successful_generation'],geometry_warnings=manifest['geometry_warning_count'],geometry_failures=manifest['geometry_failure_count'],divergence_warnings=manifest['divergence_warning_count'],ideas=len(ideas),selected_DNA=False),ensure_ascii=False))
