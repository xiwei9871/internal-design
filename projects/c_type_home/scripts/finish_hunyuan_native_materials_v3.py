"""Retain generated whole-object geometry, reuse validated substances by UV color evidence."""
import bpy,json,hashlib,colorsys,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/hunyuan_asset_v3';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_HUNYUAN_FINISH_V3.blend'
if dest.exists():raise SystemExit('Preserved finish exists')
bpy.ops.wm.open_mainfile(filepath=str(src));sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
wood=bpy.data.materials['V5_NATURAL_ASH_PLANKS_OIL'];linen=bpy.data.materials['V5_NATURAL_FLAX_COTTON'];P=Parts(bpy.context.scene.collection,wood,linen);report=[]
for role in ['COUPLE_BED','LIVING_L_SOFA','COUPLE_TV_CONSOLE']:
 o=bpy.data.objects['HUNYUAN_V3_'+role];o.data=o.data.copy();original=o.data.materials[0];base=original.copy();base.name='HUNYUAN_V3_'+role+'_RETAINED_TEXTURE_FINISH'
 # Preserve source diffuse/normal, remove generated metallic transport for
 # nonmetal bed,woodsofa,woodconsole. Blackglass/decor are not truly classified.
 p=base.node_tree.nodes.get('Principled BSDF')
 for name,value in [('Metallic',0),('Specular IOR Level',.5),('Roughness',.65 if role=='COUPLE_BED' else .55)]:
  socket=p.inputs[name]
  for link in list(socket.links):base.node_tree.links.remove(link)
  socket.default_value=value
 if 'Specular Tint' in p.inputs:
  socket=p.inputs['Specular Tint']
  for link in list(socket.links):base.node_tree.links.remove(link)
  socket.default_value=(1,1,1,1)
 o.data.materials[0]=base
 if role=='COUPLE_TV_CONSOLE':report.append({'object':o.name,'retained':'full embedded color/normal for tabletop and supplied decor','calibration':'metal0/spec.5/rough.55','classification':'not attempted becauseplant/decorpaintedcolors mixed'});continue
 color_node=next(n for n in original.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'metallic' not in n.image.name and 'normal' not in n.image.name)
 image=color_node.image;w,h=image.size;pixels=list(image.pixels);uv=o.data.uv_layers.active;chosen=[]
 def sample(u,v):
  x=min(w-1,max(0,int(u*w)));y=min(h-1,max(0,int(v*h)));i=(y*w+x)*4;return pixels[i:i+3]
 woodslot=len(o.data.materials);o.data.materials.append(wood)
 clothslot=len(o.data.materials);o.data.materials.append(linen)
 counts={'wood':0,'native_fabric':0,'retained_fabric':0}
 for face in o.data.polygons:
  # Average source corner/centre samples: generation texture distinguishes
  # yellow ash rail from low-saturation grey/ivory upholstery. This is a
  # heuristic proposal, not material identity certification; renders reviewed.
  coords=[uv.data[li].uv.copy() for li in face.loop_indices];u=sum(v.x for v in coords)/len(coords);v=sum(v.y for v in coords)/len(coords);samples=[sample(u,v)]+[sample(v.x,v.y) for v in coords];rgb=[sum(c[i] for c in samples)/len(samples) for i in range(3)];hh,ss,vv=colorsys.rgb_to_hsv(*rgb)
  iswood=(.045<hh<.16 and ss>.18 and rgb[0]>rgb[2]*1.20)
  if iswood:face.material_index=woodslot;counts['wood']+=1;chosen.append(face.index)
  elif role=='LIVING_L_SOFA':face.material_index=clothslot;counts['native_fabric']+=1
  else:face.material_index=0;counts['retained_fabric']+=1
 # Keep original UV active for embedded texture; native shaders already use
 # namedProductMeters. Create separate texturecoordinates without changingUV0.
 original_active=o.data.uv_layers.active_index;P.uv(o);o.data.uv_layers.active_index=original_active
 for layer in o.data.uv_layers:layer.active_render=False
 o.data.uv_layers[original_active].active_render=True
 report.append({'object':o.name,'counts':counts,'classification_threshold':{'hue':[.045,.16],'saturation_min':.18,'r_over_b_min':1.20},'classification_review':'required final multiview; incorrect partitions are possible','wood_face_indices_sha256':hashlib.sha256(json.dumps(chosen).encode()).hexdigest(),'embedded_uv_unchanged':True,'geometry_unchanged':True})
bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['raw_material_candidate']={'path':str(src),'sha256':a['output_sha256']};a['output']=str(dest);a['output_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['native_material_finish']=report
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print('NATIVE_HUNYUAN_FINISH',a['output_sha256'],report)
