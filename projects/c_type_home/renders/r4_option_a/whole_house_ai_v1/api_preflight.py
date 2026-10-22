import json,hashlib,subprocess,time,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;P=json.loads((OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json').read_text());SRC=Path(P['source_path']);BRANCH=Path(P['working_copy']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference():
 import bpy
 from mathutils import Vector
 assert sha(SRC)==P['sha256'];bpy.ops.wm.open_mainfile(filepath=str(BRANCH));bpy.context.view_layer.update();col=bpy.data.collections.new('WHOLE_HOUSE_PREFLIGHT_CAM');bpy.context.scene.collection.children.link(col)
 d=bpy.data.cameras.new('WH_PREFLIGHT_A1');o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(7.15,8.25,1.55);o.rotation_euler=(Vector((4.85,11.45,1.2))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=28;d.clip_start=.03;d.clip_end=100
 for obj in bpy.data.objects:
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS'] for c in obj.users_collection):obj.hide_render=True
 s=bpy.context.scene;s.camera=o;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1024;s.render.resolution_y=688;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.render_aa='16'
 f=OUT/'00_manifest/API_TEST_R4_REFERENCE.png';s.render.filepath=str(f);bpy.ops.render.render(write_still=True);assert sha(SRC)==P['sha256'];print(str(f))
def test():
 ref=OUT/'00_manifest/API_TEST_R4_REFERENCE.png';out=OUT/'00_manifest/API_TEST_GENERATED.png';pf=OUT/'00_manifest/API_TEST_PROMPT.txt';pf.write_text('基于这一张R4客厅白模生成一张日间室内灵感图：严格保留墙窗、飘窗与两组沙发及茶几位置，浅白蜡木、暖白墙、燕麦织物，柔和自然光。保持原3:2近似画幅与相机；不改布局，不增删门窗，无文字。')
 if out.exists():print('PREFLIGHT_EXISTS');return
 start=time.monotonic();cli=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'
 try:
  r=subprocess.run(['rtk','proxy',str(cli),'edit','--image',str(ref),'--prompt-file',str(pf),'--model','gpt-image-2','--quality','medium','--size','1024x688','--n','1','--timeout','180','--max-attempts','1','--out',str(out)],capture_output=True,text=True,timeout=200);log=r.stdout+'\n'+r.stderr;status='PASS' if r.returncode==0 and out.exists() else 'FAIL';error=log[-900:] if status=='FAIL' else None
 except subprocess.TimeoutExpired:status='FAIL';log='bounded image API preflight timed out';error=log
 (OUT/'00_manifest/logs/API_PREFLIGHT.log').write_text(log)
 report=dict(status=status,source_sha256=P['sha256'],reference=str(ref),image=str(out),model='gpt-image-2',endpoint='dotenv configured /v1/images/edits',request_mode='multipart image edit',elapsed_seconds=round(time.monotonic()-start,2),HTTP_status='success2xx' if status=='PASS' else 'seeCLI error if provided',error=error)
 (OUT/'00_manifest/WHOLE_HOUSE_API_PREFLIGHT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if status=='FAIL':(OUT/'00_manifest/WHOLE_HOUSE_AI_PREFLIGHT_FAILURE.md').write_text('# 全屋API preflight失败\n\n已停止，未启动全屋批次。\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':globals()[sys.argv[sys.argv.index('--')+1]]()
