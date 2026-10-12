"""Reject UV-color partition failure; use clear structural sofa height boundary."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_HUNYUAN_MATERIAL_REVIEW_V3.blend'
if dest.exists():raise SystemExit('Preserved correctedfinish exists')
bpy.ops.wm.open_mainfile(filepath=str(src));changes=[]
bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED']
for f in bed.data.polygons:f.material_index=0
changes.append({'object':bed.name,'rule':'retain completeembeddedbedtexture; reject woodcolor facepartition because fabricedge shadows misclassified'})
sofa=bpy.data.objects['HUNYUAN_V3_LIVING_L_SOFA'];wood=next(i for i,m in enumerate(sofa.data.materials) if m.name=='V5_NATURAL_ASH_PLANKS_OIL');cloth=next(i for i,m in enumerate(sofa.data.materials) if m.name=='V5_NATURAL_FLAX_COTTON');counts={'wood':0,'cloth':0}
for f in sofa.data.polygons:
 # Source model has large woodenplatformbelow filledbags. Colour-based
 # threshold mistook bakedwarmambientshade aswood; geometry boundary clear.
 z=sum(sofa.data.vertices[i].co.z for i in f.vertices)/len(f.vertices)
 f.material_index=wood if z<.287 else cloth;counts['wood' if z<.287 else 'cloth']+=1
changes.append({'object':sofa.name,'rule':'woodenplinth below287mm; upperfilledbags linen; inferred from renderedsource form','counts':counts,'not_exact_semantic_parts':'singlemesh; boundaryneedsvisualcheck'})
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['failed_color_partition']={'path':str(src),'sha256':a['output_sha256'],'result':'REJECTED wood patches on softbags from warmbakedcolour'};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['material_partition_repair']=changes
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('PARTITION_REPAIR',a['output_sha256'],counts)
