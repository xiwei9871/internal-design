"""Original reference-inspired patterns, no AI or reference pixel copying."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import random
random.seed(109)
out=Path(__file__).resolve().parents[1]/'design/living_dining_detail_v1/textures'
out.mkdir(parents=True,exist_ok=True)
cream=(219,210,190); rust=(147,76,49); ink=(48,65,73)
im=Image.new('RGB',(1800,1800),cream); d=ImageDraw.Draw(im)
d.rectangle((105,105,1695,1695),outline=rust,width=50)
d.rectangle((210,235,1420,680),outline=rust,width=95)
d.rectangle((420,680,1570,1400),outline=ink,width=75)
d.rectangle((100,1450,880,1565),fill=rust)
d.rectangle((950,1540,1570,1600),fill=ink)
im.save(out/'rug_original.png')
im=Image.new('RGB',(1500,1200),(221,211,190)); d=ImageDraw.Draw(im)
d.polygon([(60,0),(760,0),(720,350),(1010,415),(960,620),(480,570),(420,920),(45,1040)],fill=rust)
d.polygon([(0,755),(450,700),(610,530),(1110,575),(1480,400),(1500,710),(1010,820),(780,1090),(120,1190)],fill=ink)
d.rectangle((1050,820,1500,1200),fill=(157,91,62))
for i in range(5200):
 x=random.randrange(1500); y=random.randrange(1200); c=im.getpixel((x,y)); shift=random.randrange(-25,26)
 d.line((x,y,x+random.randrange(1,15),y+random.randrange(1,8)),fill=tuple(max(0,min(255,v+shift)) for v in c),width=random.randrange(1,4))
im.save(out/'art_original.png')
print(out)
