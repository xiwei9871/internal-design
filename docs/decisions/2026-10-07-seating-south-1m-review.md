# Translate packet-selected seating group one metre south

TASK STATUS: HUMAN_REVIEW. BRANCH: codex/c-type-living-furniture. No auto-merge or CLI login setup. PR not created due the existing GitHub CLI authentication limitation.

Owner packet9a00ef2b selects exactly three entities: L sofa ent_d25c02916e634c6b810c2d13e29a9a62 / B11_Rectangle046_CATALOG_00_00; round side table ent_d7c82245358e4d1dbc1dc644c11322e9 / B11_Circle_CATALOG_00_00; coffee table ent_58cf3a9dc50143578ee3d8cfd272c045 / B11_Rectangle049_CATALOG_00_00. Source review6 SHAe428fbedc2aeaf6f35d530c4dd33bbb61057a70eaede4d99683f376883360e05 is read-only.

CHANGE: translate all three by sourceXYZ[0,-1,0] metres (source south=-Y), corresponding proxyXYZ[0,0,1]. Preserve meshes,materials,rotations,scale,relative arrangement and global/native IDs. No other objects move: bookshelf,reading bench,three steps,short rail and north-window fitness outline remain at review6 states.

GATES: exact1m world-bounds displacement verified for all three; all other Blender object states identical; moved envelopes have actual lower floor below; no surface intersections against indexed nearby walls,steps,rail,reading furniture or other two moved objects; fresh Blender reopen; freshGLB1010 entities,all stable IDs and selected bounds correct; real browser sofa hit returns review7.

NORTH SPACE: sofa northern envelopeY12.25 becomesY11.25; coffee northern envelopeY11.49 becomesY10.49. Existing2.4x1.2m candidate outline stays unchanged. This clears more room but does not certify equipment fit; actual machine footprints,operating clearances and door swing remain unverified. Surface-separation checks are not a full circulation-code assessment.

GROUND TRUTH: review6 byte hash unchanged; frozenR4 d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb unchanged.

FILES CHANGED: move/package/verification scripts and this decision. Generated artifacts remain outside Git.

ARTIFACTS: /Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/OPTION_A_R4_SEATING_SOUTH_1M_REVIEW_7.blend;proxy_review7/;SEATING_SOUTH_REVIEW7_QA.json;REVIEW7_FINAL_QA.json;SEATING_SOUTH_1M_REVIEW7_WORKSPACE.png;seating_south_1m_review_7.view-preset.json. Workspace1010 entities loaded at packet camera,unlocked.

NEXT: owner reviews south shift and supplies fitness equipment dimensions for a later placement task. No unrelated furniture or architecture edits.
