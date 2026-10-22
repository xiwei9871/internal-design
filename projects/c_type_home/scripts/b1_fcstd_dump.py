"""B1: dump all objects + WINDOW_REF link targets from approved FCStd master."""
import FreeCAD as App
import json

SRC = '/Users/xiwei/interior_design/projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd'
OUT = '/Users/xiwei/interior_design/projects/c_type_home/design/b1_blockout/b1_fcstd_objects.json'

doc = App.openDocument(SRC)
objs = {}
ref_links = {}
for o in doc.Objects:
    rec = {'label': o.Label, 'type': o.TypeId}
    s = getattr(o, 'Shape', None)
    try:
        bb = o.Shape.BoundBox
        rec['bbox'] = [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax]
    except Exception:
        rec['bbox'] = None
    try:
        rec['pos'] = list(o.Placement.Base)
        q = o.Placement.Rotation.Q
        rec['rot'] = list(q)
    except Exception:
        pass
    if o.TypeId == 'App::DocumentObjectGroup' or 'Link' in o.TypeId or o.Name.startswith('WINDOW_REF'):
        pass
    for prop in o.PropertiesList:
        try:
            if o.getTypeIdOfProperty(prop) == 'App::PropertyLinkList':
                tgts = o.getPropertyByName(prop)
                if tgts:
                    ref_links[o.Name] = [t.Name for t in tgts if t]
        except Exception:
            pass
    objs[o.Name] = rec

# union bbox per WINDOW_REF over linked physical objects
ref_unions = {}
for ref, names in ref_links.items():
    xs0 = ys0 = 1e18; xs1 = ys1 = -1e18; ok = 0
    for n in names:
        o = doc.getObject(n)
        try:
            bb = o.Shape.BoundBox
            xs0 = min(xs0, bb.XMin); ys0 = min(ys0, bb.YMin)
            xs1 = max(xs1, bb.XMax); ys1 = max(ys1, bb.YMax); ok += 1
        except Exception:
            pass
    ref_unions[ref] = {'linked': len(names), 'resolved': ok,
                       'union_bbox_xy': [xs0, ys0, xs1, ys1] if ok else None}

json.dump({'objects': objs, 'window_ref_links': ref_links,
           'window_ref_unions': ref_unions,
           'source': SRC}, open(OUT, 'w'), ensure_ascii=False, indent=1)
App.closeDocument(doc.Name)
