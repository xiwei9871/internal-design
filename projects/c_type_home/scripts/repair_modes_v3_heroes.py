"""One bounded visual revision per flagged hero; no overwriting originals or auto-gates."""
import fcntl,json,sys
from whole_house_modes_v3 import OUT,CFG,run_job

def main():
 lock=(OUT/"00_MANIFEST/COORDINATOR.lock").open("a")
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("QUEUE_RUNNING_REPAIR_DEFERRED");return
 for j in json.loads((CFG/"HERO_REPAIRS.json").read_text()):
  room=j["room"];level=j["level"];d=OUT/room/level
  output=d/"VIEW_01_repair1.png";prompt=d/"VIEW_01_repair1.prompt.txt"
  if output.exists() or output.with_suffix(".json").exists():continue
  faithful=OUT/room/"A_faithful/VIEW_01.png"
  text="Image1 is current candidate; image2 is original room photo, spatial/lightwood context only for Creative, main furniture authority for Designer. Owner style ALWAYS simple PALE NATURAL WOOD, ivory/flax, bright neutrallight, sparse objects. "+j["instruction"]+" No people/lettering. This is a targeted new candidate, source model unchanged."
  prompt.write_text(text)
  job={"room_id":room,"view_id":"VIEW_01_repair1","level":level,"images":[str(d/"VIEW_01.png"),str(faithful)],"prompt":str(prompt),"out":str(output)}
  r=run_job(job)
  if r["status"]=="API_FAILED":break
if __name__=="__main__":main()
