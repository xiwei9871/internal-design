import json,hashlib,statistics
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
JOBS=json.loads((OUT/'working/prompts/jobs.json').read_text());CAMS=json.loads((OUT/'working/cameras/LIVING_CAMERA_REGISTER.json').read_text());RESULTS=json.loads((OUT/'logs/GENERATION_RESULTS.json').read_text());S=json.loads((OUT/'logs/BATCH_GENERATION_SUMMARY.json').read_text());G=json.loads((OUT/'logs/GEOMETRY_LOCK_QA.json').read_text())
assert len(JOBS)==15;assert S['generated']==15 and not S['interface_fallback'];assert sha(G['source'])==G['source_sha256'];assert sha(G['working_branch'])==G['working_sha256']
R={r['id']:r for r in RESULTS}
for j in JOBS:
 assert R[j['id']]['status'].startswith('GENERATED') or R[j['id']]['status']=='EXISTS_PRESERVED'
 im=Image.open(j['output']);im.load();assert im.size==(1536,1024);assert im.format=='PNG'
LINK=lambda title,p:f'[{title}]({Path(p).resolve()})'
highlights={
 'A1':{'strict':'原会客组合的暖白/浅木表达，浅木框挂画和织物建立住宅感。','design':'轻窗帘、柔和台灯、低矮茶几与地毯形成更完整的主视角。','explore':'更圆润的沙发外观和自然植物层次，保持两组座位关系。'},
 'A2':{'strict':'反向空间和电视柜功能清楚，原错层平台与台阶关系可见。','design':'电视区、木色收纳表面和公共区层次更统一。','explore':'更克制的电视柜造型、轻茶几和前景织物组合。'},
 'A3':{'strict':'适合核对会客区家具组合，布艺、茶几和地毯层次清楚。','design':'浅木圆角茶几与织物细节更成熟，可作为选家具参考。','explore':'软装更精简，植物和挂画提供自然住宅的近景氛围。'},
 'A4':{'strict':'公共区域、曲线平台和台阶总体关系清楚。','design':'暖白与木色从客厅延续到餐区，公共区联动较完整。','explore':'轻躺椅、辅助边几和平台侧面表达提供搭配灵感。'},
 'A5':{'strict':'窗框、平台和沙发遮挡关系的日光表达。','design':'窗边软垫与轻薄织物提供阅读/休憩灵感。','explore':'更简洁的窗边木面、绿植和柔和软装。'},
}
notes={
 'A1':'两组沙发、茶几、边几与北侧窗的功能关系整体保留；AI对镜头裁切、扶手和茶几比例有微小再解释，不作尺寸确认。',
 'A2':'北侧飘窗在机位背后，结果未另造前方大窗；可见平台、台阶和公共区关系保留。电视屏幕和部分木饰面是AI功能/材质表达，原白模未确认这些具体造型。',
 'A3':'原会客功能区保持；design/explore的圆角、茶几尺寸及软装不同属于可替换同类家具灵感，尚未回写模型。',
 'A4':'原台阶、曲线平台和餐区开口整体对应；木饰面与柜面解读需与模型复核，不能视为新增固定柜已确认。',
 'A5':'窗框及外挑窗边逻辑保持，平台有部分被沙发遮挡。木饰面/软垫仅为灵感；AI不能证明台面高度和进深，尤其需防止把低平台误读为更高更深的固定窗边柜。',
}
rec=['living_A1_design_v1','living_A2_design_v1','living_A3_design_v1','living_A4_design_v1','living_A5_explore_v1']
index=['# 客厅候选图索引','',LINK('15张总览联系图',OUT/'exports/contact_sheets/LIVING_AI_CONTACT_SHEET_v1.png'),' · '+LINK('5机位白模索引',OUT/'exports/contact_sheets/LIVING_CAMERA_INDEX_v1.png'),'', '| 相机 | strict | design | explore |','|---|---|---|---|']
for cam in CAMS:
 row=[cam['id']+' '+cam['name']]
 for mode in ['strict','design','explore']:
  j=next(j for j in JOBS if j['camera']==cam['id'] and j['version']==mode);row.append(LINK(mode,j['output']))
 index.append('| '+' | '.join(row)+' |')
index.extend(['','## 每张记录','','| 图像 | 生成时间（上海） | 耗时 | 提示词 | 简短说明 |','|---|---|---|---|---|'])
for j in JOBS:
 r=R[j['id']];index.append('| '+LINK(j['id'],j['output'])+' | '+r['completion_time']+' | '+str(r['duration_seconds'])+'秒 | '+LINK('prompt',j['prompt_file'])+' | '+highlights[j['camera']][j['version']]+' |')
index.extend(['','## 建议优先筛选',''])
for id in rec:
 j=next(j for j in JOBS if j['id']==id);index.append('- '+LINK(id,j['output'])+'：'+highlights[j['camera']][j['version']])
(OUT/'LIVING_IMAGE_INDEX.md').write_text('\n'.join(index)+'\n')
dur=[r['duration_seconds'] for r in RESULTS if r['status'].startswith('GENERATED')]
report=['# 客厅批量跑图 V1 · 2026-10-02','',
 '交付完成：5个R3机位、5张白模、15张AI候选（strict/design/explore各5张）、相机索引、15图总览、完整prompt pack和逐图记录。候选用于人工筛选与装修灵感讨论，不作为施工尺寸确认。','',
 LINK('打开15张候选总览',OUT/'exports/contact_sheets/LIVING_AI_CONTACT_SHEET_v1.png'),' · '+LINK('打开图像索引',OUT/'LIVING_IMAGE_INDEX.md'),' · '+LINK('全部prompt',OUT/'LIVING_PROMPT_PACK.md'),'',
 '## 执行与耗时','',
 f'白模导出使用Workbench，共约4秒；未使用Cycles、没有投入Blender高精材质。AI请求使用用户配置的gpt-image-2编辑接口，1536×1024、high、每次n=1、并发3。按strict→design→explore顺序执行。AI批量阶段共{S["duration_seconds"]:.2f}秒（约3分23秒），单张{min(dur):.2f}–{max(dur):.2f}秒，平均{statistics.mean(dur):.2f}秒。15/15成功，未发生接口fallback。',
 '逐图开始时间、完成时间、耗时、输入和输出路径见logs/GENERATION_RESULTS.json；每张native CLI输出单独存为日志。密钥仅由skill入口读取私有~/.env，未写入项目、prompt或报告。','',
 '## 几何源与相机','',
 f'唯一模型源：{LINK("OPTION_A_SLIDING_R3.blend",G["source"])}。SHA256 `{G["source_sha256"]}`，结束时仍一致。独立工作文件：{LINK("living_batch_v1.blend",G["working_branch"])}。{G["locked_source_objects"]}个原对象的网格、位置/旋转/缩放、父子关系、修改器保持；工作分支只加相机和白模显示材质，排除非物理参考辅助体。母版未改。','',
 '| 机位 | 位置m | 目标m | 焦距 | 视高 | 重点 |','|---|---|---|---|---|---|']
for c in CAMS:report.append('| '+c['id']+' '+c['name']+' | '+str(c['pos'])+' | '+str(c['target'])+' | '+str(c['lens'])+'mm | '+str(c['eye_height_above_ffl_m'])+'m | '+c['story']+' |')
report.extend(['',LINK('白模相机索引',OUT/'exports/contact_sheets/LIVING_CAMERA_INDEX_v1.png'),'','## 三种自由度','',
 'strict：主要保留输入中的布局/组合，只优化材质、光线和少量软装。design：硬锁定空间和主功能区，同类家具款式、茶几/地毯/窗帘/灯具等可优化。explore：仍锁定结构和动线，小范围探索次要家具、窗边与更有设计感的搭配。','',
 '每张都直接以对应R3白模作为编辑输入，没有把上一张AI图作为下一张几何源，避免连锁空间漂移。五个机位已先自查通过，见working/cameras/CAMERA_SELF_REVIEW.json。','',
 '## 逐机位视觉核对',''])
for c in CAMS:report.append('- '+c['id']+'：'+notes[c['id']])
report.extend(['','人工查看了全部15张的小型分组代理，检查了门窗/墙体基本关系、主要家具占位、错层与平台、尺度是否离谱、材质与光感。整体适合作为候选讨论；仍有细微比例、裁切、窗沿与饰面再解释，不能将“AI生成成功”当作“精确几何认证”。原模型和白模保持真值权威。外景、电视设备、挂画、灯具、软垫、植物均是设计表达，未新增进定稿3D模型。','',
 '## 值得保留和新的灵感',''])
for id in rec:
 j=next(j for j in JOBS if j['id']==id);report.append('- '+LINK(id,j['output'])+'：'+highlights[j['camera']][j['version']])
report.extend(['',
 '可重点比较浅木细框艺术画、窗帘分量、台灯与落地灯、圆角茶几、地毯层次、电视柜的轻量化造型以及窗边软垫。A1/A2 design宜用于整体风格，A3 design宜用于家具材质，A4 design宜用于公共区联动，A5 explore宜用于窗边氛围。final_selected文件夹保留为空，等待用户筛选，不自动把建议当成定稿。','',
 '## 文件','',LINK('LIVING_IMAGE_INDEX.md',OUT/'LIVING_IMAGE_INDEX.md'),' · '+LINK('LIVING_PROMPT_PACK.md',OUT/'LIVING_PROMPT_PACK.md'),' · '+LINK('工作模型与相机文件夹',OUT/'working'),' · '+LINK('全部正式AI图',OUT/'exports/ai_outputs'),'',
 '所有大图、白模、联系图和代理均保存在项目文件系统，只按路径交付。批次来源任务书保存在USER_BATCH_TASK_BRIEF.txt。',
])
(OUT/'LIVING_BATCH_REPORT.md').write_text('\n'.join(report)+'\n')
(OUT/'exports/final_selected/README.md').write_text('等待用户人工筛选。推荐候选见LIVING_BATCH_REPORT.md；当前无自动定稿。\n')
qa=dict(status='CANDIDATES_READY_FOR_HUMAN_REVIEW',source_model_unchanged=True,geometry_exactness='Blender/clay locked; AI outputs visually checked, not construction-dimension authority',camera_notes=notes,images=[dict(id=j['id'],status='VISUALLY_REVIEWED_CANDIDATE',description=highlights[j['camera']][j['version']],needs_human_review=True) for j in JOBS],recommended=rec)
(OUT/'logs/VISUAL_REVIEW.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
files=[Path(j['output']) for j in JOBS]+[Path(j['prompt_file']) for j in JOBS]+[Path(c['clay_path']) for c in CAMS]+[OUT/'LIVING_BATCH_REPORT.md',OUT/'LIVING_IMAGE_INDEX.md',OUT/'LIVING_PROMPT_PACK.md',OUT/'exports/contact_sheets/LIVING_AI_CONTACT_SHEET_v1.png',OUT/'exports/contact_sheets/LIVING_CAMERA_INDEX_v1.png',Path(G['working_branch']),OUT/'working/cameras/LIVING_CAMERA_REGISTER.json',OUT/'logs/GEOMETRY_LOCK_QA.json',OUT/'logs/GENERATION_RESULTS.json',OUT/'logs/BATCH_GENERATION_SUMMARY.json',OUT/'logs/VISUAL_REVIEW.json']
manifest=dict(status='DELIVERED_CANDIDATE_BATCH',official_ai_images=15,clay_images=5,source_sha256=G['source_sha256'],api_phase_seconds=S['duration_seconds'],human_selection_pending=True,report=str(OUT/'LIVING_BATCH_REPORT.md'),contact_sheet=str(OUT/'exports/contact_sheets/LIVING_AI_CONTACT_SHEET_v1.png'),files_sha256={str(p):sha(p) for p in files})
(OUT/'LIVING_BATCH_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(delivery='PASS',ai_images=15,clay_images=5,api_seconds=S['duration_seconds'],files=len(files),source_preserved=True,report=manifest['report']),ensure_ascii=False))
