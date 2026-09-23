"""Bounded appearance experiment: native Image2 CLI, eroded material/object masks."""
from pathlib import Path
import json
import os
import subprocess
import sys
import hashlib
import re
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion,binary_dilation,gaussian_filter
import OpenEXR
ROOT=Path(__file__).resolve().parent
CLI=Path.home()/'.codex/skills/codex-image2/bin/codex-image2-darwin-arm64'

def prepare(key):
    out=ROOT/'surface_edits'; out.mkdir(exist_ok=True)
    f=OpenEXR.File(str(ROOT/'renders'/f'{key}_passes.exr')); header=f.header(0)
    manifest=json.loads(next(v for k,v in header.items() if k.endswith('/manifest') and header.get(k.rsplit('/',1)[0]+'/name')=='ViewLayer.CryptoMaterial'))
    ids=[int(manifest[k],16) for k in ['White ash / matte grain','Ivory cotton','Warm linen woven']]
    coverage=None; object_ids=None
    for p in f.parts:
        if 'CryptoMaterial' in p.name():
            ch=p.channels; prefix=p.name()+'.'
            pair1=ch[prefix+'r'].pixels.astype(np.float32).view(np.uint32); pair2=ch[prefix+'b'].pixels.astype(np.float32).view(np.uint32)
            add=np.isin(pair1,ids)*ch[prefix+'g'].pixels+np.isin(pair2,ids)*ch[prefix+'a'].pixels
            coverage=add if coverage is None else coverage+add
        if p.name()=='ViewLayer.CryptoObject00': object_ids=p.channels[p.name()+'.r'].pixels.astype(np.float32).view(np.uint32)
    edge=np.zeros(object_ids.shape,bool); edge[:,1:]|=object_ids[:,1:]!=object_ids[:,:-1]; edge[1:,:]|=object_ids[1:,:]!=object_ids[:-1,:]
    allowed=binary_erosion(coverage>.98,iterations=9)&~binary_dilation(edge,iterations=9)
    Image.fromarray((allowed*255).astype(np.uint8)).save(out/f'{key}_allowed.png')
    mask=np.zeros((*allowed.shape,4),np.uint8); mask[:,:,:3]=255; mask[:,:,3]=np.where(allowed,0,255)
    Image.fromarray(mask).save(out/f'{key}_api_mask.png')
    prompt='''Asset type: Interior visualization, localized material refinement.
Input image is the exact approved geometric render. Improve only texture realism inside the editable mask: fine pale ash wood grain, tactile woven neutral linen, natural cotton bedding folds within the existing surfaces. Retain original color, luminance, material direction and lighting distribution. Keep all furniture edges and shapes, cabinet divisions, camera, walls, windows, doors, appliance order and perspective unchanged. Keep the same image crop and aspect ratio. Do not add any objects, plants, artwork, lights, handles, shelves, trim, patterns, openings, reflections of new objects, text or watermark. Do not redesign the room. This is a surface-detail pass, not a new scene.'''
    (out/f'{key}_prompt.txt').write_text(prompt)
    return out

def main(key):
    out=prepare(key); raw=out/f'{key}_raw.png'
    env=dict(os.environ)
    dotenv=Path.home()/'.env'
    if dotenv.exists():
        for line in dotenv.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1)
                if k.strip() in ['CODEX_API_URL','CODEX_API_KEY']: env.setdefault(k.strip(),v.strip().strip('"').strip("'"))
    if not env.get('CODEX_API_KEY'): raise SystemExit('CODEX_API_KEY is not configured locally')
    if not raw.exists():
        command=[str(CLI),'edit','--image',str(ROOT/'renders'/f'{key}.png'),'--mask',str(out/f'{key}_api_mask.png'),'--prompt-file',str(out/f'{key}_prompt.txt'),'--size','auto','--quality','high','--out',str(raw),'--max-attempts','1','--timeout','240']
        cp=subprocess.run(command,env=env,capture_output=True,text=True)
        if cp.returncode:
            # Never echo remote response/headers or process environment.
            match=re.search(r'API request failed with HTTP \d{3}|API request failed: network error or timeout|API returned invalid JSON|API response contains no image data',cp.stderr)
            reason=match.group(0) if match else 'CLI failed; no image produced'
            (out/f'{key}_status.json').write_text(json.dumps({'status':'generation_failed','returncode':cp.returncode,'reason':reason}))
            print(reason)
            raise SystemExit('Native Image2 edit failed; no candidate published')
    base=Image.open(ROOT/'renders'/f'{key}.png').convert('RGB'); gen=Image.open(raw).convert('RGB')
    if abs(gen.width/gen.height-base.width/base.height)>.01: raise ValueError('Generated crop/aspect changed; reject candidate')
    gen=gen.resize(base.size,Image.Resampling.LANCZOS)
    allowed=np.asarray(Image.open(out/f'{key}_allowed.png'))>0
    weight=np.minimum(gaussian_filter(allowed.astype(float),2),allowed.astype(float))*.45
    b=np.asarray(base); g=np.asarray(gen); merged=np.rint(b*(1-weight[:,:,None])+g*weight[:,:,None]).astype(np.uint8)
    Image.fromarray(merged).save(out/f'{key}_composited.png')
    assert np.array_equal(merged[~allowed],b[~allowed])
    report={'status':'candidate_manual_review_pending','model':'gpt-image-2','quality':'high','size_requested':'auto','generated_size':Image.open(raw).size,'output_size':base.size,'allowed_area_fraction':float(allowed.mean()),'unmasked_pixels_changed':0,'blend_strength':.45,'source_sha256':hashlib.sha256((ROOT/'renders'/f'{key}.png').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((out/f'{key}_composited.png').read_bytes()).hexdigest(),'scope':'Material interiors only; object boundaries protected; not automatic approval'}
    (out/f'{key}_status.json').write_text(json.dumps(report,indent=2))
    print(key,json.dumps(report),flush=True)

if __name__=='__main__': main(sys.argv[1])
