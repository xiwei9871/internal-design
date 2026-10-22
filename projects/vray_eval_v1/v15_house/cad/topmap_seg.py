#!/usr/bin/env python3
import json, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union
root=Path('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house')
img=np.asarray(Image.open(root/'cad/topmap.png').convert('RGB')).astype(int)
H,W,_=img.shape
R,G,B=img[...,0],img[...,1],img[...,2]
wall=(B>120)&(B>R+40)&(B>G+40)
tile=(G>120)&(G>R+40)&(G>B+40)
wood=(R>120)&(R>G+40)&(R>B+40)
# 墙膨胀2px封口(每px~10mm)
wall=ndimage.binary_dilation(wall,iterations=2)
interior=~wall
# 连通区
lab,n=ndimage.label(interior)
comps=[]
for i in range(1,n+1):
    m=lab==i
    if m.sum()<4000: continue  # <0.4m²
    ys,xs=np.where(m)
    comps.append((i,m,xs.min(),ys.min(),xs.max(),ys.max(),m.sum()))
print('COMPS',len(comps))
SPAN=20.4; CX,CY=8.5,6.8
def px2mm(x,y): return ((x-W/2)/W*SPAN+CX,(H/2-y)/H*SPAN+CY)
for i,m,x0,y0,x1,y1,area in comps:
    a=px2mm(x0,y0); b=px2mm(x1,y1)
    wt=wood[m].sum(); tl=tile[m].sum()
    print(f'comp{i} area={area*0.01:.1f}m² bounds=({a[0]*1000:.0f},{a[1]*1000:.0f})-({b[0]*1000:.0f},{b[1]*1000:.0f}) wood_px={wt} tile_px={tl}')
np.save(root/'cad/seg_lab.npy',lab); np.save(root/'cad/seg_wall.npy',wall)
np.save(root/'cad/seg_wood.npy',wood); np.save(root/'cad/seg_tile.npy',tile)
json.dump({'span':SPAN,'cx':CX,'cy':CY,'W':W,'H':H},open(root/'cad/seg_meta.json','w'))
