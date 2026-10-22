import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from room_plan import ROOMS

def build(room_id,mode='initial',cameras=None):
 room=next(r for r in ROOMS if r['id']==room_id);D=OUT/room['folder'];cams=json.loads((D/'reports/CAMERA_REGISTER.json').read_text());rows=json.loads((D/'reports/IMAGES.json').read_text())
 if cameras:cams=[c for c in cams if c['id'] in cameras]
 path=D/'reports/proxies'/('QC_'+mode+'_'+('_'.join(c['id'] for c in cams))+'.jpg');path.parent.mkdir(exist_ok=True)
 board=Image.new('RGB',(1120,212*len(cams)+28),'#f5f3ee');dr=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
 dr.text((6,5),room_id+' | '+mode+' | R4 / Faithful / Designer / Creative',fill='#243b30',font=font)
 for ci,c in enumerate(cams):
  files=[Path(c['reference'])]
  for v in ['faithful','designer','creative']:
   row=next((r for r in rows if r['camera']==c['id'] and r['variant']==v),None)
   f=Path(row['output']) if row else None
   if mode=='retry' and f:
    candidate=f.with_name(f.stem+'_review_retry.png')
    if candidate.exists():f=candidate
   files.append(f)
  for col,f in enumerate(files):
   x=col*280;y=28+ci*212
   dr.text((x+5,y),c['id']+' '+['R4','FAITHFUL','DESIGNER','CREATIVE'][col],font=font,fill='#243b30')
   if f and f.exists():
    im=Image.open(f).convert('RGB');im.thumbnail((274,184));board.paste(im,(x+3,y+22))
   else:dr.text((x+5,y+85),'NOT AVAILABLE',font=font,fill='#a33')
 board.save(path,quality=90)
 return str(path)
if __name__=='__main__':
 mode=sys.argv[2] if len(sys.argv)>2 else 'initial'
 cams=sys.argv[3].split(',') if len(sys.argv)>3 else None
 print(build(sys.argv[1],mode,cams))
