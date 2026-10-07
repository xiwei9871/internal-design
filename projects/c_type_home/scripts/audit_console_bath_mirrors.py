"""Bounded vanity/wall audit for the owner's three-bath mirror brief."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/console_bath_mirrors_review'
reg=json.loads((ROOT/'design/secondary_bath850_review/spatial-canvas.bindings.full.json').read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update()
prefixes=('B11_Rectangle030','B11_Rectangle035','R3_VANITY','BW1_COUPLE_SHALLOW','BW1_COUPLE_BOOK',
 'V4_D-GUEST-BATH','V4_D-BATHM','V4_W-BATH','R3_SLIDING','VIEW_WALL_R3_')
names=[b['native_id'] for b in reg['bindings'] if b['native_id'].startswith(prefixes)]
idx=json.loads(Path('/Users/xiwei/interior_design/projects/c_type_home/design/wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
zones={'master':(13.0,16.5,4.45,6.55),'secondary':(8.95,11.45,4.50,6.55),'guest':(7.8,9.85,7.85,10.95)}
groups={}
for zone,(x0,x1,y0,y1) in zones.items():
 groups[zone]=[r['native_id'] for r in idx['parts'] if r['world_bounds'][1][0]>x0 and r['world_bounds'][0][0]<x1 and r['world_bounds'][1][1]>y0 and r['world_bounds'][0][1]<y1]
names+=sum(groups.values(),[]);rows=[]
for n in sorted(set(names)):
 o=bpy.data.objects.get(n)
 if not o or o.type!='MESH':continue
 vs=[o.matrix_world@v.co for v in o.data.vertices];a=[min(v[i] for v in vs) for i in range(3)];b=[max(v[i] for v in vs) for i in range(3)]
 r={'name':n,'min':a,'max':b,'size':[b[i]-a[i] for i in range(3)],'active':not(o.hide_render or o.hide_viewport),'faces':len(o.data.polygons),'materials':[m.name if m else None for m in o.data.materials]};rows.append(r)
 print(json.dumps(r))
(R/'VANITY_BOUNDED_AUDIT.json').write_text(json.dumps({'source':reg['source_locator'],'sha256':reg['source_sha256'],'rows':rows,'wall_groups':groups},indent=2)+'\n')
