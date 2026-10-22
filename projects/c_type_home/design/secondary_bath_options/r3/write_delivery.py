import json,hashlib,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];PARENT=OUT.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def link(label,p):return f'[{label}]({Path(p).resolve()})'
L=json.loads((OUT/'LAYOUT_CONTRACT.json').read_text());Q=json.loads((OUT/'CLEARANCE_QA.json').read_text());T=json.loads((OUT/'STUDY_TEA_REGISTER.json').read_text())
M={o:json.loads((OUT/f'OPTION_{o}_MANIFEST.json').read_text()) for o in 'AB'}
for opt in 'AB':
 assert Q['options'][opt]['geometry_gates_pass']
 assert json.loads((OUT/f'{opt}_FRESH_OPEN_QA.json').read_text())['status']=='PASS'
 assert sha(M[opt]['model'])==M[opt]['model_sha256']
assert Q['shared_fixtures_equal_AB'];assert T['tea_table']['shift_north_mm']==0
assert Q['options']['A']['rail_hanger_channel_wall_overlap_mm2']<1
assert sha(L['freecad'])==L['freecad_sha256']
PRE=json.loads((OUT/'RESTORED_STATE_MANIFEST.json').read_text());assert sha(PRE['model'])==PRE['model_sha256']
QA=json.loads((OUT/'A_FRESH_OPEN_QA.json').read_text())
images=json.loads((OUT/'REVIEW_IMAGE_MANIFEST.json').read_text())['images']
for row in images:assert sha(row['path'])==row['sha256']
body=f'''# R3 修订与对比 · 2026-10-02

本轮按最后的明确指示，先撤回后来补建的斜门及门框、门套、门上墙、侧墙和转角连接，恢复到补门以前的开放状态，再按最新 FreeCAD 建完整西侧隔断。后加围合墙的七组来源已从活动墙壳中移除；原始黑色实墙没有打拆。固定基础文件和厨房冻结包完整保留，R3 是独立审阅分支。

书房采用参考图的自然木色和格架关系：长茶台后方是书柜，旁边低柜改成专用茶水台，带水槽、龙头、给排水示意、独立电热煮茶位及收纳。用户已选择保持 FreeCAD 家具位置；长茶台没有北移。

## 先看这几张图

- {link('撤回斜门 → 新建西墙，同角度顺序图',OUT/'renders/WEST_WALL_RESTORE_SEQUENCE.png')}
- {link('A/B 同角度模型对比',OUT/'renders/AB_MODEL_COMPARISON.png')}
- {link('A/B 同尺度平面和尺寸',OUT/'renders/AB_PLAN_COMPARISON.png')}
- {link('书房木色格架与茶水台功能',OUT/'renders/STUDY_STYLE_AND_FUNCTION.png')}

## 模型文件

| 状态 | 文件 | 用途 |
|---|---|---|
| 撤回围合、未建新西墙的中间状态 | {link('RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend',PRE['model'])} | 核对恢复顺序；原浴室家具尚未替换 |
| A：南侧推拉门 | {link('OPTION_A_SLIDING_R3.blend',M['A']['model'])} | 当前推荐比较分支，包含最新浴室布局和书房修订 |
| B：南侧向内平开门 | {link('OPTION_B_INWARD_R3.blend',M['B']['model'])} | 同一入口、同一洁具位置，包含相同书房修订 |

两案时间轴 1 帧为关闭、100 帧为开启。完整模型包含真实完整墙体；内部剖视仅在出图时临时剖切，不写回模型。原始来源对象隐藏保存，便于追溯；活动场景内已没有后加斜门和围合墙。

## A/B 取舍

| 比较项 | A 推拉门 | B 向内开门 |
|---|---|---|
| 南侧入口 | 衣柜西侧可达位置 | 与 A 相同 |
| 门扇收纳 / 开启 | 向东收入南侧墙后、衣柜背后的隐藏段 | 西侧铰链向内约85°，设置门挡 |
| 墙体、门套、门上墙 | 完整，轨道贯穿门洞及收入段，吊轮有连续净空 | 完整，有三处铰链和限位门挡 |
| 室内开门回转 | 0 | 含把手约 {Q['options']['B']['indoor_swing_area_m2']:.3f} m² |
| 门扇与墙 / 台盆 / 马桶 / 淋浴 | 本轮运动检查通过 | 721 个角度采样通过；避免把手在90°时碰西墙 |
| 马桶前操作区（深800×宽600示意） | 门运动和实体墙不占用 | 门运动和实体墙不占用 |

推荐 A：在现有小空间中，推拉门保留内部操作面积，入口可达，隐藏段与衣柜关系正确。B 可作为密封和构造取舍的备选；本版使用85°限位。

## 最新布局依据

源文件为 {link('世纪欣园FF_freecad_WORKING.FCStd',L['freecad'])}，实际读取 Shape.BoundBox 与 Shape.Vertexes；哈希 `{L['freecad_sha256']}`。坐标换算为 x=FreeCAD x−1298172、y=FreeCAD y+296458（mm）。

| 部件 | 当前坐标包络 mm | 实施 |
|---|---|---|
| 西墙 Rectangle054 | x9059–9209，y4507.25–6507.25 | 完整150mm直墙；没有避让凹口 |
| 南侧补墙 Rectangle067 | x9988.125–10738.125，y4523.9375–4673.9375 | 保留原补墙关系，并闭合至既有东侧墙，浴室内侧连续齐平 |
| 台盆 Rectangle068 | x9228–10428，y5925.219–6425.219 | 西北侧1200×500 |
| 马桶 Rectangle061 | x10763.75–11363.75，y4935.531–5435.531 | 东南侧，朝西 |
| 淋浴 Wire | 东北角切角屏风轮廓 | 保留切角，托盘靠既有东、北墙闭合 |
| 外侧衣柜 Rectangle066 | x9972.25–11372.25，y3908.094–4508.094 | 1400×600；入口在其西侧 |

两案浴室和衣柜包络完全一致，已对照独立重开的实际网格。1200×100 的推拉示意矩形作为装配参考登记，不能当作1200mm净门宽。墙间毛口约779mm，本版两边示意门框各25mm，净通行约729mm；完整轨道约1.57m。

## 书房造型和功能

| 部件 | 保留位置 / 尺寸 | 当前模型 |
|---|---|---|
| 书柜 Rectangle024 | 4200×450，高2000，位于长茶台后方东侧 | 开放木色格架、少量书籍，原包络保留 |
| 长茶台 Rectangle026 | 2200×800，高750，位置不变 | 木色长台和细木格条收边 |
| 原矮书柜 Rectangle025 | 1600×450，高900，位置不变 | 改为专用茶水台、封闭下柜；350×280水槽和350×300煮茶位 |
| 主人椅 / 条凳 | 原家具位置保留 | 主人椅改为朝茶台的木格背造型，条凳木色统一 |

茶水台模型具有台面开孔、水槽、龙头、排水弯管、给水管及待确认接点。锅具、加热板和干区电源接点用于表达煮茶功能；管道去向和电源安装未按现场放行。原打印机 / NAS 占位没有继续放在新湿操作台上。

原茶台与茶水台之间净距约297mm。用户明确要求本轮保留 FreeCAD 位置，故没有借造型调整家具位置；此间距不能作为舒适站立操作通道的确认。

## 校验与后续尺寸

独立重开 A/B，各核对1244个原对象状态；厨房原对象和冻结文件哈希保留。新增隔断、局部撤回后的墙壳均为闭合索引网格，边界边和非流形边均为0。局部撤回区外4405处原墙面采样复核，最大测得偏差约{QA['unrelated_wall_max_deviation_mm']:.3f}mm；长而薄的水平三角面采用双精度复核，避免单精度最近点误报。

- {link('门运动、墙体闭合和 FreeCAD 包络校验',OUT/'CLEARANCE_QA.json')}
- {link('A 独立重开和书房位置校验',OUT/'A_FRESH_OPEN_QA.json')}
- {link('B 独立重开和书房位置校验',OUT/'B_FRESH_OPEN_QA.json')}
- {link('斜门围合撤回来源',OUT/'D107_ROLLBACK_REGISTER.json')}
- {link('书房功能登记',OUT/'STUDY_TEA_REGISTER.json')}

当前属于几何、造型和功能审阅，尚未施工放行。约729mm净入口和门框截面要复尺、选型；切角淋浴托盘约842×785mm、面积约0.619m²，切角段约418mm，不能直接把这段当作已确认的淋浴净门宽。淋浴门形式、洁具 SKU、给排水、墙体构造和电源点位仍需下一阶段确认。书房本轮仅更新造型和功能，保留用户选择的既有位置。

所有生成图保存在项目文件系统，以路径交付。Workbench1800×1400、32级抗锯齿、Standard色彩管理；简单审阅材质，未做最终材料和光照。旧根目录 A/B 及 R2 为历史候选，不能作为本轮最终结果使用。
'''
(OUT/'R3_REVIEW.md').write_text(body)
index='\n'.join(['# 当前交付：R3', '', '按最新 FreeCAD 布局、明确撤回后加斜门围合、书房低茶水台功能修订。旧 A/B 和 R2 已被本轮修订替代。', '', link('完整修订说明与所有路径',OUT/'R3_REVIEW.md'),''])
(PARENT/'CURRENT_REVIEW.md').write_text(index)
for name in ['OPTION_SPEC.md','OPTION_COMPARISON.md','DELIVERY_MANIFEST.json']:
 p=PARENT/name
 hist=PARENT/(p.stem+'_HISTORICAL_R1'+p.suffix)
 if p.exists() and not hist.exists():shutil.copy2(p,hist)
(PARENT/'OPTION_SPEC.md').write_text(index+'\n两案保持最新西北台盆、东北切角淋浴、东南马桶和南侧衣柜布局；入口位于衣柜西侧。西墙按 Rectangle054 完整建设。先在活动模型撤回后加斜门及围合，再建西墙；冻结基础文件保留。\n')
(PARENT/'OPTION_COMPARISON.md').write_text(index+'\n推荐 A 推拉门；B 内开85°、含把手回转约0.423m²。两案保持相同净入口、洁具位置和书房修订。\n')
state='''# Work state R3

Completed: explicit removal of added D107 leaf/frame/casings AND seven added surround wall operands from active branch geometry; separately saved the restored open state before bathroom construction. Frozen V2 file and kitchen freeze remain preserved. The source outside the rollback box retains the approved baked surfaces; original black wall operands retained.

Completed: A/B rebuilt with full FreeCAD west rectangle, accessible southwest entrance, east sliding storage, complete flush south closure, latest NW vanity/NE chamfer shower/SE WC/wardrobe. A track and hanger channel continuous; B west-hinged inward85deg floor stop. Actual mesh QA and fresh-open QA PASS. Models have CLOSED frame1 / OPEN frame100.

Completed: study uses natural wood long tea table and rear open bookcase; old low bookcase replaced by wet/boiling tea-service counter. User explicitly chose original FreeCAD positions. No350mm north table move. Keep297mm counter/table gap as a documented real-use limitation. Study group is Rectangle024/025/026 in the historical R-BED-N furniture register, not the other room also historically labeled R-STUDY.

Authority: R3_REVIEW.md, LAYOUT_CONTRACT.json, D107_ROLLBACK_REGISTER.json, STUDY_TEA_REGISTER.json, OPTION_A_MANIFEST.json and OPTION_B_MANIFEST.json. Earlier root A/B and R2 are obsolete for this decision. The restored pre-bath state is an intermediate, not a selected final bathroom.

Remaining design decisions: user choice A/B (A recommended), exact entrance/frame profiles, cramped shower entry/glass configuration, sanitary SKU/drainage/partition build-ups; tea-counter feed/drain/power connections. No construction release or final material/lighting approval. All images paths only; bounded proxies for inspection.
'''
(OUT/'work_state.md').write_text(state)
deliver=dict(status='R3_MODELS_AND_REVIEW_READY',stage='GEOMETRY_STYLE_FUNCTION_REVIEW',recommended_option='A',models={o:M[o]['model'] for o in 'AB'},restored_state=PRE['model'],review=str(OUT/'R3_REVIEW.md'),study_positions='PRESERVED_BY_EXPLICIT_USER_CHOICE',context_policy='FILESYSTEM_PATHS_ONLY',base_sha256=M['A']['base_sha256'],freecad_sha256=L['freecad_sha256'])
 paths=[OUT/'R3_REVIEW.md',OUT/'LAYOUT_CONTRACT.json',OUT/'STUDY_TEA_REGISTER.json',OUT/'CLEARANCE_QA.json',OUT/'A_FRESH_OPEN_QA.json',OUT/'B_FRESH_OPEN_QA.json',Path(PRE['model']),*[Path(M[o]['model']) for o in 'AB'],*[Path(i['path']) for i in images]]
deliver['files_sha256']={str(p):sha(p) for p in paths}
(OUT/'DELIVERY_MANIFEST.json').write_text(json.dumps(deliver,ensure_ascii=False,indent=2)+'\n')
(PARENT/'DELIVERY_MANIFEST.json').write_text(json.dumps(dict(current=str(OUT/'DELIVERY_MANIFEST.json'),review=str(OUT/'R3_REVIEW.md'),revision='R3',status='REVIEW_READY'),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(delivery='PASS',revision='R3',files=len(paths),review=str(OUT/'R3_REVIEW.md'),models=deliver['models']),ensure_ascii=False))
