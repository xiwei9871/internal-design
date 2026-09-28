#!/usr/bin/env python3
"""F1R.2 dining-only geometry optimization for frozen F1R-01H.

No formal CAD/canonical/V02/V03 edits. Searches 0/90-degree dining-table
placements on a 50 mm grid and renders actual A0.4 blocks in each candidate.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox as ezbbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
QC = ROOT / "qc/f1r_public_zone"
FURNITURE = ROOT / "concept/furniture_l1_final.json"
CANONICAL = ROOT / "current_existing/canonical_plan_v1.json"
WINDOWS = ROOT / "current_existing/window_register.json"
LEGENDS = ROOT / "assets/cad_library/standard/manifests/design_legend_manifest_v01.json"
RULES = ROOT / "knowledge/design_rules/design_rulebook_v01.json"
PATTERNS = ROOT / "knowledge/precedents/pattern_library_v01.json"
STD = ROOT / "assets/cad_library/standard"
PUBLIC_BOUNDS = [2500, -300, 8500, 13750]
DINING_REGION = [2700, 1800, 5400, 4500]
KITCHEN_KEEP = [5500, 0, 8200, 4700]
G_DIN_LIV = [2950, 4530, 5650, 4715]
BLOCKS = {
    "SOFA_3S_2200x900_PLAN": STD / "normalized/SOFA_3S_2200x900_PLAN.dxf",
    "SOFA_2S_1800x850_PLAN": STD / "normalized/SOFA_2S_1800x850_PLAN.dxf",
    "LOUNGE_CHAIR_900x900_PLAN": STD / "normalized/LOUNGE_CHAIR_900x900_PLAN.dxf",
    "DINING_TABLE_1500x600_PLAN": STD / "normalized/DINING_TABLE_1500x600_PLAN.dxf",
    "DINING_CHAIR_450x500_PLAN": STD / "normalized/DINING_CHAIR_450x500_PLAN.dxf",
}
sys.path.insert(0, str(SCRIPT_DIR))
import build_f1r_01h as base


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def intersection(a,b):
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3])
    return [x1,y1,x2,y2] if x2>x1 and y2>y1 else None
def area(r): return max(0,r[2]-r[0])*max(0,r[3]-r[1])
def center(r): return ((r[0]+r[2])/2,(r[1]+r[3])/2)
def edge_gap(a,b):
    dx=max(0,max(a[0],b[0])-min(a[2],b[2])); dy=max(0,max(a[1],b[1])-min(a[3],b[3])); return math.hypot(dx,dy)

def transformed_bbox(doc, refs):
    out=[]
    for obj, ref in refs:
        e=ezbbox.extents([ref]); actual=[float(e.extmin.x),float(e.extmin.y),float(e.extmax.x),float(e.extmax.y)]
        delta=max(abs(actual[i]-float(obj['rect'][i])) for i in range(4))
        out.append({**obj,"actual_rect":actual,"bbox_delta_mm":round(delta,3),"bbox_pass":delta<=1.0})
    return out

def actual_block_bboxes(doc, refs):
    return transformed_bbox(doc, refs)

def table_bbox(cx,cy,rot):
    return [cx-750,cy-300,cx+750,cy+300] if rot==0 else [cx-300,cy-750,cx+300,cy+750]

def chair_rects(table,rot):
    cx,cy=center(table)
    if rot==0:
        return [
            [cx-600, table[3]+100, cx-150, table[3]+600],
            [cx+150, table[3]+100, cx+600, table[3]+600],
            [cx-600, table[1]-600, cx-150, table[1]-100],
            [cx+150, table[1]-600, cx+600, table[1]-100],
        ]
    return [
        [table[0]-600, cy-600, table[0]-100, cy-150],
        [table[0]-600, cy+150, table[0]-100, cy+600],
        [table[2]+100, cy-600, table[2]+600, cy-150],
        [table[2]+100, cy+150, table[2]+600, cy+600],
    ]

def candidate_placements(cx,cy,rot):
    table=table_bbox(cx,cy,rot); chairs=chair_rects(table,rot)
    out=[{"id":"DIN-TABLE","block_id":"DINING_TABLE_1500x600_PLAN","rect":table,"rotation":rot,"role":"dining table","reason":"candidate table placement"}]
    for i,r in enumerate(chairs,1): out.append({"id":f"DIN-CHAIR-{i}","block_id":"DINING_CHAIR_450x500_PLAN","rect":r,"rotation":rot,"role":"dining chair","reason":"candidate four-seat daily configuration"})
    return out

def fixed_obstacles(canonical, furniture, living_bboxes):
    obs=[w['rect_mm'] for w in canonical['walls'] if w.get('disposition')=='EXISTING']
    obs += [KITCHEN_KEEP,[5300,4715,7800,5815],[7200,6600,7800,7800],[2900,6800,3400,7200]]
    obs += [x for x in living_bboxes]
    return obs

def candidate_metrics(placements, bbox_rows, canonical, furniture, windows):
    rows={x['id']:x['actual_rect'] for x in bbox_rows}; table=rows['DIN-TABLE']; chairs=[rows[f'DIN-CHAIR-{i}'] for i in range(1,5)]
    table_rotation=next(x['rotation'] for x in placements if x['id']=='DIN-TABLE')
    fixed=fixed_obstacles(canonical,furniture,[rows[x] for x in ['LIV-SOFA-3','LIV-SOFA-2','LIV-LOUNGE'] if x in rows])
    overlaps=[]
    for x in [table,*chairs]:
        for o in fixed:
            if intersection(x,o): overlaps.append({'object':x,'obstacle':o,'area_mm2':area(intersection(x,o))})
    for i,a in enumerate([table,*chairs]):
        for b in [table,*chairs][i+1:]:
            if intersection(a,b): overlaps.append({'object':a,'obstacle':b,'area_mm2':area(intersection(a,b))})
    path_blockers=[]; p2_blockers=[]
    for name,segs in furniture['paths'].items():
        for seg in segs:
            for obj in [table,*chairs]:
                if intersection(seg,obj):
                    hit={'path':name,'object':obj,'area_mm2':area(intersection(seg,obj))}
                    path_blockers.append(hit)
                    if name=="P2 entry->dining->kitchen": p2_blockers.append(hit)
    # Correct semantics: table edge -> chair near edge and table edge -> chair back edge.
    near_gaps=[]; seated=[]
    if table_rotation==0:
        table_top,table_bottom=table[3],table[1]
        for ch in chairs[:2]: near_gaps.append(ch[1]-table_top); seated.append(ch[3]-table_top)
        for ch in chairs[2:]: near_gaps.append(table_bottom-ch[3]); seated.append(table_bottom-ch[1])
    else:
        table_left,table_right=table[0],table[2]
        for ch in (chairs[0],chairs[1]): near_gaps.append(table_left-ch[2]); seated.append(table_left-ch[0])
        for ch in (chairs[2],chairs[3]): near_gaps.append(ch[0]-table_right); seated.append(ch[2]-table_right)
    opening=G_DIN_LIV
    north_chair_gap=max(0,opening[1]-max(ch[3] for ch in chairs if ch[1]<opening[1]))
    group_end_gap=max(0,opening[1]-max(ch[3] for ch in chairs))
    transition_clear=north_chair_gap if table_rotation==0 else group_end_gap
    kitchen_gap=KITCHEN_KEEP[0]-table[2] if table[2]<=KITCHEN_KEEP[0] else table[0]-KITCHEN_KEEP[2] if table[0]>=KITCHEN_KEEP[2] else 0
    chair_kitchen_gaps=[edge_gap(ch,KITCHEN_KEEP) for ch in chairs]
    chair_kitchen_gaps=[edge_gap(ch,KITCHEN_KEEP) for ch in chairs]
    # Additional chair pull-out reserve follows the chair's outward seating axis
    # and stops at the first wall or the KEEP kitchen boundary.
    pullout_reserve=[]
    for i,ch in enumerate(chairs):
        if table_rotation==0:
            direction=(0,1) if i<2 else (0,-1)
        else:
            direction=(-1,0) if i<2 else (1,0)
        cx=(ch[0]+ch[2])/2; cy=(ch[1]+ch[3])/2; reserves=[]
        for ob in fixed:
            if direction==(1,0) and ob[0]>=ch[2] and ob[1] < cy < ob[3]: reserves.append(ob[0]-ch[2])
            elif direction==(-1,0) and ob[2]<=ch[0] and ob[1] < cy < ob[3]: reserves.append(ch[0]-ob[2])
            elif direction==(0,1) and ob[1]>=ch[3] and ob[0] < cx < ob[2]: reserves.append(ob[1]-ch[3])
            elif direction==(0,-1) and ob[3]<=ch[1] and ob[0] < cx < ob[2]: reserves.append(ch[1]-ob[3])
        if direction==(0,1) and ch[1] < opening[1]: reserves.append(max(0,opening[1]-ch[3]))
        pullout_reserve.append({'chair_id':f'DIN-CHAIR-{i+1}','back_direction':direction,'extra_pullout_travel_available_mm':round(min(reserves) if reserves else 9999,3)})
    min_extra_pullout=min(x['extra_pullout_travel_available_mm'] for x in pullout_reserve)
    p2_clear=not p2_blockers
    return {
        'table_actual_bbox_mm':table,'chairs_actual_bboxes_mm':chairs,
        'table_to_chair_near_edge_gap_mm':round(min(near_gaps),3),
        'seated_envelope_from_table_edge_mm':round(min(seated),3),
        'extra_pullout_travel_available_mm':round(min_extra_pullout,3),
        'extra_pullout_travel_by_chair':pullout_reserve,
        'through_passage_behind_seated_mm':round(north_chair_gap,3) if table_rotation==0 else None,
        'g_din_liv_transition_clear_mm':round(transition_clear,3),
        'g_din_liv_transition_basis':'behind occupied north-side chairs' if table_rotation==0 else 'clear passage around north end of occupied dining group',
        'table_to_keep_kitchen_gap_mm':round(kitchen_gap,3),
        'closest_chair_to_keep_kitchen_gap_mm':round(min(chair_kitchen_gaps),3),
        'closest_chair_to_keep_kitchen_gap_mm':round(min(chair_kitchen_gaps),3),
        'chair_to_keep_kitchen_gaps_mm':[round(x,3) for x in chair_kitchen_gaps],
        'p2_path_clear':p2_clear,'p2_path_blockers':p2_blockers,'all_named_paths_clear':not path_blockers,'path_blockers':path_blockers,
        'overlaps':overlaps,'bbox_qa':all(x['bbox_pass'] for x in bbox_rows),
        'targets':{'seated_envelope_min_mm':600,'behind_seated_passage_min_mm':900,'table_to_keep_kitchen_min_mm':1000,'g_din_liv_transition_min_mm':900},
        'status': 'FEASIBLE_CANDIDATE' if not overlaps and not path_blockers and transition_clear>=900 and kitchen_gap>=1000 and min_extra_pullout>0 else 'REVIEW_REQUIRED'
    }

def render_candidate(doc, canonical, windows, furniture, placement_rows, metrics, path):
    fig,ax=plt.subplots(figsize=(8,11),dpi=180); base.draw_background(ax,canonical,windows,furniture['paths']); base.draw_geometry(ax,doc)
    for r in [metrics['table_actual_bbox_mm'],*metrics['chairs_actual_bboxes_mm']]: ax.add_patch(Rectangle((r[0],r[1]),r[2]-r[0],r[3]-r[1],fill=False,edgecolor='#a23d2d',linewidth=1.3,linestyle='--',zorder=20))
    ax.add_patch(Rectangle((5600,7800),2100,3000,fill=False,edgecolor='#1c9c5b',linewidth=1.5,linestyle='--',zorder=19)); ax.text(5620,10740,'actual clear region',fontsize=8,color='#1c9c5b',zorder=20)
    fig.suptitle(f"F1R.2 dining candidate — rot {placement_rows[0]['rotation']}°",x=0.07,y=0.99,ha='left',fontsize=13)
    ax.set_xlim(PUBLIC_BOUNDS[0],PUBLIC_BOUNDS[2]);ax.set_ylim(PUBLIC_BOUNDS[1],PUBLIC_BOUNDS[3]);ax.set_aspect('equal');ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)');ax.grid(True,linewidth=.35,alpha=.5);fig.tight_layout(rect=[0,0,1,0.96]);fig.savefig(path,bbox_inches='tight');plt.close(fig)

def main():
    furniture=load(FURNITURE);canonical=load(CANONICAL);windows=load(WINDOWS)['windows'];legend=load(LEGENDS); rules=load(RULES)['rules']; patterns=load(PATTERNS)['patterns']
    # Freeze F1R-01H living placement; only table/chairs vary.
    living=[x for x in base.hybrid_placements() if x['id']!='DIN-TABLE']; fixed_candidates=[]
    candidates=[]
    for rot in (0,90):
        # 0-degree placements start far enough east to avoid placing the table
        # short end flush to the west wall, while still meeting kitchen clearance.
        xs=range(3750,4301,50) if rot==0 else range(3500,4201,50)
        ys=range(2400,3101,50) if rot==0 else range(2550,3501,50)
        for cx in xs:
            for cy in ys:
                dining=candidate_placements(cx,cy,rot); placements=living+dining; chairs=base.chair_placements()
                # Fast search uses normalized target footprints; actual DXF extents are
                # rechecked only for the selected candidates after the grid search.
                bbox_rows=[{**x,"actual_rect":x["rect"],"bbox_delta_mm":0.0,"bbox_pass":True} for x in placements]
                metrics=candidate_metrics(placements,bbox_rows,canonical,furniture,windows)
                if metrics['status']=='FEASIBLE_CANDIDATE':
                    # First maximize real chair-back reserve; then transition and
                    # kitchen gap. Keep score descriptive and deterministic.
                    metrics['score']=round(metrics['extra_pullout_travel_available_mm']*10 + metrics['g_din_liv_transition_clear_mm']/100 + metrics['table_to_keep_kitchen_gap_mm']/1000,3)
                    candidates.append({'rotation':rot,'center_mm':[cx,cy],'placements':dining,'metrics':metrics,'bbox_rows':bbox_rows})
    candidates.sort(key=lambda x:(-x['metrics']['score'],x['rotation'],x['center_mm']))
    selected=[]
    # Reserve a comparison slot for each feasible orientation, then choose the
    # strongest spatially distinct candidate for the third slot.
    for rot in (0,90):
        match=next((c for c in candidates if c['rotation']==rot),None)
        if match: selected.append(match)
    for c in candidates:
        if len(selected)>=3: break
        if c in selected: continue
        if all(c['rotation']!=s['rotation'] or abs(c['center_mm'][0]-s['center_mm'][0])>=200 or abs(c['center_mm'][1]-s['center_mm'][1])>=250 for s in selected): selected.append(c)
    if not selected: raise RuntimeError('No feasible dining candidates found under requested targets')
    orientation_counts={str(rot):sum(c['rotation']==rot for c in candidates) for rot in (0,90)}
    result={'version':'f1r-02-v0.1','status':'HUMAN_REVIEW','scope':'dining-only optimization; living and formal CAD frozen','search':{'grid_mm':50,'orientations_deg':[0,90],'feasible_candidates_by_orientation':orientation_counts,'candidate_count_feasible':len(candidates)},'frozen_living_ids':['LIV-SOFA-3','LIV-SOFA-2','LIV-LOUNGE','LIV-MEDIA-WALL'],'existing_limitation':{'id':'G-LIV-NBALC','clear_width_mm':850,'classification':'EXISTING_CONFIRMED_LIMITATION','rule':'NO_WORSENING'},'knowledge_refs':{'rules':['DIN-CIR-005','DIN-CIR-006','DIN-CIR-007','SPC-ZONE-015','SPC-GRP-003'],'patterns':['PAT-LIV-04','PAT-LIV-05'],'reference_note':'numeric values are planning references, not automatic code gates'},'candidates':[],'input_hashes':{'furniture_l1_final.json':sha(FURNITURE),'canonical_plan_v1.json':sha(CANONICAL),'window_register.json':sha(WINDOWS),'design_legend_manifest_v01.json':sha(LEGENDS)}}
    for idx,c in enumerate(selected,1):
        # Rebuild the actual A0.4 block scene once for the selected candidate.
        placements=living+c['placements']; chairs=[]; doc,refs=base.make_doc(canonical,windows,legend,placements,chairs)
        bbox_rows=actual_block_bboxes(doc,refs); metrics=candidate_metrics(placements,bbox_rows,canonical,furniture,windows); c['metrics']=metrics; c['bbox_rows']=bbox_rows
        if metrics['status'] != 'FEASIBLE_CANDIDATE' or not metrics['bbox_qa']:
            raise RuntimeError(f"selected candidate failed actual transformed-geometry recheck: rotation={c['rotation']} center={c['center_mm']} status={metrics['status']}")
        plan_path=QC/f'F1R_02_candidate_{idx}.png'; render_candidate(doc,canonical,windows,furniture,c['placements'],c['metrics'],plan_path)
        entry={k:v for k,v in c.items() if k not in {'doc'}}; entry['plan_png']=str(plan_path); result['candidates'].append(entry)
    result['selection_policy']='All selected candidates satisfy zero obstacle overlap, zero named P2 blockers, seated envelope >=600 mm, table-to-KEEP kitchen >=1000 mm, and a clear G-DIN-LIV transition >=900 mm; through-passage-behind-seated is reported only for 0-degree layouts where occupied chairs directly face that route. Final choice remains human review.'
    (QC/'F1R_02_metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    lines=['# F1R.2 — Dining Geometry Optimization','', 'Dining-only concept comparison. Living F1R-01H, media wall, stair/ramp, walls/openings, KEEP kitchen and canonical data are frozen.', '', '## Semantics', '', '- `table_to_chair_near_edge_gap_mm`: table edge to chair near edge; it is not pullout space.', '- `seated_envelope_from_table_edge_mm`: table edge to chair back edge when occupied.', '- `extra_pullout_travel_available_mm`: minimum chair-back edge reserve to the first wall/opening/KEEP obstruction along that chair outward axis; per-chair values are listed.', '- `through_passage_behind_seated_mm`: reported only when occupied chairs are directly between dining and G-DIN-LIV; for 90° orientation it is N/A, and the clear route around the north end is separately reported as `g_din_liv_transition_clear_mm`.', '- Existing G-LIV-NBALC 850 mm is recorded as `EXISTING_CONFIRMED_LIMITATION / NO_WORSENING`.', '- Both 0° and 90° table orientations were searched on a 50 mm grid; selected drawings use actual transformed A0.4 geometry.', '- Reference rules: `DIN-CIR-005` chair pullout, `DIN-CIR-006` passage behind a seated diner, `DIN-CIR-007` dining/kitchen route. Values remain planning references, not automatic code gates.', '- Pattern context: `PAT-LIV-04` dining as kitchen extension and `PAT-LIV-05` dual-mode dining.', '']
    for i,c in enumerate(selected,1):
        m=c['metrics']; table_trade="greater kitchen gap" if m['table_to_keep_kitchen_gap_mm']>1100 else "meets kitchen-gap target with little extra"; transition_trade="large clear transition" if m['g_din_liv_transition_clear_mm']>=1200 else "transition clear but closer to the target"; pull_trade=f"minimum outward reserve {m['extra_pullout_travel_available_mm']} mm"; orientation_trade="chairs sit on table long sides; G-DIN-LIV passes around north table end" if c['rotation']==90 else "north occupied chairs sit between dining and G-DIN-LIV; inspect occupied-state passage"
        lines += [f"## Candidate {i} — rotation {c['rotation']}°, center {c['center_mm']}", '', f"- Plan: `F1R_02_candidate_{i}.png`", f"- Table bbox: `{m['table_actual_bbox_mm']}`", f"- Chair bboxes: `{m['chairs_actual_bboxes_mm']}`", f"- Table→chair near-edge gap: **{m['table_to_chair_near_edge_gap_mm']} mm** (placement gap, not pullout space)", f"- Seated envelope from table edge: **{m['seated_envelope_from_table_edge_mm']} mm**", f"- Extra pullout travel available (minimum of 4): **{m['extra_pullout_travel_available_mm']} mm**; per chair: `{m['extra_pullout_travel_by_chair']}`", f"- Through-passage behind occupied seat: **{m['through_passage_behind_seated_mm'] if m['through_passage_behind_seated_mm'] is not None else 'N/A for this orientation'}**", f"- G-DIN-LIV transition: **{m['g_din_liv_transition_clear_mm']} mm**; basis: {m['g_din_liv_transition_basis']}", f"- Table→KEEP kitchen actual gap: **{m['table_to_keep_kitchen_gap_mm']} mm**; closest chair→KEEP: **{m['closest_chair_to_keep_kitchen_gap_mm']} mm**", f"- P2 entry/dining/kitchen path clear: `{m['p2_path_clear']}`; all named paths clear: `{m['all_named_paths_clear']}`; overlaps `{len(m['overlaps'])}`", f"- Pros: {table_trade}; {transition_trade}; four-seat setup preserved.", f"- Trade-offs: {pull_trade}; {orientation_trade}.", '']
    lines += ['## Boundary','', 'No candidate is written to formal CAD. Select one dining candidate only after human review of the real plan and chair crossing behavior.']
    (QC/'F1R_02_design_audit.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'HUMAN_REVIEW','candidate_count':len(selected),'metrics':str(QC/'F1R_02_metrics.json'),'audit':str(QC/'F1R_02_design_audit.md')},ensure_ascii=False))

if __name__=='__main__': main()
