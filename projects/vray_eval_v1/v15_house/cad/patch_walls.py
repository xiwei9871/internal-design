#!/usr/bin/env python3
# 墙体拆改同步: A201/A202/A302/A303 (A103已改)
import ezdxf
DEL=[(2700,12750,7900,12950),(7900,13400,13000,13600),(1300,450,1500,2400),(1300,2400,5800,2560)]
NEW=[(9050,5120,9200,6450),(9209,4524,11400,4823),(9059,4507,9209,6507),(9200,6450,11400,6600),
 (9050,4942,9200,5150),(9050,5230,9200,6450),(11900,6400,13100,6600),
 (10850,7800,12900,8000),(8000,10900,9700,11100),(9900,10900,12900,11100),
 (13100,10900,13700,11100),(15600,10900,16200,11100),(13500,11100,13600,11700),
 (15700,11100,15800,11700),(13600,11700,15700,11800),(13100,11100,13500,11800),
 (2900,13000,3800,13200),(6900,13000,7800,13200),(7800,13000,8200,13400),
 (2700,13200,2900,14953),(3700,13790,7000,13900),(3600,13200,3700,13800),(7000,13200,7100,13800),
 (5900,0,7800,200),(8000,0,8600,200),(10800,0,11400,200),(11600,0,12200,200),(14700,0,15300,200),
 (8500,-700,10900,-600),(12100,-700,14800,-600),(8400,-600,8500,0),(10900,-600,11000,0),
 (12000,-600,12100,0),(14700,-600,14900,0),(7450,150,7800,500),(7400,200,7800,500),
 (1300,450,1500,2400),(1300,450,5800,650),(1300,2400,3300,2560)]  # 含恢复的阳台墙+保留段
def patch(path):
    doc=ezdxf.readfile(path); msp=doc.modelspace()
    def bbo(e):
        pts=[(float(p[0]),float(p[1])) for p in e.get_points('xy')]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        return min(xs),min(ys),max(xs),max(ys)
    def addw(x0,y0,x1,y1):
        msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':'A-WALL'})
    for e in list(msp):
        if e.dxftype()!='LWPOLYLINE' or e.dxf.layer!='A-WALL': continue
        b=bbo(e)
        if all(abs(a-c)<300 for a,c in zip(b,(5700,-150,5900,4700))):
            msp.delete_entity(e); addw(5700,-150,5900,1800); addw(5700,3800,5900,4700)
        elif all(abs(a-c)<300 for a,c in zip(b,(7800,4670,7900,13550))):
            msp.delete_entity(e); addw(7800,4670,7900,5000); addw(7800,7800,7900,13550)
        elif any(all(abs(a-c)<300 for a,c in zip(b,d)) for d in DEL):
            msp.delete_entity(e)
    existing=[bbo(e) for e in msp if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-WALL']
    n=0
    for nb in NEW:
        if not any(all(abs(a-b)<200 for a,b in zip(nb,eb)) for eb in existing):
            addw(*nb); n+=1
    # 客厅北墙窗线
    if 'A-WINDOW' not in [l.dxf.name for l in doc.layers]:
        doc.layers.new('A-WINDOW').color=4
    for yy in (13020,13180): msp.add_line((3900,yy),(6900,yy),dxfattribs={'layer':'A-WINDOW'})
    msp.add_line((3900,13100),(6900,13100),dxfattribs={'layer':'A-WINDOW'})
    doc.saveas(path); print(path.split('/')[-1],'new walls',n)
import sys
for sh in sys.argv[1:]: patch(f'cad/{sh}.dxf')
