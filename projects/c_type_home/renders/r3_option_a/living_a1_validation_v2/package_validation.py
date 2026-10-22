import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
M=json.loads((OUT/'A1_SOURCE_AND_CAMERA_MANIFEST.json').read_text());S=json.loads((OUT/'A1_GENERATION_SUMMARY.json').read_text());R=json.loads((OUT/'A1_GENERATION_RESULTS.json').read_text())
assert sha(M['source'])==M['source_sha256'];assert sha(M['branch'])==M['branch_sha256'];assert sha(M['base'])==M['base_sha256']
files=[('BASE_REFERENCE','白模｜建筑与占位约束'),('FAITHFUL','FAITHFUL｜原家具形态'),('DESIGNER','DESIGNER｜木平台底座与木石茶几'),('CREATIVE','CREATIVE｜开放木框、弧线与组合茶几')]
board=Image.new('RGB',(2400,1790),'#f5f3ee');d=ImageDraw.Draw(board);ft=lambda n:ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',n)
d.text((35,20),'客厅 A1 首轮验证｜同一几何与相机，三种明确设计方向',font=ft(37),fill='#344d40')
proxy=OUT/'proxies';proxy.mkdir(exist_ok=True)
for i,(key,title) in enumerate(files):
 p=OUT/('LIVINGROOM_A1_'+key+'.png');x=(i%2)*1200+20;y=(i//2)*835+100
 d.text((x,y),title,font=ft(28),fill='#344d40')
 if p.exists():
  im=Image.open(p);im.load();assert im.size==(1536,1024);im.thumbnail((1160,774));board.paste(im,(x,y+48));sm=im.copy();sm.thumbnail((720,480));sm.save(proxy/(key+'.png'))
 else:d.text((x,y+170),'接口失败：参考失败报告',font=ft(26),fill='#81634b')
out=OUT/'LIVINGROOM_A1_CONTACT_SHEET.png';board.save(out)
small=board.copy();small.thumbnail((1000,746));small.save(proxy/'CONTACT_SHEET.png')
result=dict(status='GENERATED_PENDING_VISUAL_REVIEW' if S['generated']==3 else 'INTERFACE_FAILURE_WITH_BASE_READY',source_unchanged=True,geometry_locked_objects=M['source_objects_locked'],official_images=S['generated'],target=3,scope='A1_ONLY_STOP_AFTER_DELIVERY',contact_sheet=str(out),generation_seconds=S['total_seconds'],files_sha256={str(OUT/('LIVINGROOM_A1_'+key+'.png')):sha(OUT/('LIVINGROOM_A1_'+key+'.png')) for key,_ in files if (OUT/('LIVINGROOM_A1_'+key+'.png')).exists()})
(OUT/'A1_PREVIEW_MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
