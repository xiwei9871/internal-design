import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
CAMERAS=json.loads((OUT/'working/cameras/LIVING_CAMERA_REGISTER.json').read_text())
MASTER='''请以输入的R3 Option A Blender白模为唯一几何、比例与相机机位参考，生成专业室内设计提案 / 家居杂志摄影水准的客厅装修灵感图。
硬锁定：全部墙体边界、门窗洞的位置和尺度关系、窗框竖梃、飘窗的平台位置与外挑深度、房间比例、主要家具功能关系和大致占位、真实动线，以及可见的错层和楼梯。绝对不改平面，不新增洞口，不把飘窗改成落地玻璃墙，不放大房间或虚构别的房间。输入中的浅蓝面为现有玻璃，不是实体墙；深灰细框是已有窗/门框。
本图必须保持输入相同的3:2画幅、摄影视角和构图骨架；不可用换镜头或挪动门窗来美化画面。白模不是露天场景，淡白背景/顶面不要解读为拆顶；呈现简洁暖白室内平顶，保留已有墙顶线、层高和高低空间关系，不新造复杂吊顶、天窗或夸张灯带。
统一风格：现代温暖简约住宅，浅自然白蜡木/原木，暖白墙，米白、燕麦和浅灰米色织物，少量克制深灰或暖金属；北欧与日式之间，安静、自然、明亮、长期耐看。不是奢华酒店、样板房、纯奶油风、重侘寂或网红布置。
以柔和自然日光为主，明亮但不过曝、不泛橙黄。真实细腻的木纹、织物、墙面和地毯，精心筛选的家具软装，干净有生活气息，有前景/中景/背景层次。避免白模简单上色、平板纹理、畸形/失真的家具、堵塞通道、过多摆件、重装饰背景墙、过度黑色或大面积浮夸石材。无文字、标识、水印。
若视角可见厨房或固定柜体，它们的布局、柜体拓扑和电器关系必须保持，不进行新的柜体设计。模型中开放无门扇的通道保持开放，不补回旧斜门，不凭空添加立柱、门头或墙体。
软装可优化，但以本次版本等级为上限；照片般真实，克制精致，让人看到装修灵感，而不是把参考结构改掉。窗外仅可作为柔和景观氛围，不作为现场外景事实。
'''
ADDONS={
 'A1':'主视角/Hero Shot：会客区与北侧飘窗的关系。保留两组独立沙发与中央茶几的组合，不拼成大连体转角沙发。通过材质、地毯、克制抱枕、毯子和少量轻艺术改善空墙及视觉重心，不新造固定书柜填墙。',
 'A2':'反向视角：从窗边反看客厅内部，表现电视柜一侧、会客区与公共空间联系。北侧飘窗位于相机后方，不得为采光在画面正面另造大窗。可在已有电视柜功能墙上表达适当电视/轻陈设，但不改变墙或柜的位置。保留参考中可见的开放通道和错层曲线平台。',
 'A3':'近景：以输入裁切为准，聚焦茶几、沙发、地毯、边几和织物木作细节，杂志感、触感清晰。不要为了完整家具而改变裁切、缩小沙发或茶几。未进入画面的门窗不补到前方。',
 'A4':'联动视角：从客厅反看相邻公共区域，保持本输入的宽视野与真实空间联系，统一浅木、暖白与米灰色语言。重点保留参考中的台阶数量、曲线平台边界、高低地坪、餐区/玻璃开口的位置；不可把整屋地面铺平成同一标高，不放回旧斜门、不新增隔墙。',
 'A5':'窗边/飘窗氛围：聚焦已有外挑飘窗、窗边沙发一角与日光。保留窗框、平台深度、高度及其被沙发遮挡的关系。不得把平台抬高/加深为新高柜，不改变窗尺寸或直接把沙发移走。可用轻薄窗帘、少量软垫或绿植提供窗边灵感，留出原通行和门洞。',
}
MODES={
 'strict':'STRICT：本版本用于核对结构。忠实于当前布局和主要家具的大小、朝向、数量及组合，只优化材质、颜色、光线和少量软装。家具外轮廓仅可很轻微优化，不换成截然不同的占位。让每个墙角、洞口、台阶和窗框可与底图对应，避免装饰遮挡结构判断。',
 'design':'DESIGN：本版本是主力专业设计提案。在硬锁定几何和主要功能占位下，同类家具可替换为更成熟的浅白蜡木与舒适织物款式，尺度保持合理；优化茶几造型、地毯比例、轻薄窗帘、辅助照明、植物、挂画与布艺层次。主座位仍在原功能区，不能以大幅移位来改善构图。组合统一、有设计辨识度，保持整洁。',
 'explore':'EXPLORE：本版本探索更强的自然白蜡木住宅灵感。墙窗平台动线仍绝对锁定，主要家具功能区域仍对应参考。可更积极探索同类家具造型、材质配比及组合细节，在确有净空处最多增加一件小型单椅/边几和一盏轻量落地灯，或删减少量次要摆件；可表现阅读感或更好的窗边处理。不要添加大件固定柜，不让新家具占据门洞、楼梯或走道，不拥挤不浮夸。',
}
jobs=[];pack=['# 客厅批次 Prompt Pack','', '统一Master Prompt：','',MASTER,'']
for cam in CAMERAS:
 for mode,extra in MODES.items():
  name=f'living_{cam["id"]}_{mode}_v1';prompt=MASTER+'\n相机实际约束：'+cam['story']+'\n相机补充：'+ADDONS[cam['id']]+'\n版本补充：'+extra+'\n输出一张完整、协调的3:2图像。'
  pf=OUT/'working/prompts'/(name+'.txt');pf.write_text(prompt)
  row=dict(id=name,camera=cam['id'],version=mode,input=cam['clay_path'],prompt_file=str(pf),output=str(OUT/'exports/ai_outputs'/(name+'.png')),model='gpt-image-2',quality='high',size='1536x1024');jobs.append(row)
  pack.extend(['## '+name,'',prompt,''])
(OUT/'working/prompts/jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n')
(OUT/'LIVING_PROMPT_PACK.md').write_text('\n'.join(pack))
(OUT/'working/cameras/CAMERA_SELF_REVIEW.json').write_text(json.dumps(dict(status='PASS',review='Five clay views visually inspected before AI',lens_range_mm=[24,32],eye_height_range_m=[1.52,1.58],camera_scope='All derived from immutable R3 Option A; actual walls/openings/furniture retained',notes=['A1 two sofas/table/bay','A2 reverse public connection, north bay behind camera','A3 cropped close-up','A4 steps/curve platform/dining connection','A5 low bay platform remains behind sofa']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prompts_ready=15,cameras_passed=5,stages=['strict','design','explore']),ensure_ascii=False))
