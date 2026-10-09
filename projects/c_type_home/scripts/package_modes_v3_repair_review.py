"""Generate small review sheets only; never accept or generate images."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
from whole_house_modes_v3 import OUT,CFG,geometry
p=argparse.ArgumentParser();p.add_argument("--start",type=int,required=True);p.add_argument("--count",type=int,default=4);a=p.parse_args()
jobs=json.loads((CFG/"VIEW_REPAIRS.json").read_text())[a.start:a.start+a.count]
canvas=Image.new("RGB",(1500,315*len(jobs)),"white");draw=ImageDraw.Draw(canvas)
for row,j in enumerate(jobs):
 room=j["room"];v=j["view"];l=j["level"]
 for col,f in enumerate([geometry(room,v),OUT/room/l/(v+".png"),OUT/room/l/(v+"_repair1.png")]):
  if not f.exists():continue
  with Image.open(f) as im:im=im.convert("RGB");im.thumbnail((495,280));canvas.paste(im,(col*500,row*315+24))
  draw.text((col*500+5,row*315+4),f"{a.start+row} {room} {v} {l} "+["geometry","before","repair"][col],fill="black")
out=OUT/"00_MANIFEST"/f"REPAIR_SCREEN_{a.start:02d}.jpg";canvas.save(out,quality=82);print(out)
