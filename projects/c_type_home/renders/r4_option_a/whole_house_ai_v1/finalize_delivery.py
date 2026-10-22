"""Install bounded technical corrections and assemble unranked human-review package."""
import json,hashlib,shutil,datetime,sys,collections
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from room_plan import ROOMS
from room_package import package
import prompt_system
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
P=read(OUT/'00_manifest/R4_WHOLE_HOUSE_PREFLIGHT.json');assert sha(P['source_path'])==P['sha256']
assert read(OUT/'00_manifest/GENERATION_RUN_DONE.json')['status']=='GENERATION_COMPLETE_PENDING_VISUAL_QA'
QA=read(OUT/'00_manifest/VISUAL_REVIEW_DATA_V1.json')
retry_results=[r for fn in ['REVIEW_RETRY_RESULTS.json','REVIEW_RETRY_RESULTS_EXTRA.json'] for r in read(OUT/'00_manifest'/fn)]
assert len({r['image_id'] for r in retry_results})==len(retry_results)
RM={r['image_id']:r for r in retry_results}
assert all(r['status'].startswith('RETRY_') for r in retry_results)
now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
allrows=[];room_summaries=[];install=[]
for room in ROOMS:
 D=OUT/room['folder'];rows=read(D/'reports/IMAGES.json');cams=read(D/'reports/CAMERA_REGISTER.json');cm={c['id']:c for c in cams}
 for row in rows:
  id=row['image_id'];orig=Path(row['output']);assert orig.exists();Image.open(orig).verify()
  if id in QA:
   qa=QA[id];rr=RM.get(id)
   if rr and not row.get('bounded_review_processed'):
    assert row['retry_count']==0
    before=dict(row);candidate=Path(rr['candidate']);initial_sha=sha(orig);origprompt=row['prompt']
    history=D/'reports/rejected';history.mkdir(exist_ok=True)
    if qa['accept_retry'] and candidate.exists() and rr['status'] in ['RETRY_GENERATED','RETRY_SIZE_WARNING','RETRY_EXISTING']:
     archived=history/(id+'_initial.png');shutil.copy2(orig,archived)
     initial=dict(before,archived_image=str(archived),image_sha256=initial_sha,archive_reason=rr['reason'])
     if row['room']=='kitchen' and row['camera']=='K3':initial.update(initial_reference_stale=True,initial_reference_sha256=None,reference_note='Initial request used pre-correction side camera; exact historical reference bytes unavailable. Effective retry binds to current corrected camera; no claim of matching initial to current reference.')
     dump(history/(id+'_initial_record.json'),initial)
     shutil.copy2(candidate,orig);row['prompt']=rr['prompt'];row['reference']=cm[row['camera']]['reference'];row['status']='GENERATED_REVIEW_RETRY';row['initial_image_archive']=str(archived);row['initial_prompt']=origprompt;row['initial_record_archive']=str(history/(id+'_initial_record.json'));install.append(id)
    else:
     row['rejected_retry']=dict(candidate=str(candidate),reason=qa['candidate_review_notes'] or 'Candidate not adopted on technical geometry grounds; retain original, without choosing a stylistic winner.',candidate_sha256=sha(candidate) if candidate.exists() else None)
    row['review_retry_attempt']=rr;row['retry_count']=1;row['bounded_review_processed']=True
    row['attempts']=list(row.get('attempts',[]))+[dict(attempt=2,kind='BOUNDED_VISUAL_REVIEW_RETRY',seconds=rr.get('seconds'),status=rr['status'],log=str(D/'reports'/(id+'_review_retry.log')),candidate=rr['candidate'],prompt=rr['prompt'],reference=rr.get('reference',cm[row['camera']]['reference']))]
   row.update({k:v for k,v in qa.items() if k not in ['accept_retry','candidate_review_notes']})
   row['retry_acceptance']='ADOPTED_TECHNICAL_CORRECTION' if rr and qa['accept_retry'] else 'REJECTED_TECHNICAL_REGRESSION_OR_NOT_REQUIRED'
  else:
   assert row['room']=='living' and row['geometry_preservation'] in ['PASS','WARNING','FAIL']
   row['visual_review']='COMPLETE_IN_VERIFIED_R4_LIVING_RUN';row['review_method']='Preserved prior visual QA; source SHA and reference identity verified before reuse'
  c=cm[row['camera']];row['source_sha256']=P['sha256'];row['reference_sha256']=sha(row['reference']);row['image_sha256']=sha(orig);row['prompt_sha256']=sha(row['prompt']);row['actual_size']=list(Image.open(orig).size);row['camera_pose']={k:c[k] for k in ['pos','target','lens'] if k in c};row['reference_camera_QA']=c.get('reference_camera_QA','VERIFIED_R4_LIVING_REFERENCE');row['qa_status']='FAIL' if row['geometry_preservation']=='FAIL' else 'WARNING' if row['geometry_preservation']=='WARNING' or row.get('divergence_gate','').startswith('WARNING') else 'PASS';row['geometry_QA_is_not_dimensional_certification']=True
  assert row['retry_count']<=1
 dump(D/'reports/IMAGES.json',rows);cs=package(room)
 totals=collections.Counter(r['geometry_preservation'] for r in rows);div=collections.Counter(r.get('divergence_gate','NOT_REQUIRED') for r in rows);warning=sum(r['qa_status']=='WARNING' for r in rows);failed=sum(r['qa_status']=='FAIL' for r in rows)
 cp=read(D/'reports/ROOM_DONE.json');cp.update(warning_images=warning,geometry_failed_images=totals['FAIL'],qa_failed_images=failed,geometry_preservation_summary=dict(totals),divergence_summary=dict(div),visual_review='COMPLETE_LIGHTWEIGHT_VISUAL_QA',visual_review_timestamp=now,retry_count=sum(r['retry_count'] for r in rows),reference_contact_sheet=str(D/'contact_sheet/ROOM_REFERENCE_CONTACT_SHEET.png'),review_report=str(D/'reports/ROOM_REVIEW.md'))
 dump(D/'reports/ROOM_DONE.json',cp)
 md=['# '+room['name']+'｜候选核查','',f'共{len(rows)}张已生成候选；geometry PASS={totals["PASS"]}, WARNING={totals["WARNING"]}, FAIL={totals["FAIL"]}。所有候选未选择，QA只用于装修灵感讨论。','', '[候选对比表]('+cs+') · [R4参考表]('+str(D/'contact_sheet/ROOM_REFERENCE_CONTACT_SHEET.png')+')','','| 图像 | 几何 | 差异门槛 | 补试 | 观察 |','|---|---|---|---|---|']
 for r in sorted(rows,key=lambda x:(x['camera'],['faithful','designer','creative'].index(x['variant']))):
  md.append('| ['+r['image_id']+']('+r['output']+') | '+r['geometry_preservation']+' | '+r.get('divergence_gate','NOT_REQUIRED')+' | '+str(r['retry_count'])+' | '+r.get('review_notes','').replace('|','／').replace('\n',' ')+' |')
 md+=['','## 使用限制','', '本轮不选方案、不改R4。图片不能证明尺寸、窗框分格、台阶高度、湿区排水或五金安装净空。未通过者保留为问题证据；WARNING图只可抽取不依赖错误几何的表面/家具灵感。窄视角与固定厨房/卫浴不具备完整活动家具发散空间，补试后差异不足仍标WARNING，不能通过改建筑满足门槛。']
 (D/'reports/ROOM_REVIEW.md').write_text('\n'.join(md)+'\n')
 allrows.extend(rows);room_summaries.append(dict(id=room['id'],name=room['name'],folder=str(D),expected_images=len(cams)*3,generated_images=len(rows),successful_candidates=len(rows)-failed,generation_failed_images=0,qa_failed_images=failed,warning_images=warning,geometry_preservation=dict(totals),divergence_gate=dict(div),retry_count=sum(r['retry_count'] for r in rows),camera_count=len(cams),contact_sheet=cs,reference_contact_sheet=cp['reference_contact_sheet'],checkpoint=str(D/'reports/ROOM_DONE.json'),review=cp['review_report']))
assert len(allrows)==144 and len(room_summaries)==15 and sum(r['camera_count'] for r in room_summaries)==48
# Idea extraction: convert all observed ideas into source-specific unranked records.
oldideas=read(OUT.parent/'living_exploration_v1/06_reports/LIVING_AI_IDEA_REGISTER_V1.json')['ideas'];idealist=[]
for row in allrows:
 descriptors=row.get('new_ideas',[])
 if row['room']=='living':
  oldid=row.get('reuse_source','').split('/')[-1].removesuffix('.png')
  descriptors=[dict(category=i['category'],description=i['description'],implementation_complexity=i.get('implementation_complexity','MEDIUM'),geometry_change_required=i.get('geometry_change_required',False),site_measure_required=i['category'] in ['furniture','lighting','joinery','storage']) for i in oldideas if oldid in i.get('source_images',[i.get('source_image')])]
  if not descriptors:descriptors=[dict(category='textile',description='米白/燕麦织物、轻帘与浅木家具形成暖亮基准。',implementation_complexity='LOW',geometry_change_required=False,site_measure_required=False)]
 source_ids=[]
 for item in descriptors:
  assert isinstance(item,dict)
  iid='WH_IDEA_'+str(len(idealist)+1).zfill(4);rec=dict(idea_id=iid,room=row['room'],camera=row['camera'],variant=row['variant'],source_image=row['output'],source_image_id=row['image_id'],category=item['category'],description=item['description'],implementation_complexity=item.get('implementation_complexity','LOW'),geometry_change_required=item.get('geometry_change_required',False),site_measure_required=item.get('site_measure_required',False),source_geometry_QA=row['geometry_preservation'],source_divergence_gate=row.get('divergence_gate'),selection_status='UNSELECTED_HUMAN_DISCUSSION',caution='Extract only the stated idea; source image has unresolved geometry' if row['geometry_preservation']!='PASS' else 'R4 and site measurements remain dimensional authority')
  idealist.append(rec);source_ids.append(iid)
 row['new_ideas']=source_ids
# Keep per-room image records synchronized with final idea IDs.
for room in ROOMS:dump(OUT/room['folder']/'reports/IMAGES.json',[r for r in allrows if r['room']==room['id']])
geo=collections.Counter(r['geometry_preservation'] for r in allrows);levels=collections.Counter(r['design_divergence'] for r in allrows);gates=collections.Counter(r.get('divergence_gate','NOT_REQUIRED') for r in allrows);qa=collections.Counter(r['qa_status'] for r in allrows)
status='HUMAN_REVIEW_WITH_FAILED_IMAGES' if geo['FAIL'] else 'HUMAN_REVIEW'
summary=dict(rooms_discovered=15,rooms_completed=15,independent_physical_spaces=14,storage_topic=1,expected_image_count=144,generated_images=144,generation_failed_images=0,successful_images=144-geo['FAIL'],failed_images=geo['FAIL'],warning_images=qa['WARNING'],geometry_warning_images=geo['WARNING'],retry_count=sum(r['retry_count'] for r in allrows),current_run_visual_retry_requests=len(retry_results),reused_living_retry_images=2,camera_count=48,reference_count=48,ideas_count=len(idealist),geometry_preservation=dict(geo),design_divergence=dict(levels),divergence_gate=dict(gates),image_qa_status=dict(qa))
manifest=dict(schema_version='1.0',status=status,source=P,source_unchanged=sha(P['source_path'])==P['sha256'],completed=now,model='gpt-image-2',endpoint='https://www.shenlanqaq.com/v1',request_mode='images/edit',quality='high',size='1536x1024',selected_DNA=None,winner_selection_performed=False,summary=summary,semantic_notes=read(OUT/'00_manifest/R4_ROOM_INVENTORY.json')['semantic_notes'],rooms=room_summaries,images=allrows)
dump(OUT/'WHOLE_HOUSE_AI_MANIFEST_V1.json',manifest);dump(OUT/'AI_DESIGN_IDEA_REGISTER_V1.json',dict(status='UNRANKED_HUMAN_REVIEW',geometry_change_definition='Changes to architecture, door/window topology, fixed-cabinet footprint or plumbing layout; loose-furniture/material replacement alone is false',ideas=idealist))
md=['# 全屋 AI 设计灵感登记 V1','',f'{len(idealist)}条逐来源观察记录（同一想法在不同机位出现会分别记录）。没有评分、排名、winner或最终选择。','', 'geometry_change_required指改变建筑、门窗/固定柜体占地或排水布局；活动家具、表面或灯具更换不自动等于建筑变更。FAIL/WARNING来源只能抽取不依赖其错误几何的独立想法。']
for room in ROOMS:
 md+=['','## '+room['name'],'','| ID / 来源 | 类别 | 观察到的想法 | 复杂度 | 改建筑几何 | 现场复尺 | 来源几何 |','|---|---|---|---|---|---|---|']
 for i in idealist:
  if i['room']==room['id']:md.append('| ['+i['idea_id']+' / '+i['camera']+' '+i['variant']+']('+i['source_image']+') | '+i['category']+' | '+i['description'].replace('|','／')+' | '+i['implementation_complexity']+' | '+str(i['geometry_change_required']).lower()+' | '+str(i['site_measure_required']).lower()+' | '+i['source_geometry_QA']+' |')
(OUT/'AI_DESIGN_IDEA_REGISTER_V1.md').write_text('\n'.join(md)+'\n')
# Contact-sheet index: one modest image per room, never one giant whole-house board.
md=['# 全屋 R4 Option A｜人工审核索引','',f'状态：{status}。15个空间/功能专题，48个机位，144张生成文件；无接口失败，{geo["FAIL"]}张几何QA未通过，{qa["WARNING"]}张存在几何或差异WARNING。所有图片和参考只保存在项目目录。','', '| 空间 | 机位/张数 | 候选对比表 | R4参考表 | 问题说明 | QA失败 | WARNING |','|---|---|---|---|---|---|---|']
for r in room_summaries:md.append('| '+r['name']+' | '+str(r['camera_count'])+' / '+str(r['generated_images'])+' | [打开候选]('+r['contact_sheet']+') | [打开参考]('+r['reference_contact_sheet']+') | [核查记录]('+r['review']+') | '+str(r['qa_failed_images'])+' | '+str(r['warning_images'])+' |')
md+=['','## 总文件','']
for label,file in [('空间清单','00_manifest/R4_ROOM_INVENTORY.md'),('完整manifest','WHOLE_HOUSE_AI_MANIFEST_V1.json'),('设计灵感登记','AI_DESIGN_IDEA_REGISTER_V1.md'),('提示词包','WHOLE_HOUSE_PROMPT_PACK_V1.md'),('总报告','WHOLE_HOUSE_AI_EXPLORATION_REPORT_V1.md')]:md.append('- ['+label+']('+str(OUT/file)+')')
md+=['','## 优先核对的问题','', '- kitchen K1 Designer：新增横向窗分格，未通过。K1 Faithful/Creative上方为卷帘而不是同一横框错误，但clay未清楚显示登记窗，宽高与透视仍WARNING。','- main_bath BA3 Faithful：台盆已恢复，但画面左侧新增玻璃与R4湿区方向不符，未通过。','- leisure LE3 Designer补试新增曲线三阶，已技术拒绝，正式对比表保留初稿；初稿差异仍不足。','- 固定厨房、卫浴、衣柜、狭窄门口等多数Creative未满足六类明显差异；已经单次补试，不再自动出图。','- 原衣帽间已变次主卫，09是现有卧室衣柜专题；洗烘和冷柜在北阳台，公卫3kg洗衣/NAS/打印/备用睡眠仍不能视作已安装。']
(OUT/'WHOLE_HOUSE_CONTACT_SHEET_INDEX.md').write_text('\n'.join(md)+'\n')
# Export architecture/style/room/camera/variant system plus exactly effective prompts.
md=['# 全屋提示词包 V1','', '每张采用原R4 clay图执行image edit。下面保留共享组件和实际有效prompt原文；已有输出不因prompt升级而改写。没有Selected DNA。']
for heading,value in [('MASTER_ARCH_LOCK',prompt_system.MASTER_ARCH_LOCK),('WHOLE_HOUSE_STYLE_DNA',prompt_system.WHOLE_HOUSE_STYLE_DNA)]:md+=['','## '+heading,'',value]
for room in ROOMS:
 md+=['','## '+room['name']+'｜共享房间说明','',prompt_system.ROOM_PROMPTS.get(room['id'],''),'']
 for row in sorted((r for r in allrows if r['room']==room['id']),key=lambda x:(x['camera'],x['variant'])):
  md+=['','### '+row['image_id'],'','- reference: '+row['reference'],'- prompt: '+row['prompt'],'- prompt_sha256: '+row['prompt_sha256'],'- geometry: '+row['geometry_preservation']+'; divergence: '+row.get('divergence_gate','NOT_REQUIRED'),'','```text',Path(row['prompt']).read_text().strip(),'```']
(OUT/'WHOLE_HOUSE_PROMPT_PACK_V1.md').write_text('\n'.join(md)+'\n')
# Explicit failed-image list with retained originals/candidates.
failures=[dict(image_id=r['image_id'],room=r['room'],camera=r['camera'],variant=r['variant'],failure_type='GEOMETRY_QA_FAIL',output=r['output'],reference=r['reference'],prompt=r['prompt'],retry_count=r['retry_count'],reason=r['review_notes']) for r in allrows if r['geometry_preservation']=='FAIL']
dump(OUT/'00_manifest/FINAL_FAILED_IMAGES.json',failures);dump(OUT/'00_manifest/FINAL_RETRY_INSTALLATION.json',dict(installed_technical_corrections=install,rejected_technical_retry=[r['image_id'] for r in allrows if r.get('rejected_retry')],all_current_retry_results=retry_results,bounded_once=True))
md=['# R4 Option A｜全屋 AI 探索报告 V1','', '全屋必须空间的出图和逐张轻量核查已结束，进入 '+status+'。144张正式文件均生成成功；其中142张可作候选（包含WARNING），2张几何QA未通过并保留问题证据。未选winner、未建立Selected DNA、未回写母版。','', '## R4权威与完整性','', '- source: '+P['source_path'],'- SHA256: `'+P['sha256']+'`','- object_count: '+str(P['object_count'])+'; collection_count: '+str(P['collection_count']),'- 独立参考工作副本: '+P['working_copy'],'- source_unchanged: '+str(manifest['source_unchanged']).lower(),'- 所有新增房间参考从R4直接派生；客厅复用经同source SHA与reference identity验证的R4出图。K3初稿使用旧侧向机位，全部三图已以当前正向参考补试替换，旧图仅归档。','', '## 数量与状态','', '```json',json.dumps(summary,ensure_ascii=False,indent=2),'```','', 'failed_images指保留的几何QA失败图；generation_failed_images=0。warning_images是图像综合WARNING数量，geometry_warning_images只统计几何WARNING，不可混为一谈。单张最多一次补试：本批95次视觉补试，另客厅复用2张已有补试，共97张使用过补试额度。preflight测试不计正式图。','', '## 覆盖语义','']+['- '+s for s in manifest['semantic_notes']]
md+=['','## 几何与差异核查','', '核查在小尺寸参考/三版本对照图上逐张进行；必要时单张768px细查。PASS表示未发现明显结构/功能矛盾，不能认证尺寸。玻璃白模语义易被AI误读为木面，主卫/公卫已用一次定向补试恢复；不清晰的原参考和玻璃分格仍保留WARNING。','', '主要未通过图：','']
for f in failures:md.append('- ['+f['image_id']+']('+f['output']+')：'+f['reason'])
md+=['', 'LE3 Designer补试出现额外曲线三阶，已拒绝，正式图保留没有该主要错误的初稿。此为技术修正决定，不是风格winner选择。','', '餐厅和部分休闲机位的桌型、就座组合、灯具和艺术焦点有明显差异。卧室和书房仍有补试后变化不足；固定厨房、卫浴、衣柜和门口局部在硬几何锁定下不具备充分活动家具发散范围。没有通过虚构家具、扩大房间、改变柜体或洁具来凑4/6类别；所有不足均记WARNING。Creative同时检查就座组成、主家具轮廓、灯和焦点，不能只凭数量通过。','', '全屋浅木/暖白/燕麦为探索基线，各候选未组成统一最终家具DNA，机位之间仍有设计物件差别；本轮是候选探索，后续选定后才传播统一设计。','', '## 灵感与安装限制','', f'登记{len(idealist)}条按来源提取的观察，未排序；重复概念可跨机位出现。厨房柜体与衣柜仅作表面灵感，不重新决定拓扑。可移阅读椅/坐凳/设备车的净空、电位和实际尺寸必须现场核对。书房原297mm长台/茶水台净距未在R4中改动，AI图不能证明能站立使用或备用睡眠。适老折座、灯位、五金、上水/下水也不是施工承诺。','', '## 输出与停止点','', '- [全屋contact sheet索引]('+str(OUT/'WHOLE_HOUSE_CONTACT_SHEET_INDEX.md')+')','- [空间清单]('+str(OUT/'00_manifest/R4_ROOM_INVENTORY.md')+')','- [完整manifest]('+str(OUT/'WHOLE_HOUSE_AI_MANIFEST_V1.json')+')','- [设计灵感登记]('+str(OUT/'AI_DESIGN_IDEA_REGISTER_V1.md')+')','- [提示词包]('+str(OUT/'WHOLE_HOUSE_PROMPT_PACK_V1.md')+')','- [逐张失败记录]('+str(OUT/'00_manifest/FINAL_FAILED_IMAGES.json')+')','', '各房间reference、正式候选、contact_sheet、prompts和checkpoint均保留在索引所列目录；补试与初稿保留作溯源。未做bonus夕照，未扩展施工图。本轮到此停止，等待人工集中审阅。']
(OUT/'WHOLE_HOUSE_AI_EXPLORATION_REPORT_V1.md').write_text('\n'.join(md)+'\n')
dump(OUT/'00_manifest/LIVE_PROGRESS.json',dict(status=status,completed_rooms=[r['id'] for r in ROOMS],generated_images=144,target_images=144,source_sha256=P['sha256'],finished=now,visual_review='COMPLETE',next_action='HUMAN_REVIEW',automatic_generation_stopped=True))
dump(OUT/'00_manifest/FINAL_DELIVERY_STATUS.json',dict(status=status,summary=summary,source_sha256=P['sha256'],source_unchanged=manifest['source_unchanged'],finished=now,automatic_generation_stopped=True))
assert sha(P['source_path'])==P['sha256'];print(json.dumps(dict(status=status,summary=summary),ensure_ascii=False))
