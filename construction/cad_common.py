"""施工图公共制图层：图层/文字/标注样式、墙门窗家具绘制、图框图签、PNG 预览。

坐标约定与 FreeCAD 底模一致：源 PNG 像素 × 9.82mm/px，
原点 (200,1337)px → 模型 (0,0)mm，Y 轴向上。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from design_model import load_design, door_leaf_rect
DATA = load_design()
OUT = ROOT / 'deliverables' / 'v14' / 'cad'
OUT.mkdir(parents=True, exist_ok=True)
MM = DATA['metres_per_pixel'] * 1000
OX, OY = DATA['origin_source_px']
BLACK = (18, 18, 18)  # ACI 7 在白色预览底上不可见，文字/图框用真彩色黑

LAYERS = {
    "A-WALL": 7, "A-WINDOW": 4, "A-DOOR": 3, "A-FURN": 30,
    "A-FIXT": 6, "A-DIMS": 1, "A-TEXT": 7, "A-HATCH": 8,
    "A-FRAME": 7, "A-FLOR": 2, "A-CEIL": 5, "A-ELEC": 1, "A-PLUM": 140, "A-VPORT": 7, "A-MASK": 7,
}

# 洁具/家电/厨柜归 A-FIXT，其余家具归 A-FURN
FIXT_KEYS = ("马桶", "台盆", "淋浴", "镜柜", "冰箱", "洗烘", "微波", "橱柜", "备餐台", "蒸", "烤")


def m(px: float, py: float) -> tuple[float, float]:
    return ((px - OX) * MM, (OY - py) * MM)


def rect_pts(r):
    x, y, w, h = r
    return [m(x, y + h), m(x + w, y + h), m(x + w, y), m(x, y)]


def is_fixt(name: str) -> bool:
    return any(k in name for k in FIXT_KEYS)


def new_doc() -> ezdxf.EzDxf:
    doc = ezdxf.new("R2018")
    doc.units = 4  # mm
    for name, color in LAYERS.items():
        doc.layers.add(name, color=7, lineweight=50 if name == 'A-WALL' else 18 if name in ('A-DIMS', 'A-TEXT') else 25)
    doc.linetypes.add('DASHED', pattern=[150, 100, -50])
    doc.linetypes.add('CENTER', pattern=[240, 140, -40, 20, -40])
    doc.styles.add("CN", font="/Library/Fonts/Arial Unicode.ttf")
    ds = doc.dimstyles.new("ARCH")
    ds.dxf.dimtxt = 200
    ds.dxf.dimasz = 140
    ds.dxf.dimexe = 120
    ds.dxf.dimexo = 60
    ds.dxf.dimgap = 60
    ds.dxf.dimtxsty = "CN"
    ds.dxf.dimblk = "ARCHTICK"
    ds.dxf.dimdec = 0  # 毫米整数
    return doc


def add_text(msp, s: str, height: float, pos, align=TextEntityAlignment.LEFT, layer="A-TEXT"):
    t = msp.add_text(s, height=height, dxfattribs={
        "layer": layer, "style": "CN", "true_color": colors.rgb2int(BLACK)})
    t.set_placement(pos, align=align)
    return t


def draw_walls(msp, fill: bool = True, lw: int = 50):
    for w in DATA["walls"]:
        pts = [m(x, y) for x, y in w["polygon"]]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-WALL", "lineweight": lw})
        if fill:
            h = msp.add_hatch(color=8, dxfattribs={"layer": "A-WALL"})
            h.paths.add_polyline_path(pts, is_closed=True)
    msp.add_lwpolyline([m(x, y) for x, y in DATA["outer"]], close=True,
                       dxfattribs={"layer": "A-WALL", "lineweight": 70})


def draw_windows(msp):
    for win in DATA["windows"]:
        (x1, y1), (x2, y2) = m(*win["segment"][:2]), m(*win["segment"][2:])
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "A-WINDOW", "lineweight": 25})
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * 45, dx / L * 45  # 45mm 偏移框线
        msp.add_line((x1 + nx, y1 + ny), (x2 + nx, y2 + ny), dxfattribs={"layer": "A-WINDOW"})
        msp.add_line((x1 - nx, y1 - ny), (x2 - nx, y2 - ny), dxfattribs={"layer": "A-WINDOW"})


def draw_doors(msp):
    for d in DATA["doors"]:
        if d['type'] == 'pocket_sliding':
            msp.add_lwpolyline(rect_pts(door_leaf_rect(d)), close=True,
                               dxfattribs={'layer': 'A-DOOR', 'lineweight': 35})
            continue
        hp, lp, cp = m(*d["hinge"]), m(*d["leaf"]), m(*d["closed"])
        msp.add_line(hp, lp, dxfattribs={"layer": "A-DOOR", "lineweight": 35})
        r = math.hypot(lp[0] - hp[0], lp[1] - hp[1])
        a1 = math.degrees(math.atan2(lp[1] - hp[1], lp[0] - hp[0]))
        a2 = math.degrees(math.atan2(cp[1] - hp[1], cp[0] - hp[0]))
        if (a2 - a1) % 360 > 180:
            a1, a2 = a2, a1
        msp.add_arc(hp, r, a1, a2, dxfattribs={"layer": "A-DOOR"})


def draw_furniture(msp, labels: bool = True):
    """1:1 blocks preserve the approved footprints; interior lines explain usage."""
    for index, f in enumerate(DATA["furniture"], 1):
        x, y, pw, ph = f['rect']
        w, h = pw * MM, ph * MM
        layer = "A-FIXT" if is_fixt(f["name"]) else "A-FURN"
        name = f"FURN_{index:03d}"
        if name not in msp.doc.blocks:
            block = msp.doc.blocks.new(name)
            att = {'layer': layer, 'lineweight': 25}
            def rectangle(a, b, c, d):
                block.add_lwpolyline([(a,b),(a+c,b),(a+c,b+d),(a,b+d)], close=True, dxfattribs=att)
            def line(a,b,c,d):
                block.add_line((a,b),(c,d),dxfattribs=att)
            rectangle(0, 0, w, h)
            n = f['name']
            if '床' in n:
                # Template head is at -X. Mirror/rotate its detail coordinates into
                # the approved world head axis while preserving the source footprint.
                head=f['head_axis']
                length,breadth=(w,h) if head.endswith('X') else (h,w)
                def bed_point(a,b):
                    if head=='+X': return (w-a,b)
                    if head=='-X': return (a,b)
                    if head=='+Y': return (b,h-a)
                    if head=='-Y': return (b,a)
                    raise ValueError(f'Unsupported bed head axis: {head}')
                def bed_rectangle(a,b,c,d):
                    block.add_lwpolyline([bed_point(a,b),bed_point(a+c,b),
                        bed_point(a+c,b+d),bed_point(a,b+d)],close=True,dxfattribs=att)
                bed_rectangle(length*.03,breadth*.05,length*.18,breadth*.9)
                bed_rectangle(length*.24,breadth*.09,length*.68,breadth*.82)
                for py in (.14,.57): bed_rectangle(length*.07,breadth*py,length*.12,breadth*.29)
                block.add_line(bed_point(length*.3,breadth*.09),
                               bed_point(length*.3,breadth*.91),dxfattribs=att)
            elif '沙发' in n and '边几' not in n:
                rectangle(w*.73,0,w*.27,h)
                rectangle(0,0,w*.73,h*.12)
                rectangle(0,h*.88,w*.73,h*.12)
                for py in (.12,.38,.64): rectangle(w*.05,h*py,w*.64,h*.24)
            elif '马桶' in n:
                rectangle(0,h*.12,w*.23,h*.76)
                block.add_ellipse((w*.59,h*.5), major_axis=(w*.32,0), ratio=min(h*.35/(w*.32),1), dxfattribs=att)
                block.add_ellipse((w*.57,h*.5), major_axis=(w*.23,0), ratio=min(h*.24/(w*.23),1), dxfattribs=att)
            elif '台盆' in n:
                rectangle(w*.15,h*.14,w*.7,h*.72)
                block.add_circle((w*.55,h*.5),22,dxfattribs=att)
                line(w*.05,h*.5,w*.2,h*.5)
            elif '浴缸' in n:
                rectangle(w*.06,h*.1,w*.88,h*.8)
                block.add_ellipse((w*.5,h*.5),major_axis=(w*.4,0),ratio=h*.32/(w*.4),dxfattribs=att)
                block.add_circle((w*.2,h*.5),22,dxfattribs=att)
            elif '椅' in n:
                rectangle(w*.12,h*.12,w*.76,h*.7)
                rectangle(w*.08,h*.82,w*.84,h*.15)
            elif '淋浴' in n:
                line(0,0,w,h); line(0,h,w,0)
                rectangle(w*.45,h*.45,70,70)
            elif '桌' in n or '茶几' in n or '边几' in n:
                rectangle(w*.04,h*.04,w*.92,h*.92)
                for px in (.08,.88):
                    for py in (.08,.88): rectangle(w*px,h*py,30,30)
            elif '洗烘' in n:
                rectangle(w*.12,h*.08,w*.76,h*.84)
                block.add_circle((w*.5,h*.5),min(w,h)*.26,dxfattribs=att)
            else:
                depth = min(w,h)*.08
                rectangle(depth,depth,w-2*depth,h-2*depth)
                if w > h:
                    for frac in (.33,.67): line(w*frac,0,w*frac,h)
                else:
                    for frac in (.33,.67): line(0,h*frac,w,h*frac)
        msp.add_blockref(name, m(x,y+ph), dxfattribs={'layer':layer})
        if labels and pw*ph>1500:
            add_text(msp, f"F{index:02d}", 100, m(x+pw/2,y+ph/2), TextEntityAlignment.MIDDLE_CENTER)
    # Counter equipment comes from the same contract as the 3D scene.
    for key in ('sink_rect_px', 'hob_rect_px'):
        r = DATA['design']['kitchen'][key]
        msp.add_lwpolyline(rect_pts(r), close=True, dxfattribs={'layer':'A-FIXT','lineweight':25})
        if key.startswith('hob'):
            for fx in (.25,.75):
                msp.add_circle(m(r[0]+r[2]*fx,r[1]+r[3]*.5),85,dxfattribs={'layer':'A-FIXT'})


def linear_dimension(msp, p1, p2, base, angle=0, text='<>'):
    dim = msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,text=text,
        dimstyle='ARCH',override={'dimtxt':115,'dimasz':80,'dimgap':35},
        dxfattribs={'layer':'A-DIMS'})
    dim.render()
    return dim


def draw_position_dims(msp):
    # Chained source grid dimensions; source pixels are preserved here for traceability.
    for a,b in zip([224,415,592,655,779,1160],[415,592,655,779,1160,1458]):
        linear_dimension(msp,m(a,157),m(b,157),m(a,95))
    for a,b in zip([157,322,413,483,556,674,797,1151],[322,413,483,556,674,797,1151,1314]):
        linear_dimension(msp,m(1458,a),m(1458,b),m(1520,a),90)
    # Key furniture envelopes and approved service bays.
    for bay in DATA['design']['service_wall']['bays']:
        x,y,w,h = bay['rect_px']
        linear_dimension(msp,m(x,y+h),m(x,y),m(x-25,y),90)
    selected_ids={'FURN-001','FURN-014','FURN-039'}
    for f in (item for item in DATA['furniture'] if item['id'] in selected_ids):
        x,y,w,h=f['rect']
        base_y=1390 if f['id']=='FURN-039' else y+h+23
        linear_dimension(msp,m(x,y+h),m(x+w,y+h),m(x,base_y))


def draw_room_labels(msp, height: float = 200):
    for name, px, py in DATA["labels"]:
        add_text(msp, name, height, m(px, py), TextEntityAlignment.MIDDLE_CENTER)


def draw_point_labels(msp, records, layer):
    """Place numbered white label boxes in open floor area, then lead to true points."""
    from shapely.geometry import Polygon, Point, box
    from shapely.ops import unary_union
    from ezdxf import bbox
    walls=unary_union([Polygon([m(*p) for p in w['polygon']]) for w in DATA['walls']]).buffer(35)
    floor=Polygon([m(*p) for p in DATA['outer']]).buffer(-35)
    point_keepouts=[Point(m(px,py)).buffer(150) for _,px,py in records]
    occupied=[]
    for entity in msp.query('TEXT'):
        ext=bbox.extents([entity],fast=True)
        if ext.has_data:
            occupied.append(box(ext.extmin.x-40,ext.extmin.y-40,ext.extmax.x+40,ext.extmax.y+40))
    placed=[]
    for code,px,py in records:
        x,y=m(px,py)
        candidate=None
        for radius in (280,420,580,780,1000,1300,1650):
            for i in range(16):
                angle=i*math.pi/8
                cx,cy=x+radius*math.cos(angle),y+radius*math.sin(angle)
                rect=box(cx-155,cy-100,cx+155,cy+100)
                if (floor.contains(rect) and not walls.intersects(rect)
                    and not any(rect.intersects(o) for o in occupied)
                    and not any(rect.intersects(o) for o in point_keepouts)):
                    candidate=(cx,cy,rect);break
            if candidate is not None: break
        if candidate is None:
            raise ValueError(f'No collision-free label position found for {code}')
        cx,cy,rect=candidate
        occupied.append(rect.buffer(30))
        placed.append({'code':code,'bbox':list(rect.bounds),'point':[x,y],'center':[cx,cy]})
    # Draw all leaders first; masks then protect all labels from neighboring leaders.
    for label in placed:
        msp.add_line(label['point'],label['center'],dxfattribs={'layer':layer,'lineweight':13})
    for label in placed:
        x0,y0,x1,y1=label['bbox'];cx,cy=label['center']
        msp.add_solid([(x0,y0),(x1,y0),(x0,y1),(x1,y1)],
                      dxfattribs={'layer':'A-MASK','true_color':0xffffff})
        msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,
                          dxfattribs={'layer':layer,'lineweight':13})
        add_text(msp,label['code'],120,(cx,cy),TextEntityAlignment.MIDDLE_CENTER,layer=layer)
    msp.doc._point_label_boxes=placed
    return placed


def outer_bounds():
    xs = [p[0] for p in (m(x, y) for x, y in DATA["outer"])]
    ys = [p[1] for p in (m(x, y) for x, y in DATA["outer"])]
    return min(xs), max(xs), min(ys), max(ys)


def draw_overall_dims(msp, off: float = 500):
    x0, x1, y0, y1 = outer_bounds()
    attribs = {"layer": "A-DIMS", "true_color": colors.rgb2int(BLACK)}
    dim = msp.add_linear_dim(base=(x0, y1 + off), p1=(x0, y1), p2=(x1, y1),
                             dimstyle="ARCH", dxfattribs=attribs)
    dim.render()
    dim = msp.add_linear_dim(base=(x0 - off, y0), p1=(x0, y0), p2=(x0, y1), angle=90,
                             dimstyle="ARCH", dxfattribs=attribs)
    dim.render()


def draw_frame_and_title(msp, title: str, sheet_no: str, notes: list[str]):
    # Frames and titles belong in paper space, never in 1:1 geometry.
    msp.doc._sheet_metadata = (sheet_no, title, notes)


def make_paper_layout(doc, sheet_no, title, scale=50, notes=None, sidebar=True, bounds=None):
    from ezdxf import bbox
    paper = doc.layouts.new(sheet_no) if sheet_no not in doc.layouts else doc.layouts.get(sheet_no)
    paper.page_setup(size=(594,420),margins=(0,0,0,0),units='mm',scale=(1,1))
    for ent in list(paper):
        if ent.dxftype() != 'VIEWPORT' or ent.dxf.status != 1: paper.delete_entity(ent)
    paper.add_lwpolyline([(10,10),(584,10),(584,410),(10,410)],close=True,dxfattribs={'layer':'A-FRAME','lineweight':50})
    paper.add_line((10,48),(584,48),dxfattribs={'layer':'A-FRAME'})
    add_text(paper, '学道街44号 | 住宅室内设计', 4, (18,35))
    add_text(paper,title,3.4,(18,24))
    add_text(paper, 'A7 PNG标定 / v14共享底模 / 单位mm / 2026-09-18',2.5,(18,15))
    add_text(paper,sheet_no,7,(535,30))
    add_text(paper,f'1:{scale} @ A2  |  v14',3,(468,16))
    add_text(paper,'设计复核版 · 非现场测绘/加工放样图',2.5,(320,36))
    add_text(paper,'按100%打印；请勿缩放页面',2.5,(320,25))
    add_text(paper,f'{sheet_no}  /  {title}',3.5,(18,395))
    w,h = (378,326) if sidebar else (552,326)
    left,bottom=18,58
    if bounds is None:
        ext=bbox.extents(doc.modelspace(),fast=True)
        cx,cy=(ext.extmin.x+ext.extmax.x)/2,(ext.extmin.y+ext.extmax.y)/2
        if ext.size.x > w*scale or ext.size.y > h*scale:
            raise ValueError(f'{sheet_no} geometry exceeds viewport at 1:{scale}: {ext.size}')
    else:
        cx,cy=(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2
    vp=paper.add_viewport(center=(left+w/2,bottom+h/2),size=(w,h),
        view_center_point=(cx,cy),view_height=h*scale,dxfattribs={'layer':'A-VPORT'})
    vp.dxf.flags |= 16384  # lock viewport zoom
    if sidebar:
        paper.add_line((405,58),(405,383),dxfattribs={'layer':'A-FRAME'})
        add_text(paper,'图纸说明 / NOTES',3.2,(414,377))
        y=366
        for note in notes or []:
            for i in range(0,len(note),49):
                add_text(paper,note[i:i+49],2.5,(414,y));y-=5.5
            y-=3
    # Graphic scale is in paper millimetres and remains valid at 100% print.
    length=5000/scale
    paper.add_line((22,66),(22+length,66),dxfattribs={'layer':'A-DIMS'})
    for i in range(6):
        x=22+i*1000/scale
        paper.add_line((x,64.5),(x,67.5),dxfattribs={'layer':'A-DIMS'})
        add_text(paper,str(i),2,(x,60))
    add_text(paper,'m',2,(26+length,60))
    return paper


def render_preview(doc, msp, png_path: Path, figsize=(16,12), dpi=160):
    from paper_export import export_sheet
    export_sheet(doc,png_path)
