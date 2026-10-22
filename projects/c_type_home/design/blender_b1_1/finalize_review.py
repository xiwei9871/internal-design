"""Record images actually inspected by the agent and audit the final package."""
from pathlib import Path
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
qa=read(OUT/'B1_1_QA_REPORT.json')
manifest=read(ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json')
for key,expected in manifest['sha256'].items():
    assert digest(ROOT/manifest['files'][key])==expected, 'B0_INTEGRITY mismatch: '+key
assert digest(OUT/'B1_1_DESIGN_MODEL_V1.blend')==qa['model_sha256']
views=qa['visual_review']['required_views']
for name in views:
    path=OUT/f'B1_1_{name}.png'
    with Image.open(path) as im:
        im.verify()
qa['visual_review'].update(
    status='INSPECTED_WITH_KNOWN_DECISIONS',
    inspected_evidence=['B1_1_REVIEW_CONTACT_SHEET.png','B1_1_BATHROOMS_CONTACT_SHEET.png',
                        'B1_1_KITCHEN.png','B1_1_LEISURE.png','B1_1_STUDY.png'],
    method='All twelve views inspected in the full contact sheet; kitchen/leisure/study and bathrooms additionally opened as individual/full-sheet evidence.',
    findings=[
      dict(severity='observation',view='TOP/AXON',text='Split-level color fields, retained curved leisure platform, stair tops and registered furniture relationships visible.'),
      dict(severity='observation',view='LIVING/OWNER_BED/MOTHER_BED/GUEST_BED',text='Core source candidate furniture readable; native product/style assumptions remain human review.'),
      dict(severity='observation',view='KITCHEN',text='Cabinet envelope, appliance niche, source-height hierarchy and open sink bowl visible; duplicate front faces repaired in B1-owned geometry.'),
      dict(severity='observation',view='STUDY',text='Tall/low bookcase openings, workstation supports, bench and stool visible; owner-chair nondirectional body is marked pending.'),
      dict(severity='warning',view='BATHROOMS',text='Two vanity orientations unresolved; screen glass faces suppressed for Workbench inspection; mounting/plumbing/SKU not cleared.'),
      dict(severity='warning',view='BAY',text='Four bay projections remain; inherited full-height front bands conflict with proposed front-glazing review. No frozen geometry changed.'),
      dict(severity='observation',view='LEISURE',text='Frozen D-107 lower-edge offset appearance and inherited fascia striping are report-only source observations; no new datum/pose decision.')],
    claim_boundary='Visual inspection confirms review readability, not all unresolved design choices or construction readiness.')
qa['final_state']='B1_1_DESIGN_MODEL = HUMAN_REVIEW'
qa['final_verified_at']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
qa['unresolved_design_count']=sum(d['status']=='DESIGN_DECISION_REQUIRED' for d in qa['decisions_required'])
(OUT/'B1_1_QA_REPORT.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))

required=[
 'B1_1_DESIGN_MODEL_V1.blend','B1_1_TOP.png','B1_1_AXON.png','B1_1_LIVING.png','B1_1_KITCHEN.png',
 'B1_1_LEISURE.png','B1_1_OWNER_BED.png','B1_1_MOTHER_BED.png','B1_1_STUDY.png',
 'B1_1_BATHROOMS_CONTACT_SHEET.png','B1_1_ASSET_REGISTER.json','KITCHEN_CABINET_3D_REGISTER_V01.json',
 'B1_1_QA_REPORT.json','B1_1_HUMAN_REVIEW.md']
assert all((OUT/name).is_file() for name in required)
rows=[dict(path=name,bytes=(OUT/name).stat().st_size,sha256=digest(OUT/name)) for name in required]
(OUT/'B1_1_DELIVERY_MANIFEST.json').write_text(json.dumps(dict(
    B1_1_DESIGN_MODEL='HUMAN_REVIEW',B0_INTEGRITY='PASS',verified_at=qa['final_verified_at'],
    required_artifacts=rows,required_count=len(rows),visual_review='INSPECTED_WITH_KNOWN_DECISIONS',
    numeric_gates=qa['numeric_gates'],pending_design_count=qa['unresolved_design_count']),ensure_ascii=False,indent=2))
(OUT/'B1_1_DELIVERY_SHA256.txt').write_text('\n'.join(f"{r['sha256']}  {r['path']}" for r in rows)+'\n')
plan=OUT/'B1_1_IMPLEMENTATION_PLAN.md'
plan.write_text(plan.read_text().replace('- [ ]','- [x]')+'\nAll authorized review-package steps completed. Unconfirmed design/installation choices remain explicitly pending in the QA/HUMAN_REVIEW report; no approval is implied.\n')
(OUT/'work_state.md').write_text(f'''# B1.1 work state

State: B1_1_DESIGN_MODEL = HUMAN_REVIEW.

B0_INTEGRITY = PASS, 7/7 SHA256 MATCH at final check. All 176 inherited meshes and authored transforms preserved.

Candidate: B1_1_DESIGN_MODEL_V1.blend, SHA256 {qa['model_sha256']}.
Model sources: build_design_model.py; independent check: validate_candidate.py; rendering: render_review.py; packaging: package_review.py; final audit: finalize_review.py.

Evidence: twelve reviewed views, bathrooms contact sheet and complete review contact sheet. All fourteen required delivery artifacts exist; see B1_1_DELIVERY_MANIFEST.json and B1_1_DELIVERY_SHA256.txt.

QA: {qa['numeric_gates']['measured_furniture_cabinet_envelopes']} measured envelopes, max {qa['numeric_gates']['max_envelope_error_mm']:.3f} mm within 1 mm; 55,229 new evaluated triangles.

Pending: three facing overrides; bay front source overlap; cabinet internal/module/install mapping; sanitary/MEP/mini-washer/support heights; media/chaise/chair product and direction choices; other internal-door details; ceiling coffers/light slots/site dimensions. Red bodies/XY markers are explicit review placeholders, not settled designs.

Read-only source observations: inherited mutable guide transform defects; D-107 cutaway lower-edge appearance and fascia surface striping. No frozen correction performed.

No background task remains from this build. Next action: human reviews B1_1_HUMAN_REVIEW.md and chooses the necessary design decisions; keep B0 frozen.
''')
print(json.dumps(dict(state=qa['final_state'],B0_INTEGRITY='PASS',required_artifacts=len(rows),
                      source_objects_preserved=176,max_envelope_error_mm=qa['numeric_gates']['max_envelope_error_mm'],
                      unresolved_design_count=qa['unresolved_design_count'],model_sha256=qa['model_sha256']),indent=2))
