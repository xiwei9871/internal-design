# Repository Source-Boundary Cleanup V2.1

TASK STATUS: HUMAN_REVIEW
BASE: origin/improve/design-output-v14
BRANCH: chore/c-type-source-boundary-v2

This correction pass classifies by semantic role, current version, and authority records. Directory names and extensions are not sufficient evidence by themselves.

## Metrics

CURRENT_VISIBLE: files = 1265; bytes = 717549159
TRACK_NOW: 346 files / 5235278 bytes
TRACK_LATER_OR_LFS: 7 files / 4769409 bytes
REFERENCE_EXTERNAL: 228 files / 301100321 bytes
IGNORE_GENERATED: 672 files / 405831858 bytes
MANUAL_REVIEW: 12 files / 612293 bytes

## V2 to V2.1

V2: TRACK_NOW 275; TRACK_LATER_OR_LFS 7; REFERENCE_EXTERNAL 296; IGNORE_GENERATED 687; MANUAL_REVIEW 0.
V2.1: TRACK_NOW 346; TRACK_LATER_OR_LFS 7; REFERENCE_EXTERNAL 228; IGNORE_GENERATED 672; MANUAL_REVIEW 12.

## Track Now

Exact baseline paths are in REPO_BASELINE_TRACK_NOW.txt (346 files).

Largest 20 TRACK_NOW files:
- 116213 bytes — PATH projects/c_type_home/design/blender_b0/PASCAL_LAYOUT_FROZEN_v3.json
- 116213 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_master_direct_furnished_v3.json
- 112667 bytes — PATH projects/c_type_home/design/wall_junctions_v4/SOURCE_EXTERIOR_SAMPLES.json
- 108853 bytes — PATH projects/c_type_home/design/blender_b0/B0_LEVEL_FIELD.json
- 106940 bytes — PATH projects/c_type_home/design/pascal_b1/wall_audit/ARCH_GROUND_TRUTH_FINGERPRINT.json
- 103685 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_blocks_scene.json
- 103533 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_full_scene.json
- 103470 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_master_direct_furnished_v2.json
- 101518 bytes — PATH projects/c_type_home/design/s2_current_design_v1/latest_fcstd_structure_v2.json
- 101215 bytes — PATH projects/c_type_home/design/pascal_b1/export_pascal_b1_blocks_v1.json
- 100818 bytes — PATH projects/c_type_home/design/pascal_b1/export_pascal_b1_full_v2.json
- 99890 bytes — PATH projects/c_type_home/design/pascal_b1/pascal_master_direct_furnished_v1.json
- 99700 bytes — PATH projects/c_type_home/design/site_photos/B1_1_SITE_ASSET_REGISTER.json
- 95844 bytes — PATH projects/c_type_home/design/pascal_b1/export_pascal_b1_full_v1.json
- 92964 bytes — PATH projects/c_type_home/design/blender_b1_1/B1_1_ASSET_REGISTER.json
- 91663 bytes — PATH projects/c_type_home/design/s2_current_design_v1/latest_fcstd_structure_v3.json
- 84308 bytes — PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_REJECTED.design_model.json
- 84308 bytes — PATH projects/c_type_home/design/s2_current_design_v1/design_model_v01.json
- 80177 bytes — PATH projects/c_type_home/design/bedroom_door_r4/THRESHOLD_ACTUAL_GEOMETRY_DEBUG.json
- 75962 bytes — PATH projects/c_type_home/design/living_correction_v1/LIVING_MODEL_INVENTORY.json

## Track Later / LFS

Advisory only. LFS_REQUIRED_FOR_POLICY is not established; current small authority binaries are LFS_OPTIONAL and the current DXF is NORMAL_GIT_ACCEPTABLE.
- PATH projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend — 1584568 bytes; R4 rendering authority; FROZEN; CURRENT; SHA256 d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb; LFS_OPTIONAL
- PATH projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend — 374932 bytes; B0 existing-as-is authority; FROZEN; CURRENT; SHA256 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb; LFS_OPTIONAL
- PATH projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend — 820968 bytes; frozen kitchen authority; FROZEN; CURRENT; SHA256 28b289a38dbabafbc312e18b3057f232c51c44c07735b1cfcbd39aea39fd0536; LFS_OPTIONAL
- PATH projects/c_type_home/design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend — 1263850 bytes; frozen house-base geometry; FROZEN; CURRENT; SHA256 f2d57433a9984f3a5b214dd4a1afad2e16e0ee913d525ccdc983005baf44c6b5; LFS_OPTIONAL
- PATH projects/c_type_home/cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd — 213027 bytes; current architectural CAD geometry source; PHYSICAL_GROUND_TRUTH; CURRENT; SHA256 0c30510bc3fe4862d5759c5402146987b6384558a063983b0cab66786de85469; LFS_OPTIONAL
- PATH projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.FCStd — 407000 bytes; current FreeCAD design guide source; HUMAN_DESIGN_GUIDE; CURRENT; SHA256 17340e63f808f7563c64674ad4b43942765044d946b463cb2fb32d373a7817d1; LFS_OPTIONAL
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_1.dxf — 105064 bytes; current DXF source derivative; DERIVED_DESIGN_MODEL; CURRENT; SHA256 9777b153e7379f123d0ab727cdbfb5eafaaba4260da2f57d71ba36d6e1e071b1; NORMAL_GIT_ACCEPTABLE

## Manual Review

- PATH projects/c_type_home/design/pascal_poc/.agents/skills/furniture-fit/.clawhubignore — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: IGNORE_GENERATED; question: Should this local tool metadata be retained in the source baseline?
- PATH projects/c_type_home/design/pascal_poc/.agents/skills/pascal-3d/.clawhubignore — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: IGNORE_GENERATED; question: Should this local tool metadata be retained in the source baseline?
- PATH projects/c_type_home/design/s2_current_design_v1/LATEST_FCSTD_UPDATE_AUDIT.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/R2_2_HUMAN_REVIEW_PACK.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/R2_2_LOCAL_DETAIL_REVIEW.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_1.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_R2_2_AUDIT.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_REJECTED.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V1.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?
- PATH projects/c_type_home/design/s2_current_design_v1/S2_GUIDE_BASELINE_V2.pdf — candidates: REFERENCE_EXTERNAL, IGNORE_GENERATED; why: The file is a review/document payload whose source role cannot be established from shallow metadata alone.; default: REFERENCE_EXTERNAL; question: Is this document an external reference to retain, or a derived review artifact to ignore?

## Proposed Ignore Rules

No blanket /reports/ rule is proposed. These narrower patterns are proposed for later human review; .gitignore was not modified.
- PATTERN projects/c_type_home/design/**/drafts/** — safe because named draft branches are superseded studies; false-positive risk: a future draft may be intentionally retained
- PATTERN projects/c_type_home/design/**/proxies/** — safe because proxy images are derived review outputs; false-positive risk: a future source proxy contract would need an explicit exception

## Required Validation

- material asset-manifest.json => TRACK_NOW
- material texture payload => IGNORE_GENERATED
- site_photos/*.jpg/png => REFERENCE_EXTERNAL
- site_photos source .py evaluated by filename/role, not directory
- reports/BRANCH_CONTRACT.json => TRACK_NOW
- historical versions are not tracked solely by extension
- FreeCAD master => PHYSICAL_GROUND_TRUTH
- R4 SHA256: d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb (expected d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb)
- B0 SHA256: 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb (expected 717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb)
- category counts and bytes reconcile exactly

GROUND TRUTH: UNCHANGED
BLENDER: NOT STARTED
FREECAD: NOT STARTED

NEXT ACTION: HUMAN_REVIEW before any baseline candidate commit.
