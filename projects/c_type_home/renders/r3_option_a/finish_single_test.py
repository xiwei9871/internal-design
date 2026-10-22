import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((OUT/'TEST_PREFLIGHT.json').read_text());m=json.loads((OUT/'TEST_BRANCH_MANIFEST.json').read_text())
source=Path(p['source']);assert sha(source)==p['source_sha256']
base=OUT/'living/authoritative/LIVING_01_DAY_CYCLES_TEST.png';edited=OUT/'living/inspiration/LIVING_01_ASH_DAY_IMAGE2_TEST.png'
a=Image.open(base);b=Image.open(edited);a.load();b.load();assert a.size==b.size==(1536,1024);assert b.format=='PNG'
board=Image.new('RGB',(3072,1140),'#f5f3ee');board.paste(a,(0,105));board.paste(b,(1536,105));d=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',32)
d.text((30,28),'Blender：R3 A 几何基准 · Cycles日间底图',font=font,fill='#354d42');d.text((1566,28),'gpt-image-2：单张灵感测试 · 待风格审核',font=font,fill='#354d42')
bp=OUT/'living/diagnostics/LIVING_01_BLENDER_VS_IMAGE2.png';board.save(bp)
review=f'''# R3 客厅单张生成测试 · 2026-10-02

测试已完成，状态 `R3_VISUAL_STYLE = HUMAN_REVIEW_SINGLE_TEST`。本轮没有展开任务书中的全屋或16张首批计划。

- [生成的单张灵感测试图]({edited})
- [对应Blender权威底图]({base})
- [底图与AI结果并排核对]({bp})
- [固定相机与平面包络]({OUT/'living/diagnostics/LIVING_01_CAMERA_PLAN.png'})
- [独立渲染分支]({p['branch']})
- [实际使用的提示词]({OUT/'LIVING_01_INSPIRATION_PROMPT.txt'})

## 生成服务结果

使用用户指定仓库 `fengfengzhidao/codex-image2-skill` 的原生CLI，请求模型 `gpt-image-2`、quality `high`、n=1。输入为该相机的Cycles底图，输出验证为PNG / RGB /1536×1024，约{edited.stat().st_size/1024/1024:.2f}MiB，非空白图像。此前旧接口返回HTTP400；按用户提供的新接口配置后生成成功。

API基址已设为用户指定的 `https://www.shenlanqaq.com/v1`。运行入口每次只从私有0600 `~/.env` 读取 CODEX_API_URL / CODEX_API_KEY，覆盖当前进程继承的旧值；替换了两个旧LaunchAgent，新的单一任务在登录和.env变化时同步到launchctl。已验证旧继承值不会覆盖dotenv，并验证LaunchAgent已注册且退出码0。密钥不写入新启动plist、项目文件或本报告。

## 图像审核

可见结果符合浅自然木、暖白、日间、自然织物、简洁居住感；两组沙发、边几与两层茶几的整体关系保持，没有被改成连体转角沙发，没有新增门洞或电视墙。生成图增加了地毯、绿植、书本、杯具和搭毯等软装，属于灵感表达，没有写回模型。

仍有轻微的窗沿、墙顶交线和家具表面轮廓差异。该图片不能作为逐像素或施工尺寸的几何证明；墙体、门窗、平台和家具定位继续以Blender底图及R3 A模型为准。外景绿化属于生成的氛围背景，并非对现场外景的确认。

## 模型和相机校验

唯一设计源为 `{source}`，SHA256 `{p['source_sha256']}`；测试结束哈希一致。所有材质、相机、灯光只改渲染分支，{m['geometry_locked_objects']}个源对象的网格、位置、旋转、缩放、父子关系和修改器保持。没有恢复旧门/旧卫生间方案，没有重建厨房或移动主家具。

本次相机28mm、视高1.55m，分辨率1536×1024。底图使用Blender5.2.1 / Cycles / Metal /64采样 /去噪 /AgX。先修正过亮底图再请求AI，原过曝光草稿保留在diagnostics中。相机、材质和几何锁登记分别为 R3_CAMERA_REGISTER.json、R3_MATERIAL_REGISTER.json、R3_SOURCE_GEOMETRY_LOCK.json。

所有图片、对照图和检查代理只保存在文件系统，以路径交付。下一步风格仍需用户审核；本次不自动推进其他房间。
'''
(OUT/'R3_RENDER_REVIEW.md').write_text(review)
report=dict(status='SINGLE_IMAGE_TEST_GENERATED_HUMAN_REVIEW',api_generation='PASS',requested_model='gpt-image-2',quality='high',actual_size=list(b.size),format=b.format,source_geometry_and_file='PASS',source_sha256=p['source_sha256'],source_locked_objects=m['geometry_locked_objects'],style_gate='HUMAN_REVIEW',ai_geometry='APPROXIMATE_VISUAL_MATCH_NOT_DIMENSION_AUTHORITY',test_image=str(edited),blender_base=str(base),prompt=str(OUT/'LIVING_01_INSPIRATION_PROMPT.txt'),review=str(OUT/'R3_RENDER_REVIEW.md'),paths_only=True)
files=[source,Path(p['branch']),base,edited,bp,OUT/'LIVING_01_INSPIRATION_PROMPT.txt',OUT/'R3_RENDER_REVIEW.md',OUT/'R3_RENDER_STYLE_GUIDE.md',OUT/'R3_CAMERA_REGISTER.json',OUT/'R3_MATERIAL_REGISTER.json']
report['files_sha256']={str(f):sha(f) for f in files}
(OUT/'SINGLE_IMAGE_TEST_MANIFEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(test='PASS',image=str(edited),size=list(b.size),source_geometry='PRESERVED',source_hash='MATCH',ai_geometry='VISUAL_REVIEW_ONLY'),ensure_ascii=False))
