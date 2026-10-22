"""Three controlled high-quality kitchen surface candidates via installed Image2."""
import json,subprocess,time,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PARENT=ROOT/'renders/whole_house_final_study_v1';OUT=PARENT/'kitchen_photo_pilot_v2';CONFIG=ROOT/'render_config/kitchen_prompt_review_v2';CLI=Path.home()/'.codex/skills/codex-image2/scripts/image2.py';GEOMETRY=PARENT/'kitchen/00_camera_gate/VIEW_01_preview.png';STYLE=Path('/Users/xiwei/interior_design/projects/c_type_home/renders/r4_option_a/whole_house_ai_v1/03_kitchen/designer/kitchen_K2_designer_v1.png')
SOURCE=ROOT/'design/console_bath_mirrors_review/CONSOLE400_THREE_BATH_MIRRORS.blend';EXPECTED='1c66d6c98443543de15ca0cf532929067b9d4928d5c4acfb4811869908c04644'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
args=sys.argv[1:];variants=args or ['A_natural_ash','B_warmwhite_grey','C_sage_tile'];records=[]
for name in variants:
 image=OUT/(name+'.png');meta=OUT/(name+'.json');prompt=CONFIG/(name+'.prompt.txt');runprompt=OUT/(name+'.prompt.txt')
 if image.exists() and meta.exists():print('CACHE',name,flush=True);continue
 runprompt.write_text(prompt.read_text()+"""
VIEW-SPECIFIC VISIBILITY: this camera looks toward the cooktop/east worktop and refrigerator tall zone. The real sink and south window are BEHIND camera; do not bring them into this view. Image1 gray/wood patch above hob is the existing hood/cabinet zone, not a new window. Image2 is a HISTORICAL kitchen photo style reference only; its view, cabinet order, crop and window placements must never transfer to image1. Geometry image1 alone defines this shot. Cabinet panels may change color according to direction but every seam/appliance remains in place.
""")
 command=[sys.executable,str(CLI),'edit','--image',str(GEOMETRY),'--image',str(STYLE),'--prompt-file',str(runprompt),'--model','gpt-image-2','--quality','high','--size','1920x1080','--max-attempts','1','--timeout','240','--out',str(image)]
 t=time.time();p=subprocess.run(command,capture_output=True,text=True,timeout=270);log=p.stdout+chr(10)+p.stderr;(OUT/(name+'.cli.log')).write_text(log)
 r={'variant':name,'status':'GENERATED_PENDING_VISUAL_QA' if p.returncode==0 and image.exists() else 'API_FAILED','returncode':p.returncode,'seconds':time.time()-t,'model':'gpt-image-2','quality':'high','requested_size':'1920x1080','image':str(image),'geometry_reference':str(GEOMETRY),'style_reference':str(STYLE),'style_role':'texture/photography only, not architecture','source_sha256':EXPECTED,'retry_count':0};meta.write_text(json.dumps(r,ensure_ascii=False,indent=2));records.append(r);print(name,r['status'],round(r['seconds'],1),flush=True)
 if r['status']=='API_FAILED':print(p.stderr.strip(),flush=True);break
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
(OUT/'RUN_CHECKPOINT.json').write_text(json.dumps({'records_this_run':records,'variants_requested':variants,'source_unchanged':True,'status':'HUMAN_REVIEW' if all((OUT/(n+'.png')).exists() for n in ['A_natural_ash','B_warmwhite_grey','C_sage_tile']) else 'PARTIAL'},ensure_ascii=False,indent=2))
