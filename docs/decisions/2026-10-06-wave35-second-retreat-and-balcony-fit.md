# Four-step trial and frame-derived north balcony glazing

TASK STATUS: HUMAN_REVIEW. This is an owner-requested design trial, not an approved construction solution.
BRANCH: codex/c-type-living-furniture.
PR: not created; existing GitHub CLI authentication blocker remains, and no login setup is requested.

The owner requested350mm wave treads, then a second500mm shift toward the lower living floor after the first500mm trial still constrained the upper landing. Keep four112.5mm risers to450mm for this review; revert to three only if the owner rejects this last four-step trial. The shift is source-X negative. The rear upper floor is joined to the moved arrival with a planar landing strip; unrelated upper floors remain geometrically unchanged. Terminate the south stair body atY4.7161 to clear the existing dining/living pier.

The selected east pane ent_a2952e234a065c97bf34fae0fe4021ec previously ended atY13.40 while the corner post started atY13.58, leaving180mm uncovered. The new pane matchesY11.17..13.58 andZ1.10..2.74;12mm review glass sits inside the110mm-deep frame. North panes match their own frame openings. Retain stable IDs. Use transparent pale glass and dark gray aluminum only on these12 balcony parts; all other proxy objects retain the requested wall/floor/furniture zoning. The glazing is a design proposal; frame profile, opening hardware and fabrication details remain unapproved.

GROUND TRUTH: frozen R4 SHA remains d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb. Start from the completed furniture review SHA c371efb418964fcb575ac92d18f18e1a027b6c2e683a78e93647046fc254d72b; generate a separate review2 file.

GENERATED ARTIFACTS: /Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006/OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend; proxy_aluminum_fit_2; FIT2_FINAL_QA.json; WAVE35_SECOND_RETREAT_WORKSPACE.png; BALCONY_FRAME_FIT_2_WORKSPACE.png.

FILES CHANGED: five procedural/package/verification scripts and this decision. No Blender binaries, proxies, screenshots or logs enter Git.

GATES: fresh Blender reopen; step solids manifold;350mm local runs;1000mm total shift; no stair/nearby wall surface crossings below tread heights; clear panes match all four frame boundaries; fresh GLB import987 stable entities with correct pane bounds and transparency; frozen R4 hash unchanged; real browser stair click returns review2 and stableSTEP_2 ID. The user's saved numeric stair camera is restored for comparison.

KNOWN ISSUES: review quality/circulation still requires owner judgment. Former lounge and old stair spatial/transition claims are downgraded to candidate after geometry changes. Assembly evidence alone does not prove circulation or site dimensions.

NEXT ACTION: owner reviews this four-step trial in Workspace. If still unsuitable, replace it with a three-step design in a new review revision. No automatic merge.
