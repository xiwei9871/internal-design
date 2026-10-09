"""Room-specific high-quality Image2 studies, reusing confirmed geometry cameras."""
import argparse, concurrent.futures, hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'renders/whole_house_final_study_v1'
OUT = PARENT / 'photo_study_v2'
M = OUT / '00_MANIFEST'
CLI = Path.home() / '.codex/skills/codex-image2/scripts/image2.py'
STYLE = PARENT / 'kitchen_appliance_review_v3/A_gas_hood.png'
ROOMS = json.loads((PARENT/'00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text())['rooms']
CAMS = json.loads((M/'CAMERA_REGISTER.json').read_text())
LEVELS = ['A_faithful', 'B_designer', 'C_creative']
POLICY = ROOT / "render_config/photo_study_v2/GENERATION_POLICY.json"

def select_levels(enabled, requested):
    selected = [level for level in requested if level in enabled]
    if not selected:
        raise ValueError("Requested levels are deferred by owner policy")
    return selected

def input_preflight(images, prompt):
    image_bytes = sum(Path(path).stat().st_size for path in images)
    # Conservative allowance also covers possible base64 encoding and multipart headers.
    estimated = (image_bytes * 4 + 2) // 3 + len(prompt.encode()) + 65536
    if estimated > 24 * 1024 * 1024:
        raise ValueError("Input exceeds conservative 24 MiB budget; preserve originals and inspect references")
    return {"image_count": len(images), "image_bytes": image_bytes,
            "estimated_encoded_bytes": estimated, "limit_bytes": 24 * 1024 * 1024}

def retryable_failure(error, retry_count):
    return retry_count < 1 and any(value in error for value in
        ["HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504", "HTTP 507", "HTTP 524", "timeout after"])
SPECS = {
 'living': {
  'invariants': 'One L-shaped main sofa, one independent window chaise, one coffee table, existing low cabinets. Keep the open fitness reserve EMPTY: no equipment, chair or console there. No separate ottoman or second sofa. Existing coffee-table footprint stays. Chaise is a lounging chaise, not an upright chair. No TV or new ceiling cove.',
  'references': ['sofa_woodframe', 'console', 'sofa_platform', 'sofa_round'],
  'variants': [
   'Retain original L sofa/chaise silhouettes with a clearly crafted light-ash base and tapered supports, oatmeal linen with genuine seams/compression. Retain rectangular thin-frame two-level ash coffee table. Natural ash low cabinets and neutral flax flatweave rug. Natural joinery rather than blanket pale coloring.',
   'Same L sofa and chaise envelopes with a low integrated ash platform, thin exposed wood arms and deeply comfortable linen cushions. Same coffee-table position and SINGLE count, but mature rounded-rectangular light warm-grey stone top on a light ash support, within original footprint. Quiet warmwhite and ash low-cabinet finish, taupe woven rug; materials have deliberate soft/hard contrast.',
   'Same one L sofa, one chaise and single coffee-table footprint. More rounded soft upholstery at corners with visible fine ash side frame, sage/flax fabric contrast; chaise retains reclining length. Single soft-corner natural-edge ash coffee table with slender sculptural supports, no extra table. Low existing cabinet surfaces lightly combine ash and subtle woven-front texture without new panels or enlarging them. Refined neutral rug and sparse ceramics, not rounded architecture.']},
 'dining': {
  'invariants':'One 1600x800 dining table and FOUR tucked-in chairs in source positions. Preserve kitchen/service strip and sliding-glass connection. Do not add bench, chairs, cabinets or major hanging pendant absent from geometry; table capacity and aisle unchanged. Kitchen glimpses retain REAL two-burner gas hob if visible, not electric discs.',
  'references':['chair','chair_cane','console'],
  'variants':['Faithful ash rectangular table, original chair shapes refined into real light wood joinery and comfortable thin seats; clear matte warmgreige tile, nickel cabinet hardware.','Same table footprint/count, soft racetrack corners and refined ash base; four slim curved-back ash chairs with upholstered taupe seats within source chair footprints. Existing storage fronts ash+warmwhite, gentle grey stone counter only where already modeled.','Same single table/four chairs with natural-edge ash table surface and light taper legs; four low-profile woven/cane back ash chairs with muted sage seating. Storage surface finish ash+subtle greige. Distinct real joinery and chair construction, not moving the table.']},
 'service_balcony': {
  'invariants':'This is the south kitchen/service storage strip, NOT the north laundry balcony. No washer/dryer or extra refrigerator here. Preserve full under-window wall, utility tall cabinet, upper AC unit and existing buffet: same doors/drawers/open niche.',
  'references':['console','shelf'],
  'variants':['Natural ash fronts, matte offwhite worktop and clear glazing, recognizable utility AC casing if visible.','Existing upper/tall fronts warmwhite; lower fronts ash, light warmgrey stone worktop/niche back, nickel existing handles.','Existing opaque upper fronts muted sage, ash lower fronts; existing niche warmwhite fine vertical tile finish, same geometry; warmmetal existing hardware.']},
 'entry': {
  'invariants':'Existing entry double door, shoe cabinet, dining glazing, living furniture and stairs stay. Show3wave steps if visible, no ramp, no extra furniture in entry.',
  'references':['console','shelf'],
  'variants':['Crafted ash existing shoe cabinet and door surfaces, flax neutrals, wooddryfloor; retain simple straight ceiling and existing openings.','Existing shoe-cabinet front warmwhite/ash split; adjacent existing low surface subtle quietstone, nickel handles; living glimpses integrated ash/linen.','Existing shoe cabinet softly greige/sage front with ash surround and light woven texture in original panel boundaries; sparse ONE tray on existing cabinet; retain door seams/geometry and clear passage.']},
 'reading_transition': {
  'invariants':'EXACTLY3 existing wave steps, 0 to450mm, same curve, landing and clear guestbath access. Source5015 reading shelf and wallhandrail retained. No added chair, cushions on circulation, new rounded ceiling/cove or staircase tier.',
  'references':['shelf'],
  'variants':['Real ash step edges and original5015 open shelf with limited books; nickel wallrail, clear wave profile, no new lightinggeometry.','Same3step geometry and shelf: ash treadfinish, subtle warmgrey verticalriserfinish; original shelf base warmwhite+ash, simple tasklighting concealed in source shelves only.','Same3steps in matte ash, shelf with muted sage closedbase fronts and naturalwood uprights, a very restrained wovenbackfinish on original cabinet panel; keep rail and landing unchanged, no fourthstep.']},
 'hallway': {
  'invariants':'Same door sequence, casing, corridor width,450mm level and view to living. No new openings, chairs, runners narrowing path or ceiling profiles.',
  'references':['console'],
  'variants':['Real lightash doors, warmwhite plaster, dry woodfloor, quietnickel handles.','Warmwhite original door faces with ash trim, slightly greige walltone and nickel handles, subtle woodgrain floor; keep source joints.','Existing doors mutedgreige/ash split, fine warmmetal original handles, quietnaturalwood floor and softly textured plaster. Distinguish surface finish, no invented architecture.']},
 'mother_bedroom': {
  'invariants':'1500mm bed, two nightstands, existing wardrobe, TV cabinet and vanity with chair stay. The flat green plane across BED is a FABRIC BED RUNNER; drape it softly on the mattress, never a rigid board, bench or stone slab. No thick headboard wall, extra chair or bed size change.',
  'references':['bed_wood','bed_soft','console'],
  'variants':['Real thin ash headboard with modest linen softheadrest, refined original bedframe; warmwhite cotton bedding and flexible sagebedrunner; ash nightstands/wardrobe/vanity.','Samebed envelope with thin exposedash platform and comfortable warmtaupe upholstered headrest, genuine bedding folds; existing nightstandfronts warmwhite+ash, originalTV/vanity surfaces lightwood with subtlegrey finish only where appropriate.','Samebed dimensions and furniturecount; soft rounded corners to linen upholstery with lightash structure, muted sage/cream fabrics, flexible clothrunner. Existing wardrobe remains opaque same doors, greige+ash surface blocks; vanity remains real desk/mirror/chair.']},
 'couple_bedroom': {
  'invariants':'1800mm bed, two nightstands,1200mm THREE-door wardrobe,850mm bathroom entry and2000x400lowconsole stay. NO TV cabinet added. BED greenplane is textile runner draped on mattress, NOT a hard slab or table. Thin headboard only. Retain console asymmetrical supports and actual mirror/opening glimpses.',
  'references':['bed_wood','bed_soft','console'],
  'variants':['Refined original lowash bed and thinsoftheadrest, offwhite real cotton/linen bedding with draped muted sage runner; ash three-door wardrobe and natural-edge console.','Samebed with integratedlightash lowplatform and slim warmgreyupholstered headboard, taupe layered bedding; wardrobe original3faces warmwhite, ash frame; existingconsole light warmgreystone-like top over sourceash supports.','Same1800bed with rounder linen softcorners and fineash edgeframe, sage/ivory fabrics and flexible runner; original3wardrobe doors greige/sage withash surround; naturaledgeash console with quietstone-look drawer finish, no new furniture.']},
 'study': {
  'invariants':'ONE2000x800tea/work desk, ONE master chair in its source position, fixeddaybed underwindow and existing shelves/lowtea-service sink stay. Chair is behind desk and may be hidden: do not invent a front guest chair. No spare stool, second desk, extra bed or sink move. SparseAsian study, notNorthAmerican office.',
  'references':['shelf','chair','chair_cane'],
  'variants':['Naturalash tea/worktable, originalopenash shelves, real linen daybed cushion and quiettea ceramics; existing workchair only if visible.','Sametable/refinedash joinery, warmgrey stone finish on EXISTING tea-service worktop, warmwhite/ash closedstorage, mutedtaupe daybed linen; small refined tasklight only source fixture.','Sametable with subtle naturaledgewithin envelope, ashuprights and mutedgreige/sage closedstorage, wovenpanel texture only source doors; sage linen daybed, ONE sourcechair with refined woven/wood appearance if visible. No added chair to make a pretty image.']},
 'guest_bedroom': {
  'invariants':'ONE1200mm singlebed, continuous eastdesk, ONEchair, THREE-door wardrobe, currentcloudwall lamp and house-shaped display/pegboard stay. No doublebed/bunk/secondbed. Sourcegreen bedplane is fabricrunner, nothardtable. Keep sunroomdoor clear; retained youthful features subtle, notthemepark.',
  'references':['bed_wood','chair','shelf'],
  'variants':['Paleash bed/desk with originalthinheadrest, realivory bedding and sage textile; playfulcloudlight/house shelf readable, originalpegboard.','Samebed/desk envelopes, ashtable and warmwhite existing wardrobe faces, warmtaupe texturedbedhead and softsage deskchair; simpleclear smallchild-friendly design withnoextra fixtures.','Same1200bed with roundedthinsoftheadrest and ash base, muted sage/cream closedstoragepanels, subtle pastel textiles; retain cloud/house/pegboard geometry, nocartooncharacter mural/new canopy.']},
 'master_bath': {
  'invariants':'Fixed sourcevanity/sink/toilet/shower partition/mirror and storage shape unchanged; keep glass transparent and correct tinyroom. No secondbasin/newwindow/bath tub. Mirror is rectangle. Source incomplete shower fixtures are not permission to invent plumbing.',
  'references':[],
  'variants':['Realwhite ceramic basin/toilet, matte warmgreige tile, ash vanityfronts, clear slimmetal glassshowerframe and nickel tap; framed mirrorand openstorage source shapes.','Samefixed layout, lowerash fronts, warmwhite existingstorage, largeformatwarmgrey stone-look tile, thin nickel mirrorframe and subdued existing mirrorlight.','Samefixed layout and rectangularmirror, muted sage vanityfronts withash edge, warmwhite finevertical walltile finish and beige mattefloor, subtlewarmmetal tap/frame; noarchedopening or cabinetshape change.']},
 'secondary_bath': {
  'invariants':'Source850slidingbathdoor,1200vanity,ROUND mirror,sourceupperstorage,toiletorientation andchamferedshower stay. No rectangularmirror or wideningroom, no toiletshift, noopaque woodshower glass.',
  'references':[],
  'variants':['Ashvanity, realwhiteceramicbasin, nickel tap, ROUND mirror, matte warmgreige tile andclear chamferedshower.','Samevanity/roundmirror/storage, warmwhiteupperface/ashlower, greyfine stone-look walltile and warmmattefloor, nickelmirror edge.','Same roundmirror/currentfixtures, muted sage lowerpanel andash storage, warmwhite fineverticaltile backsplash finish, brushedwarmmetal tap, mattebeigefloor; avoid boldhotel marble.']},
 'guest_bath': {
  'invariants':'Keep sink/toilet/rectangularmirror/openstorage, northclearglassshower and entry topology. Pending3kgwasher is NOT an installedlarge appliance: do notgenerate washingmachine absent in image. No addedshowerhead overvanity or secondbasin.',
  'references':[],
  'variants':['Realwhiteceramic, ashvanity, mattewarmgreige tiles, nickelhardware andtransparentglass.','Warmwhiteupperstorageandashvanity, palegrey largeformatstone tile, slimnickel mirrorframe andclear shower.','Muted sage originalvanityfaces, ash upperstorage, fineverticalcreamtile whereoriginalwallplane exists, brushedwarmmetal details andmattefloor.']},
 'north_sunroom': {
  'invariants':'AlreadyENCLOSED with aluminum frame/glass, southweststackedWASHER+DRYER,integrateduppercabinet and2-seatsofa, northlongplantledge, eastTOP-OPENING freezer816 andadjacentcabinet. Freezer is not a tallfridge: NO countertop/lid-cover overit, top lidcanopen. Twofrontloadinglaundrydevices havecircleportholes/controlpanels, notwooddoors. Keepallappliancespositions andslidingdoorsclear.',
  'references':['sofa_woodframe','console'],
  'variants':['Realwhite stackedfrontloadingappliances andchestfreezer, ash cabinetry andsofaframe withlinen, clearglazing/aluminum, beige mattefloor.','Sameequipment/counts withwarmwhiteexistingupper/tallpanels andashlower/ledge, taupesofalinen, lightgrey stoneexistingcounter ONLY adjacentfreezer notoverit.','Samewhiteappliancesandchestfreezer, muted sage/greige uppercabinetfaces,ashplantledge/lowcabinet, naturalwovenlinen sofa details; preservefrontloadingportholes and separatefreezerlid, no newloungeseat.']}
}

COMMON = '''Produce one credible high-end residential interior photograph, in this actual modest Asian natural-wood home. Image1 is the current approved Blender geometry/camera view ONLY. Its placeholder colors, flat shading and coarse upholstered surfaces are NOT style/photo authority. Preserve exact perspective/crop and all walls, openings, mullions, floor levels, steps, fixed-cabinet envelopes and seams, furniture count/position/envelopes and clear passages. Do not enlarge the room, zoom or relocate furniture. Simple flat ceiling, no cove, curve, beam, skylight or extra window. Dark window glass in clay is real glazing, not an opaque panel. No duplicated mirrors, doors or objects behind camera.
Image2 is the owner-liked corrected KITCHEN photo: transfer natural texture/lighting/material separation and workmanship ONLY, never kitchen furniture, hob, hood, cabinetry or camera into this room. Subsequent catalogue images are actual furniture construction references ONLY, adapted to source functional footprints, not copied layout or dimensions. Output no labels/collage/people/brand text.
Photograph quality: neutral soft afternoon daylight from REAL source windows, believable shadow falloff and furniture contact shadows, visible real joinery at supports, crisp but natural wood grain at true scale, cloth seams/soft weight/cushion compression, gentle highlights on stone/metal, whites keep texture, dark elements retain detail. One direction of daylight, restrained warm practical fill, no orange/yellow wash, no uniformly bleached beige, no flat CGI or waxy/blurred microtexture. Normal dry rooms pale matte woodfloor; kitchen/bath/service/sunroom warmgreige matte tile. Rugs only within existing furniture area. Sparse purposeful ceramics/books; do not fill circulation. Lights cannot invent architecture. Camera foreground crops remain, do not shrink furniture to reveal everything.'''

SPECS["kitchen"] = {
    "invariants": "Preserve fixed kitchen cabinets, every seam, sink position, refrigerator, window and door. If visible the hob is a real two-burner GAS hob with raised metal pan supports, burner caps and controls, never electric discs. Existing hood stays under its cabinet with real intake, controls and lights. No new hood chimney, kitchen island, appliance, tap or opening.",
    "references": [],
    "variants": ["Match the accepted kitchen A: natural ash cabinets, quiet cream countertop, real metallic refrigerator and gas cooking equipment. Keep all functional locations and cabinet panel boundaries.", "Deferred wood/warmwhite finish within original seams.", "Deferred sage finish within original seams."]
}

def geometry(room, view):
    path = PARENT/'camera_review_v3'/f'{room}_{view}_preview.png'
    if room=='living' and view in ['VIEW_03','VIEW_05']:
        return PARENT/'living/camera_review_v2'/f'{view}_preview.png'
    return path if path.exists() else PARENT/room/'00_camera_gate'/f'{view}_preview.png'

def make_job(room, view, level):
    spec = SPECS[room]; idx=LEVELS.index(level); d=OUT/room/level; d.mkdir(exist_ok=True,parents=True)
    refpaths=[STYLE]+[OUT/'references'/(name+'.jpg') for name in spec['references'][:3]]
    if view!='VIEW_01': refpaths=[d/'VIEW_01.png', STYLE]
    text=COMMON+'\nROOM INVARIANTS: '+spec['invariants']+'\nSURFACE/FURNITURE DIRECTION: '+spec['variants'][idx]
    if room == "kitchen":
        text=text.replace("Image2 is the owner-liked corrected KITCHEN photo: transfer natural texture/lighting/material separation and workmanship ONLY, never kitchen furniture, hob, hood, cabinetry or camera into this room.", "The accepted kitchen A is this SAME ROOM appearance reference: retain its real gas hob, hood mechanism and materials only where this geometry view actually shows them; never transfer its viewpoint or occluded fixtures.")
    if level == "A_faithful":
        text += "\nFAITHFUL CONTRACT: Preserve the original furniture family, cabinet divisions, support construction and silhouette. Add realistic texture, fabric softness and workmanship without redesigning furniture. Preserve the existing Faithful hero material allocations across views. No new stone table, cane panel, sculptural support or statement color unless already present in this Faithful hero. Existing source geometry controls camera and architectural boundaries."
    if view!='VIEW_01':
        text+='\nREFERENCE ROLES OVERRIDE: image1 is THIS view geometry/camera. Image2 is the SAME ROOM/SAME VARIANT approved photo hero: retain its exact furniture family, table system, material allocations and styling density while looking from image1 camera; do NOT copy image2 crop. Image3 is kitchen photo character only. No cross-view furniture replacement. Hidden furniture stays hidden.'
    if level != "A_faithful":
        # Future targeted edits have their own appearance contract and no kitchen anchor.
        refpaths=[OUT/room/"A_faithful"/(view+".png")]
        if view != "VIEW_01":refpaths.append(d/"VIEW_01.png")
        materials = ("B_designer: apply only the room-specific wood/stone, neutral upholstery and warmwhite finish allocations below; preserve unrelated surfaces. Use controlled neutral residential photography."
                     if level == "B_designer" else
                     "C_creative: apply only the room-specific sage/greige, weave or wood allocations below, where explicitly permitted. Use selective color blocks and directional editorial daylight through the same real openings; retain open divisions and unrelated surfaces.")
        text="Image1 is exact current geometry and camera authority. Image2 is this room/view Faithful photo: preserve its untouched appearance, object count, positions and footprints. Do not copy another room. Flat ceiling, same openings/levels and all clearances. No camera, architecture or layout change. Photographic realism remains required.\nROOM INVARIANTS: "+spec["invariants"]
        text+="\nCHANGE LEDGER: "+materials+"\nROOM TARGET: "+spec["variants"][idx]
        text+="\nVisible differentiation must come from at least two named dominant surface regions, not a global warm tint or extra decoration. No wholesale beige recoloring. No people, lettering or extra furniture. Confirm eligible visible regions with the human before generating; hidden regions stay hidden."
        if view != "VIEW_01":text+="\nImage3 is the approved SAME VARIANT hero; carry its material allocation and construction without copying its viewpoint."
    if room=='living':
        text+='\nVIEW: '+{'VIEW_01':'Look toward northbay, reclinedchaise,eastlowcabinet and sunroomdoor; stairs/dining behindcamera mustnot appear.', 'VIEW_02':'Reverse toward Lsofa,3wavesteps,diningslidingopening; northwindow behindcamera mustnot appear.', 'VIEW_03':'Near northwindow toward3steps/reading shelf/diningdepth. NO invented curvedceiling above stairs.', 'VIEW_04':'Northbay glazing, projectingwindowsill,sunroomdoor andpartialchaise; do not force wholeLsofa into crop.', 'VIEW_05':'Dining/stair approach towardcompleteLsofa/chaise/coffeetable/northbay/eastlowcabinet.'}[view]
    pf=d/(view+'.prompt.txt')
    if not (d/(view+'.png')).exists() and not (d/(view+'.json')).exists():
        pf.write_text(text+'\n')
    return {'room_id':room,'view_id':view,'level':level,'geometry':str(geometry(room,view)),'refs':[str(p) for p in refpaths],'prompt':str(pf),'output':str(d/(view+'.png'))}

def run_job(job):
    output=Path(job['output']);meta=output.with_suffix('.json')
    if output.exists():
        return json.loads(meta.read_text()) if meta.exists() else {"job":job,"status":"CACHE_PRESERVED_PENDING_VISUAL_QA"}
    if meta.exists():return {**json.loads(meta.read_text()),'skipped_prior_attempt':True}
    policy=json.loads(POLICY.read_text())
    if job["level"] not in policy["enabled_levels"]:
        raise ValueError("Generation of this level is deferred by owner")
    preflight=input_preflight([job["geometry"],*job["refs"]],Path(job["prompt"]).read_text())
    cmd=['rtk','proxy','python3',str(CLI),'edit','--image',job['geometry']]
    for ref in job['refs']:cmd+=['--image',ref]
    cmd+=['--prompt-file',job['prompt'],'--model','gpt-image-2','--quality','high','--size','1920x1080','--max-attempts','1','--timeout','240','--out',str(output)]
    started=time.time()
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=270)
    except subprocess.TimeoutExpired:
        result=subprocess.CompletedProcess(cmd,124,stdout="",stderr="Provider launcher timeout after 270 seconds")
    log=result.stdout+'\n'+result.stderr;output.with_suffix('.cli.log').write_text(log)
    record={'job':job,'status':'GENERATED_PENDING_VISUAL_QA' if result.returncode==0 and output.exists() else 'API_FAILED','seconds':time.time()-started,'returncode':result.returncode,'retry_count':0,'model':'gpt-image-2','quality':'high','requested_size':[1920,1080],'geometry_sha256':hashlib.sha256(Path(job['geometry']).read_bytes()).hexdigest()}
    record["input_preflight"]=preflight
    if result.returncode:record['error']=result.stderr.strip()
    if result.returncode and not output.exists() and retryable_failure(record.get("error", ""), 0):
        output.with_suffix(".attempt0.json").write_text(json.dumps(record,ensure_ascii=False,indent=2))
        time.sleep(10)
        try:
            retry=subprocess.run(cmd,capture_output=True,text=True,timeout=270)
        except subprocess.TimeoutExpired:
            retry=subprocess.CompletedProcess(cmd,124,stdout="",stderr="Provider launcher timeout after 270 seconds")
        output.with_suffix(".retry1.cli.log").write_text(retry.stdout+"\n"+retry.stderr)
        record.update({"retry_count":1,"returncode":retry.returncode,"seconds":time.time()-started,
                       "status":"GENERATED_PENDING_VISUAL_QA" if retry.returncode==0 and output.exists() else "API_FAILED",
                       "original_error":record.get("error"),"error":retry.stderr.strip() if retry.returncode else None})
    meta.write_text(json.dumps(record,ensure_ascii=False,indent=2));print('PHOTO_V2',job['room_id'],job['view_id'],job['level'],record['status'],round(record['seconds'],1),flush=True);return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--room',required=True,choices=list(SPECS));parser.add_argument('--phase',choices=['hero','followup','prepare'],default='hero');parser.add_argument('--levels',nargs='+',choices=LEVELS,default=None);args=parser.parse_args()
    enabled=json.loads(POLICY.read_text())["enabled_levels"]
    levels=select_levels(enabled,args.levels or enabled)
    views=['VIEW_01'] if args.phase in ['hero','prepare'] else [f'VIEW_{i:02d}' for i in range(2,6)]
    if args.phase=='followup':
        for level in levels:
            qa=OUT/args.room/("HERO_QA_"+level+".json")
            if not qa.exists():qa=OUT/args.room/'HERO_QA.json'
            assert qa.exists() and json.loads(qa.read_text())['status']=='PASS_FOR_PROPAGATION','Review enabled hero before followup'
    jobs=[make_job(args.room,v,l) for v in views for l in levels]
    if args.phase=='prepare':print('JOBS_PREPARED',len(jobs));return
    # One serial provider call; preserve prior attempts and stop on non-transient errors.
    results=[];failed=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        for start in range(0,len(jobs),1):
            batch=list(pool.map(run_job,jobs[start:start+1]));results+=batch
            failures=[r for r in batch if r['status']=='API_FAILED'];failed+=len(failures)
            if failures:break
    (OUT/args.room/(args.phase+'_'+'_'.join(levels)+'_RUN.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
