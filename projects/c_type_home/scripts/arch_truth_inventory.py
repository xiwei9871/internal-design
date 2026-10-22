"""MASTER_V2 inventory incl. DWG-layer membership (Layer.Group hidden link list)."""
import FreeCAD as App
import json
from collections import defaultdict

SRC = '/Users/xiwei/interior_design/projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd'
OUT = '/Users/xiwei/interior_design/projects/c_type_home/design/pascal_b1/wall_audit/MASTER_ARCH_OBJECT_INVENTORY.json'

doc = App.openDocument(SRC)

member_of = defaultdict(list)   # object name -> [layer labels]
for o in doc.Objects:
    if o.Name.startswith('Layer'):
        try:
            grp = o.Group
        except Exception:
            continue
        for m in grp:
            member_of[m.Name].append(o.Label)

out = {}
for o in doc.Objects:
    rec = {'label': o.Label, 'type': o.TypeId,
           'original_layer': getattr(o, 'OriginalLayer', None),
           'dwg_layers': member_of.get(o.Name, [])}
    try:
        sh = o.Shape
        bb = sh.BoundBox
        rec['bbox'] = [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax]
        rec['shape_null'] = bool(sh.isNull())
        rec['edge_count'] = len(sh.Edges)
        rec['face_count'] = len(sh.Faces)
        rec['shape_type'] = str(sh.ShapeType)
        # per-edge geometry: line / arc / circle / bspline with endpoints
        edges = []
        for e in sh.Edges:
            try:
                c = e.Curve
                t = str(c.TypeId if hasattr(c, 'TypeId') else type(c).__name__)
                pts = [list(v.Point) for v in e.Vertexes]
                edges.append({'curve': t, 'pts': pts})
            except Exception:
                edges.append({'curve': '?', 'pts': []})
        rec['edges'] = edges
    except Exception:
        rec['bbox'] = None
    out[o.Name] = rec

json.dump({'objects': out,
           'layer_members': {k: v for k, v in
                             ((lbl, [m.Name for m in o.Group]) for o in doc.Objects
                              for lbl in [o.Label] if o.Name.startswith('Layer')
                              and hasattr(o, 'Group'))},
           'source': SRC}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('INVENTORY_OK', len(out))
