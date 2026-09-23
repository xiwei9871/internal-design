"""A402 节点详图（示意）：5 个关键收口/防水节点剖面，常规做法第一版。

每个节点为分层条带剖面 + 引注；具体材料/型材/防水高度标"待确认"，
最终以深化设计与现场做法为准。
"""
from __future__ import annotations

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

from cad_common import (BLACK, OUT, add_text, new_doc, render_preview)


def band(msp, ox, oy, x, y, w, h, label, layer="A-FURN", dashed=False):
    attribs = {"layer": layer, "lineweight": 25}
    if dashed:
        attribs["linetype"] = "DASHED"
    msp.add_lwpolyline([(ox + x, oy + y), (ox + x + w, oy + y),
                        (ox + x + w, oy + y + h), (ox + x, oy + y + h)],
                       close=True, dxfattribs=attribs)
    if label:
        add_text(msp, label, 85, (ox + x + w / 2, oy + y + h / 2),
                 TextEntityAlignment.MIDDLE_CENTER)


def title(msp, ox, oy, w, s):
    add_text(msp, s, 150, (ox + w / 2, oy - 250), TextEntityAlignment.MIDDLE_CENTER)


def main() -> None:
    doc = new_doc()
    msp = doc.modelspace()
    from cad_common import draw_frame_and_title

    def detail_heading(x,y,title):
        add_text(msp,title,140,(x,y+2000))
    def legend(x,y,rows):
        for i,row in enumerate(rows):
            add_text(msp,row,90,(x+1950,y+1200-i*200))
    def numbered(x,y,items):
        for i,(rx,ry,w,h,note,layer) in enumerate(items,1):
            band(msp,x,y,rx,ry,w,h,'',layer=layer)
            cy=y+ry+h/2
            # Leaders are separated at a fixed landing, never printed in thin layers.
            landing=y+1200-(i-1)*200
            msp.add_lwpolyline([(x+rx+w/2,cy),(x+1800,landing),(x+1890,landing)],
                dxfattribs={'layer':'A-DIMS','lineweight':13})
        legend(x,y,[item[4] for item in items])

    x,y=0,0
    detail_heading(x,y,'D1 卫浴门槛 / 防水连续性示意')
    numbered(x,y,[(0,0,900,100,'01 湿区地砖与粘结层 / 厚度待核','A-FLOR'),
        (900,0,300,130,'02 门槛石 / 压边及高差待核','A-FURN'),
        (1200,0,600,80,'03 木地板与基层 / 完成面待核','A-FLOR'),
        (0,-60,1800,60,'04 结构与找平层 / 原地面复核','A-WALL'),
        (0,100,900,5,'05 防水连续上翻 / 高度待确认','A-PLUM')])
    band(msp,x,y,0,100,5,300,'',layer='A-PLUM')

    x,y=4500,0
    detail_heading(x,y,'D2 淋浴玻璃 / 固定节点示意')
    numbered(x,y,[(0,0,1600,100,'01 瓷砖基层与连续防水','A-FLOR'),
        (750,100,100,60,'02 槽或夹件 / 选型与锚固待核','A-FIXT'),
        (795,160,10,900,'03 玻璃10厚示意 / 安全构造待核','A-FIXT'),
        (700,100,40,60,'04 密封胶 / 不代替结构固定','A-FURN')])

    x,y=9000,0
    detail_heading(x,y,'D3 厨房台面 / 后挡水示意')
    numbered(x,y,[(0,0,200,1500,'01 原墙及墙砖基层','A-WALL'),
        (200,870,1100,30,'02 台面完成面900 / 厚30暂定','A-FURN'),
        (200,900,30,120,'03 后挡水 / 材质高度待确认','A-FURN'),
        (1230,100,20,770,'04 柜门与柜体 / 厂家深化','A-FURN')])

    x,y=0,-4100
    detail_heading(x,y,'D4 地板与地砖 / 齐平收口示意')
    numbered(x,y,[(0,0,900,80,'01 木地板及基层 / 总厚待确认','A-FLOR'),
        (900,0,20,80,'02 极窄收口 / 型材待确认','A-FIXT'),
        (920,0,880,80,'03 地砖及基层 / 总厚待确认','A-FLOR'),
        (0,-60,1800,60,'04 结构层 / 两侧完成面齐平','A-WALL')])

    x,y=4500,-4100
    detail_heading(x,y,'D5 衣柜上部 / 留空与收边示意')
    # Full-size section; lower cabinet is omitted with an explicit break.
    numbered(x,y,[(0,0,100,1600,'01 原墙 / 墙高2700暂定','A-WALL'),
        (100,1500,1400,100,'02 吊顶完成面2600暂定','A-CEIL'),
        (100,200,600,1000,'03 柜顶标高2300 / 顶部留空300','A-FURN')])
    add_text(msp,'下部省略；本局部原点=FFL+1100',90,(x,y-180))
    msp.add_lwpolyline([(x+100,y+100),(x+250,y+160),(x+400,y+100),(x+550,y+160),(x+700,y+100)],dxfattribs={'layer':'A-FURN'})

    draw_frame_and_title(msp,'节点详图（做法示意）','A402',[
        '结构层厚度与节点材料均为示意假设；无现场节点确认，不用于施工放样。',
        '玻璃固定、防水高度、门槛与收边型材待现场和厂家深化。'])
    path=OUT/'A402_节点详图.dxf'
    doc.saveas(path)
    render_preview(doc,msp,OUT/'A402_节点详图_preview.png')


if __name__ == '__main__':
    main()
