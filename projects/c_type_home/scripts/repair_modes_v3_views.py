"""One visual derivative for known drift; locks same queue and preserves originals."""
import fcntl,json
from pathlib import Path
from PIL import Image
from whole_house_modes_v3 import OUT,CFG,geometry,selected_image,run_job,directions

def main():
 lock=(OUT/"00_MANIFEST/COORDINATOR.lock").open("a")
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("QUEUE_RUNNING_REPAIR_DEFERRED");return
 for j in json.loads((CFG/"VIEW_REPAIRS.json").read_text()):
  room=j["room"];view=j["view"];level=j["level"];d=OUT/room/level;original=d/(view+".png");output=d/(view+"_repair1.png")
  if not original.exists() or output.exists() or output.with_suffix(".json").exists():continue
  geo=geometry(room,view);cropdir=OUT/room/"review/repair_refs";cropdir.mkdir(parents=True,exist_ok=True)
  selected=selected_image(OUT,room,level,"VIEW_01");im=Image.open(selected).convert("RGB");w,h=im.size
  refs=[]
  for name,box in [("surface",(.20,.45,.55,.75)),("furniture",(.25,.52,.70,.90))]:
   c=im.crop(tuple(int(v*(w if k%2==0 else h)) for k,v in enumerate(box)));c.thumbnail((500,400));f=cropdir/(level+"_"+name+".jpg")
   if not f.exists():c.save(f,quality=85)
   refs.append(f)
  if j["kind"]=="decor":
   images=[original,geo];text="Image1 is the current rendered view; image2 is its accurate source camera/architecture. Correct only relocated decorations: "+j["reason"]+" Keep current textiles, rug, main furniture, camera/crop and architecture. Do not place hero art on another wall or transplant curtains into other-room openings."
  else:
   images=[geo,*refs];text="Image1 is the ONLY viewpoint/crop authority: create the exact pictured close/detail crop, same perspective, visible planes, doorway/window positions and clipped furniture. Image2/image3 are tightly cropped same-room material/furniture appearance samples, NOT a layout/view reference. Do not turn this into a whole-room hero. "+j["reason"]
   text+=" Room functions and recognition: "+directions()[room]["functions"]
   if level=="A_faithful":text+=" Strict Faithful original furniture/cabinet topology, no art/lamp or extra furnishings. Soft bedrunner is textile. Chair must have source back, no stool replacement."
   elif level=="B_designer":text+=" Keep original mainfurniture and use modest approved soft styling visible here only."
   else:text+=" Creative idea is inspiration only; preserve same room concept furniture family through these cropped appearance samples, not new design. Actual crop and room-envelope stay."
  text+=" Overall simple paleash/ivory, bright neutrallight, realistic materials/contacts, no people/labels. No extra windows or duplicated mirrors/fixtures."
  prompt=d/(view+"_repair1.prompt.txt");prompt.write_text(text)
  r=run_job({"room_id":room,"view_id":view+"_repair1","level":level,"images":[str(f) for f in images],"prompt":str(prompt),"out":str(output)})
  if r["status"]=="API_FAILED":break
if __name__=="__main__":main()
