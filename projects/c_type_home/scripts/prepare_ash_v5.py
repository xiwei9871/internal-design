"""CC0 ash plank maps: aligned single-board crops, linear color adaptation."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/lookdev_v5'
SRC=OUT/'assets/texturecan_ash_0038';DEST=OUT/'assets/ash_furniture_atlas';DEST.mkdir(exist_ok=True)
# Visible board joints were checked in the source maps; omit floor grout in furniture.
CROPS=[(0,446,4096,786),(0,1262,4096,1602),(0,2090,4096,2430),(0,2890,4096,3230)]
FILES={'color':'wood_0038_color_4k.jpg','roughness':'wood_0038_roughness_4k.jpg','normal':'wood_0038_normal_opengl_4k.png','height':'wood_0038_height_4k.png'}
records={}
for role,name in FILES.items():
    im=Image.open(SRC/name).convert('RGB' if role in ['color','normal'] else 'L')
    atlas=Image.new(im.mode,(4096,1360))
    for i,box in enumerate(CROPS):atlas.paste(im.crop(box),(0,i*340))
    if role=='color':
        rgb=np.asarray(atlas,dtype=np.float32)/255
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        mean=linear.mean(axis=(0,1));target=np.array([.31,.195,.102],dtype=np.float32)
        # Preserve board and pore variation; no whitening of the source or fake grain.
        finished=mean+.40*(linear-mean)
        corrected=np.clip(finished*(target/mean),0,1)
        srgb=np.where(corrected<=.0031308,corrected*12.92,1.055*corrected**(1/2.4)-.055)
        atlas=Image.fromarray(np.uint8(np.clip(srgb*255,0,255)))
    p=DEST/(role+'.png');atlas.save(p)
    records[role]={'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':name,'colorspace':'sRGB' if role=='color' else 'Non-Color'}
manifest={'source':'https://www.texturecan.com/details/389/','license':'CC0','kind':'published procedural ash PBR; not photogrammetric scan','crops_xyxy':CROPS,'target_mean_linear_rgb':[.31,.195,.102],'source_variation_retained':.40,'trial_repeat_m':[2.4,.8],'scale_status':'documented furniture lookdev assumption; vendor did not supply physical tile dimensions','files':records}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('ASH_MAPS_READY',list(records))
