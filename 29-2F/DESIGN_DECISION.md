# 29-2F TV Wall Material Study

## User Decision - 2026-10-13

- Selected: warm-white, matte, plain wall panels for the living-room TV wall.
- Rejected for this study: repainting the TV wall with latex paint or exploring a darker gray alternative.
- Moisture history: the user reports prior water ingress, efflorescence, peeling, or mold at this wall. The cause and repair status are uncertain.
- Selection approves the visual direction. It does not approve covering an actively damp substrate or establish construction readiness.
- Actual panel composition, supplier, product, color code, fire performance, fastening system, substrate condition, and joint layout are not established.

## Evidence And Scope

- Eleven supplied photos show the construction condition; two supplied images show the original design concept.
- The supplied PDF contains three floor-layout sheets. Its first sheet contains the living/dining room discussed here, although the project folder is named 29-2F. Folder naming does not establish a floor-level identity.
- No confirmed 3D model, measured TV-wall elevation, product asset, or frozen geometry exists for this new project.
- The existing C-Type home's frozen authorities are unrelated and out of scope.
- Preserve supplied files. Do not derive construction dimensions or installed furniture identities from an AI image.
- Existing wood recess, dark lower plinth/fireplace concept, television, and furniture in the original rendering are reference context, not newly selected products or construction commitments.

## Execution Plan

1. Use the installed Image2 launcher to create one surface-only study from the site photo and one surface-only study from the original room rendering.
2. Edit only the visible TV-wall finish; retain camera, openings, wall silhouette, ceiling, adjacent finishes, and all existing objects.
3. For the site image, preserve the construction state, exposed wiring, people, boxes, and floor protection. Do not invent the finished television installation.
4. For the original-render study, change the white TV surround to warm-white matte panels while preserving the wood recess and dark lower unit.
5. Request one image per input, serially, with one transport attempt. Allow at most one logical retry for a transient provider failure across the task.
6. Check each image against its input for unrelated changes; verify source hashes. Report image failures and residual drift honestly.
7. Keep all references, generated images, preservation manifests, and provider metadata local. Commit only this decision record, local exclusions, and exact prompts.
8. Stop at HUMAN_REVIEW after presenting the candidates. Do not auto-merge or approve construction.

## Visual Contract

- Warm white with a restrained neutral warmth, no conspicuous yellow, pink, or blue tint.
- Matte, plain finish with no wood grain, stone veins, fluting, or decorative metallic strips.
- Any depicted panel joint is indicative only; actual panel sizes and setting-out remain unresolved.
- Preserve the source lighting and exposure so the material change can be compared.
- These are raster color/finish studies, not CAD-locked or dimension-validated architectural renders.

## Construction Follow-Up

Before concealing the wall, establish and repair the moisture source, inspect the wood substrate for moisture damage or mold, and confirm suitable installation conditions with the selected panel system. Use physical samples in the room to select the final color and sheen.

## Review Status

- Generation: two successful serial Image2 edit requests; one transport attempt per request, no retries.
- Model/quality: gpt-image-2 / high.
- Site study: options/warm_white_v1/site_warm_white_v1.png; requested 1600x1200, actual native 1448x1086.
- Original-design study: options/warm_white_v1/room_warm_white_v1.png; requested 1920x1208, actual native 1581x995.
- Contact-sheet comparisons: options/warm_white_v1/site_review.jpg and room_review.jpg.
- Visual review: the site study replaces the OSB face with matte warm-white panels while retaining the passage, adjacent gray panels, lower opening, wiring, people, and boxes. The room study retains the TV-surround silhouette, wood recess, lower fireplace/plinth, openings, ceiling, and furniture arrangement. No obvious major topology/layout change was found in visual inspection.
- Limitation: generative editing redraws small texture, reflection, and wiring details. Visual inspection is not proof of exact geometric or pixel preservation. No dimensions, joint positions, or final product colors are validated by these images.
- Source preservation: the two named input images and supplied PDF passed SHA256 verification after generation; the preservation manifest is local at options/warm_white_v1/input_preservation.json.
- Source review: only this decision record, the two prompts, and the project-local .gitignore are in scope. Reference binaries, all previews, generated studies, provider metadata, and contact sheets are excluded from Git review.
- User acceptance of generated images: pending.
- Construction readiness: unresolved moisture cause and unselected panel system.
