"""A401 立面展开图：厨房/服务墙/衣柜/卫浴 9 个立面，常规划分第一版。

全部立面元素为 (x,y,w,h,label,虚线?) mm 矩形，原点在各框左下角。
柜体内部分隔、开门方向、设备型号均为常规假设，标注"待确认"。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, DATA, OUT, add_text, new_doc, render_preview)

CEIL = DATA['design']['ceiling_mm']['dry']


def frame(msp, ox, oy, w, title, h=CEIL):
    """画一面墙的立面框：外轮廓 + 吊顶线 + 标题 + 总宽标注"""
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": "A-WALL", "lineweight": 50})
    msp.add_line((ox, oy + h), (ox + w, oy + h),
                 dxfattribs={"layer": "A-CEIL", "linetype": "DASHED"})
    add_text(msp, f"吊顶 H{h}", 100, (ox + w, oy + h + 100), TextEntityAlignment.RIGHT)
    add_text(msp, title, 160, (ox + w / 2, oy - 420), TextEntityAlignment.MIDDLE_CENTER)
    dim = msp.add_linear_dim(base=(ox, oy - 180), p1=(ox, oy), p2=(ox + w, oy),
                             dimstyle="ARCH", override={"dimtxt":115,"dimasz":80},
                             dxfattribs={"layer": "A-DIMS", "true_color": colors.rgb2int(BLACK)})
    dim.render()


def elem(msp, ox, oy, x, y, w, h, label, dashed=False, lw=25, layer="A-FURN"):
    attribs = {"layer": layer, "lineweight": lw}
    if dashed:
        attribs["linetype"] = "DASHED"
    msp.add_lwpolyline([(ox + x, oy + y), (ox + x + w, oy + y),
                        (ox + x + w, oy + y + h), (ox + x, oy + y + h)],
                       close=True, dxfattribs=attribs)
    if label:
        add_text(msp, label, 90, (ox + x + w / 2, oy + y + h / 2),
                 TextEntityAlignment.MIDDLE_CENTER)


def wardrobe(msp, ox, oy, w, title, doors=4, note="内部格局待确认"):
    """通顶衣柜常规立面：顶柜线 + 均分门扇"""
    frame(msp, ox, oy, w, title)
    elem(msp, ox, oy, 0, 0, w, 2300, "", lw=35)
    msp.add_line((ox, oy + 2100), (ox + w, oy + 2100), dxfattribs={"layer": "A-FURN"})
    add_text(msp, "顶柜 H2100-2300 / 顶部留空300", 90, (ox + w / 2, oy + 2200), TextEntityAlignment.MIDDLE_CENTER)
    dw = w / doors
    for i in range(1, doors):
        msp.add_line((ox + i * dw, oy), (ox + i * dw, oy + 2100), dxfattribs={"layer": "A-FURN"})
        add_text(msp, "挂/叠", 80, (ox + (i - 0.5) * dw, oy + 1050), TextEntityAlignment.MIDDLE_CENTER)
    add_text(msp, note, 90, (ox + w / 2, oy + 150), TextEntityAlignment.MIDDLE_CENTER)


def service_elevation(msp, ox, oy):
    service = DATA['design']['service_wall']
    widths = [b['width_mm'] for b in service['bays']]
    total = sum(widths)
    frame(msp, ox, oy, total, 'E3 服务墙 H2400暂定')
    x = 0
    bay_x = {}
    # Looking west from the eastern corridor: south is left, north is right.
    for bay in reversed(service['bays']):
        bay_x[bay['id']] = x
        elem(msp,ox,oy,x,0,bay['width_mm'],service['height_mm'],'',lw=35)
        x += bay['width_mm']
    for appliance in service['appliances']:
        bay = next(b for b in service['bays'] if b['id']==appliance['bay'])
        x=bay_x[bay['id']]+(bay['width_mm']-appliance['width_mm'])/2
        elem(msp,ox,oy,x,appliance['z_mm'],appliance['width_mm'],appliance['height_mm'],
            appliance['id'].upper(),layer='A-FIXT')
    return total


def child_study_elevation(msp, ox, oy):
    desk=next(f for f in DATA['furniture'] if f['name'].startswith('儿童窗边学习桌'))
    book=next(f for f in DATA['furniture'] if f['name'].startswith('儿童窗边书柜'))
    scale=DATA['metres_per_pixel']*1000
    x0=desk['rect'][0]
    total=(book['rect'][0]+book['rect'][2]-x0)*scale
    frame(msp,ox,oy,total,'E8 儿童窗边区')
    elem(msp,ox,oy,0,0,desk['rect'][2]*scale,desk['height_m']*1000,'学习桌 H750')
    elem(msp,ox,oy,(book['rect'][0]-x0)*scale,0,book['rect'][2]*scale,book['height_m']*1000,'')
    add_text(msp,'矮柜H1100',90,(ox+total,oy+1200),TextEntityAlignment.RIGHT)


def kitchen_elevation(msp, ox, oy, side):
    """Orthographic interior views: north X+, west south-to-north, east north-to-south."""
    kitchen=DATA['design']['kitchen']
    scale=DATA['metres_per_pixel']*1000
    zone=next(z for z in DATA['zones'] if z['name']=='厨房')
    x0=min(p[0] for p in zone['polygon']); x1=max(p[0] for p in zone['polygon'])
    y0=min(p[1] for p in zone['polygon']); y1=max(p[1] for p in zone['polygon'])
    counter=kitchen['counter_height_mm']; thickness=kitchen['counter_thickness_mm']
    ceiling=DATA['design']['ceiling_mm']['wet']
    titles={'north':'E1 厨房北立面','west':'E2 厨房西立面','east':'E11 厨房东立面'}
    width=((x1-x0) if side=='north' else (y1-y0))*scale
    frame(msp,ox,oy,width,titles[side],h=ceiling)
    cabinets=[f for f in DATA['furniture'] if f['name'].startswith('厨房')]
    for f in cabinets:
        x,y,w,h=f['rect']
        if side=='north' and f['name']!='厨房橱柜': continue
        if side=='east' and f['name']!='厨房橱柜': continue
        start=(x-x0) if side=='north' else (y1-y-h) if side=='west' else (y-y0)
        length=w if side=='north' else h
        elem(msp,ox,oy,start*scale,0,length*scale,counter-thickness,'')
        elem(msp,ox,oy,start*scale,counter-thickness,length*scale,thickness,'',lw=35)
    if side in ('north','east'):
        win=next(w for w in DATA['windows'] if w['name']==('厨房北窗' if side=='north' else '厨房东窗'))
        seg=win['segment']
        start=(min(seg[0],seg[2])-x0) if side=='north' else (min(seg[1],seg[3])-y0)
        length=abs(seg[2]-seg[0]) if side=='north' else abs(seg[3]-seg[1])
        elem(msp,ox,oy,start*scale,win['sill_mm'],length*scale,win['head_mm']-win['sill_mm'],'',layer='A-WINDOW')
        add_text(msp,'窗台850 / 台面900冲突待复核',95,(ox,oy+2850))
        if side=='north':
            add_text(msp,'窗端超净边108，源线保留待复尺',95,(ox,oy+3060))
    if side in ('north','west'):
        r=kitchen['hob_rect_px'] if side=='north' else kitchen['sink_rect_px']
        start=(r[0]-x0) if side=='north' else (y1-r[1]-r[3])
        length=r[2] if side=='north' else r[3]
        a,b=(ox+start*scale,oy+counter),(ox+(start+length)*scale,oy+counter)
        msp.add_line(a,b,dxfattribs={'layer':'A-FIXT','lineweight':50})
        label='灶台投影' if side=='north' else '水槽投影'
        add_text(msp,label,95,((a[0]+b[0])/2,oy+counter-180),TextEntityAlignment.MIDDLE_CENTER)
    add_text(msp,'设备/吊柜待深化',90,(ox+width/2,oy-690),TextEntityAlignment.MIDDLE_CENTER)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()
    GX, GY = 5600, 4000  # 立面框网格间距

    kitchen_elevation(msp,0,0,'north')
    kitchen_elevation(msp,GX,0,'west')
    kitchen_elevation(msp,GX+2500,0,'east')
    service_elevation(msp,2*GX,0)

    # ---- 第二行：三个衣柜 ----
    ox, oy = 0, -GY
    wardrobe(msp, ox, oy, 2199, "E4 主卧北衣柜立面 1:50", doors=4)
    ox += GX
    wardrobe(msp, ox, oy, 2308, "E5 衣帽区长柜立面 1:50", doors=4)
    ox += GX
    wardrobe(msp, ox, oy, 2013, "E6 老人房衣柜立面 1:50", doors=4)

    # ---- 第三行：儿童房 + 两卫 ----
    ox, oy = 0, -2 * GY
    wardrobe(msp, ox, oy, 1993, "E7 儿童房衣柜立面 1:50", doors=3)
    ox += GX
    child_study_elevation(msp,ox,oy)
    ox += 2700  # E8/E9 之间的空档放次卫
    frame(msp, ox, oy, 1493, "E10 次卫湿区", h=2400)
    elem(msp, ox, oy, 0, 0, 1493, 2400, "淋浴区+玻璃隔断", dashed=True, layer="A-FIXT")
    elem(msp, ox, oy, 200, 1600, 60, 300, "花洒", layer="A-FIXT")
    ox += 2900
    frame(msp, ox, oy, 2799, "E9 主卫湿区", h=2400)
    elem(msp, ox, oy, 0, 0, 1500, 550, "浴缸1500×700", layer="A-FIXT")
    elem(msp, ox, oy, 1500, 0, 1299, 2400, "淋浴区+玻璃隔断", dashed=True, layer="A-FIXT")
    elem(msp, ox, oy, 2400, 1600, 60, 300, "花洒", layer="A-FIXT")

    from cad_common import draw_frame_and_title
    draw_frame_and_title(msp, '立面展开图', 'A401', ['柜体高2300；服务墙2400；层高均为设计假设待现场复核。', '设备开孔、散热、五金及净空待SKU确认。', '儿童书柜高1100；低柜保持窗边采光。'])

    dxf_path = OUT / "A401_立面展开图.dxf"
    doc.saveas(dxf_path)
    render_preview(doc, msp, OUT / "A401_立面展开图_preview.png", figsize=(20, 14), dpi=150)
    print(dxf_path)
    print(OUT / "A401_立面展开图_preview.png")


if __name__ == "__main__":
    main()
