"""Preserve uploaded originals and build the persistent site evidence inventory."""
from pathlib import Path
import json
import hashlib
import shutil
from PIL import Image, ImageDraw, ImageFont, ExifTags

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
INPUT=Path('/private/var/folders/ch/yf284jsj7f7_b0tgqkpxhwq00000gn/T')
SOURCES=[
 ('03c642c5-c2ea-45ab-a67f-377f20eef07f','KITCHEN','冰箱、侧高柜与冰箱上柜','approx north fridge run'),
 ('51ffddad-4c85-4cd4-a744-904652aba989','KITCHEN','冰箱转角、微波炉架与台面','approx north/east corner'),
 ('842dcee4-8a04-4596-b455-650e594f4466','KITCHEN','长柜、灶台、抽屉、洗碗机与开放格','approx east cabinet run'),
 ('fddd0fe3-3391-499c-be80-61c321ab869c','KITCHEN_ADJACENT','水槽端、台面旁矮柜、柱侧与高储物柜','approx sink/west return; exact new-cabinet placement unconfirmed'),
 ('67f7a546-d678-4571-8b09-50c490b066ab','KITCHEN','水槽、窗前设备、侧开放架与回转矮柜','approx south sink and west return'),
 ('b0d38a6a-862b-4ae8-971a-48a1b0e2b767','ADJACENT_BALCONY','窗边餐边／储物柜与木质斜顶','adjacent balcony cabinet; R029/R032 identity pending')]
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
records=[];panels=[]
(OUT/'originals').mkdir(exist_ok=True)
(OUT/'previews').mkdir(exist_ok=True)
for n,(uuid,room,description,direction) in enumerate(SOURCES,1):
    photo_id=f'SITE_PHOTO_KITCHEN_{n:03d}'
    source=INPUT/f'codex-clipboard-{uuid}.jpg'
    dest=OUT/'originals'/f'{photo_id}.jpg'
    if dest.exists():
        assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest()
    else:shutil.copy2(source,dest)
    im=Image.open(dest);exif=im.getexif();values={ExifTags.TAGS.get(k,str(k)):str(v) for k,v in exif.items()}
    info=dict(photo_id=photo_id,filename=str(dest.relative_to(ROOT)),original_upload=str(source),
        sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),room=room,approx_direction=direction,
        image_size=list(im.size),exif_focal_length=values.get('FocalLength'),
        exif_focal_length_35mm=values.get('FocalLengthIn35mmFilm'),exif_camera_model=values.get('Model'),
        description=description,status='INGESTED_REGISTRATION_PENDING',
        visible_architectural_anchors=['wall/cabinet verticals','counter edges','window/column edges where visible'],
        dimension_authority='PHOTO_RELATIONSHIPS_ONLY_UNTIL_REGISTRATION_AND_SCALE_GATE',
        source_context='User states old cabinet PDF was initial installation; photos show subsequent alterations')
    records.append(info)
    preview=im.convert('RGB');preview.thumbnail((1400,1400));preview.save(OUT/'previews'/f'{photo_id}.png')
    small=im.convert('RGB');small.thumbnail((740,700))
    panel=Image.new('RGB',(780,800),'#f4f6f7');panel.paste(small,((780-small.width)//2,78))
    draw=ImageDraw.Draw(panel);draw.text((20,12),photo_id,font=ImageFont.truetype(FONT,23),fill='#243b47')
    draw.text((20,44),description,font=ImageFont.truetype(FONT,19),fill='#53656f');panels.append(panel)
sheet=Image.new('RGB',(2340,1600),'#d7dfe3')
for n,panel in enumerate(panels):sheet.paste(panel,((n%3)*780,(n//3)*800))
sheet.save(OUT/'SITE_PHOTO_CONTACT_SHEET.png')
(OUT/'SITE_PHOTO_REGISTER_V01.json').write_text(json.dumps(dict(register='SITE_PHOTO_REGISTER_V01',
    scope='KITCHEN_AND_PHOTOGRAPHED_ADJACENT_CABINETRY_ONLY',authority='USER_SUPPLIED_CURRENT_SITE_PHOTOS',
    photos=records,photo_count=len(records),focal_length_source='NO_USABLE_FOCAL_EXIF_IN_CLIPBOARD_IMAGES'),ensure_ascii=False,indent=2))
print(json.dumps({'photo_count':len(records),'copied_originals':True,'contact_sheet':str(OUT/'SITE_PHOTO_CONTACT_SHEET.png')},ensure_ascii=False,indent=2))
