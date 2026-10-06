# Move only bookshelf assembly, shorten existing handrail

TASK STATUS: HUMAN_REVIEW. BRANCH: codex/c-type-living-furniture. No automatic merge or new CLI authentication setup.

User correction supersedes the prior assumed reading position: move only the bookshelf assembly, leave reading bench,three steps,fitness reserve and all other furniture unchanged. Target packetfe7a7f8b resolves to ent_689bedcf7fb7490d9358a8078ab4a0cc / B11_G-DIN-LIV_HOST_GLASS2, source hit5.28164,4.62650,1.44189. It is the83cm-wide dining/living partition panel, not the opaque guest-bath wall.

Bookcase: ten existing objects (cabinet,three shelves,two posts,four books) rigidly rotate-90deg and translate to align their82cm width with the target panel. Keep a250mm back offset from the glass to clear the grip/handrail; this is freestanding furniture, no anchors are added to glass. Check actual floor at all four cabinet corners and surface intersections against partition,treads,rail,post and bench. Preserve global/native IDs.

Owner then requested shorter rail: shorten its horizontal span from1650mm to900mm; start the sloping part at the first actual tread nosing, end at the third; each horizontal end100mm. Retain900mm top height above nosings and23.20deg slope. Reposition original post,base,returns and three brackets so no detached supports remain. The100mm ends differ from the300mm accessibility reference; this is an owner-requested domestic design trial and is not an accessibility-compliance certification.

SOURCE: review5 SHA c396497077bc564d06d3c8855c731d977ca7dbdfc7cce104456f6bba16e78b20 preserved. FrozenR4 SHA d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb preserved.

GATES: every non-bookcase/non-rail object state identical; moved bookshelf meshes/materials unchanged; four actual-floor checks; no surface intersections against named partition/steps/rail/bench; fresh Blender reopen; fresh GLB1010 entities with all exact stable IDs and bookcase bounds; three riser heights unchanged. Workspace review6 loaded with packet-matched camera.

KNOWN ISSUES: partition door operation and construction anchors are not certified by this visual trial; equipment placement remains pending actual machine dimensions. No other layout edits in this correction.

ARTIFACTS: /Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/OPTION_A_R4_BOOKCASE_SHORT_RAIL_REVIEW_6.blend;proxy_review6/;BOOKCASE_MOVE_REVIEW6_QA.json;REVIEW6_FINAL_QA.json;BOOKCASE_SHORT_RAIL_REVIEW6_WORKSPACE.png.

NEXT ACTION: owner inspects bookshelf location and short rail; no auto-merge. PR not created because existing GitHub CLI authentication is unavailable; do not ask to set up login again.
