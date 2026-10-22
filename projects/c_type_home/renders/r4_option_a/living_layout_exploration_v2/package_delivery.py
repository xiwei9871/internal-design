import json,sys,hashlib,shutil,textwrap,math,datetime,statistics
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from layout_spec import *
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
font=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
rows=read(OUT/'reports/IMAGES.json');corrections=read(OUT/'reports/CORRECTION_RESULTS.json');qa=read(OUT/'reports/VISUAL_QA_V2.json');cams=read(OUT/'reports/CAMERA_REGISTER.json');cammap={(c['layout'],c['camera']):c for c in cams};pre=read(OUT/'reports/PREFLIGHT.json')
assert len(rows)==15 and len(cams)==15 and len({r['image_id'] for r in corrections})==len(corrections)==7
assert all(q.get('visual_review')=='COMPLETE' for q in qa.values())
# Capture actual input hashes before adopting any output, then bind moved files by their hashes.
archive=OUT/'reports/corrections';archive.mkdir(exist_ok=True)
for r in corrections:
 r['request_style_anchor_path']=r.get('style_anchor');r['style_anchor_sha256']=sha(r['style_anchor']) if r.get('style_anchor') else None;r['reference_sha256']=sha(r['reference']);r['candidate_sha256']=sha(r['output']) if Path(r['output']).exists() else None
cm={r['image_id']:r for r in corrections}
for i,row in enumerate(rows):
 id=row['image_id'];c=cammap[(row['layout'],row['camera'])]
 if id in cm:
  r=cm[id];assert r['status'].startswith('GENERATED')
  raw=Path(r['output']);canonical=Path(row['output']);initial=OUT/'reports/initial'/canonical.name;assert initial.exists()
  rawcopy=archive/raw.name;shutil.copy2(raw,rawcopy);shutil.copy2(raw,canonical)
  anchor=r.get('style_anchor')
  if anchor and anchor.endswith('_retry.png'):anchor=str(archive/Path(anchor).name)
  elif r['layout']=='C' and r['camera']=='L1':anchor=str(OUT/'reports/initial'/Path(anchor).name)
  rows[i]=dict(**{k:v for k,v in r.items() if k not in ['output','style_anchor','status','retry_count']},output=str(canonical),style_anchor=anchor,raw_correction=str(rawcopy),initial_image=str(initial),initial_request_record=str(OUT/'reports/initial'/(id+'_record.json')),status='GENERATED_BOUNDED_CORRECTION',retry_count=1)
  row=rows[i]
 row.update(qa[id]);row['reference']=c['reference'];row['reference_sha256']=sha(c['reference']);row['image_sha256']=sha(row['output']);row['prompt_sha256']=sha(row['prompt']);row['source_sha256']=SOURCE_SHA;row['camera_pose']={k:c[k] for k in ['pos','target','lens']};row['camera_adjustment']=c['camera_adjustment'];row['original_camera_target']=c['base_camera_target'];row['actual_size']=list(Image.open(row['output']).size);row['geometry_truth']='IMMUTABLE_R4_ARCHITECTURE; LOOSE_LAYOUT_IS_UNSELECTED_INSPIRATION';row['source_model_writeback']=False
 if row.get('style_anchor') and not row.get('style_anchor_sha256'):row['style_anchor_sha256']=sha(row['style_anchor'])
for r in corrections:
 p=Path(r['output'])
 if p.exists():p.unlink() # Generated retry is preserved byte-for-byte in reports/corrections and canonical output.
for r in corrections:
 r['request_output_path']=r['output'];r['output']=str(archive/Path(r['output']).name)
 anchor=r.get('style_anchor')
 if anchor and anchor.endswith('_retry.png'):r['style_anchor']=str(archive/Path(anchor).name)
 elif r['layout']=='C' and r['camera']=='L1':r['style_anchor']=str(OUT/'reports/initial'/Path(anchor).name)
dump(OUT/'reports/CORRECTION_RESULTS.json',corrections)
# L1 used as an anchor before/after correction as specified; manifest carries actual file hash, not just current filename.
for row in rows:
 if row.get('style_anchor'):assert sha(row['style_anchor'])==row['style_anchor_sha256'],row['image_id']+' anchor provenance changed'
dump(OUT/'reports/IMAGES.json',rows)
# Three scheme sheets, five views per scheme; no winner or ratings.
order=['L1','L2','L5','L3','L4'];notes={
 'A':['保留三人位，贵妃椅到窗前。','双人位转到内侧，面向会客中心。','圆开放边几＋木腿浅石主副茶几。','优势：会客容量保留，改动较少。','关注：内侧仍较满，双人位取茶偏远。'],
 'B':['三人位＋窗前贵妃椅。','取消双人位，内侧只一件轻单椅。','小圆边几承接单椅饮茶功能。','优势：公共区更轻、更松弛。','关注：少一个常规会客座位。'],
 'C':['统一L型模块主沙发。','窗前一张轻躺靠观景椅。','茶几向内移270mm，改善座位前净距。','优势：会客中心完整，家具语言统一。','关注：L转角与窗椅净距需实物校核。']}
for key,l in LAYOUTS.items():
 board=Image.new('RGB',(1800,970),'#f5f3ee');dr=ImageDraw.Draw(board);dr.text((24,18),l['name']+'｜未定稿布局候选',font=font(32),fill='#30493e')
 for j,cid in enumerate(order):
  r=next(r for r in rows if r['layout']==key and r['camera']==cid);x=j%3*600+15;y=j//3*445+75;dr.text((x,y),cid+'  '+r['geometry_stability'],font=font(23),fill='#30493e');im=Image.open(r['output']);im.thumbnail((570,380));board.paste(im,(x,y+41))
 x=1215;y=555;dr.text((x,y),'布局意图与取舍',font=font(27),fill='#30493e')
 for j,n in enumerate(notes[key]):dr.text((x,y+60+j*52),n,font=font(22),fill='#536254')
 path=OUT/'contact_sheet'/('LIVING_LAYOUT_'+key+'_CONTACT_SHEET.png');board.save(path)
 # Separate current references remain inspectable by scheme.
 rb=Image.new('RGB',(1800,970),'#f5f3ee');rd=ImageDraw.Draw(rb);rd.text((24,18),l['name']+'｜R4建筑＋临时家具层参考',font=font(30),fill='#30493e')
 for j,cid in enumerate(order):
  c=cammap[(key,cid)];x=j%3*600+15;y=j//3*445+75;rd.text((x,y),cid,font=font(24),fill='#30493e');im=Image.open(c['reference']);im.thumbnail((570,380));rb.paste(im,(x,y+41))
 rb.save(OUT/'contact_sheet'/('LIVING_LAYOUT_'+key+'_REFERENCE_SHEET.png'))
# Compare the same camera across A/B/C in five rows.
board=Image.new('RGB',(1800,2325),'#f5f3ee');dr=ImageDraw.Draw(board);dr.text((24,18),'客厅二次布局｜同机位 A / B / C 对照',font=font(32),fill='#30493e')
for j,cid in enumerate(order):
 for vi,key in enumerate(['A','B','C']):
  row=next(r for r in rows if r['layout']==key and r['camera']==cid);x=vi*600+15;y=j*450+75;dr.text((x,y),key+' '+cid,font=font(26),fill='#30493e');im=Image.open(row['output']);im.thumbnail((570,380));board.paste(im,(x,y+43))
board.save(OUT/'contact_sheet/LIVING_LAYOUT_ABC_COMPARISON.png')
# Review markdown: requested five checks for each image, and explicit unranked trade-offs.
md=['# R4 客厅二次布局探索｜审阅 V2','', '15张正式候选：A/B/C各L1、L2、L5、L3、L4。仅供灵感选择；未选择最终方案，未建立Selected DNA，未回写Blender或FreeCAD。几何“稳定”指逐图未发现主要建筑关系漂移，不是毫米级尺寸认证。','', '## 三方向的取舍','', '| 方向 | 布局 | 优势 | 需要权衡 |','|---|---|---|---|', '| A · Swap | 三人位不动；贵妃椅到北窗；双人位到内侧朝北 | 保留约6个常规座位，最接近现有家具体系，窗边躺坐采光更直接 | 内侧仍有双人沙发的量感；它距主茶几包络约1345mm，不能直接取茶，最终宜核对是否另配轻边几 |', '| B · Light Lounge | 三人位＋窗前贵妃椅，内侧换一件轻木单椅＋圆边几 | 约5个座位，内侧和台阶前更轻，活动范围更松弛，独立小边几承担单椅饮茶 | 少一个常规会客席位；需要确认家庭更看重开放感还是聚会容量 |', '| C · L-Sofa | 主沙发统一L模块，窗边留轻躺靠椅 | 会客中心更完整、主副茶几和家具语言统一；L模块容量取决于最终尺寸 | 不完全保留原贵妃椅伸腿尺度；窗椅被AI转向室内，观景需转身；L回转段、椅和边几净距需校核 |','', '贵妃椅移近窗在A/B中让阅读与自然光的关系更清楚，也降低原窗前双人沙发的遮挡感。但椅边到窗台仅约140mm，这不是走道；窗前操作仍要从侧面接近。三方向都取消正方形封闭抽屉角几，改圆开放腿边几，视觉上已摆脱床头柜感。','', 'C临时参考发现副茶几距回转座位前沿约166mm，已把双茶几向南移270mm，参考净距改善到约436mm；西侧主桌至沙发约409mm。A/B L4曾被AI加入大黑电视，单次补试已去掉。全部初稿保留在reports/initial，修正只发生在候选图和临时家具参考层。','', '## 逐张核查','', '| 图像 | 建筑关系 | 窗边关系 | 明亮白蜡木 | 边几摆脱床头柜 | 茶几系统 | 关注点 |','|---|---|---|---|---|---|---|']
for key in ['A','B','C']:
 for cid in order:
  r=next(r for r in rows if r['layout']==key and r['camera']==cid);window='躺椅与窗更直接' if key!='C' else '轻椅保留观景休闲'
  if cid in ['L2','L4']:window='反向机位不见北窗'
  if key=='C' and cid in ['L1','L3','L5']:window='偏室内阅读，观景需转身'
  side='开放圆边几' if cid not in ['L2'] else '可见或局部可见'
  coffee='主副木石、比原方桌更轻' if r['coffee_table_system']=='PASS_VISIBLE' else '部分入画，参见L1/L3' if r['coffee_table_system']=='PARTIAL' else '在画外，参见L1/L3'
  attention='窗椅朝向/边几位置有漂移，需选择后核对' if key=='C' and cid in ['L1','L3','L5'] else '侧面接近窗台' if cid=='L5' and key!='C' else '躺靠椅不是完整长贵妃椅' if cid=='L5' else '内侧双人位取茶距离偏远' if key=='A' and cid in ['L2','L4'] else '保留单椅旁小边几' if key=='B' and cid in ['L2','L4'] else '茶几已移开回转座位前沿' if key=='C' and cid!='L5' else '帘后窗框细部以R4参考为准'
  md.append('| ['+key+'-'+cid+']('+r['output']+') | '+('稳定' if r['geometry_stability']=='PASS_VISUAL' else '需复核')+' | '+window+' | 保留 | '+side+' | '+coffee+' | '+attention+' |')
md+=['','## 看图入口','']
for key in ['A','B','C']:md.append('- ['+LAYOUTS[key]['name']+' 五视角联系图]('+str(OUT/'contact_sheet'/('LIVING_LAYOUT_'+key+'_CONTACT_SHEET.png'))+') · [对应参考]('+str(OUT/'contact_sheet'/('LIVING_LAYOUT_'+key+'_REFERENCE_SHEET.png'))+')')
md+=['- [同机位A/B/C对照]('+str(OUT/'contact_sheet/LIVING_LAYOUT_ABC_COMPARISON.png')+')','- [全部单张大图与资料索引]('+str(OUT/'LIVING_LAYOUT_IMAGE_INDEX_V2.md')+')','', 'L1/L2/L3/L4沿用R4原机位；L5位置与32mm焦距不变，只将取景目标下调以拍清新窗前座位。所有参考中建筑、固定柜体和非客厅家具保持；每方向只用临时活动家具层，未保存任何新.blend或.FCStd。下一步等待人工选择布局，再正式建模和高质量真实渲染。']
(OUT/'LIVING_LAYOUT_REVIEW_V2.md').write_text('\n'.join(md)+'\n')
index=['# 客厅二次布局｜图像索引','', '本轮15张单图均1536×1024、gpt-image-2 high。图片仅存项目文件系统。所有A/B/C都是未选候选。','', '[审阅说明与布局优劣]('+str(OUT/'LIVING_LAYOUT_REVIEW_V2.md')+') · [同机位总对照]('+str(OUT/'contact_sheet/LIVING_LAYOUT_ABC_COMPARISON.png')+')','','| 布局 | 五视角联系图 | R4/临时家具参考 |','|---|---|---|']
for k in ['A','B','C']:index.append('| '+LAYOUTS[k]['name']+' | [打开]('+str(OUT/'contact_sheet'/('LIVING_LAYOUT_'+k+'_CONTACT_SHEET.png'))+') | [打开参考]('+str(OUT/'contact_sheet'/('LIVING_LAYOUT_'+k+'_REFERENCE_SHEET.png'))+') |')
index+=['','| 机位 | A Swap | B Light Lounge | C L-Sofa |','|---|---|---|---|']
for cid in order:index.append('| '+cid+' | '+' | '.join('['+k+'-'+cid+']('+next(r['output'] for r in rows if r['layout']==k and r['camera']==cid)+')' for k in ['A','B','C'])+' |')
index+=['','- [家具包络与机位平面示意]('+str(OUT/'reports/LAYOUT_PLAN_CAMERA_ENVELOPES.png')+')','- [完整manifest]('+str(OUT/'LIVING_LAYOUT_MANIFEST_V2.json')+')','- [实际提示词包]('+str(OUT/'LIVING_LAYOUT_PROMPT_PACK_V2.md')+')']
(OUT/'LIVING_LAYOUT_IMAGE_INDEX_V2.md').write_text('\n'.join(index)+'\n')
pack=['# 客厅二次布局提示词包 V2','', '结构第一输入为R4建筑/本方向临时家具clay；同方向L1仅作家具外观第二输入。以下保留实际有效prompt。']
for r in sorted(rows,key=lambda r:(r['layout'],order.index(r['camera']))):pack+=['','## '+r['image_id'],'','reference: '+r['reference'],'style_anchor: '+str(r.get('style_anchor')),'','```text',Path(r['prompt']).read_text().strip(),'```']
(OUT/'LIVING_LAYOUT_PROMPT_PACK_V2.md').write_text('\n'.join(pack)+'\n')
# Lock evidence: source and every recorded FreeCAD file are unchanged.
assert sha(SRC)==SOURCE_SHA
for path,h in pre['freecad_sources'].items():assert sha(path)==h,path
locks=read(OUT/'reports/ARCHITECTURE_LOCK.json');assert len(locks)==3 and all(l['protected_geometry_and_authored_pose']=='PASS_UNCHANGED' for l in locks)
manifest=dict(status='HUMAN_REVIEW',scope='LIVING_ROOM_SECOND_LAYOUT_EXPLORATION_ONLY',source=str(SRC),source_sha256=SOURCE_SHA,source_unchanged=True,freecad_unchanged=True,freecad_source_hashes=pre['freecad_sources'],saved_new_blend=False,saved_new_freecad=False,architecture_lock=locks,layout_specs=LAYOUTS,counts=dict(layouts=3,views_per_layout=5,formal_images=15,references=15,raw_generated_images=22,bounded_corrections=7,generation_failures=0,architecture_visual_pass=15,furniture_pose_warnings=3),image_api=dict(model='gpt-image-2',quality='high',size='1536x1024',request_mode='images/edit'),camera_policy='L1/L2/L3/L4 retain R4 poses/lenses. L5 retains position and32mm lens, target lowered to new window seating only.',candidate_geometry_notes=dict(main_circulation_band_mm=1118,C_satellite_to_return_sofa_mm=436,C_main_to_west_sofa_mm=409,A_inner_loveseat_to_main_table_mm=1345,AB_chaise_to_bay_sill_mm=140,not_site_measurements=True),selected_DNA=None,winner=None,all_candidates_unselected=True,images=rows,completed=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'))
dump(OUT/'LIVING_LAYOUT_MANIFEST_V2.json',manifest);dump(OUT/'reports/FINAL_STATUS.json',dict(status='HUMAN_REVIEW',automatic_generation_stopped=True,formal_images=15,model_writeback=False,freecad_writeback=False,selected_DNA=None))
print(json.dumps(dict(status='HUMAN_REVIEW',images=15,corrections=7,source_unchanged=True,freecad_files_unchanged=len(pre['freecad_sources'])),ensure_ascii=False))
