import hashlib,json,html
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'design/whole_house_model_v1'; PRE=OUT/'preview'; WEB=ROOT/'renders/whole_house_final_study_v1/whole_house_model_v1'; WEB.mkdir(exist_ok=True)
manifest=json.loads((OUT/'PREVIEW_MANIFEST.json').read_text()); decisions=json.loads((ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json').read_text()); audit=json.loads((OUT/'VERIFICATION.json').read_text())
records=[]
for item in manifest['images']:
    src=Path(item['path']); dest=WEB/(Path(item['path']).stem+'.jpg')
    with Image.open(src) as im:
        size=list(im.size);im.convert('RGB').save(dest,quality=88)
    records.append({'room_id':item['room_id'],'mode':item['mode'],'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'web_name':dest.name,'size':size,'web_bytes':dest.stat().st_size})
def card(r):return f'<article><h3>{html.escape(r["room_id"])} · {html.escape(r["mode"])}</h3><a href="{r["web_name"]}" target="_blank"><img src="{r["web_name"]}" alt="{html.escape(r["room_id"])}" loading="lazy"></a></article>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>C-Type 全屋模型 V1 · 房间方向候选</title><style>body{margin:0;background:#f4f0e8;color:#302d27;font-family:system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:29px}h2{font-size:22px;margin-top:35px}p,li{line-height:1.8}aside{background:#e6ddcc;padding:18px;border-radius:10px;line-height:1.8}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{background:#fff;padding:12px;border-radius:8px}img{display:block;width:100%;height:auto}table{width:100%;border-collapse:collapse;background:white}td,th{text-align:left;padding:10px;border-bottom:1px solid #ddd8ce}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){.grid{grid-template-columns:1fr}main{padding:16px}}</style><main><p>2026-10-12 · 低成本全屋模型预览 · 待逐房人工确认</p><h1>全屋模型 V1：15 房间模式候选</h1><aside>客厅和餐厅沿用已确认方向；其他房间按本轮逐项指定的 Faithful / Designer / Creative 模式标记。模型来自现有生产场景的独立副本。厨房窗户、阅读角书柜墙面、三阶台阶、原木扶梯、母亲主卧梳妆台、北阳台上柜均作为硬约束记录。当前是 Workbench 几何 / 模式预览，不是最终灯光或全屋 225 张效果图。</aside><h2>房间候选</h2><div class="grid">'''
for r in records:page+=card(r)
page+='</div><h2>房间决定表</h2><table><tr><th>房间</th><th>模式</th><th>说明</th></tr>'
for rid,c in decisions['rooms'].items():page+=f'<tr><td>{html.escape(rid)}</td><td>{html.escape(c["mode"])}</td><td>{html.escape(c["notes"])}</td></tr>'
page+=f'''</table><h2>技术状态</h2><p>源模型对象数 {audit['source_object_count']}；候选对象数 {audit['candidate_object_count']}；房间标记 {audit['room_markers']}；材料族标签 {audit['material_family_tags']}；13 项受保护哈希保持；缺失贴图 {len(audit['missing_images'])}。候选文件：<code>{html.escape(str(OUT/'WHOLE_HOUSE_MODEL_V1.blend'))}</code>。</p><p>未调用 Image2，未启动全屋批量队列，未改动源模型、Ground Truth 或用户正在使用的 Blender。下一步是逐房人工确认，再决定哪些房间进入高精度物件建模和效果图阶段。</p></main></html>'''
(WEB/'review_gallery.html').write_text(page);(WEB/'WEB_ARTIFACTS.json').write_text(json.dumps({'status':'HUMAN_REVIEW','records':records},ensure_ascii=False,indent=2)+'\n');print(WEB/'review_gallery.html')
