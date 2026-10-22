"""Reuse project-tested ash maps and the owner's marble sample; no generated imagery."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]
D = R / 'design/finishes_v11/assets'
D.mkdir(parents=True, exist_ok=True)
wood_source = R / 'renders/whole_house_final_study_v1/assets/ash/ash_veneer_diffuse_2k.jpg'
tile_source = Path('/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T/codex-clipboard-a2a12490-0a11-4c9e-8e8c-6107a4544a02.png')
hashfile = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = []
# Retain the existing 1200x180mm staggered-board method in a portable raster atlas.
# The image is the same tested ash asset; only an explicit color normalization,
# board offset and 1mm joint are baked, so WebGL and Blender share the color.
N = 1536
im = np.asarray(Image.open(wood_source).convert('RGB').resize((N, N)), dtype=np.float32) / 255
linear = np.where(im <= .04045, im / 12.92, ((im + .055) / 1.055) ** 2.4)
target = np.array([.42, .325, .215])
linear *= target / linear.mean(axis=(0, 1))
atlas = np.zeros_like(linear)
for row in range(6):
    y0, y1 = row * N // 6, (row + 1) * N // 6
    strip = np.roll(linear[y0:y1], row * 193, axis=1).copy()
    strip *= [.98, 1.02, .99, 1.01, .97, 1.03][row]
    # Six 180mm boards repeat over 1080mm; end joints stagger by600mm.
    seam = 0 if row % 2 == 0 else N // 2
    strip[:, max(0, seam - 1):seam + 1] *= .66
    strip[:2] *= .72
    atlas[y0:y1] = strip
atlas = np.clip(atlas, 0, 1)
srgb = np.where(atlas <= .0031308, atlas * 12.92, 1.055 * atlas ** (1 / 2.4) - .055)
wood = D / 'pale_ash_floor_1200x1080.jpg'
Image.fromarray(np.uint8(np.clip(srgb, 0, 1) * 255)).save(wood, quality=94)
records.append({'output':str(wood), 'sha256':hashfile(wood), 'source':str(wood_source), 'source_sha256':hashfile(wood_source), 'license':'Inherited project asset, see assets/ash/asset-manifest.json', 'repeat_m':[1.2,1.08], 'board_mm':[1200,180], 'target_mean_linear_rgb':target.tolist()})
# Crop whitespace and retain an undistorted 2:1 sample from owner Image3.
# This is appearance guidance, not a selected vendor/SKU or certified PBR scan.
sample = Image.open(tile_source).convert('RGB').crop((58, 100, 458, 300)).resize((1536,768), Image.Resampling.LANCZOS)
tile = np.asarray(sample, dtype=np.float32)
# Restrained warm-grey2mm grout for1200x600mm tiles, straight grid.
tile[:3] = [221,220,216]
tile[:,:3] = [221,220,216]
tilepath = D / 'owner_subtle_marble_1200x600.jpg'
Image.fromarray(np.uint8(tile)).save(tilepath, quality=96)
records.append({'output':str(tilepath), 'sha256':hashfile(tilepath), 'source':str(tile_source), 'source_sha256':hashfile(tile_source), 'crop_xyxy':[58,100,458,300], 'repeat_m':[1.2,.6], 'grout_mm':2, 'source_status':'Owner supplied appearance reference; product and slip rating pending'})
(D/'manifest.json').write_text(json.dumps({'method':'Reused existing tested ash photography and owner sample; no AI image request', 'assets':records}, indent=2)+'\n')
print('FINISH_TEXTURES', [(p['repeat_m'], p['sha256']) for p in records])
