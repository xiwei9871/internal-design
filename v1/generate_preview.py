from base64 import b64encode
from pathlib import Path

root = Path(__file__).resolve().parent
content = root / 'preview_inline.html'
svg = (root / 'floorplan_v1.svg').read_text().replace('<svg ', '<svg style="width:100%;height:auto;display:block" ')
png = b64encode((root / 'blockout_v1.png').read_bytes()).decode('ascii')
html = f'''<h2>住宅方案级重建 V1</h2>
<p class="subtitle">自包含预览｜平面图与 Blender 体块均已内嵌，点击区域选择下一轮优化重点。</p>
<div class="split">
  <div class="mockup"><div class="mockup-header">平面草模｜PNG 尺寸链重建</div><div class="mockup-body">{svg}</div></div>
  <div class="mockup"><div class="mockup-header">Blender 体块｜验证房间关系</div><div class="mockup-body"><img src="data:image/png;base64,{png}" style="width:100%;height:auto" /></div></div>
</div>
<div class="options" data-multiselect>
  <div class="option" data-choice="living" onclick="toggleSelect(this)"><div class="letter">A</div><div class="content"><h3>先优化客餐厅</h3><p>研究餐桌、沙发、电视墙和入户动线。</p></div></div>
  <div class="option" data-choice="storage" onclick="toggleSelect(this)"><div class="letter">B</div><div class="content"><h3>先优化收纳</h3><p>研究玄关、卧室衣柜、厨房和家政柜。</p></div></div>
  <div class="option" data-choice="wetareas" onclick="toggleSelect(this)"><div class="letter">C</div><div class="content"><h3>先优化厨卫</h3><p>研究厨房、次卫、主卫和洗烘设备关系。</p></div></div>
</div>'''
content.write_text(html)
print(content)
