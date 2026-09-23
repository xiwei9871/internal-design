"""Verify generated model identity, furniture envelopes, placement and camera clearance."""
from pathlib import Path
import sys
import json
from shapely.geometry import Point, Polygon, LineString, box
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from design_model import load_design,design_hash,world_mm,door_leaf_rect

def camera_door_issues(anchors,data):
    issues=[]
    for key,c in anchors.items():
        px,py=c['camera_px']; tx,ty=c['target_px']
        length=((tx-px)**2+(ty-py)**2)**.5
        travel=.15/data['metres_per_pixel']
        sight=LineString([(px,py),(px+(tx-px)*travel/length,py+(ty-py)*travel/length)])
        for door in data['doors']:
            if c['height_mm']>=door['height_mm']: continue
            x,y,w,h=door_leaf_rect(door)
            if sight.intersects(box(x,y,x+w,y+h)):
                issues.append(key+' near-camera sightline blocked by '+door['id'])
    return issues

def validate():
    data=load_design(); issues=[]; sh=design_hash()
    scene=json.loads((ROOT/'scene_manifest.json').read_text())
    issues.extend(camera_door_issues(scene['camera_anchors'],data))
    geometry=json.loads((ROOT/'geometry_audit.json').read_text())
    cad=json.loads((ROOT/'cad/manifest.json').read_text())
    for label,doc in [('scene',scene),('geometry',geometry),('FreeCAD',cad)]:
        if doc['design_sha256']!=sh: issues.append(label+' stale design hash')
    actual={r['id']:r for r in geometry['furniture']}
    cad_objects={r['id']:r for r in cad['objects']}
    for f in data['furniture']:
        if f.get('status')=='reserved_not_installed': continue
        if f['id'] not in actual:
            issues.append(f['id']+' missing scene assembly'); continue
        r=f['rect']; x,y=world_mm(r[0],r[1]+r[3]); s=data['metres_per_pixel']
        lo=[x/1000,y/1000,f['z_mm']/1000]; hi=[lo[0]+r[2]*s,lo[1]+r[3]*s,lo[2]+f['assembly_height_m']]
        b=actual[f['id']]['bbox_m']
        if f['id'] not in cad_objects:
            issues.append(f['id']+' missing CAD envelope')
        elif any(abs(a-b)>.05 for a,b in zip(cad_objects[f['id']]['bbox_mm'],[v*1000 for v in lo+hi])):
            issues.append(f['id']+' CAD envelope differs from shared dimensions')
        if any(b[0][i]<lo[i]-.015 or b[1][i]>hi[i]+.015 for i in range(3)):
            issues.append(f['id']+' exceeds approved assembly envelope')
        if f['kind'] not in ['shower'] and abs(b[0][2]-lo[2])>.01:
            issues.append(f['id']+' does not meet mounting/finished floor datum')
    for key,c in scene['camera_anchors'].items():
        p=Point(c['camera_px'])
        if any(Polygon(w['polygon']).contains(p) for w in data['walls']): issues.append(key+' camera inside wall')
        x,y=world_mm(*c['camera_px']); pos=[x/1000,y/1000,c['height_mm']/1000]
        for id,r in actual.items():
            lo,hi=r['bbox_m']
            if all(lo[i]+.01<pos[i]<hi[i]-.01 for i in range(3)): issues.append(key+' camera inside '+id)
    result={'design_sha256':sh,'furniture_assemblies':len(actual),'camera_count':len(scene['camera_anchors']),'issues':issues,'status':'pass' if not issues else 'fail','scope':'envelopes, mounting datum, camera clearance, shared hash; not full collision/site validation'}
    (ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    r=validate(); print(json.dumps(r,ensure_ascii=False,indent=2)); raise SystemExit(bool(r['issues']))
