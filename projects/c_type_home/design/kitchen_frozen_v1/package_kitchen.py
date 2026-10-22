"""Small textual registers and filesystem-only image evidence for kitchen V1."""
import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageChops, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SITE=ROOT/'design/site_photos'
MANIFEST=OUT/'KITCHEN_FREEZE_MANIFEST.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def read(name):return json.loads((OUT/name).read_text())
def write(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def pin(paths):
    m=read(MANIFEST.name)
    for p in paths:m['files_sha256'][str(p)]=sha(p)
    write(MANIFEST.name,m)


def dimensions():
    rows=[]
    def add(item,parameter,value,status,authority,verify='加工前复尺'):
        rows.append(dict(项目=item,参数=parameter,模型值_mm=value,依据等级=status,
                         依据=authority,加工复核=verify))
    for p,v in [('台面高度',820),('台面深度',600)]:
        add('厨房主台面',p,v,'用户明确确认','现状用户确认')
    for p,v in [('宽',905),('深',710),('高',1700)]:
        add('冰箱',p,v,'用户明确确认','现有冰箱；固定柜列位置','替换型号时核对开门和散热要求')
    add('外侧窄柜','宽',320,'用户明确确认','门口向内第一列')
    add('外侧窄柜','深',765,'已确认范围的模型代表值','用户范围760–770；与冰箱前脸齐平')
    add('冰箱','后部插座余量',55,'已确认范围的模型代表值','用户范围50–60；背墙Y4500')
    add('外侧窄柜','门板数量',4,'用户明确确认','顶部与冰箱吊柜齐平；下三段等高','门缝、五金、内部分隔待深化')
    add('内侧高柜凹格列','宽',935,'保留并确认现模型','原审阅包络；顺序在冰箱内侧')
    add('柜列','柜顶高度',2410,'保留并确认现模型','继承柜列审阅高度')
    add('厨房小窗','跨度',1000,'保留并确认现模型','对应窗体X6100–7100；不从墙长推算')
    add('厨房小窗','窗台',1020,'用户确认关系推导','主台面820 + 窗下露墙200')
    add('厨房小窗','窗顶',2400,'继承并保留','对应窗体原窗顶标高')
    add('阳台蓝色窗段','跨度',3000,'登记图约值','蓝段约X2100–5100；撤回4米推断','现场实测跨度；3000不是测量值')
    add('阳台蓝色窗段','窗台',1050,'继承并保留','完整窗下墙；禁止剖切成低柜显示')
    add('阳台蓝色窗段','窗顶',2400,'继承并保留','保留原窗高关系')
    for p,v in [('宽',1500),('深',500),('模型总高',2710),('台面标高',1100)]:
        add('图5储物柜',p,v,'已确认模型/PDF分段','保留导引1500×500位置；PDF原名义1580×600另存','复尺解决1500×500与PDF1580×600差异')
    add('图5储物柜','中段名义高度',450,'PDF分段名义尺寸','台面1100→上柜底板上表面1550','18mm底板后模型净开口432；核对实际板厚')
    add('图5储物柜','中段模型净开口',432,'模型实际净空','台面1100→底板下表面1532','复尺和板厚核对')
    for p,v in [('台面宽',800),('台面深',467),('台面高',960),('石材厚',40),
                ('回转段总长',1690),('连接段长',890)]:
        add('原岛台与连接柜',p,v,'用户确认保留原件+初装PDF','原PDF第1/4页C立面；当前放置关系已确认')
    add('原岛台','圆角半径',40,'审阅示意','现有模型圆角','按实物圆角复核')
    for p,v,s in [('宽',600,'用户明确确认'),('高',2000,'用户明确确认'),('名义深',500,'审阅示意')]:
        add('旁侧高柜',p,v,s,'现状照片和用户确认；深度500仅示意','实际模型含前板包络深501；加工复尺')
    for p,v in [('名义宽',780),('名义深',220),('名义高',280),('底标高',2150)]:
        add('高柜上方挂机',p,v,'审阅示意','用户确认存在和在高柜上方；外形/安装标高为占位','确认设备型号、检修和安装要求')
    return rows


def report(status):
    base=str(OUT)
    text=f'''# 厨房现状模型冻结 V1

冻结日期：2026-10-01（Asia/Shanghai）。状态：{status}。

业主已确认当前几张图基本正确，本版将厨房布局、柜列、岛台、旁柜、设备相邻关系、窗体修正和图5储物柜正式收口。后续厨房工作从本版继承；更改已锁定的空间关系需要业主明确要求，并另存新版本。

## 正式入口

- [冻结母版]({base}/KITCHEN_APPROVED_AS_IS_V1.blend)
- [冻结清单]({base}/KITCHEN_FREEZE_MANIFEST.json)
- [尺寸台账]({base}/KITCHEN_DIMENSION_SCHEDULE.csv)
- [模型对象/坐标台账]({base}/KITCHEN_MODEL_REGISTER.json)
- [11张检查图索引]({base}/KITCHEN_VIEW_INDEX.md)
- [长期上下文规则]({ROOT.parents[1]}/AGENTS.md)

## 已锁定的关系

| 部位 | 冻结内容 |
|---|---|
| 冰箱柜列 | 门口向内：320窄柜 → 冰箱及上柜 → 内侧高柜/凹格；窄柜与冰箱前脸齐平 |
| 窄柜门板 | 四段；顶段与冰箱吊柜上下边齐平；下三段等高 |
| 主厨房 | 保留V4灶台、水槽、转角、长边柜和岛台/连接柜坐标及朝向；主台面H820/D600 |
| 冰箱 | 905×710×1700；窄柜模型深765；背部余量55（各自原确认范围已在台账注明） |
| 厨房小窗 | 对应窗体X6100–7100，跨度1000；窗台1020；比台面高200；窗顶2400 |
| 阳台蓝色窗段 | 登记图约X2100–5100，约3000；撤回4米推断；不以整段墙长代替窗长 |
| 窗下墙 | 完整保留1050高度，连续墙面；红圈部位语义为窗下墙；出图剖切不得截短它 |
| 图5储物柜 | 导引位置及1500×500包络保留；上四门、下四门、两抽屉、中部开放台；正/侧视角固定 |
| 岛台与旁柜 | 原岛台台面800×467/H960及连接段保留；600宽、2000高旁柜及上方挂机相邻关系固定 |

单位为毫米；约值、继承值和示意尺寸的证据等级见尺寸台账。冻结母版保留V4全部源对象和隐藏的历史代理，不重新解释户型。B0原始建筑基线保持独立冻结；厨房窗体使用B1现状修正覆盖层。

## 锁定机制与检验

厨房相关对象加选择与平移/旋转/缩放保护，检查相机一并保护。清单钉住母版、源V4、相机源、对象状态、来源登记和11张检查图的SHA256。对象快照覆盖网格、姿态、层级、材质、修饰器、可见状态及相机参数。

复核命令（在项目根目录执行）：

```bash
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python projects/c_type_home/design/kitchen_frozen_v1/freeze_kitchen.py -- verify
rtk proxy .venv/bin/python projects/c_type_home/design/kitchen_frozen_v1/package_kitchen.py audit
```

核验文件：[母版校验]({base}/KITCHEN_QA.json)、[视角像素比较]({base}/PIXEL_EQUIVALENCE_QA.json)、[业主确认依据]({base}/APPROVAL_EVIDENCE.json)。临时剖切只存在于重出图进程，母版完整墙体不被写回裁切。

## 加工深化边界

空间方案和现状模型已锁定；本包未放行下单加工。现场复尺和设备/五金深化需补齐：约3米窗跨实测，旁柜深度，挂机型号及安装/检修尺寸，继承柜体细部，台面开孔与收口，以及图5柜导引1500×500和原PDF1580×600之间的差异。图5柜中段450为名义分段，当前模型18厚底板下净空为432。

保留简单审阅材质；最终表面、照明、生产节点在后续对应阶段处理。复尺更新只进入新版本，并保留本次确认关系与来源。

## 文件与聊天规则

所有渲染、叠加图、联系表和照片代理图保存到项目文件系统，聊天只返回路径。高分辨率原图按需一次检查一张或少数几张。禁止把大二进制或图像批量内联到上下文。
'''
    (OUT/'KITCHEN_FREEZE_REPORT.md').write_text(text)


def prepare():
    m=read(MANIFEST.name)
    assert m['status']=='HUMAN_APPROVED_SPATIAL_MODEL_FROZEN'
    rows=dimensions()
    write('KITCHEN_DIMENSION_SCHEDULE.json',rows)
    with (OUT/'KITCHEN_DIMENSION_SCHEDULE.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    evidence=OUT/'approval_evidence';evidence.mkdir(exist_ok=True)
    pairs=[('sink',Path('/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T/codex-clipboard-ea01d04f-45a0-4c52-b2dc-357dda4fd865.png'),'05'),
           ('buffet',Path('/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T/codex-clipboard-8e955fbe-7a05-4b37-90ac-b19dd3866bb8.png'),'10')]
    views=read('CAMERA_REGISTER.json');approvals=[]
    for label,source,vid in pairs:
        dest=evidence/f'USER_APPROVED_{label.upper()}.png'
        if not dest.exists():shutil.copy2(source,dest)
        v=next(v for v in views if v['id']==vid)
        with Image.open(dest) as a, Image.open(v['original_render_path']) as b:
            assert a.size==b.size
            equal=ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox() is None
            assert equal
            approvals.append(dict(view_id=vid,attachment=str(dest),attachment_sha256=sha(dest),
                                  v4_render=v['original_render_path'],size=list(a.size),
                                  rgb_pixels_identical=True))
    write('APPROVAL_EVIDENCE.json',dict(date='2026-10-01',
          human_request=m['human_authorization'],approval='CURRENT_KITCHEN_SPATIAL_MODEL',
          attachments=approvals,image_inline=False))
    index=['# 厨房冻结 V1 — 11视角索引','',
           '全部2000×1500，Workbench简单材质。V4图已按冻结来源核验哈希。窗下墙不剖短。','',
           '| 编号 | 检查内容 | 原图 |','|---|---|---|']
    for v in views:
        index.append(f"| {v['id']} | {v['name']} | [{v['path']}]({v['original_render_path']}) |")
    contact=OUT/'KITCHEN_CONTACT_SHEET.png'
    sheet=Image.new('RGB',(1200,1328),'#e7e9eb')
    draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/Library/Fonts/Arial Unicode.ttf',16)
    for n,v in enumerate(views):
        x=(n%3)*400;y=(n//3)*332
        with Image.open(v['original_render_path']) as im:
            proxy=im.convert('RGB');proxy.thumbnail((400,300));sheet.paste(proxy,(x,y))
        draw.text((x+8,y+306),v['id']+' '+v['name'],fill='#20252b',font=font)
    sheet.save(contact)
    index.extend(['',f'[联系表（仅落盘）]({contact})','',
                  '05与10分别对应本轮两张附件；用户附件已存档并验证与V4原图RGB像素一致。'])
    (OUT/'KITCHEN_VIEW_INDEX.md').write_text('\n'.join(index)+'\n')
    report('母版已保存；独立进程和重出图核验进行中')
    pin([OUT/'KITCHEN_DIMENSION_SCHEDULE.csv',OUT/'KITCHEN_DIMENSION_SCHEDULE.json',
         OUT/'APPROVAL_EVIDENCE.json',OUT/'KITCHEN_VIEW_INDEX.md',contact,Path(__file__),
         *evidence.glob('*.png')])
    print(json.dumps(dict(prepare='PASS',dimension_rows=len(rows),approved_attachments=2,
                         indexed_views=len(views),images_returned='PATHS_ONLY'),ensure_ascii=False))


def finalize():
    qa=read('KITCHEN_QA.json');assert qa['status']=='PASS'
    renders=read('RENDER_VERIFICATION_MANIFEST.json');assert len(renders)==2
    matches=[]
    for r in renders:
        with Image.open(r['path']) as a,Image.open(r['reference']) as b:
            assert a.size==b.size==tuple(r['resolution'])
            diff=ImageChops.difference(a.convert('RGB'),b.convert('RGB'))
            equal=diff.getbbox() is None
            assert equal, f"Approved image changed: {r['id']}"
            matches.append(dict(view_id=r['id'],render=r['path'],reference=r['reference'],
                                rgb_pixels_identical=True,max_rgb_difference=0))
    write('PIXEL_EQUIVALENCE_QA.json',dict(status='PASS',matches=matches,
          approved_attachment_to_v4='2/2 PIXEL_IDENTICAL',
          frozen_master_to_v4='2/2 PIXEL_IDENTICAL',generated_images_in_chat=False))
    report('HUMAN_APPROVED_SPATIAL_MODEL_FROZEN；独立重开与重出图核验 PASS')
    m=read(MANIFEST.name)
    m['verification_status']='PASS'
    m['verification_summary']=dict(b0_files_match=qa['b0_files_match'],
          source_objects_preserved=m['source_object_count'],fresh_open_objects_match=qa['fresh_open_object_states_match'],
          protected_objects=qa['protected_objects'],approved_cameras=qa['approved_cameras'],
          approved_views_reproduced_pixel_identically=2)
    write(MANIFEST.name,m)
    pin([OUT/'KITCHEN_FREEZE_REPORT.md',OUT/'KITCHEN_QA.json',
         OUT/'PIXEL_EQUIVALENCE_QA.json',OUT/'RENDER_VERIFICATION_MANIFEST.json',
         *[Path(r['path']) for r in renders]])
    audit()


def audit():
    m=read(MANIFEST.name)
    count=0
    for category in ['files_sha256','sources_sha256','approved_render_sha256']:
        for path,expected in m[category].items():
            assert sha(path)==expected,f'Frozen file changed: {path}'
            count+=1
    b0=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
    assert all(sha(ROOT/b0['files'][k])==v for k,v in b0['sha256'].items())
    assert read('KITCHEN_QA.json')['status']=='PASS'
    if m.get('verification_status')=='PASS':assert read('PIXEL_EQUIVALENCE_QA.json')['status']=='PASS'
    print(json.dumps(dict(package_audit='PASS',pinned_files_match=count,B0_files_match=7,
                         freeze_status=m['status'],fabrication_release=m['fabrication_release']),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','finalize','audit'])
    {'prepare':prepare,'finalize':finalize,'audit':audit}[p.parse_args().mode]()
