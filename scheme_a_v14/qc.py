"""Symmetric structural comparison. Scores rank candidates; review controls publication."""
from pathlib import Path
import argparse
import json
import math
import hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, sobel

REVIEW_KEYS=('openings','equipment_order','furniture_orientation','no_unapproved_objects')

def compare_edges(base,candidate,tolerance=5):
    base=np.asarray(base,dtype=bool); candidate=np.asarray(candidate,dtype=bool)
    if base.shape!=candidate.shape: raise ValueError('Edge maps must share one evaluation canvas')
    if not base.any() or not candidate.any(): raise ValueError('Empty structural map: cannot score')
    de=distance_transform_edt(~candidate); db=distance_transform_edt(~base)
    recall=float((de[base]<=tolerance).mean()); precision=float((db[candidate]<=tolerance).mean())
    return {'recall':recall,'precision':precision,'f1':2*recall*precision/(recall+precision) if recall+precision else 0,
            'symmetric_chamfer_px':float((de[base].mean()+db[candidate].mean())/2),'tolerance_px':tolerance}

def can_publish(reference_meta,candidate_meta,review,score,previous_score):
    """Only comparable, reviewed candidates can be promoted. No magical quality cutoff."""
    if any(not reference_meta.get(k) or reference_meta[k]!=candidate_meta.get(k) for k in ('design_sha256','camera_signature')): return False
    if not all(review.get(k) is True for k in REVIEW_KEYS): return False
    for s in [score]+([previous_score] if previous_score is not None else []):
        try:
            if not math.isfinite(s['f1']) or not 0<=s['f1']<=1: return False
            if len(s['evaluation_size'])!=2 or any(v<=0 for v in s['evaluation_size']): return False
            if not math.isfinite(s['tolerance_px']) or s['tolerance_px']<=0 or not s['reference_sha256']: return False
        except (KeyError,TypeError,ValueError): return False
    if previous_score is not None and any(score[k]!=previous_score[k] for k in ('evaluation_size','tolerance_px','reference_sha256')): return False
    return previous_score is None or score['f1']>=previous_score['f1']

def edge_map(path,size):
    im=Image.open(path).convert('L').resize(size,Image.Resampling.LANCZOS)
    a=np.asarray(im,dtype=float); magnitude=np.hypot(sobel(a,0),sobel(a,1))
    # Source should be a structural pass/mask, not a textured beauty render.
    return magnitude>max(20,float(np.percentile(magnitude,90)))

def score_files(base_path,candidate_path,out_dir):
    base=Image.open(base_path); candidate=Image.open(candidate_path)
    if abs(base.width/base.height-candidate.width/candidate.height)>.005:
        raise ValueError('Aspect ratio mismatch: crop must be explicitly reconciled')
    size=(1000,round(1000*base.height/base.width)); b=edge_map(base_path,size); e=edge_map(candidate_path,size)
    result=compare_edges(b,e); result.update(evaluation_size=size,status='ranking_only_requires_semantic_review',
        reference_sha256=hashlib.sha256(Path(base_path).read_bytes()).hexdigest(),
        candidate_sha256=hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest())
    de=distance_transform_edt(~e); db=distance_transform_edt(~b)
    overlay=np.full((*b.shape,3),255,np.uint8)
    overlay[b & (de<=5)]=[30,30,30]; overlay[b & (de>5)]=[215,45,45]; overlay[e & (db>5)]=[40,155,85]
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    Image.fromarray(overlay).save(out/'overlay.png')
    (out/'score.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('base'); p.add_argument('candidate'); p.add_argument('output')
    a=p.parse_args(); print(json.dumps(score_files(a.base,a.candidate,a.output),indent=2))
