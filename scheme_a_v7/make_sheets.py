from pathlib import Path
import runpy, html
root=Path(__file__).parent
ns=runpy.run_path(str(root/'generate_function_living_plan.py'))
diagram=ns['diagram']; text=ns['text']; box=ns['box']

def sheet(title, crop, notes, out, panels=None):
    W,H=1400,1300
    if panels is None: panels=[(crop,100,90,760,1090)]
    els=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1300" viewBox="0 0 1400 1300">',f'<rect width="{W}" height="{H}" fill="#fcfcf8"/>',text(50,55,title,30,anchor='start',weight=600)]
    for i,(cr,ox,oy,pw,ph) in enumerate(panels):
        x,y,w,h=cr; s=min(pw/w,ph/h)
        els.append(f'<clipPath id="clip{i}"><rect x="{ox}" y="{oy}" width="{pw}" height="{ph}"/></clipPath>')
        els.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" fill="#f6f3ea" stroke="#d3d9d3"/>')
        els.append(f'<g clip-path="url(#clip{i})"><g transform="matrix({s} 0 0 {s} {ox-s*x} {oy-s*y})">{diagram}</g></g>')
    els.append('<rect x="860" y="90" width="490" height="1120" rx="12" fill="#fff8df" stroke="#e0c886"/>')
    yy=135
    for line in notes:
        if line=='---': yy+=18; continue
        els.append(text(895,yy,line,18,color='#314844',anchor='start')); yy+=37
    els.append('</svg>')
    (root/out).write_text(''.join(els))

sheet('A7 · 客厅功能与动线核对', (770,740,390,600), [
    '客厅家具：直排沙发约 2200×900',
    '电视/影音矮柜约 1800×350；电视暂按55–65寸',
    '茶几约 900×550，位于沙发前侧，不压主通行线',
    '餐边/充电收纳柜约 900×400，沿原柜体连续布置',
    '---',
    '动线：入户→餐区→客厅；绕过茶几进入沙发区',
    '餐边柜采用浅柜/推拉或抽屉分段，避免开启侵入通道',
    '空调采用壁挂或风管机预留，暂不放立式柜机',
    '本页是家具包络，不替代最终产品选型'
], '方案A7_客厅功能说明.svg')

sheet('A7 · 主卫/次卫器具尺寸核对', (200,300,650,650), [
    '主卫：淋浴区约 1750×1000',
    '主卫：马桶本体约 700×400；预留使用区约 800×600',
    '主卫：台盆/台盆柜约 600×500',
    '主卫：浴缸备选 1500×700；本版不同时落地，待你确认',
    '---',
    '次卫：淋浴区约 1500×1000',
    '次卫：马桶本体约 700×400；台盆约 600×500',
    '次卫不放浴缸，保持内嵌推拉门和位置3通行',
    '器具外形按常见产品包络；施工前仍需按品牌尺寸复核'
], '方案A7_厨卫尺寸说明.svg')

sheet('A7 · 主卧/儿童窗边功能核对', (410,1120,360,215), [
    '主卧窗边：梳妆/阅读/临时办公弹性台约 1200×450',
    '主卧：活动椅＋镜面预留；不固定榻榻米',
    '儿童窗边：书桌约 1800×600＋书柜约300深',
    '儿童房内只保留床、衣柜、床头柜，不再放第二张书桌',
    '---',
    '老人房：整墙衣柜；主卧：长衣/叠衣/被褥分区',
    '书桌和柜体均为家具包络，需在现场复尺后定制'
], '方案A7_卧室窗边说明.svg', panels=[((410,1120,360,215),40,90,760,450),((1130,1120,350,215),40,600,760,450)])
