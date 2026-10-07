"""Summaries/dimension overlays/delivery packaging; binaries remain local."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/study_room_v1'
audit=json.loads((R/'STUDY_ROOM_EXISTING_AUDIT.json').read_text())
layout=json.loads((R/'STUDY_ROOM_LAYOUT_V1.json').read_text())
clear=json.loads((R/'STUDY_ROOM_CLEARANCE_V1.json').read_text())
def write(n,s):(R/n).write_text(s.strip()+'\n')
write('STUDY_ROOM_EXISTING_AUDIT.md',f"""
# C-Type Study Room — Existing Audit
Status: measured model evidence; source frozenR4-derived currentreview14, not a site resurvey.
Git base: origin/improve/design-output-v14 (bd22a84). Study-specific names + existing wallpartindex only.
Frame: source X east, Y north, Z up, meter. Room floorZ450mm. Approximate main clear rectangle3100×4300mm.
Inherited source: {audit['source']}
Source SHA256: {audit['source_sha256']}

Sill plate measured2200×723mm atZ900mm,450mm above roomfloor. The inner opening/wallpiers restrict the continuous furniture/sleeping length to1880mm, not2200mm.
Usable bay depth to glass-side margin is650mm; existing structural sill AABB and usable envelope are different measurements.
Sillfront-to-oldtable1460mm; sillfront-to-nearestbookcaseedge207mm, laterally outside the sleeping envelope.
Old desk2200×800×750mm; rearchairgap664mm; tea counter-to-tablegap297mm.
Old openbookcase4200×450×2000mm,9×6=54 equalgridcells; approximately69.8% projectedwhole-wallcoverage (4300×2800mm wallreference).
Door leaf850mm,hinge[13.0,6.7]sourceXY; inherited doorgeometry untouched.
Tea servicecounter1600×450mm, top900mm above FFL, including sink/drain/feed, is retained.

Frozen R4 SHA256: {audit['authority_hash_before']['R4']}
Frozen B0 SHA256: {audit['authority_hash_before']['B0']}
""")
write('STUDY_ROOM_LAYOUT_V1.md',"""
# C-Type Study Room V1 — HUMAN_REVIEW
Authority: DERIVED_DESIGN_MODEL. Architecture, walls,door/windowopenings,levels,frozenR4/B0 unchanged.
Study-first,fixedDaybed+storage,lighterbookcase;noindependentsofa or sofabed. NoImage2/Cycles/finalmaterialwork.

FixedDaybed1880×1200mm. Existingusablebaydepth650mm plus550mm fixedfurnitureextension.
Structuralwalllimitsclosedstoragecarcass to390mmdepth; thetimbertop bridgesabovetheunmodifiedsill.
TopZ925mm (475mm above FFL). Daily seat610mmdeep plus570mm visiblewood;3 removablebackcushions.
3 hollowfrontdrawers, approximately577×331×276mm nominalinteriorperdrawer.
Guestmode uses1880×1200×30mm thinremovabletopperproxy. Thefoldedstorageproxy is NOT a verifiedproductpackingclaim.
Thickmattress is notvalidated; thinfoldable/modulartopper choice and drawerpacking need human/productreview.

Bookcase: continuous4000×380×800mm lowerclosedcabinet with ventilatedprinter/NAS reserve fromexistingownerbrief.
Upper300mmdeep,1200mmhigh,unequal500/900/1050mm niches across2450mm width. Central1550mm wallleftblank.
61.25% upperbandoccupied/38.75% breathing. Whole-wallopenprojection drops from69.8% to24.4%;
these are distinct denominators and not contradictory. No fakefull-wallgrid. Fourbookproxiesonly.

Tea/worktable2000×800×750mm,lightframe,independentmovable. Daily sourcebounds[14.21,7.58,.45]to[15.01,9.58,1.20].
Guest deskshift[0,-.35,0]m;chairmoves[-.34,-.35,0]m andstoolparksunderdesk. One chair+one smallstool.
Existingtea/servicecounterandplumbingremaininherited. Unrelatedhousefurnitureunchanged.
Samewhole-house successor inDAILY/GUEST states, taskproxies onlyboundedstudycontext.

Owner correction: deskedge-to-bookcasefront750mm;chair500×500mm;chairbackgap300mm;chairfront50mmundertable for operation only. Mainroute is1110mm onthefront/westside ofdesk. Door850mm controlswhole-routeminimum.
Decision: reviewroomtopology/daybeddepth/circulation/bookshelfmassing/deskposition beforeanylookdev.
""")
write('STUDY_ROOM_CLEARANCE_V1.md',f"""
# Study Room Clearance — HUMAN_REVIEW
DAYBED_1200_CLEARANCE_GATE = {clear['daybed_1200_clearance_gate']}
Native furniture-vs-namedarchitecturetriangleintersections: none.
Inherited850mm doorleaf0..90degree swept in5degreesteps againstcurrentdaily/guestfurniture: no hits.
This is a model-basedstudy, not a code/installcertification.

| Measurement | Daily | Guest |
|---|---:|---:|
| Daybed front to desk | 920mm | 1270mm |
| Deskedge tobookcasefront | 750mm | 750mm |
| Chair footprint/rear operationgap | 500×500mm /300mm | parkedunderdesk |
| Mainroute infront/westofdesk | 1110mm | 1110mm |
| Entry clearwidth/inheriteddoor | 850mm | 850mm |
| Minimum whole-route includingentry | 850mm | 850mm |
| Open drawer to desk | 470mm | 820mm |

Mainfront/westroute1110mm meets900mmdaily preference. 300mmbehindchair is NOT a through-route and is not used forclearanceGate.
Retrievingdrawersusestheoppositesidepassage;470mm isnotdescribed as a walkingaisle.
Guestshift350mm south hasbeen includedindoorsweepcheck.
DailybookcasefrontdooropeningandNASventilationinstallare notshop-drawingcertified.
Topperstoragefold/comfortneedproductconfirmation; no assertion that an80mmthick mattress fitsdrawers.
Tea/worktable2000x800mm replaces1500x700; singlehostentersfromnorth920mm; southcountergap473mm isnotthroughroute. Guestcountergap123mm afterlocalshift isalsoNOT a route; entryremainswest/north. Nochairsaddedforthispass; otherseatingsidepositions arefuturereview. Roomgeometrynotdistorted.

R4 hash after: {clear['authority_hash_after']['R4']}
B0 hash after: {clear['authority_hash_after']['B0']}
Finalbeautyrendering: NOT_STARTED.
""")
write('WORK_STATE.md',"""
# C-Type Study Room Optimization V1
Stage: geometry+requiredWorkbenchpreviews+taskproxyexport;HUMAN_REVIEW.
Branch study/c-type-study-room-daybed-v1, Gitbasebd22a84 origin/improve/design-output-v14.
Model inherited currentreview14, studyunchangedfromR4 beforetask; nofullhousesemanticrediscovery.
MeasuredDaybed1880×1200mm, extension550mm, realstorage390mmdeep becausewallremains.
Owner revised deskposition:750mmcabinetgap/500mmchair/300mmbackgap/50mmunder-tablefrontinset;mainfront/westroute1110mm. Daily/Guestshiftanddoorclearance documented;thin30mmtopperpackingunverified.
Bookcase61.25% upperbandopen,4000mmclosedbase;tea/worktable2000×800mm. Singlehost approachesfromnorth920mm; southcountergap473mm isnotthroughroute.
FrozenR4/B0 SHA unchanged; otherinheritedobjectstatesprotectedbyexactretirementallowlist.
Generatedblend/png/glb/json/logs are localartifacts. Finalbeautyrendering notstarted. Noauto-merge.
""")
# Artifact aliases requested byowner, compatiblemanifest+GLB perstate.
for mode in ['daily','guest']:
 out=R/('proxy_'+mode);m=json.loads((out/'interaction_proxy.manifest.json').read_text())
 alias='study_room_v1_proxy' if mode=='daily' else 'study_room_v1_guest_proxy'
 shutil.copy2(out/m['proxy_uri'],R/(alias+'.glb'));m['proxy_uri']=alias+'.glb'
 (R/(alias+'.manifest.json')).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
# Annotategeometric topview using exactcamera scale;Englishlabelsavoidfontdependencies.
from PIL import Image,ImageDraw,ImageFont
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,19);big=ImageFont.truetype(fontpath,25)
def pos(x,y):return (450+(x-14.65)*(1100/5.7),550-(y-9.18)*(1100/5.7))
def tag(draw,x,y,s,color='#244b42'):
 p=pos(x,y);bb=draw.textbbox(p,s,font=font);draw.rectangle((bb[0]-4,bb[1]-3,bb[2]+4,bb[3]+3),fill='#fffdf5');draw.text(p,s,font=font,fill=color)
def dim(draw,a,b,s):
 a=pos(*a);b=pos(*b);draw.line((a,b),fill='#9b4d35',width=3)
 for p in [a,b]:draw.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill='#9b4d35')
 mid=((a[0]+b[0])/2,(a[1]+b[1])/2);box=draw.textbbox(mid,s,font=font);draw.rectangle((box[0]-3,box[1]-3,box[2]+3,box[3]+3),fill='#fffdf5');draw.text(mid,s,font=font,fill='#9b4d35')
for mode in ['daily','guest']:
 p=R/('STUDY_ROOM_TOP_'+mode.upper()+'.png');im=Image.open(p).convert('RGB');draw=ImageDraw.Draw(im)
 draw.rectangle((0,0,900,46),fill='#fffdf5');draw.text((18,10),'STUDY V1 | '+mode.upper()+' | HUMAN REVIEW',font=big,fill='#244b42')
 tag(draw,13.82,11.5,'1880 x 1200 Daybed')
 tag(draw,14.24,7.95 if mode=='daily' else 7.60,'2000 x 800 tea desk')
 tag(draw,15.89,8.50,'closed')
 tag(draw,15.89,8.30,'storage')
 dim(draw,(14.40,9.58 if mode=='daily' else 9.23),(14.40,10.50),'920 mm' if mode=='daily' else '1270 mm')
 dim(draw,(13.1001,8.20),(14.21,8.20),'1110 mm FRONT')
 if mode=='daily':
  dim(draw,(15.01,9.75),(15.76,9.75),'750 mm')
  tag(draw,15.03,8.90,'500 chair')
  tag(draw,15.47,8.45,'Rear 300 mm')
  tag(draw,13.22,7.36,'Counter gap 473 mm')
 draw.rectangle((0,1050,900,1100),fill='#fffdf5')
 draw.text((16,1057),'Door 850 mm | source Z-up | top slice below 1.4 m | geometry preview',font=font,fill='#244b42')
 im.save(R/('STUDY_ROOM_TOP_'+mode.upper()+'_DIMENSIONED.png'))
a=Image.open(R/'STUDY_ROOM_TOP_DAILY_DIMENSIONED.png');b=Image.open(R/'STUDY_ROOM_TOP_GUEST_DIMENSIONED.png')
canvas=Image.new('RGB',(1800,1100),'white');canvas.paste(a,(0,0));canvas.paste(b,(900,0));canvas.save(R/'STUDY_ROOM_DAILY_GUEST_COMPARE.png')
delivery=Path('/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/study_room_v1');delivery.mkdir(parents=True,exist_ok=True)
for p in R.iterdir():
 if p.suffix in ['.blend','.png','.json','.md','.glb'] and not p.name.endswith('.blend1'):shutil.copy2(p,delivery/p.name)
print('PACKAGED_STUDY',str(delivery))
