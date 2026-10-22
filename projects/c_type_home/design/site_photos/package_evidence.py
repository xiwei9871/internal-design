"""Current-site relationships and failed/conditional camera evidence, without invented dimensions."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import hashlib
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def font(n):return ImageFont.truetype(FONT,n)
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
report=read(OUT/'PHOTO_REGISTRATION_REPORT.json')
facts=[]
def fact(id_,typ,photos,relation,b0,b1,category='DESIGN_RELEVANT_GEOMETRY',status='PHOTO_CONFIRMED'):
    facts.append(dict(detail_id=id_,room='KITCHEN_AND_ADJACENT',semantic_type=typ,
        source_photos=[f'SITE_PHOTO_KITCHEN_{n:03d}' for n in photos],
        related_B0_objects=b0,related_B1_objects=b1,authority=status,classification=category,
        observed_relationship=relation,dimensional_authority='TO_VERIFY_UNLESS_HUMAN_CONFIRMED_REFERENCE',
        global_B0_coordinate_mapping='NOT_YET_METRIC_ACCEPTED'))
fact('K-SITE-01','FRIDGE_LEFT_TALL_STORAGE',[1],
     '冰箱左侧存在直达可见木质顶面的窄高柜，分段门面；B1 的 935 mm 宽服务柜形态不对应此窄柜。',[ 'FLOOR_LOWER'],['B11_K-TALL-L'])
fact('K-SITE-02','FRIDGE_OVERHEAD_WITH_GAP',[1,2],
     '冰箱上方有吊柜；冰箱顶与柜底之间保留开放空隙，不能直接接成实体高柜。',['FLOOR_LOWER'],['B11_K-FRIDGE-OVERHEAD'])
fact('K-SITE-03','MICROWAVE_RISER_SHELF',[1,2],
     '冰箱与长台面转角附近有架高的微波炉承台/开放架；具体宽、深、标高待核。',['W_wall_md_0015'],['B11_K-TALL-L','B11_K-RUN-E'])
fact('K-SITE-04','UPPER_CABINET_RUN',[2,3],
     '长边为连续封闭吊柜，顶部另有收口带；柜门分缝与旧 B1 等分通用门板不同。',['W_wall_md_0015'],['B11_K-WALL-E'])
fact('K-SITE-05','VERTICAL_HOOD_ASSEMBLY',[2,3],
     '灶具上方存在较高的竖向烟机面板和下部金属集烟体；B1 的薄横块不足以表达实际轮廓。',['W_wall_md_0015'],['B11_K-COOK_HOOD_REVIEW'])
fact('K-SITE-06','DRAWER_STACK_UNDER_HOB',[3,4],
     '灶具下方为宽抽屉组；完整层数与各层高度待确认，不能按均匀门板替代。',[],['B11_K-RUN-E'])
fact('K-SITE-07','DISHWASHER_ORDER',[3,4,5],
     '照片中黑色洗碗机位于灶具右侧、靠水槽方向；物理先后关系可确认，当前 CAD y 位置仍需注册。',[],['B11_K-DISHW'])
fact('K-SITE-08','OPEN_DISPLAY_RECESS',[3,4],
     '烟机右侧吊柜下方有横向开放展示凹格。', ['W_wall_md_0015'],['B11_K-WALL-E'])
fact('K-SITE-09','WALL_BRACKET_GLASS_SHELF',[3,4],
     '开放凹格下面另有墙托玻璃置物板；它是收纳构件，不是窗口或玻璃隔墙。', ['W_wall_md_0015'],[])
fact('K-SITE-10','SINK_AT_WINDOW',[4,5],
     '水槽位于窗前，周围台面形成转角；人物和设备遮挡部分窗框/台面角，不能把隐蔽边缘当可靠定位点。', ['GLZ_W-KIT-S'],['B11_K-SINK'])
fact('K-SITE-11','WINDOW_ADJACENT_UTILITY_APPLIANCE',[4,5],
     '窗边有白色壁挂设备、外露软管/连接管；具体设备型号和 MEP 接点待核。', ['GLZ_W-KIT-S'],[])
fact('K-SITE-12','SINK_SIDE_OPEN_RACK',[5],
     '水槽右侧、柱/墙侧有多层开放架。', ['W_wall_md_0009'],[])
fact('K-SITE-13','COLUMN_SIDE_RETURN_COUNTER',[4,5],
     '柱/墙侧有回转矮柜和浅色台面，外端有圆角；其与厨房、木地板相邻区的关系可见。不是独立中岛。', ['W_wall_md_0009'],[])
fact('K-SITE-14','ADJACENT_TALL_DRAWER_STORAGE',[4,5],
     '柱另一侧、邻窗处存在上部高门和下部抽屉组合；是否对应现有阳台柜或改造新增，待用户确认。', ['W_wall_md_0009','GLZ_W-LBALC-S'],['B11_Rectangle029','B11_Rectangle032'])
fact('K-SITE-15','WINDOW_SIDE_BUFFET_ASSEMBLY',[6],
     '另一窗边柜为上部封闭门、中部开放台面、抽屉带和下部封闭柜；不能直接套为整块矮柜。R029/R032 的对应关系尚未确认。', ['GLZ_W-LBALC-S'],['B11_Rectangle029','B11_Rectangle032'])
fact('K-SITE-16','SLOPING_WOOD_FINISH_PROFILE',[1,2,3,4,5,6],
     '可见木质斜顶、转折/脊线和横向构件；是否为结构斜顶还是下挂装饰面未证明。实际高点/低点与 B0 水平吊顶 datum 的关系需核验。', ['CEILING_LOWER'],[],category='EXISTING_FINISH',status='POSSIBLE_B0_CONFLICT')
fact('K-SITE-17','CLUTTER_AND_DECOR_REFERENCE',[1,2,3,4,5,6],
     '台面器物、照片、人物、餐椅、灯和木纹只作现场参考；本阶段不复制生活杂物或制作最终材质/灯光。',[],[],category='EXISTING_FURNITURE')
(OUT/'SITE_DETAIL_REGISTER_V01.json').write_text(json.dumps(dict(register='SITE_DETAIL_REGISTER_V01',
    facts=facts,scope='CURRENT_KITCHEN_PHOTOGRAPHED_DETAILS',correction_status='PENDING_REGISTRATION_AND_HUMAN_DIMENSION_GATE'),ensure_ascii=False,indent=2))

known=report['confirmed_current_reference_dimensions']
needs=[('K-SITE-01','窄高柜宽度、深度、顶面标高及其相对北墙/门框位置'),
       ('K-SITE-02','冰箱上柜底标高、柜深、左右分隔'),
       ('K-SITE-03','微波炉架宽/深及承台标高'),
       ('K-SITE-04','吊柜门分缝、柜底/顶收口标高'),
       ('K-SITE-05','烟机实际外轮廓尺寸和安装标高'),
       ('K-SITE-08','开放展示凹格宽/深/高及其左右位置'),
       ('K-SITE-09','玻璃板宽/深和标高'),
       ('K-SITE-12','水槽侧开放架宽/深/高'),
       ('K-SITE-13','回转矮柜沿柱的长度、深度、外伸边界和圆角半径'),
       ('K-SITE-14','邻窗高门/抽屉柜尺寸与 CAD 对应关系'),
       ('K-SITE-15','窗边餐边柜尺寸与 CAD 对应关系'),
       ('K-SITE-16','斜顶高点/低点/坡向和横向构件尺寸')]
estimates=dict(register='SITE_DIMENSION_ESTIMATES_V01',metric_gate='NOT_PASSED',
    current_human_confirmed_reference=known,accepted_photo_estimates=[],
    items=[dict(detail_id=id_,requested_dimension=description,estimated_mm=None,uncertainty_mm=None,
                confidence='NOT_METRIC_ACCEPTED',authority='TO_VERIFY',
                reason='Global camera registration is LOW/FAILED; no millimetre output is authorized.',
                source_photos=next(f['source_photos'] for f in facts if f['detail_id']==id_)) for id_,description in needs])
(OUT/'SITE_DIMENSION_ESTIMATES_V01.json').write_text(json.dumps(estimates,ensure_ascii=False,indent=2))

for r in report['photos']:
    name=r['photo_id'];photo=Image.open(OUT/'previews'/f'{name}.png').convert('RGB')
    model=Image.open(OUT/f'MODEL_REG_{name}.png').convert('RGBA')
    back=Image.new('RGBA',photo.size,'#e3e7e9');render=Image.alpha_composite(back,model).convert('RGB')
    overlay=Image.blend(photo,render,.5)
    w,h=photo.size;page=Image.new('RGB',(w*3,h+155),'#f6f8f9');draw=ImageDraw.Draw(page)
    titles=['现场照片 / SITE','当前 B1 + 相机候选 / MODEL','50% overlay · 未通过注册']
    for n,im in enumerate([photo,render,overlay]):
        page.paste(im,(n*w,115));draw.text((n*w+20,67),titles[n],font=font(25),fill='#334a58')
    draw.text((20,13),f"{name} · {r['confidence']} · 禁止用于毫米级估尺寸",font=font(31),fill='#a3483d')
    err='N/A（可靠对应不足）' if r['mean_reprojection_error_px'] is None else f"mean {r['mean_reprojection_error_px']:.1f} / max {r['max_reprojection_error_px']:.1f} px (original image)"
    draw.text((20,h+122),f"候选点 {r['anchor_count']}；{err}；B0/B1 几何未移动。",font=font(23),fill='#586b75')
    page.save(OUT/f'PHOTO_REG_{name}.png')
boards=[]
for r in report['photos']:
    im=Image.open(OUT/f"PHOTO_REG_{r['photo_id']}.png");im.thumbnail((1800,680));boards.append(im.copy())
sheet=Image.new('RGB',(1800,sum(im.height+18 for im in boards)),'#d7e0e6');y=0
for im in boards:sheet.paste(im,(0,y));y+=im.height+18
sheet.save(OUT/'KITCHEN_SITE_COMPARE.png')

# Annotate physical facts on photographs without claiming current CAD coordinates.
callouts={
1:[((.28,.14),'A 冰箱左窄高柜：柜宽/改造身份待核'),((.49,.15),'冰箱上柜 + 柜底空隙'),((.73,.33),'微波炉承台位于转角')],
3:[((.52,.12),'连续吊柜 + 顶部收口'),((.37,.47),'竖向烟机面板'),((.64,.51),'B 开放展示凹格'),((.62,.64),'墙托玻璃板'),((.4,.84),'灶下宽抽屉组'),((.76,.82),'洗碗机靠水槽侧')],
5:[((.56,.43),'水槽侧多层开放架'),((.36,.22),'窗边壁挂设备/管线'),((.67,.6),'C 沿柱回转矮柜 + 圆角台面')],
6:[((.44,.48),'D 上柜 / 开放台面 / 抽屉 / 下柜'),((.40,.20),'木质斜顶：层高关系待核')]}
for n,labels in callouts.items():
    name=f'SITE_PHOTO_KITCHEN_{n:03d}';im=Image.open(OUT/'previews'/f'{name}.png').convert('RGB');draw=ImageDraw.Draw(im)
    for (u,v),label in labels:
        x=int(u*im.width);y=int(v*im.height);bbox=draw.textbbox((x,y),label,font=font(20))
        x=min(x,max(6,im.width-(bbox[2]-bbox[0])-14));y=min(y,im.height-40)
        bbox=draw.textbbox((x,y),label,font=font(20));draw.rounded_rectangle((bbox[0]-6,bbox[1]-6,bbox[2]+6,bbox[3]+6),radius=5,fill='#f3f5f6',outline='#ac5a43',width=2)
        draw.text((x,y),label,font=font(20),fill='#623d31')
    im.save(OUT/f'SITE_DETAIL_ANNOTATED_{n:03d}.png')

manifest=read(ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json')
frozen=[dict(key=k,path=manifest['files'][k],match=sha(ROOT/manifest['files'][k])==v) for k,v in manifest['sha256'].items()]
assert all(i['match'] for i in frozen)
md='''# Kitchen site evidence — registration review

当前状态：`B1_SITE_CORRECTION = HUMAN_REVIEW`；**几何修正未实施**，相机注册的 metric gate 未通过。

用户确认：改造后台面 H/D = 820/600 mm，冰箱 W/D/H = 905/710/1700 mm。旧柜体 PDF 是初始安装资料；现状构造以此次现场照片为依据。冻结 B0 仍是建筑坐标权威。

六张原图已保留、记录 SHA256，建立六个 `SITE_CAM_KITCHEN_*` 相机和背景参考。原图未包含可用焦距 EXIF。已使用已知尺寸尝试 pinhole camera pose/focal fitting，并检查误差；未移动 B0 或现有 B1 柜体来凑照片。

## 阅读证据

- [照片联系表](SITE_PHOTO_CONTACT_SHEET.png)
- [全部现场 / 模型 / 叠加对比](KITCHEN_SITE_COMPARE.png)
- [A 冰箱与高柜标注](SITE_DETAIL_ANNOTATED_001.png)
- [B 长柜 / 烟机 / 开放格标注](SITE_DETAIL_ANNOTATED_003.png)
- [C 窗前和回转矮柜标注](SITE_DETAIL_ANNOTATED_005.png)
- [D 邻窗柜标注](SITE_DETAIL_ANNOTATED_006.png)
- [相机审阅文件](B1_1_SITE_REGISTERED_V1.blend)
- [注册报告](PHOTO_REGISTRATION_REPORT.json) · [构造事实](SITE_DETAIL_REGISTER_V01.json) · [尺寸门槛](SITE_DIMENSION_ESTIMATES_V01.json)

## 已确认的形状与关系

冰箱左侧为窄高柜；冰箱上柜和冰箱之间有空隙；转角存在微波炉承台；烟机有竖向面板和下部集烟体；灶下为宽抽屉组；烟机右侧有开放展示凹格、其下另有墙托玻璃板；水槽侧有开放架；柱侧存在回转矮柜与圆角台面。邻窗还有高门/抽屉柜，以及照片 6 的上柜—开放台面—抽屉—下柜组合。

这些是 `PHOTO_CONFIRMED` 构造关系。它们不自动给出安装坐标或毫米尺寸。台面器物、人物、照片、灯、木纹等只是现状参考，不复制成最终方案。

## 注册结果及限度

| 照片 | 候选点 | 原分辨率 mean / max px | 判定 |
|---|---:|---|---|
'''
for r in report['photos']:
    err='N/A' if r['mean_reprojection_error_px'] is None else f"{r['mean_reprojection_error_px']:.1f} / {r['max_reprojection_error_px']:.1f}"
    md+=f"| {r['photo_id'][-3:]} | {r['anchor_count']} | {err} | {r['confidence']} |\n"
md+='''
照片 1 的六个冰箱参考点可以局部拟合；原分辨率 mean 17.4 px / max 31.2 px。但该相机对相邻门框的候选投影偏差很大，说明局部商品拟合不能证明整屋定位。六点同面，冰箱改造后绝对位置又未实测；全局等级必须降为 LOW。门框对应本身也需核验，不能据此断言 B0 有错。

照片 3 使用初始柜位/烟机边作为候选，出现较大残差且求解触及参数边界；这些修改后的柜体不能直接充当可靠旧图锚点。照片 4/5 的窗角受设备、人物和裁切遮挡；照片 6 的柜体 ID 尚不能对应到 R029/R032。未核实的候选点不计入已验证建筑 XY 锚点。

附件要求 **“LOW / FAILED 不允许用于毫米级尺寸推算”**，并要求 **“人工确认关键估值 → 修改 B1”**。本轮遵守这两个门槛：尺寸登记没有虚构数值；只输出相机/证据审阅文件，尚未生成冒称已修正的 `B1_1_SITE_CORRECTED_V1.blend`。

## 下一步需要确认

先明确改造范围，才能区分“旧图仍适用的锚点”和“已改动的柜体”。请确认 A（照片 1 冰箱左窄高柜）、B（照片 3 开放凹格/玻璃板）、C（照片 4/5 柱侧回转台）、D（照片 6 窗边柜）哪些新增、哪些原有；若已知柜宽/长/深，也可直接填入。未知尺寸仍保留 TO_VERIFY。

现状照片可见木质斜顶，但它可能是装饰层，不能证明结构屋顶改变。其高点/低点与冻结水平吊顶体块的关系列 `POSSIBLE_B0_CONFLICT / REPORT ONLY`；不改 B0 datum，不推导梁高或坡度。

完成可靠世界坐标定位和必要尺寸确认后，才另存修正后的 B1；使用这些同名相机重新做现场 / 模型 / overlay 比较。当前 B0 SHA256 7/7 MATCH，B1 原候选保持原样。其他房间未提供照片，本轮不生成假对比图。
'''
(OUT/'SITE_CORRECTION_REPORT.md').write_text(md)
(OUT/'SITE_EVIDENCE_QA.json').write_text(json.dumps(dict(state='B1_SITE_CORRECTION = HUMAN_REVIEW',
    photo_count=6,site_camera_count=6,B0_INTEGRITY='PASS',frozen_checks=frozen,
    metric_gate='NOT_PASSED',geometry_correction_applied=False,
    accepted_photo_estimate_count=0,photo_confirmed_relationship_count=16,
    original_b1_sha256=sha(ROOT/'design/blender_b1_1/B1_1_DESIGN_MODEL_V1.blend'),
    registered_scene_sha256=sha(OUT/'B1_1_SITE_REGISTERED_V1.blend'),
    generated_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()),ensure_ascii=False,indent=2))
print(json.dumps({'state':'HUMAN_REVIEW','B0_INTEGRITY':'PASS','metric_gate':'NOT_PASSED',
                  'fact_count':len(facts),'accepted_photo_estimates':0,'report':str(OUT/'SITE_CORRECTION_REPORT.md')},ensure_ascii=False,indent=2))
