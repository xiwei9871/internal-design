#!/usr/bin/env python3
"""Audit the newest FCStd update; proposal ghosts are never applied."""

from pathlib import Path
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Patch, Rectangle


ROOT = Path("/Users/xiwei/interior_design")
BASE = ROOT / "projects/c_type_home"
OUT = BASE / "design/s2_current_design_v1"
INGEST = OUT / "latest_fcstd_round3.json"
CANONICAL = BASE / "current_existing/canonical_plan_v1.json"
WINDOWS = BASE / "current_existing/window_register.json"
KITCHEN = BASE / "current_existing/kitchen_cabinet_register.json"
GEOMETRY = BASE / "data/geometry.json"


def load():
    ingest = json.loads(INGEST.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    windows = json.loads(WINDOWS.read_text(encoding="utf-8"))["windows"]
    kitchen = json.loads(KITCHEN.read_text(encoding="utf-8"))["cabinets"]
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    boxes = {}
    for row in ingest["objects"]:
        if row.get("bbox_abs_mm"):
            b = row["bbox_abs_mm"]
            boxes[row["label"]] = [b[0] - 1298172.0, b[1] + 296458.0, b[2] - 1298172.0, b[3] + 296458.0]
    rooms = {row["id"]: [min(p[0] for p in row["polygon_mm"]), min(p[1] for p in row["polygon_mm"]), max(p[0] for p in row["polygon_mm"]), max(p[1] for p in row["polygon_mm"])] for row in geometry["spaces"]}
    openings = {row["id"]: row["rect_mm"] for row in canonical["openings"]}
    return ingest, boxes, rooms, openings, canonical, windows, kitchen


def translation_to_separate(a, b):
    candidates = [(abs(b[0] - a[2]), b[0] - a[2], 0.0, "move left"), (abs(b[2] - a[0]), b[2] - a[0], 0.0, "move right"), (abs(b[1] - a[3]), 0.0, b[1] - a[3], "move down"), (abs(b[3] - a[1]), 0.0, b[3] - a[1], "move up")]
    return min(candidates, key=lambda x: x[0])


def draw_base(ax, canonical, windows, kitchen, boxes, focus=None, xlim=None, ylim=None):
    for wall in canonical["walls"]:
        x0, y0, x1, y1 = wall["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f1f3f5", edgecolor="#adb5bd", linewidth=0.35))
    for window in windows:
        x0, y0, x1, y1 = window["opening_rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#bde0fe", edgecolor="#087f8c", linewidth=0.8, alpha=0.7))
    for cabinet in kitchen:
        x0, y0, x1, y1 = cabinet["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#f4a261", edgecolor="#9d2b1f", linewidth=0.4, alpha=0.55))
    for opening in canonical["openings"]:
        x0, y0, x1, y1 = opening["rect_mm"]; ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor="#6c757d", linewidth=0.6)); r=max(x1-x0,y1-y0); ax.add_patch(Arc((x0,y0),2*r,2*r,color="#6c757d",theta1=0,theta2=90,linewidth=0.45))
    for label, b in boxes.items():
        if focus is not None and label not in focus: continue
        x0,y0,x1,y1=b; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor="#dbeafe" if focus else "none",edgecolor="#1d3557" if focus else "#adb5bd",linewidth=1 if focus else 0.3,alpha=0.7))
        if focus is not None: ax.text((x0+x1)/2,(y0+y1)/2,label,ha="center",va="center",fontsize=5,color="#1d3557")
    ax.set_aspect("equal",adjustable="box"); ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_xlabel("Task01 X (mm)"); ax.set_ylabel("Task01 Y (mm)")


def main():
    ingest, boxes, rooms, openings, canonical, windows, kitchen = load()
    owner_wc=boxes["次主卫马桶"]; mother_wc=boxes["主卫马桶"]
    owner_room=rooms["R-CLOAK"]; mother_room=rooms["R-BATH-M"]
    owner_front_plus=owner_room[3]-owner_wc[3]; owner_front_minus=owner_wc[1]-owner_room[1]
    mother_front_plus=mother_room[3]-mother_wc[3]; mother_front_minus=mother_wc[1]-mother_room[1]
    mother_bed=boxes["主卧床"]; mother_room_box=rooms["R-MASTER"]
    desired_x0=mother_room_box[0]+(mother_room_box[2]-mother_room_box[0]-(mother_bed[2]-mother_bed[0]))/2
    mother_dx=desired_x0-mother_bed[0]
    wardrobe=boxes["次卧衣柜"]; balcony_open=windows[2]["opening_rect_mm"] if windows[2]["window_id"]=="G-GB-BALC" else next(x["opening_rect_mm"] for x in windows if x["window_id"]=="G-GB-BALC")
    wardrobe_dx=translation_to_separate(wardrobe,balcony_open)
    data={"source_mtime":ingest["source_mtime"],"source_sha256":ingest["source_sha256"],"object_count":ingest["freecad_object_count"],"named_count":ingest["named_guide_object_count"],"wc_orientation_check":{"owner_ensuite":{"bbox":owner_wc,"front_plus_y_mm":owner_front_plus,"front_minus_y_mm":owner_front_minus,"negative_is_orientation_dependent":owner_front_plus<0},"mother_bath":{"bbox":mother_wc,"front_plus_y_mm":mother_front_plus,"front_minus_y_mm":mother_front_minus,"negative_is_orientation_dependent":mother_front_plus<0}},"proposed_only":{"mother_bed":{"current_bbox":mother_bed,"proposed_dx_mm":mother_dx,"proposed_dy_mm":0.0,"rotation_delta_deg":0.0,"applied":False},"wardrobe":{"current_bbox":wardrobe,"opening":balcony_open,"proposed_dx_mm":wardrobe_dx[1],"proposed_dy_mm":wardrobe_dx[2],"rotation_delta_deg":0.0,"method":wardrobe_dx[3],"applied":False}},"new_guides":{"3kg_washer":boxes.get("3kg洗衣机"),"printer":boxes.get("打印机"),"nas":boxes.get("nas")}}
    (OUT/"latest_update_audit_v01.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Four-panel overlay: WC orientation, mother-bed proposal, wardrobe proposal, new objects.
    fig,axes=plt.subplots(2,2,figsize=(16,12),dpi=170)
    draw_base(axes[0,0],canonical,windows,kitchen,boxes,{"次主卫马桶","主卫马桶"},(8800,16500),(4300,6800)); axes[0,0].set_title("WC FRONT DIRECTION — report-only")
    for b, name in ((owner_wc,"OWNER ENSUITE WC"),(mother_wc,"MOTHER BATH WC")):
        axes[0,0].text((b[0]+b[2])/2,b[3]+120,f"{name}\nfront +Y: {owner_front_plus if name.startswith('OWNER') else mother_front_plus:.1f} mm\nfront -Y: {owner_front_minus if name.startswith('OWNER') else mother_front_minus:.1f} mm",ha="center",fontsize=7,color="#d00000")
    draw_base(axes[0,1],canonical,windows,kitchen,boxes,{"主卧床"},(11600,15400),(-200,4700)); axes[0,1].add_patch(Rectangle((mother_bed[0]+mother_dx,mother_bed[1]),mother_bed[2]-mother_bed[0],mother_bed[3]-mother_bed[1],facecolor="none",edgecolor="#00a000",linestyle="--",linewidth=1.3)); axes[0,1].annotate("",xy=(mother_bed[0]+mother_dx,(mother_bed[1]+mother_bed[3])/2),xytext=(mother_bed[0],(mother_bed[1]+mother_bed[3])/2),arrowprops={"arrowstyle":"->","color":"#00a000"}); axes[0,1].text(11800,4200,f"report-only proposal dx={mother_dx:.1f} mm, dy=0, rotation=0°",color="#008000",fontsize=8); axes[0,1].set_title("MOTHER BED — proposed horizontal translation only")
    draw_base(axes[1,0],canonical,windows,kitchen,boxes,{"次卧衣柜"},(9800,10300),(10300,11200)); axes[1,0].add_patch(Rectangle((wardrobe[0]+wardrobe_dx[1],wardrobe[1]+wardrobe_dx[2]),wardrobe[2]-wardrobe[0],wardrobe[3]-wardrobe[1],facecolor="none",edgecolor="#00a000",linestyle="--",linewidth=1.3)); axes[1,0].text(10000,11100,f"report-only {wardrobe_dx[3]} dx={wardrobe_dx[1]:.1f} mm, dy={wardrobe_dx[2]:.1f} mm",color="#008000",fontsize=8); axes[1,0].set_title("WARDROBE / G-GB-BALC — proposed minimum translation only")
    draw_base(axes[1,1],canonical,windows,kitchen,boxes,{"3kg洗衣机","打印机","nas","洗衣机+烘干机（叠放）","冰柜"},(7800,13200),(6500,13600)); axes[1,1].set_title("NEW HUMAN GUIDE OBJECTS — latest FCStd")
    fig.suptitle("Latest FCStd update audit — all proposals are report-only; no layout changes applied",fontsize=15); fig.tight_layout(rect=[0,0,1,0.97]); png=OUT/"LATEST_FCSTD_UPDATE_AUDIT.png"; pdf=OUT/"LATEST_FCSTD_UPDATE_AUDIT.pdf"; fig.savefig(png,dpi=220); fig.savefig(pdf); plt.close(fig)
    md=["# Latest FCStd Update Audit","","Status: `HUMAN_REVIEW`","",f"Source mtime: `{data['source_mtime']}`",f"Source SHA256: `{data['source_sha256']}`",f"FreeCAD objects: {data['object_count']}",f"Named objects: {data['named_count']}","","## WC front-direction verification","",f"- Owner ensuite WC bbox: `{owner_wc}`; front +Y = `{owner_front_plus:.1f} mm`; front -Y = `{owner_front_minus:.1f} mm`.",f"- Mother bath WC bbox: `{mother_wc}`; front +Y = `{mother_front_plus:.1f} mm`; front -Y = `{mother_front_minus:.1f} mm`.","- The previous negative values occur under the +Y front interpretation; the opposite direction yields positive available depth. No WC was rotated or moved.","","## Report-only permitted changes","",f"- Mother bed: proposed dx = `{mother_dx:.1f} mm`, dy = `0.0 mm`, rotation = `0°`; not applied.",f"- 次卧衣柜 vs G-GB-BALC: report-only `{wardrobe_dx[3]}` dx = `{wardrobe_dx[1]:.1f} mm`, dy = `{wardrobe_dx[2]:.1f} mm`; not applied.","","## New named objects","",f"- 3kg washing machine: `{data['new_guides']['3kg_washer']}`.",f"- Printer: `{data['new_guides']['printer']}`.",f"- NAS: `{data['new_guides']['nas']}`.","","No object was moved, rotated, or rewritten in the source FCStd.","Blender = HOLD; formal CAD = false."]
    (OUT/"LATEST_FCSTD_UPDATE_AUDIT.md").write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({"status":"HUMAN_REVIEW","png":str(png),"pdf":str(pdf),"audit":str(OUT/"LATEST_FCSTD_UPDATE_AUDIT.md"),"mother_dx":mother_dx,"wardrobe_dx":wardrobe_dx[1]},ensure_ascii=False))


if __name__=='__main__': main()
