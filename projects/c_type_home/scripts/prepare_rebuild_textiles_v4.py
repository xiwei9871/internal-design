"""Selected-reference artwork rectification and physically tiled rug artwork."""
from PIL import Image,ImageDraw
from pathlib import Path
import numpy as np,random
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4/textures';OUT.mkdir(exist_ok=True)
ref=ROOT/'renders/whole_house_final_study_v1/whole_house_modes_v3/living/B_designer/VIEW_01.png';im=Image.open(ref).convert('RGB')
# Review-coordinate corners from the selected 1100 px image; only artwork surface is rectified.
scale=im.width/1100;quad=[(826*scale,61*scale),(1063*scale,19*scale),(1063*scale,279*scale),(826*scale,263*scale)]
W,H=1500,1200;points=[(0,0),(W-1,0),(W-1,H-1),(0,H-1)];A=[];B=[]
for (x,y),(u,v) in zip(points,quad):
 A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);B.extend([u,v])
coeff=np.linalg.solve(np.array(A),np.array(B));art=im.transform((W,H),Image.Transform.PERSPECTIVE,tuple(coeff),Image.Resampling.BICUBIC);art.save(OUT/'selected_art_rectified.jpg',quality=94)
random.seed(404);im=Image.new('RGB',(1800,1700),(208,193,167));d=ImageDraw.Draw(im)
rust=(153,88,61);ink=(44,60,63)
d.rectangle((90,90,1710,1610),outline=rust,width=72)
d.rectangle((285,260,1480,825),outline=rust,width=128)
d.rectangle((540,615,1650,1390),outline=ink,width=105)
d.rectangle((90,1340,710,1450),fill=rust)
# Small woven yarn color variations; bitmap pattern remains an original reconstruction.
for i in range(17000):
 x=random.randrange(1800);y=random.randrange(1700);c=im.getpixel((x,y));s=random.randrange(-18,19);d.line((x,y,x+random.randrange(2,7),y+random.randrange(1,4)),fill=tuple(max(0,min(255,v+s)) for v in c),width=1)
im.save(OUT/'geometric_rug_woven.jpg',quality=95)
print('SELECTED_ART_AND_RUG_READY')
