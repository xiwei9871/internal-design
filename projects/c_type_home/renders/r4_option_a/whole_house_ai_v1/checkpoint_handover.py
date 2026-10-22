"""Stop only at a completed-room image boundary; resumable runner preserves all files."""
import os,signal,time,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;pid=97072;D=OUT/'04_leisure';deadline=time.monotonic()+420
while time.monotonic()<deadline:
 count=sum(len(list((D/v).glob('*.png'))) for v in ['faithful','designer','creative'])
 if count>=9:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  (OUT/'00_manifest/RUNNER_HANDOVER.json').write_text(json.dumps(dict(status='SAFE_ROOM_BOUNDARY_HANDOVER',room='leisure',existing_images=count,pid=pid,no_source_change=True,purpose='Strengthen shared variant rules before remaining rooms; resume existing images without regeneration'),ensure_ascii=False,indent=2)+'\n');print('SAFE_HANDOVER_LEISURE9_PRESERVED',flush=True);break
 time.sleep(.05)
else:print('HANDOVER_TIMEOUT_RUNNER_LEFT_ACTIVE',flush=True)
