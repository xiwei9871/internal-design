"""Owner-approved three-mode studies: isolated outputs, serial generation and hero gates."""
import argparse,fcntl,hashlib,html,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"renders/whole_house_final_study_v1"
OUT=PARENT/"whole_house_modes_v3"
CFG=ROOT/"render_config/whole_house_modes_v3"
LEVELS=["A_faithful","B_designer","C_creative"]
PY="/Users/xiwei/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
CLI=Path.home()/".codex/skills/codex-image2/scripts/image2.py"

def atomic_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+".tmp")
 temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));os.replace(temp,path)

def unattempted(path):
 path=Path(path);return not path.exists() and not path.with_suffix(".json").exists()

def selected_image(root,room,level,view):
 original=Path(root)/room/level/(view+".png")
 meta=original.with_suffix(".json")
 if meta.exists():
  chosen=json.loads(meta.read_text()).get("selected_derivative")
  if chosen:
   p=Path(chosen)
   if not p.is_file():raise ValueError("Selected derivative missing: "+chosen)
   return p
 return original

def gate_ready(root,room,level):
 gate=Path(root)/room/("HERO_QA_"+level+".json")
 return (Path(root)/room/level/"VIEW_01.png").exists() and gate.exists() and json.loads(gate.read_text()).get("status")=="PASS_FOR_PROPAGATION"

def directions():return json.loads((CFG/"ROOM_DIRECTIONS.json").read_text())

def geometry(room,view):
 if room=="living" and view in ["VIEW_03","VIEW_05"]:return PARENT/"living/camera_review_v2"/(view+"_preview.png")
 p=PARENT/"camera_review_v3"/(room+"_"+view+"_preview.png")
 return p if p.exists() else PARENT/room/"00_camera_gate"/(view+"_preview.png")

def prompt_contract(room,view,level,followup):
 d=directions()[room]
 shared="Simple pale naturalwood home: light ash/oak, ivory/flax textiles, warmoffwhite, bright neutral daylight, limited muted accent colors and ample negative space. No dark marble, heavy walnut/slat featurewall, hotel treatment, oversized dramatic art or orange wash. Realistic contact shadows, material scale, equipment mechanisms; no people/lettering. Room function: "+d["functions"]
 if level=="B_designer":
  text="DESIGNER STYLING, not furniture replacement or blanket recoloring. Image1 is THIS view Faithful for exact crop/perspective and main furniture. Image2 is the approved current clay for camera, walls, door/window/levels and original main furniture evidence. Where the photo has camera drift, image2 current framing wins. Preserve source main furniture family, count, placement and built-in divisions. Source flat ceiling and all openings stay. Added art, curtains, lamps, books, towels, cushions and plants are intentional styling proposals, but never block circulation. "+shared+" ROOM STYLING: "+d["designer"]
 else:
  text="CREATIVE INSPIRATION, not a geometry-certified installation. Image1 is THIS view Faithful as room/camera/space context, NOT a lock of original furniture. You may redesign furniture, grouping and storage ideas within the owner-approved simple pale-wood aesthetic. Image2 is spatial-envelope/view-direction evidence ONLY, its original furniture is not mandatory. Keep actual room size, openings and functional access plausible, not an enlarged invented room. "+shared+" ROOM CONCEPT: "+d["creative"]
 if followup:
  text+=" Image3 is the SAME ROOM/SAME MODE visually screened hero: continue its exact designed furniture family, art, textiles, lighting and material allocations, not a new design per view. Rotate that same room concept into THIS view: do not copy the hero crop. Current image1/image2 indicate where the camera is and what anchors are visible. Details stay detail shots, no wide shot substitution. Show only elements actually visible from this view; other-room/behind-camera props stay absent. If an object was redesigned, show the corresponding hero object here, not the original placeholder."
  text+=" Each hero artwork, lamp, curtain and accessory has ONE fixed physical location in the room. Do not copy art to a different empty wall, or move a window curtain onto other-room glazing. Objects on a wall behind this camera must be absent; fewer visible decorative objects is correct. Use wall/window/door identity, not just a matching blank region."
 else:text+=" Subsequent input pictures are actual furniture/material workmanship references ONLY; do not copy their scene, quantity or object type into this room."
 if room=="living":
  text+=" VIEW VISIBILITY: "+{"VIEW_01":"northwindow/chaise/rightcabinet/door,stairs behind","VIEW_02":"reverse toward sofa/stairs/dining,northwindow behind camera","VIEW_03":"toward stairs/reading/dining,do not invent curved ceiling","VIEW_04":"northwindow/door/partialchaise crop,not full room","VIEW_05":"dining approach toward living/window,distinct orientation"}[view]
  if view=="VIEW_02":text+=" The hero painting above the long east cabinet is behind/mostly outside this reverse crop; NEVER place it above the L sofa on the blank sofa-back wall. Hero curtains belong to the north living window behind this camera, not dining sliding doors. Hero reading lamp stays by the chaise/north window, not moved beside sofa."
 text+=" Output one finished photograph, no labels. Render the intended DESIGN, not generic extra decoration."
 return text

def prepare():
 from PIL import Image
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"00_MANIFEST").mkdir(exist_ok=True)
 reg=json.loads((PARENT/"photo_study_v2/00_MANIFEST/CAMERA_REGISTER.json").read_text())
 assert hashlib.sha256(Path(reg["source_design"]).read_bytes()).hexdigest()==reg["source_sha256"]
 atomic_json(OUT/"00_MANIFEST/CAMERA_REGISTER.json",reg)
 copies=0
 for room in directions():
  for i in range(1,6):
   view=f"VIEW_{i:02d}";src=PARENT/"photo_study_v2"/room/"A_faithful"/(view+".png");dst=OUT/room/"A_faithful"/(view+".png")
   dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists():shutil.copy2(src,dst);copies+=1
   meta=dst.with_suffix(".json")
   if not meta.exists():
    old=src.with_suffix(".json");r=json.loads(old.read_text()) if old.exists() else {}
    atomic_json(meta,{"status":"REUSED_FAITHFUL","source_path":str(src),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"native_size":list(Image.open(src).size),"visual_status":r.get("visual_status","REVIEW"),"input_authority":"ORIGINAL_BLENDER_NOT_PHOTO"})
 for level,src in [("B_designer",PARENT/"living_style_pilot_v4/DESIGNER.png"),("C_creative",PARENT/"living_style_pilot_v5/CREATIVE.png")]:
  dst=OUT/"living"/level/"VIEW_01.png";dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():shutil.copy2(src,dst)
  if not dst.with_suffix(".json").exists():atomic_json(dst.with_suffix(".json"),{"status":"OWNER_ACCEPTED_PILOT_REUSED","source_path":str(src),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"native_size":list(Image.open(src).size)})
  atomic_json(OUT/"living"/("HERO_QA_"+level+".json"),{"status":"PASS_FOR_PROPAGATION","authority":"OWNER_APPROVED_2026-10-09","notes":["Owner accepts the three-mode comparison and authorizes whole-house propagation."]})
 baseline=OUT/"00_MANIFEST/PRESERVATION_BASELINE.json"
 if not baseline.exists():
  files=list((PARENT/"photo_study_v2").glob("*/*/VIEW_*.png"))+list((PARENT/"production_batch_v1").glob("*/*/VIEW_*.png"))
  files += [PARENT/"living_style_pilot_v4/DESIGNER.png",PARENT/"living_style_pilot_v5/CREATIVE.png"]
  atomic_json(baseline,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
 update_gallery();print("PREPARED_REUSE",copies,flush=True)

def make_job(room,view,level):
 dst=OUT/room/level/(view+".png");dst.parent.mkdir(parents=True,exist_ok=True)
 images=[selected_image(OUT,room,"A_faithful",view),geometry(room,view)]
 if view!="VIEW_01":images.append(selected_image(OUT,room,level,"VIEW_01"))
 else:images += [PARENT/"photo_study_v2/references"/(n+".jpg") for n in directions()[room]["refs"][:2]]
 prompt=dst.with_suffix(".prompt.txt")
 if unattempted(dst):
  text=prompt_contract(room,view,level,view!="VIEW_01")
  if view!="VIEW_01":
   gate=json.loads((OUT/room/("HERO_QA_"+level+".json")).read_text())
   text+=" CONTINUITY REGISTER: "+" ".join(gate.get("continuity",[]))
  prompt.write_text(text)
 return {"room_id":room,"view_id":view,"level":level,"images":[str(x) for x in images],"prompt":str(prompt),"out":str(dst)}

def run_job(job):
 from PIL import Image
 dst=Path(job["out"]);meta=dst.with_suffix(".json")
 if dst.exists():return {"status":"CACHE_PRESERVED"}
 if meta.exists():return {**json.loads(meta.read_text()),"skipped_prior_attempt":True}
 images=[Path(x) for x in job["images"]];prompt=Path(job["prompt"])
 estimated=sum(((x.stat().st_size+2)//3)*4 for x in images)+prompt.stat().st_size+65536
 if estimated>24*1024*1024:raise ValueError("Input over24MiB conservative budget")
 reg=json.loads((OUT/"00_MANIFEST/CAMERA_REGISTER.json").read_text())
 assert hashlib.sha256(Path(reg["source_design"]).read_bytes()).hexdigest()==reg["source_sha256"]
 r={"job":job,"status":"RUNNING","started":time.time(),"input_hashes":{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in images},"prompt_sha256":hashlib.sha256(prompt.read_bytes()).hexdigest(),"estimated_input_bytes":estimated,"native_size":None,"retry_count":0}
 atomic_json(meta,r)
 cmd=["rtk","proxy","python3",str(CLI),"edit"]
 for x in images:cmd += ["--image",str(x)]
 cmd += ["--prompt-file",str(prompt),"--model","gpt-image-2","--quality","high","--size","1920x1080","--max-attempts","1","--timeout","240","--out",str(dst)]
 for attempt in range(2):
  try:p=subprocess.run(cmd,capture_output=True,text=True,timeout=270)
  except subprocess.TimeoutExpired:p=subprocess.CompletedProcess(cmd,124,"","timeout after270s")
  dst.with_suffix(f".attempt{attempt}.log").write_text(p.stdout+"\n"+p.stderr)
  success=p.returncode==0 and dst.exists()
  r.update({"status":"GENERATED_PENDING_VISUAL_QA" if success else "API_FAILED","returncode":p.returncode,"retry_count":attempt,"seconds":time.time()-r["started"],"error":None if success else p.stderr[:1600]})
  if success:
   with Image.open(dst) as im:r["native_size"]=list(im.size);im.verify()
  atomic_json(meta,r);atomic_json(dst.with_suffix(f".attempt{attempt}.json"),r)
  if success:break
  transient=any(x in p.stderr for x in ["HTTP 500","HTTP 502","HTTP 503","HTTP 504","HTTP 507","HTTP 524","timeout after"])
  if attempt or not transient:break
  time.sleep(10)
 print("MODE_DONE",job["room_id"],job["view_id"],job["level"],r["status"],round(r["seconds"],1),flush=True)
 return r

def update_gallery():
 from PIL import Image,ImageDraw
 counts={l:0 for l in LEVELS};records=[];sections=[];names={r["room_id"]:r["display_name"] for r in json.loads((PARENT/"00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json").read_text())["rooms"]}
 for room in directions():
  review=OUT/room/"review";review.mkdir(parents=True,exist_ok=True);canvas=Image.new("RGB",(1500,590),"#f5f2e9");draw=ImageDraw.Draw(canvas);figs=[]
  for row,level in enumerate(LEVELS):
   for i in range(1,6):
    view=f"VIEW_{i:02d}";p=OUT/room/level/(view+".png");meta=p.with_suffix(".json");r=json.loads(meta.read_text()) if meta.exists() else {};status=r.get("visual_status",r.get("status","NOT_GENERATED"));p=selected_image(OUT,room,level,view);x=(i-1)*300;y=row*195
    if p.exists():
     with Image.open(p) as image:im=image.convert("RGB");native=list(image.size)
     counts[level]+=1;thumb=review/(level+"_"+view+"_thumb.jpg")
     if not thumb.exists() or thumb.stat().st_mtime<p.stat().st_mtime or r.get("selected_derivative") and thumb.stat().st_mtime<meta.stat().st_mtime:
      t=im.copy();t.thumbnail((800,450));t.save(thumb,quality=83)
     im.thumbnail((294,165));canvas.paste(im,(x,y+20));content=f'<a href="/{p.relative_to(PARENT)}" target="_blank"><img loading="lazy" src="/{thumb.relative_to(PARENT)}"></a>'
     records.append({"room_id":room,"level":level,"view_id":view,"path":str(p),"native_size":native,"status":status})
    else:content=f'<div class="missing">{html.escape(status)}</div>';draw.rectangle((x,y+20,x+294,y+185),fill="#e6e2d8")
    draw.text((x+5,y+2),level+" "+view,fill="black");figs.append(f'<figure><small>{level} {view}</small>{content}<p>{html.escape(status)}</p></figure>')
  canvas.save(review/"ROOM_3X5.jpg",quality=83)
  gates=[]
  for level in LEVELS[1:]:
   q=OUT/room/("HERO_QA_"+level+".json")
   if q.exists():gates+=json.loads(q.read_text()).get("notes",[])
  qa=OUT/room/"VISUAL_QA.json"
  if qa.exists():gates += [f"{f.get('level','')} {f.get('view_id','')} {f.get('status','')}: {f.get('reason','')}" for f in json.loads(qa.read_text()).get("flags",[])]
  sections.append(f'<section id="{room}"><h2>{names[room]}</h2><p>{html.escape(" · ".join(gates))}</p><div class="matrix">'+"".join(figs)+"</div></section>")
 summary={"expected":225,"generated":sum(counts.values()),"counts":counts,"source_writeback":False,"creative":"INSPIRATION_ONLY","visual_acceptance":"PENDING","updated":time.time()}
 atomic_json(OUT/"00_MANIFEST/PROGRESS.json",summary);atomic_json(OUT/"00_MANIFEST/RENDER_REGISTER.json",{"summary":summary,"images":records})
 css='body{font:15px system-ui;margin:0;background:#f7f4ed;color:#333}header,section{padding:24px 3vw}nav{position:sticky;top:0;background:#f7f4ed;padding:15px;display:flex;flex-wrap:wrap;gap:12px}.matrix{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}figure{margin:0;background:white;padding:6px}img{width:100%}.missing{aspect-ratio:16/9;background:#e6e2d8;display:grid;place-content:center}figure p{font-size:10px}section{scroll-margin-top:90px}@media(max-width:850px){.matrix{grid-template-columns:repeat(2,1fr)}}'
 nav="".join(f'<a href="#{room}">{names[room]}</a>' for room in directions())
 page=f'<!doctype html><html lang="zh"><meta charset="utf-8"><meta http-equiv="refresh" content="90"><title>全屋三模式V3</title><style>{css}</style><header><h1>全屋三模式 V3</h1><p>{summary["generated"]}/225，Faithful {counts["A_faithful"]}/75 · Designer {counts["B_designer"]}/75 · Creative {counts["C_creative"]}/75</p><p>Faithful忠实模型；Designer保留主体深化软装；Creative在简洁浅原木风格内探索设计。Creative仅为灵感，不回写模型。旧图与已知Faithful问题均保留；数量不是验收通过。</p></header><nav>{nav}</nav>'+"".join(sections)+"</html>"
 (OUT/"review_gallery.html").write_text(page);return summary

def coordinate():
 OUT.mkdir(exist_ok=True);m=OUT/"00_MANIFEST";m.mkdir(exist_ok=True);lock=(m/"COORDINATOR.lock").open("a")
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALREADY_RUNNING");return
 state={"status":"RUNNING","pid":os.getpid(),"started":time.time(),"scope":"wholehouse225","waiting":[]};atomic_json(m/"BATCH_STATE.json",state)
 subprocess.Popen(["/usr/bin/caffeinate","-i","-w",str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for room in directions():
   for level in LEVELS[1:]:
    if not (OUT/room/level/"VIEW_01.png").exists():
     state.update({"room":room,"level":level,"phase":"hero","view":"VIEW_01"});atomic_json(m/"BATCH_STATE.json",state)
     r=run_job(make_job(room,"VIEW_01",level));update_gallery()
     if r["status"]=="API_FAILED" or r.get("skipped_prior_attempt"):state.update({"status":"API_FAILED_REQUIRES_REVIEW","failed":r});return
   for level in LEVELS[1:]:
    if not gate_ready(OUT,room,level):state["waiting"].append({"room":room,"level":level});continue
    for i in range(2,6):
     view=f"VIEW_{i:02d}";state.update({"room":room,"level":level,"phase":"followup","view":view});atomic_json(m/"BATCH_STATE.json",state)
     r=run_job(make_job(room,view,level));update_gallery()
     if r["status"]=="API_FAILED" or r.get("skipped_prior_attempt"):state.update({"status":"API_FAILED_REQUIRES_REVIEW","failed":r});return
  state["status"]="HERO_REVIEW_REQUIRED" if state["waiting"] else "GENERATED_PENDING_ALL_VIEW_QA"
 except Exception as exc:state.update({"status":"ERROR","error":str(exc)});raise
 finally:
  state["finished"]=time.time();atomic_json(m/"BATCH_STATE.json",state);update_gallery();print("COORDINATOR_STOP",state["status"],flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument("action",choices=["prepare","run","gallery"]);a=p.parse_args()
 if a.action=="prepare":prepare()
 elif a.action=="run":coordinate()
 else:print(update_gallery())
if __name__=="__main__":main()
