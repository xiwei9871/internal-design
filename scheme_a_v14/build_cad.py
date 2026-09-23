"""Generate a traceable FreeCAD reference directly from the approved snapshot."""
from pathlib import Path
import sys
import json
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from design_model import load_design, design_hash, door_leaf_rect, opening_infill_rect
import FreeCAD as App
import Part
import Mesh

ROOT = Path(__file__).resolve().parent
DATA = load_design()
MM = DATA['metres_per_pixel'] * 1000
OX, OY = DATA['origin_source_px']

def vec(x,y,z=0):
    return App.Vector((x-OX)*MM,(OY-y)*MM,z)

def prism(poly,z,h):
    pts=[vec(x,y,z) for x,y in poly]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,h))

def rect_shape(r,z,h):
    x,y,w,l=r
    return Part.makeBox(w*MM,l*MM,h,vec(x,y+l,z))

def main():
    out=ROOT/'cad'; out.mkdir(parents=True,exist_ok=True)
    doc=App.newDocument('Approved_A14')
    rows=[]
    def add(id,label,shape,category):
        ob=doc.addObject('PartDesign::Feature',id.replace('-','_'))
        ob.Label=label; ob.Shape=shape
        ob.addProperty('App::PropertyString','DesignID','Design'); ob.DesignID=id
        ob.addProperty('App::PropertyString','DesignHash','Design'); ob.DesignHash=design_hash()
        ob.addProperty('App::PropertyString','Basis','Design'); ob.Basis='A14 PNG calibrated / design assumption; field verification pending'
        b=shape.BoundBox
        rows.append({'id':id,'label':label,'category':category,'bbox_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]})
    for w in DATA['walls']:
        add(w['id'],w['name'],prism(w['polygon'],0,DATA['design']['wall_height_mm']),'wall')
    slab=DATA['design']['floor_slab_thickness_mm']; wall_h=DATA['design']['wall_height_mm']
    add('SLAB','地坪基准',prism(DATA['outer'],-slab,slab),'slab')
    for d in DATA['doors']:
        add(d['id'],d['name'],rect_shape(door_leaf_rect(d),0,d['height_mm']),'door')
        x1,y1=d['hinge']; x2,y2=d['closed']
        r=opening_infill_rect([x1,y1,x2,y2])
        add(d['id']+'-HEAD',d['name']+'上方墙',rect_shape(r,d['height_mm'],wall_h-d['height_mm']),'infill')
    for w in DATA['windows']:
        x1,y1,x2,y2=w['segment']; r=[min(x1,x2),min(y1,y2),max(abs(x2-x1),1),max(abs(y2-y1),1)]
        add(w['id'],w['name'],rect_shape(r,w['sill_mm'],w['head_mm']-w['sill_mm']),'window')
        horizontal=abs(x2-x1)>abs(y2-y1)
        fill=opening_infill_rect(w['segment'])
        if w['sill_mm']>0:
            add(w['id']+'-SILL',w['name']+'窗下墙',rect_shape(fill,0,w['sill_mm']),'infill')
        add(w['id']+'-HEAD',w['name']+'上方墙',rect_shape(fill,w['head_mm'],wall_h-w['head_mm']),'infill')
    for f in DATA['furniture']:
        if f.get('status')=='reserved_not_installed': continue
        add(f['id'],f['name'],rect_shape(f['rect'],f['z_mm'],f['assembly_height_m']*1000),'furniture_assembly_envelope')
    doc.recompute()
    doc.saveAs(str(out/'方案A14_统一设计底模.FCStd'))
    Mesh.export([x for x in doc.Objects if hasattr(x,'Shape')],str(out/'approved_envelopes.obj'))
    (out/'manifest.json').write_text(json.dumps({'design_sha256':design_hash(),'units':'mm','datum':'FFL Z=0','representation':'Reference envelopes; detailed appearance in Blender; site/SKU unverified','objects':rows},ensure_ascii=False,indent=2))
    print('A14_CAD_OBJECTS',len(rows))

if __name__=='__main__': main()
