"""One locked serial coordinator obeying the persistent owner level policy."""
import fcntl, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from photo_study_v2 import OUT, M, SPECS, ROOT, POLICY
PY = "/Users/xiwei/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"

def main():
    logs=OUT/"logs";logs.mkdir(exist_ok=True)
    lock=(M/"COORDINATOR.lock").open("a")
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        print("COORDINATOR_ALREADY_RUNNING",flush=True);return
    levels=json.loads(POLICY.read_text())["enabled_levels"]
    state={"status":"RUNNING","pid":os.getpid(),"started":time.time(),"enabled_levels":levels,"expected_enabled_images":len(SPECS)*5*len(levels),"visual_qa":"PER_LEVEL_HERO_GATE_REQUIRED"}
    def save(): (M/"BATCH_STATE.json").write_text(json.dumps(state,indent=2))
    def gallery():
        with (logs/"gallery.log").open("a") as handle:
            subprocess.run([PY,str(ROOT/"scripts/photo_study_v2_gallery.py")],stdout=handle,stderr=subprocess.STDOUT,check=True)
    registry=json.loads((M/"CAMERA_REGISTER.json").read_text());source=Path(registry["source_design"])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==registry["source_sha256"],"Source authority changed"
    save()
    subprocess.Popen(["/usr/bin/caffeinate","-i","-w",str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for room in SPECS:
            for level in levels:
                if all((OUT/room/level/f"VIEW_{i:02d}.png").exists() for i in range(1,6)):continue
                qa=OUT/room/("HERO_QA_"+level+".json")
                if not qa.exists():qa=OUT/room/"HERO_QA.json"
                if not qa.exists() or json.loads(qa.read_text())["status"]!="PASS_FOR_PROPAGATION":
                    state.setdefault("heroes_waiting_for_visual_review",[]).append({"room":room,"level":level});save();continue
                if not (OUT/room/level/"VIEW_01.png").exists():raise RuntimeError("Reviewed hero missing: "+room)
                state.update({"current_room":room,"phase":"followup","level":level});save()
                with (logs/(room+"_followup_"+level+".log")).open("a") as handle:
                    result=subprocess.run([sys.executable,str(ROOT/"scripts/photo_study_v2.py"),"--room",room,"--phase","followup","--levels",level],stdout=handle,stderr=subprocess.STDOUT)
                gallery()
                if result.returncode:raise RuntimeError("Room runner failed: "+room)
                for i in range(2,6):
                    image=OUT/room/level/f"VIEW_{i:02d}.png";meta=image.with_suffix(".json")
                    if meta.exists() and not image.exists():
                        record=json.loads(meta.read_text());state.update({"status":"API_FAILURE_REQUIRES_BOUNDED_REVIEW","failed_job":record.get("job"),"error":record.get("error")});save();return
        state["status"]="HERO_REVIEW_REQUIRED" if state.get("heroes_waiting_for_visual_review") else "ENABLED_LEVELS_GENERATED_PENDING_VISUAL_QA"
    except Exception as exc:
        state.update({"status":"COORDINATOR_ERROR","error":str(exc)});raise
    finally:
        state["finished_this_run"]=time.time();state["source_hash_unchanged"]=hashlib.sha256(source.read_bytes()).hexdigest()==registry["source_sha256"]
        gallery();save();print("PHOTO_V2_COORDINATOR_STOP",json.dumps(state),flush=True)
if __name__=="__main__":main()
