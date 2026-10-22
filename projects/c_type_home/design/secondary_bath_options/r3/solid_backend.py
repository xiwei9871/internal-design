"""Deterministic planar-cell wall union; avoids coplanar 3D Boolean artifacts."""
import json,math,sys
from pathlib import Path
from collections import defaultdict
import shapely
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union,polygonize
from shapely.prepared import prep

GRID=.00005
def key2(p):return tuple(round(float(x)/GRID)*GRID for x in p)
def segment_slice(vertices,triangles,z):
    segments={}
    for face in triangles:
        pts=[]
        for i in range(3):
            a=vertices[face[i]];b=vertices[face[(i+1)%3]]
            if (a[2]<z<b[2]) or (b[2]<z<a[2]):
                t=(z-a[2])/(b[2]-a[2]);pts.append(key2((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))))
        pts=list(dict.fromkeys(pts))
        if len(pts)==2 and pts[0]!=pts[1]:segments[tuple(sorted(pts))]=pts
    return list(segments.values())
def cross_section(wall,z):
    if z<=wall['minz'] or z>=wall['maxz']:return Polygon()
    if 'footprint' in wall:return shapely.set_precision(Polygon(wall['footprint']),GRID)
    segments=segment_slice(wall['vertices'],wall['triangles'],z)
    if not segments:return Polygon()
    lines=unary_union([LineString(s) for s in segments])
    polys=list(polygonize(lines));selected=[]
    for poly in polys:
        p=poly.representative_point();px,py=p.x,p.y;count=0
        for a,b in segments:
            if (a[1]>py)!=(b[1]>py):
                x=a[0]+(py-a[1])*(b[0]-a[0])/(b[1]-a[1])
                if x>px:count+=1
        if count%2:selected.append(poly)
    return unary_union(selected) if selected else Polygon()
def main(src,dest):
    d=json.loads(Path(src).read_text());walls=d['walls'];cuts=d['cuts']
    levels=set()
    for w in walls:
        zs=[v[2] for v in w['vertices']];w['minz']=min(zs);w['maxz']=max(zs)
        levels.update(round(z,5) for z in zs)
    for c in cuts:levels.update([round(c['lo'][2],5),round(c['hi'][2],5)])
    levels=sorted(levels);layers=[]
    for z0,z1 in zip(levels,levels[1:]):
        z=(z0+z1)/2
        shapes=[cross_section(w,z) for w in walls]
        shapes=[g for g in shapes if not g.is_empty]
        poly=unary_union(shapes) if shapes else Polygon()
        if not poly.is_empty:
            # A50micron plaster-skin overlap connects CAD edge-only contacts.
            poly=poly.buffer(d.get('skin_overlap_m',0),join_style=2) if d.get('skin_overlap_m',0)>0 else poly
            poly=shapely.set_precision(shapely.make_valid(poly),GRID)
        for c in cuts:
            if c['lo'][2]<z<c['hi'][2]:
                poly=poly.difference(box(c['lo'][0],c['lo'][1],c['hi'][0],c['hi'][1]))
        poly=shapely.set_precision(shapely.make_valid(poly),GRID)
        layers.append(poly)
    # One planar arrangement is shared by every height band. Therefore faces
    # at all step levels use exactly the same node/edge decomposition.
    # Blender source floats create submicron split points at old corner patches.
    # Snap the complete arrangement before triangulation, rather than snapping
    # individual output triangles after they already carry duplicate nodes.
    lines=shapely.set_precision(unary_union([p.boundary for p in layers if not p.is_empty]),GRID)
    cells=list(polygonize(lines));triangles=[];coords=[];lookup={};occupancy=[]
    prepared=[prep(p) for p in layers]
    def vid(p):
        p=key2(p)
        if p not in lookup:lookup[p]=len(coords);coords.append(p)
        return lookup[p]
    for cell in cells:
        if cell.area<GRID*GRID/10:continue
        try:
            tris=list(shapely.constrained_delaunay_triangles(cell).geoms)
        except Exception:
            Path(dest+'.failed-cell.wkt').write_text(cell.wkt)
            print('FAILED_CELL',cell.is_valid,shapely.is_valid_reason(cell),cell.area,cell.bounds)
            raise
        assert abs(sum(t.area for t in tris)-cell.area)<max(1e-10,cell.area*1e-7),'Cell triangulation lost area'
        for tri in tris:
            pt=tri.representative_point();occ=[p.covers(pt) for p in prepared]
            if not any(occ):continue
            pts=[key2(c) for c in list(tri.exterior.coords)[:3]]
            area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])
            if area<0:pts.reverse()
            ids=tuple(vid(p) for p in pts)
            if len(set(ids))<3:continue
            triangles.append(ids);occupancy.append(occ)
    adjacency=defaultdict(list)
    for i,tri in enumerate(triangles):
        for j in range(3):adjacency[tuple(sorted((tri[j],tri[(j+1)%3])))].append(i)
    assert all(len(v)<=2 for v in adjacency.values()),'Planar triangle overlap'
    verts=[];faces=[];nodes={}
    def node(i,k):
        key=(i,k)
        if key not in nodes:nodes[key]=len(verts);verts.append([*coords[i],levels[k]])
        return nodes[key]
    for i,tri in enumerate(triangles):
        occ=occupancy[i]
        for k,active in enumerate(occ):
            if not active:continue
            if k==0 or not occ[k-1]:faces.append([node(t,k) for t in reversed(tri)])
            if k==len(occ)-1 or not occ[k+1]:faces.append([node(t,k+1) for t in tri])
            for j in range(3):
                a,b=tri[j],tri[(j+1)%3];neighbor=[n for n in adjacency[tuple(sorted((a,b)))] if n!=i]
                if neighbor and occupancy[neighbor[0]][k]:continue
                faces.append([node(a,k),node(b,k),node(b,k+1),node(a,k+1)])
    edge_faces=defaultdict(int)
    for f in faces:
        for i in range(len(f)):edge_faces[tuple(sorted((f[i],f[(i+1)%len(f)])))]+=1
    counts=defaultdict(int)
    for v in edge_faces.values():counts[v]+=1
    # The indexed surface is checked before Blender's float storage and again
    # after a fresh import into the full .blend scene.
    if not all(v==2 for v in edge_faces.values()):
        print('BAD_EDGES',[(verts[a],verts[b],v) for (a,b),v in edge_faces.items() if v!=2])
    assert all(v==2 for v in edge_faces.values()),dict(counts)
    out=dict(vertices=verts,faces=faces,levels=levels,planar_cells=len(cells),planar_triangles=len(triangles),
             edge_face_counts=dict(counts),source_walls=len(walls),grid_mm=GRID*1000,skin_overlap_mm=d.get('skin_overlap_m',0)*1000)
    Path(dest).write_text(json.dumps(out,separators=(',',':')))
    print(json.dumps({k:v for k,v in out.items() if k not in ['vertices','faces']},ensure_ascii=False))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
