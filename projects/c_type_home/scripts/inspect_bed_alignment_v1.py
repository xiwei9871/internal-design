"""Read-only fixed orthographic evidence and planar-face measurements."""
import bpy,json,math
import numpy as np
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'design/bed_alignment_v6/diagnosis';out.mkdir(parents=True,exist_ok=True)
bed=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];scene=bpy.context.scene
for col in bpy.data.collections:col.hide_render=False;col.hide_viewport=False
for obj in scene.objects:obj.hide_render=obj!=bed;obj.hide_viewport=obj!=bed
bed.hide_set(False);bpy.context.view_layer.update()
world=np.array([tuple(bed.matrix_world@v.co) for v in bed.data.vertices]);lo,hi=world.min(axis=0),world.max(axis=0);center=Vector((lo+hi)/2)
faces=[]
for poly in bed.data.polygons:
 pts=world[list(poly.vertices)]
 if len(pts)!=3:continue
 cross=np.cross(pts[1]-pts[0],pts[2]-pts[0]);norm=np.linalg.norm(cross)
 if norm>1e-12:faces.append((poly.index,pts.mean(axis=0),cross/norm,norm/2))
peaks={}
for f in faces:
 if abs(f[2][2])>.999 and .60<f[1][2]<.80:
  z=round(float(f[1][2]),3);peaks[z]=peaks.get(z,0)+f[3]
plane_checks=[]
for z,area in sorted(peaks.items(),key=lambda a:-a[1])[:3]:
 selected=[f for f in faces if abs(f[2][2])>.999 and abs(f[1][2]-z)<.0005]
 indices=set(i for f in selected for i in bed.data.polygons[f[0]].vertices)
 pts=world[sorted(indices)];origin=pts.mean(axis=0)
 coeff=np.linalg.lstsq(np.column_stack((pts[:,0]-origin[0],pts[:,1]-origin[1],np.ones(len(pts)))),pts[:,2]-origin[2],rcond=None)[0]
 plane_checks.append({'z_peak_m':z,'area_m2':float(area),'point_count':len(pts),'xy_bounds_m':[pts[:,:2].min(axis=0).tolist(),pts[:,:2].max(axis=0).tolist()],'fitted_tilt_deg':float(math.degrees(math.atan(np.linalg.norm(coeff[:2])))),'height_spread_mm':float(np.ptp(pts[:,2])*1000)})
bands=[]
for a,b in [(.64,.68),(.69,.72),(.73,.78),(.78,.84),(.84,.92),(.92,1.03)]:
 selected=[f for f in faces if a<f[1][2]<b and abs(f[2][2])>.97]
 if selected:
  weights=np.array([f[3] for f in selected]);normal=sum((f[2]*(1 if f[2][2]>0 else -1)*f[3] for f in selected))/weights.sum()
  bands.append({'z_band_m':[a,b],'triangle_count':len(selected),'horizontal_area_m2':float(weights.sum()),'area_weighted_normal':normal.tolist(),'tilt_deg':float(math.degrees(math.atan2(np.linalg.norm(normal[:2]),normal[2])))})
scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.65,.65,.65);sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_object_outline=True;sh.background_type='WORLD';scene.world.color=(.12,.12,.12)
scene.view_settings.view_transform='Standard';scene.render.film_transparent=False;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam_data=bpy.data.cameras.new('TEMP_BED_ALIGNMENT_CAMERA');cam=bpy.data.objects.new('TEMP_BED_ALIGNMENT_CAMERA',cam_data);scene.collection.objects.link(cam);cam_data.type='ORTHO';cam_data.ortho_scale=2.65;scene.camera=cam;shots=[]
for name,offset,up in [('top',(0,0,5),'Y'),('side',(0,-5,0),'Y'),('foot',(-5,0,0),'Y')]:
 cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z',up).to_euler();scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);shots.append(scene.render.filepath)
report={'source':bpy.data.filepath,'object':bed.name,'rotation_euler':list(bed.rotation_euler),'bounds_m':[lo.tolist(),hi.tolist()],'dominant_planar_checks':plane_checks,'planar_bands':bands,'images':shots,'source_saved':False}
(out/'measurements.json').write_text(json.dumps(report,indent=2)+'\n');print('BED_ALIGNMENT',json.dumps(report))
