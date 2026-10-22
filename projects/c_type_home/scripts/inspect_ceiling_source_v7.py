"""Read existing source ceiling geometry without saving source .blend."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';D.mkdir(exist_ok=True)
source=R/'design/console1310_v5/WHOLE_HOUSE_CONSOLE1310_REAL_V5.blend';assert hashlib.sha256(source.read_bytes()).hexdigest()=='3d75cbabe06a0bbace8fb95fb395bcc7f645ed5d26d6fed2d1fb094f0881f63a'
bpy.ops.wm.open_mainfile(filepath=str(source))
data={}
for o in bpy.data.objects:
 if o.name.startswith('CEILING_') and o.type=='MESH' and not o.hide_render:
  data[o.name]={'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons]}
dest=D/'SOURCE_CEILING_GEOMETRY.json';assert not dest.exists(),'Preserved input exists'
dest.write_text(json.dumps({'ceilings':data},indent=2)+'\n');print('SOURCE_CEILINGS',list(data))
