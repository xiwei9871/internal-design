"""Label review views and build a traceable HUMAN_REVIEW package."""
from pathlib import Path
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def font(size):return ImageFont.truetype(FONT,size)
def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

LABELS={
 'TOP':('全屋俯视 / TOP','LOWER FFL 0 mm · UPPER FFL +450 mm · 3 × 150 mm stairs'),
 'AXON':('全屋轴测 / AXON','58 furniture/cabinet entries · 4 bay assemblies · frozen architecture preserved'),
 'LIVING':('客厅 / LIVING','沙发 2300 × 900 / 1900 × 850；茶几 550 × 1000；贵妃椅方向与电视柜候选待复核'),
 'KITCHEN':('厨房 / KITCHEN','PDF：台面 820；地柜深 600；吊柜深 380；总高 2410；冰箱 905 × 710 × 1700 mm'),
 'LEISURE':('扇形休闲厅 / LEISURE','Existing UPPER +450 mm · CAD r1000 curve · step tops 150 / 300 / 450 mm'),
 'OWNER_BED':('主人卧室 / OWNER BED','R-BED-S：床 2100 × 1500 × 550；衣柜 1500 × 600 × 2200 mm；FFL +450'),
 'MOTHER_BED':('母亲卧室 / MOTHER BED','R-MASTER：床 2100 × 1500 × 550；衣柜 2100 × 600 × 2200 mm；FFL +450'),
 'STUDY':('书房 / STUDY','R-BED-N：书柜 450 × 4200 × 2000；工作台 800 × 2200 × 750 mm；主人椅方向待决'),
 'GUEST_BED':('客卧与窄书桌 / GUEST BED','R-STUDY：床 1800 × 1200 × 550；窄书桌 350 × 1650 × 750 mm'),
 'BATH_OWNER':('主人卫生间 / OWNER BATH','台盆朝北；WC 朝南；湿区约 823 × 1547；淋浴屏高 2000 mm 为审阅值'),
 'BATH_MOTHER':('母亲卫生间 / MOTHER BATH','台盆朝向冲突待决；WC 朝南；湿区约 1000 × 1522；FFL +450'),
 'BATH_GUEST':('公卫 / GUEST BATH','台盆朝向冲突待决；WC 朝东；湿区约 1644 × 813；3 kg 洗衣机安装高度待决')}

def label_view(name):
    raw=OUT/f'RAW_B1_1_{name}.png'
    assert raw.is_file(),f'Missing review image {raw.name}'
    picture=Image.open(raw).convert('RGB');w,h=picture.size
    page=Image.new('RGB',(w,h+230),'#f7f8f9');page.paste(picture,(0,145))
    draw=ImageDraw.Draw(page)
    draw.text((38,20),'B1.1  DESIGN MODEL  ·  HUMAN_REVIEW',font=font(30),fill='#263941')
    draw.text((38,60),LABELS[name][0],font=font(32),fill='#263941')
    draw.text((38,108),LABELS[name][1],font=font(21),fill='#54616a')
    draw.text((38,h+158),'尺寸审阅剖切图：墙体临时降低；吊顶和玻璃面暂隐；所有原对象保留在 .blend。',font=font(21),fill='#56626b')
    draw.text((38,h+193),'蓝灰地面 = LOWER 0  /  米色地面 = UPPER +450  /  红色 = DESIGN_DECISION_REQUIRED',font=font(21),fill='#56626b')
    if name=='TOP':
        # TOP camera world span is 22 m horizontally with a 4:3 frame.
        def project(x,y):return (w/2+(x-8.9)*w/22,145+h/2-(y-6.6)*w/22)
        labels=[('客厅 · 0',(5.35,11.5)),('餐厅 · 0',(4.6,2.1)),('厨房 · 0',(6.9,1.05)),
                ('休闲厅 · +450',(6.65,5.45)),('主人卧室',(9.7,3.30)),('母亲卧室',(13.8,3.35)),
                ('主人卫',(9.7,5.55)),('母亲卫',(14.2,4.9)),('公卫',(8.85,8.0)),
                ('客卧',(11.4,10.6)),('书房',(14.6,10.2))]
        for title,(x,y) in labels:
            px,py=project(x,y);bb=draw.textbbox((px,py),title,font=font(22));pad=7
            draw.rounded_rectangle((bb[0]-pad,bb[1]-pad,bb[2]+pad,bb[3]+pad),radius=7,fill='#f7f8f9',outline='#c7cfd4')
            draw.text((px,py),title,font=font(22),fill='#263941')
        draw.text((w-155,150),'N ↑',font=font(32),fill='#263941')
    destination=OUT/f'B1_1_{name}.png';page.save(destination)
    return destination

for name in LABELS:label_view(name)
panels=[]
for name in ['BATH_OWNER','BATH_MOTHER','BATH_GUEST']:
    im=Image.open(OUT/f'B1_1_{name}.png').convert('RGB');im.thumbnail((860,780));panels.append(im)
sheet=Image.new('RGB',(2700,900),'#f7f8f9');draw=ImageDraw.Draw(sheet)
draw.text((40,22),'B1.1 · 三个卫生间 / BATHROOMS · HUMAN_REVIEW',font=font(36),fill='#263941')
for n,im in enumerate(panels):sheet.paste(im,(25+900*n,85))
draw.text((40,848),'两处台盆方向、淋浴 SKU / 开启方式、给排水位置、洗衣机挂墙高度需确认；图中保留原布局。',font=font(27),fill='#89564e')
sheet.save(OUT/'B1_1_BATHROOMS_CONTACT_SHEET.png')

# Compact complete review index. This supports visual inspection, not a final render.
order=['TOP','AXON','LIVING','KITCHEN','LEISURE','OWNER_BED','MOTHER_BED','STUDY','GUEST_BED','BATH_OWNER','BATH_MOTHER','BATH_GUEST']
board=Image.new('RGB',(2400,4*710),'#dbe0e4')
for n,name in enumerate(order):
    im=Image.open(OUT/f'B1_1_{name}.png').convert('RGB');im.thumbnail((780,695))
    board.paste(im,((n%3)*800+10,(n//3)*710+5))
board.save(OUT/'B1_1_REVIEW_CONTACT_SHEET.png')

validation=read(OUT/'B1_1_FRESH_OPEN_VALIDATION.json')
register=read(OUT/'B1_1_ASSET_REGISTER.json')
manifest=read(ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json')
frozen=[dict(key=k,path=manifest['files'][k],expected=v,actual=digest(ROOT/manifest['files'][k])) for k,v in manifest['sha256'].items()]
assert all(r['expected']==r['actual'] for r in frozen),'B0_INTEGRITY = FAIL; stop packaging'
required=['B1_1_DESIGN_MODEL_V1.blend','B1_1_TOP.png','B1_1_AXON.png','B1_1_LIVING.png','B1_1_KITCHEN.png',
          'B1_1_LEISURE.png','B1_1_OWNER_BED.png','B1_1_MOTHER_BED.png','B1_1_STUDY.png',
          'B1_1_BATHROOMS_CONTACT_SHEET.png','B1_1_ASSET_REGISTER.json','KITCHEN_CABINET_3D_REGISTER_V01.json']
assert all((OUT/p).is_file() for p in required),'Missing contracted output'
assert digest(OUT/'B1_1_DESIGN_MODEL_V1.blend')==validation['model_sha256'],'Candidate changed since fresh-open validation'
time=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
qa=dict(stage='B1.1',B1_1_DESIGN_MODEL='HUMAN_REVIEW',generated_at=time,
        B0_INTEGRITY='PASS',frozen_sha256=frozen,
        model_sha256=validation['model_sha256'],
        numeric_gates=dict(status='PASS',inherited_objects_preserved=validation['inherited_objects_preserved'],
            measured_furniture_cabinet_envelopes=len(validation['furniture_envelopes']),
            max_envelope_error_mm=max(c['max_bounds_error_mm'] for c in validation['furniture_envelopes']),
            envelope_tolerance_mm=1,front_vector_checks=len(validation['orientation_checks']),
            evaluated_new_triangles=validation['evaluated_new_triangles'],finite_coordinates=True,
            inherited_openings=9,D107_angle_deg=26.3,review_bay_assemblies=4,
            source_geometry_signatures='MATCH',source_authored_transforms='MATCH'),
        technical_check_scope='Declared integrity, envelope and authored-direction checks; does not approve products or unresolved designs.',
        visual_review=dict(status='PENDING_AGENT_IMAGE_INSPECTION',required_views=order,
                           render_manifest='B1_1_RENDER_MANIFEST.json',cutaway=True,
                           glass_faces_hidden=True,ceiling_hidden=True,
                           annotation='Temporary presentation cuts only, never saved to blend'),
        coverage=dict(kitchen='PDF_DIMENSIONAL_REVIEW; module splits/install positions pending',
                      bathrooms='THREE_LAYOUTS; two vanity direction proxies; plumbing/SKU pending',
                      shower='THREE_2000mm_REVIEW_SCREENS; exact mechanism/SKU pending',
                      storage='EDITABLE_DIMENSIONAL_CARCASSES',core_furniture='CALIBRATED_LOCAL_ASSETS',
                      openings='NINE_GLAZED_OPENING_FRAMES_AND_D107_HARDWARE',
                      bay='FOUR_ASSEMBLIES; frozen-front interference report-only',
                      split_level='INHERITED_DATUM_AND_CURVE; in-datum review finishing',
                      ceiling='EXACT_INHERITED_BLOCKOUT; coffers/light slots pending'),
        decisions_required=register['decisions_required'],
        not_checked=['commercial SKU fidelity','MEP routing/installation','unconfirmed fixture support heights',
                     'door swing/code or accessibility compliance','delivery path','final materials/lighting',
                     'construction certification','GLB/web export (outside requested scope)'],
        output_files=[dict(path=p,bytes=(OUT/p).stat().st_size,sha256=digest(OUT/p)) for p in required])
(OUT/'B1_1_QA_REPORT.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))

md=f'''# B1.1 Design Model — HUMAN_REVIEW

`B1_1_DESIGN_MODEL = HUMAN_REVIEW`。本轮交付可审阅的候选，尚未获得人工批准。

冻结基线复核：**B0_INTEGRITY = PASS，7/7 SHA256 MATCH**。新模型从 B1 分支加载；176 个源对象的网格与变换保持一致。B0 文件及冻结 CAD / floor-region / Z / gate / field / V8 文件均未改动。

本轮建立 58 项家具／厨房柜体登记、4 个飘窗组合、9 处冻结玻璃开口的框体与 D-107 五金、三卫布局与三套 2000 mm 淋浴审阅屏、可编辑衣柜／书柜／收纳，以及楼梯与 r1000 曲边的标高内收口。厨房 PDF 尺寸优先；全部使用简单审阅材质。

## 打开结果

- [模型](B1_1_DESIGN_MODEL_V1.blend)
- [全屋俯视](B1_1_TOP.png) · [全屋轴测](B1_1_AXON.png) · [完整视图索引](B1_1_REVIEW_CONTACT_SHEET.png)
- [客厅](B1_1_LIVING.png) · [厨房](B1_1_KITCHEN.png) · [休闲厅](B1_1_LEISURE.png)
- [主人卧室](B1_1_OWNER_BED.png) · [母亲卧室](B1_1_MOTHER_BED.png) · [书房](B1_1_STUDY.png) · [客卧](B1_1_GUEST_BED.png)
- [三卫联系表](B1_1_BATHROOMS_CONTACT_SHEET.png)
- [资产登记](B1_1_ASSET_REGISTER.json) · [厨房登记](KITCHEN_CABINET_3D_REGISTER_V01.json) · [QA](B1_1_QA_REPORT.json)

审阅图临时降低墙体并隐藏吊顶、玻璃面与 site-ground helper，使家具、柜体和 split-level 关系可见；这些剖切**未保存到模型**。模型原建筑保持完整。默认关闭 `03_EXISTING_CEILING` 的集合可见性供审阅；开启即可查看原精确吊顶体块。`05_HUMAN_DESIGN_GUIDE` 保留并隐藏。

## 数值检查

| 检查 | 结果 |
|---|---|
| 冻结文件 SHA256 | 7/7 MATCH |
| 原对象网格和变换 | 176/176 保留 |
| 家具／柜体包络 | {len(validation['furniture_envelopes'])} 项受检；最大误差 {max(c['max_bounds_error_mm'] for c in validation['furniture_envelopes']):.3f} mm；门槛 1 mm |
| 新对象求值三角面 | {validation['evaluated_new_triangles']:,} |
| 标高 | LOWER FFL 0 / ceiling 2800；UPPER FFL 450 / ceiling 3250 mm；stairs 150 / 300 / 450 |
| 冻结开口 | 9 处保留；D-107 原角度约 26.3° |
| 飘窗 | 4 组，保留原投影 XY；前侧干涉待复核 |
| 最终状态 | HUMAN_REVIEW |

以上是明确范围内的数值检查，不等于设计批准。朝向向量检查还依赖 V02 native-front 假设，需结合图片审阅。

## 优先人工裁决

1. **三个朝向冲突**：Rectangle032 生活阳台柜、西→北；Rectangle030 公卫台盆、北→东；Rectangle035 母亲卫台盆、东→南。V02 标记待复核，未收到批准。本模型保留无方向红色体块；不自动采用覆盖值。
2. **四个飘窗前侧干涉**：冻结前墙带在原场景中呈全高，与新增飘窗前玻璃审阅组合重叠。原平面 GLZ 也保留。仅报告，不切墙、不移动冻结开口；需对 frozen authority 的解释给出人工裁决，才可进一步实施。
3. **厨房安装与模块映射**：PDF 明确台面 820、吊柜深 380、总高 2410、冰箱 1700 × 905 × 710。东吊柜采用 620 面板 + 120 上封板（底 1670）；冰箱上柜采用 470 面板 + 10 封板（底 1930），替代旧登记册近似值。柜体 XY 保持登记拓扑。地柜/吊柜内部分柜、冰箱周围左右分隔、南侧水槽腿原点及上柜深度仍未确认；当前门板分隔和板厚为通用审阅细节。
4. **卫生间与设备**：三卫布局保留；淋浴精确 SKU、开启方式、管线接点／安装高度未确认。3 kg 洗衣机、打印机、NAS 的物理体块在 `COL_B11_PENDING_INSTALL` 隐藏，图中只显示 XY helper；不为它们猜安装高度。主人椅方向仍未定。
5. **家具候选与吊顶**：电视柜候选仍标 SIZE_DISTORTION，悬浮／落地最终方案未定；贵妃椅保留 V02 躺轴候选待审。吊顶仅继承精确原体块，灯槽／吊顶细节、梁／包管尺寸缺少确认，未擅自设计。

休闲厅剖切图还记录了冻结 D-107 下缘相对邻近 LOWER 地面的高差观感，以及原曲边 fascia / floor edge 的表面条纹。它们仅作 `REPORT_ONLY_SOURCE_OBSERVATION`，未改变已确认门扇姿态、层级或原网格。

其他内门尚缺已核实的净宽／门扇开向与五金尺寸；只细化 9 处冻结玻璃开口及 D-107，不从旧门符号包围框猜净宽。现阶段不提供管线施工确认、完整门扇碰撞、产品 SKU 保证或规范合规认证。

## 只读报告与可复现来源

原可变家具导引有世界原点旋转与旧负标高异常。该问题已记录，原对象未修复；B1 新对象按 V02 / 朝向登记册中的 CAD 目标矩形归一化，按冻结 datum 放置。不能把历史 350 / Pascal 700 mm 偏移带入 B1。

- 主生成脚本：`build_design_model.py`
- 独立检查：`validate_candidate.py`；结果：`B1_1_FRESH_OPEN_VALIDATION.json`
- 审阅图：`render_review.py`；视图与临时剖切：`B1_1_RENDER_MANIFEST.json`
- 打包：`package_review.py`
- 源观察：`reference_notes.md`；只读源快照：`SOURCE_SCENE_SNAPSHOT.json`
- 候选 SHA256：`{validation['model_sha256']}`

已遵守无自动重设计范围：未移动房间／调整动线／拆墙／扩大客厅／实施 ramp；未来选项保持隐藏。未开始 final materials、final lighting、Cycles final rendering、AI exploration 或 web viewer。
'''
(OUT/'B1_1_HUMAN_REVIEW.md').write_text(md)
print(json.dumps({'status':'HUMAN_REVIEW','numeric_gates':'PASS','images':len(LABELS)+2,'required_artifacts':len(required)+2,
                  'max_envelope_error_mm':qa['numeric_gates']['max_envelope_error_mm'],'human_review':str(OUT/'B1_1_HUMAN_REVIEW.md')},ensure_ascii=False,indent=2))
