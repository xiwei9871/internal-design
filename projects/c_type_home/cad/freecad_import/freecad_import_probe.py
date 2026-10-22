import FreeCAD as App
import json, traceback, pathlib, sys, collections
path=pathlib.Path(sys.argv[1])
out=path.with_suffix(path.suffix+".freecad_import.json")
report={"file":str(path),"status":"STARTED"}
try:
 import importDXF
 report["import_module"]="importDXF"
 doc=importDXF.open(str(path))
 if doc is None: doc=App.ActiveDocument
 App.ActiveDocument.recompute()
 objs=doc.Objects
 types=collections.Counter(getattr(o,"TypeId","UNKNOWN") for o in objs)
 layers=collections.Counter(str(getattr(o,"Label","")) for o in objs)
 bounds=[]
 for o in objs:
  try:
   s=o.Shape
   if not s.isNull():
    b=s.BoundBox
    bounds.append((b.XMin,b.YMin,b.XMax,b.YMax))
  except Exception:
   pass
 if bounds:
  ext=[min(x[0] for x in bounds),min(x[1] for x in bounds),max(x[2] for x in bounds),max(x[3] for x in bounds)]
 else: ext=None
 report.update({"status":"PASS","document":doc.Name,"object_count":len(objs),"types":dict(types),"labels":[str(o.Label) for o in objs],"shape_object_count":len(bounds),"shape_extents_mm":ext})
except Exception as e:
 report.update({"status":"FAIL","error":type(e).__name__+": "+str(e),"traceback":traceback.format_exc()})
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False))
