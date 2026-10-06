# Correct solid-wall bookcase placement; restore chaise; add L-chaise side cabinet

TASK STATUS: HUMAN_REVIEW. BRANCH: codex/c-type-living-furniture. No automatic merge. PR not created due existing GitHub CLI authentication limitation; no login setup requested.

OWNER CORRECTION: previousGLASS2 placement blocked the sliding door. Latest packets distinguish the bookcase(1db9eb77),the obstructed door(3eb72dec),and the correct opaque wall(5025f5f5): ent_292295d05e83519f93bf6c9fed39d766 / VIEW_WALL_W_wall_md_0044,hit sourceXYZ7.39312,4.70010,1.01196.

BOOKCASE: ten existing objects move together onto the actual450mm upper floor beside wall0044. Verify all four footprint corners raycast to the upper slab,not a tread or void. Rear clearance30mm,east wall-end margin60mm. Retain meshes/materials/global IDs. Cabinet no longer sits in front ofGLASS2. Reading bench,steps,short rail,Lsofa/roundtable/coffeetable positions remain unchanged.

OWNER ADDITION: restore the original north-window chaise ent_311cfcbe5e124d8cb67059ade476d139 / B11_Rectangle048_CATALOG_00_00. Its apparent disappearance came from visibility hiding in the fitness trial. Protect authored matrix_basis,parent_inverse,parent and all mesh/material/property state; hidden child cached world matrices may evaluate differently when shown. Independently compare visible world bounds against the accepted living-furniture QA station,then fresh GLB bounds.

SIDE CABINET: separate5015 shallow unit820x320x340 beside the south/lateral side ofLchaise,sourceboundsX4.25..5.07,Y7.58..7.90,Z0..0.34;50mm from sofa. Do not detach the low cabinet from the upper bookshelf assembly. The added object has its own deterministic sidecar ID.

FITNESS: restoration shares the candidate fitness-outline position with the chaise;equipment fit is explicitly unverified. Do not claim this outline is an empty/available gym area after restoring chaise.

GATES: source review7 SHAeec08addcab7a805756a201a1ec61d7ac6508dfcd27cdb61c5d3e1c2f8dbd354 preserved;actual upper-floor footing;no bookcase/nearby wall/tread/rail intersections;side unit on lower floor with no named furniture/step collisions;fresh Blender reopen;freshGLB1012 IDs retained;chaise matches accepted north station;frozenR4 d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb unchanged.

SOURCE FILES: movement/restoration/package/verification scripts and this record only;no generated assets staged.

ARTIFACTS: /Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/OPTION_A_R4_UPPER_BOOKCASE_SIDE_CABINET_CHAISE_REVIEW_9.blend;proxy_review9/;BOOKCASE_UPPER_WALL_REVIEW8_QA.json;SIDE_CABINET_CHAISE_REVIEW9_QA.json;REVIEW9_FINAL_QA.json;UPPER_BOOKCASE_SIDE_CABINET_CHAISE_REVIEW9_WORKSPACE.png. Workspace review9 loaded;return to user balcony planning camera,unlocked.

NEXT ACTION: owner reviews living correction. Balcony cabinetry is separately being discussed,not implemented by these scripts.
