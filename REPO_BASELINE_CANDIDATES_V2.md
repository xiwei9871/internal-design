# Repository Source-Boundary Cleanup V2

TASK STATUS: HUMAN_REVIEW
BASE: origin/improve/design-output-v14
BRANCH: chore/c-type-source-boundary-v2

This metadata-only audit classifies every currently visible untracked candidate by path, extension, size, and existing authority records. It does not delete, move, open, or modify historical assets.

## Metrics

CURRENT_VISIBLE: files = 1265; bytes = 717549159
TRACK_NOW: 275 files / 2486737 bytes
TRACK_LATER_OR_LFS: 7 files / 4769409 bytes
REFERENCE_EXTERNAL: 296 files / 323487857 bytes
IGNORE_GENERATED: 687 files / 386805156 bytes
MANUAL_REVIEW: 0 files / 0 bytes

## Track Now

Exact baseline paths are in REPO_BASELINE_TRACK_NOW.txt (275 files).

Largest 20 TRACK_NOW files:
- 106940 bytes — PATH projects/c_type_home/design/pascal_b1/wall_audit/ARCH_GROUND_TRUTH_FINGERPRINT.json
- 92964 bytes — PATH projects/c_type_home/design/blender_b1_1/B1_1_ASSET_REGISTER.json
- 75962 bytes — PATH projects/c_type_home/design/living_correction_v1/LIVING_MODEL_INVENTORY.json
- 51405 bytes — PATH projects/c_type_home/design/pascal_b1/wall_audit/EXTRACTOR_COVERAGE.json
- 49357 bytes — PATH projects/c_type_home/scripts/b0_zone_coverage_audit.py
- 49005 bytes — PATH projects/c_type_home/design/s2_current_design_v1/furniture_dimension_register_v02.json
- 46298 bytes — PATH projects/c_type_home/design/s2_current_design_v1/furniture_dimension_register_v03.json
- 45394 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_arch_truth_scene.json
- 44035 bytes — PATH projects/c_type_home/design/wall_corners_v5/CORNER_REPAIR_REGISTER.json
- 43847 bytes — PATH projects/c_type_home/design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V02.json
- 42792 bytes — PATH projects/c_type_home/design/secondary_bath_options/r2/BASE_INSPECTION.json
- 42792 bytes — PATH projects/c_type_home/design/secondary_bath_options/r3/BASE_INSPECTION.json
- 39853 bytes — PATH projects/c_type_home/design/blender_b1_1/build_design_model.py
- 39494 bytes — PATH projects/c_type_home/design/s2_current_design_v1/furniture_dimension_register_v01.json
- 34736 bytes — PATH projects/c_type_home/design/s2_current_design_v1/s2_guide_baseline_v1.json
- 34146 bytes — PATH projects/c_type_home/design/s2_current_design_v1/s2_guide_baseline_v2.json
- 32693 bytes — PATH projects/c_type_home/design/s2_current_design_v1/build_s2_current_design_v1.py
- 31262 bytes — PATH projects/c_type_home/scripts/master_v2_to_pascal.py
- 28519 bytes — PATH projects/c_type_home/design/s2_current_design_v1/build_s2_r2_normalization.py
- 28268 bytes — PATH projects/c_type_home/design/b1_blockout/furniture_orientation_register_v01.json

## Track Later / LFS

These are authoritative binaries or geometry payloads. These are recommendations only; no LFS configuration is changed.
- PATH projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend — 1584568 bytes; R4 rendering authority; FROZEN; CURRENT; SHA256 d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb; LFS YES
- PATH projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend — 374932 bytes; B0 existing-as-is authority; FROZEN; CURRENT; SHA256 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb; LFS YES
- PATH projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend — 820968 bytes; frozen kitchen authority; FROZEN; CURRENT; SHA256 28b289a38dbabafbc312e18b3057f232c51c44c07735b1cfcbd39aea39fd0536; LFS YES
- PATH projects/c_type_home/design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend — 1263850 bytes; frozen house-base geometry; FROZEN; CURRENT; SHA256 f2d57433a9984f3a5b214dd4a1afad2e16e0ee913d525ccdc983005baf44c6b5; LFS YES
- PATH projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd — 213027 bytes; current FreeCAD master source; SEMANTIC_GROUND_TRUTH; CURRENT; SHA256 0c30510bc3fe4862d5759c5402146987b6384558a063983b0cab66786de85469; LFS YES
- PATH projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.FCStd — 407000 bytes; current FreeCAD design guide source; HUMAN_DESIGN_GUIDE; CURRENT; SHA256 17340e63f808f7563c64674ad4b43942765044d946b463cb2fb32d373a7817d1; LFS YES
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_1.dxf — 105064 bytes; current DXF source derivative; DERIVED_DESIGN_MODEL; CURRENT; SHA256 9777b153e7379f123d0ab727cdbfb5eafaaba4260da2f57d71ba36d6e1e071b1; LFS MAYBE

## Manual Review

- None

## Proposed Ignore Rules

These patterns are proposed for a later human-reviewed .gitignore pass; this task does not modify .gitignore.
- PATTERN projects/c_type_home/design/**/drafts/** — safe because named draft Blender branches are superseded study outputs; false-positive risk: a future draft may be intentionally retained
- PATTERN projects/c_type_home/design/**/{*RENDER*,*PREVIEW*,*CONTACT*}* — safe because visual QA outputs are reproducible presentation artifacts; false-positive risk: a small human review index could match a broad rule
- PATTERN projects/c_type_home/design/**/reports/** — safe because reports are derived audit outputs; source manifests remain visible; false-positive risk: a small authoritative report may need an explicit negation

## Ground Truth

- R4 SHA256: d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb (expected d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb)
- B0 SHA256: 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb (expected 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb)
- GROUND TRUTH: UNCHANGED
- BLENDER: NOT STARTED
- FREECAD: NOT STARTED
- Baseline candidates are not staged or committed by this audit.

NEXT ACTION: HUMAN_REVIEW of TRACK_NOW / LFS / MANUAL_REVIEW before any baseline commit.
