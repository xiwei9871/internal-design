# C-Type Bedrooms Wood Review implementation plan

Goal: produce an editable full-house successor and load it into Spatial Canvas for HUMAN_REVIEW.
Architecture: inherit accepted study-r5 full .blend and registry. Modify only named bedroom furniture; new assemblies receive deterministic entity IDs. Reuse the full-house Blender exporter, inherit semantic candidate states, remove relationships referencing retired entities.
Runtime: Blender 5.2.1 Python, Workbench decision previews, GLB adapter. No texture payloads or Cycles. New furniture budget <=50000 evaluated triangles.

- [x] Audit local named furniture, guest bed / desk and exact doors, plus bounding wall index. Frozen R4/B0 and study source hashes must match recorded values.
- [x] Save successor BEDROOMS_WOOD_V1.blend; retain hidden retired objects for reversibility. Mother 1500 bed + TV cabinet + thin headboard + bedside storage + light vanity; couple 1800 bed + thin headboard, remove TV cabinet, add shallow shelf; guest keep 1200 bed, refine desk / display / modest cloud motifs.
- [x] Check wardrobe-front to bed-frame >=500mm; actual wall / frame / door intersections; guest balcony route; unchanged source object fingerprints outside named furniture edits. Inspect Workbench top and local perspective views.
- [x] Export full-house GLB/manifest, retain native wall boundaries and stable entity IDs, import anew and assert IDs/counts/removed objects. Make room camera bookmarks and relink inherited semantic resources without promoting candidate evidence.
- [x] Load manifest/GLB, spaces and relationships in Codex IAB5176, restore a review camera; verify current revision/entities and take screenshot.
- [ ] Explicitly stage scripts and source JSON/docs only, commit, push task branch, open PR if authenticated, never merge. Generated .blend/GLB/images remain local.

Approved design: current user instruction authorizes model changes. Scope excludes architectural changes, stairs, balcony, study, frozen kitchen, final rendering or procurement. Dimensions are review envelopes, not fabrication details.
References: MUJIE storage08; Taiwan Order blog421 house-shaped display/ordinary-bed composition; Home33 sky-city ordinary bed, cloud lamp and pegboard. Learn composition, do not copy full case floorplan, upper bunk or copyrighted IP.

Ownerreview2: continuousguestdesk andthree-doorwardrobe; neverwiden1200bed. Latestmodel BEDROOMS_WOOD_V2.blend, newrevisionbedrooms-wood-v1-review-2.
