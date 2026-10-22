import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
FILE=OUT/'00_manifest/VISUAL_REVIEW_DATA_V1.json'
CATS={'shape':'furniture silhouette','composition':'furniture composition','table':'table typology','rug':'rug','curtain':'curtain','light':'lighting','art':'art','material':'material mix','side':'side furniture','focal':'focal strategy'}
def note(room,camera,geom=('PASS','PASS','PASS'),cats=([],[],[]),ideas=([],[],[]),notes=('', '', ''),retry=(False,True,True),candidate_notes=('', '', '')):
 data=json.loads(FILE.read_text()) if FILE.exists() else {}
 for vi,v in enumerate(['faithful','designer','creative']):
  key=room+'_'+camera+'_'+v+'_v1';categories=[CATS.get(c,c) for c in cats[vi]]
  if v=='faithful':gate='NOT_REQUIRED';level='LOW'
  else:
   count=len(set(categories));required=4 if v=='designer' else 6
   mandatory=True if v=='designer' else all(c in cats[vi] for c in ['shape','composition','light']) and any(c in cats[vi] for c in ['art','focal'])
   gate='PASS' if count>=required and mandatory else 'WARNING_AFTER_BOUNDED_RETRY'
   level='HIGH' if gate=='PASS' and v=='creative' else 'MEDIUM' if count>=3 else 'LOW'
  data[key]=dict(image_id=key,room=room,camera=camera,variant=v,geometry_preservation=geom[vi],design_divergence=level,difference_categories=categories,divergence_gate=gate,new_ideas=ideas[vi],review_notes=notes[vi],accept_retry=retry[vi],candidate_review_notes=candidate_notes[vi],review_method='Visual comparison against R4 reference at small-proxy scale; inspiration QA, not construction dimensional certification',visual_review='COMPLETE')
 FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def idea(category,description,complexity='LOW',geometry=False,measure=False):
 return dict(category=category,description=description,implementation_complexity=complexity,geometry_change_required=geometry,site_measure_required=measure)
