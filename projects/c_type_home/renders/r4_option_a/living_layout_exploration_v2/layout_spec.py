from pathlib import Path
import json
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
SOURCE_SHA='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
BASE_CAMERAS=json.loads((OUT.parent/'whole_house_ai_v1/01_living/reports/CAMERA_REGISTER.json').read_text())
PRIORITY=['L1','L2','L5'];OPTIONAL=['L3','L4']
LAYOUTS={
 'A':dict(slug='swap',folder='layoutA_swap',name='A · Swap',description='保留原2300x900三人位；1700x900贵妃椅从南内侧移到北侧窗前，1900x850双人位移到南内侧并旋转180°面向会客中心；以两张木腿浅石茶几和开放圆边几替换方桌/抽屉角几。',sofa='original three-seat sofa in west position + inner two-seater facing north + window chaise',chaise_center=[5.50,12.36],two_center=[4.80,8.24],two_rotation=180,table_center=[5.28,10.32],side_centers=[[4.00,12.21]],lighting='slim warm-metal reading floor lamp beside window chaise; discreet flat ceiling lights',art='one restrained large textile abstract over west sofa',rug='large thin oatmeal rectangular wool-linen rug with soft round corners'),
 'B':dict(slug='lightlounge',folder='layoutB_lightlounge',name='B · Light Lounge',description='保留原三人位；贵妃椅移到北侧窗前；彻底取消双人位，南内侧改一件开放木框单椅和轻圆边几，不补第二件小沙发。木石主副双茶几，更少家具、更松弛。',sofa='original three-seat sofa in west position + window chaise + only one open ash-frame lounge chair in inner south area',chaise_center=[5.50,12.36],chair_center=[4.60,8.40],chair_angle=-15,table_center=[5.28,10.32],side_centers=[[4.00,12.21],[5.42,8.35]],lighting='slim adjustable floor reading lamp at window, one small sculptural portable lamp; no LED strips',art='one large softly textured pale artwork, calm designer expression',rug='thin rounded oatmeal flatweave rug, unbusy'),
 'C':dict(slug='lsofa',folder='layoutC_lsofa',name='C · L-Sofa',description='取消原独立双人位和贵妃椅；西侧主沙发整合为同一家族L型模块沙发，北侧回转段面向会客中心；北窗前仅一件轻白蜡木观景躺靠椅，保留休闲属性而不复制独立双人沙发。统一双茶几与圆边几。',sofa='one coherent L-shaped modular sofa in west + north-return seating zone + one light ash-framed reclining lounge chair at bay window; no independent loveseat or second sofa',chair_center=[5.73,12.22],chair_angle=35,table_center=[5.20,9.70],side_centers=[[4.20,12.18]],lighting='one graceful slim arc reading floor lamp at window and subtle low-glare wall wash, simple flat ceiling',art='one restrained large textile composition over western L-sofa leg',rug='generous oatmeal rectangular wool-linen rug integrated with L-seating'),
}
STYLE='浅白蜡木/自然浅原木、暖白墙、米白亚麻与燕麦布艺、明亮清爽、柔和自然日光；成熟住宅designer表达，适度creative。木腿+暖浅石材台面；无大黑电视墙、豪华酒店风、重吊顶或过量陈设。'
