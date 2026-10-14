"""Add a clearly labeled isolated pane inspection without replacing prior gallery."""
from pathlib import Path
from PIL import Image
import shutil
R=Path(__file__).resolve().parents[1];D=R/'design/pale_ash_review_v7';O=R/'renders/whole_house_final_study_v1/pale_ash_review_v7'
im=Image.open(D/'review_final/slider_isolated.png').convert('RGB');im.thumbnail((1000,1100));im.save(O/'slider_isolated.jpg',quality=88)
p=O/'review_gallery.html';backup=O/'review_gallery_pre_studio.html';assert not backup.exists();shutil.copyfile(p,backup)
s=p.read_text();section='<section><h2>玻璃门整件补充检查</h2><p>房间相机中门扇处于靠墙停靠位置，部分被墙遮挡；以下独立工作室视图检查10mm玻璃、边框及把手夹持件。背景格纹仅用于观察透射，不是室内设计元素。实际Cycles1000×1100、64samples，不替代上方房间光效。</p><img style="max-width:700px" src="slider_isolated.jpg"></section>'
s=s.replace('<section><h2>真实图册参照</h2>',section+'<section><h2>真实图册参照</h2>');p.write_text(s);print('STUDIO_EVIDENCE_ADDED')
