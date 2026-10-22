import json
from pathlib import Path
from prompt_rules import assemble,MASTER_ARCH_LOCK,MASTER_STYLE_DNA,CAMERA_PROMPTS,VARIANT_PROMPTS,DIVERGENCE_REQUIREMENTS
OUT=Path(__file__).resolve().parent
test=json.loads((OUT/'06_reports/A1_API_TEST.json').read_text());assert test['status']=='GENERATED'
cams=json.loads((OUT/'00_reference/R4_CAMERA_REGISTER.json').read_text());assert len(cams)==5
jobs=[];folders={'faithful':'01_faithful','designer':'02_designer','creative':'03_creative'}
pack=['# LIVING PROMPT PACK R4 V1','', '唯一几何：当前R4 Option A。下列规则由prompt_rules.py自动拼装，不手工维护15份规则。','', '## MASTER_ARCH_LOCK','',MASTER_ARCH_LOCK,'','## MASTER_STYLE_DNA','',MASTER_STYLE_DNA]
for c in cams:
 for v in folders:
  ident=f'living_{c["id"]}_{v}_v1';pf=OUT/'05_prompts'/(ident+'.txt');prompt=assemble(c['id'],v);pf.write_text(prompt)
  jobs.append(dict(image_id=ident,camera_id=c['id'],variant=v,source_reference=c['reference'],prompt_file=str(pf),output=str(OUT/folders[v]/(ident+'.png'))))
  pack.extend(['','## '+ident,'', '[CAMERA_PROMPT]',CAMERA_PROMPTS[c['id']],'','[VARIANT_PROMPT]',VARIANT_PROMPTS[v],'','[DIVERGENCE_REQUIREMENT]',DIVERGENCE_REQUIREMENTS[v],'', '完整可执行prompt：'+str(pf)])
(OUT/'05_prompts/LIVING_JOBS.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n');(OUT/'05_prompts/LIVING_PROMPT_PACK_R4_V1.md').write_text('\n'.join(pack)+'\n')
print(json.dumps(dict(matrix=15,A1_test_reused=True,prompt_assembly='SHARED_CODE_RULES')))
