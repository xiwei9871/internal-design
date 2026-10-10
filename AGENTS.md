# Project Instructions

@/Users/xiwei/.codex/RTK.md

## Permanent Boundaries

- Generated renders, overlays, contact sheets, proxies, retries, caches, and large binary assets stay on disk and are returned as paths only. They are not ordinary source review.
- Do not delete or move existing assets unless the user explicitly requests it.
- Do not modify frozen Ground Truth without explicit authorization. Current R4 rendering authority is projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend; SHA256 d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb.
- B0, frozen kitchen, frozen base, FreeCAD source, and approved room boundaries remain authoritative according to their manifests. Recheck hashes when in scope.
- Every door has a casing/frame and connected wall above and on both sides. Registered openings, windows, levels, stairs, and plumbing topology are not inferred from generated images.
- Kitchen changes require CODEX_HANDOFF_B1.md and the kitchen freeze manifest. Unresolved fabrication dimensions remain site verification items.

## Workflow Skills

- .codex/skills/archviz-interior-workflow/SKILL.md for interior effect-image planning, generation, resumption and review. Read the latest owner decision and relevant C-Type lessons first; Faithful-first is the current workflow, Designer/Creative require targeted visual validation.
- .codex/skills/design-task-git-workflow/SKILL.md for substantial task branches, Gates, explicit staging, commits, pushes, PRs, and HUMAN_REVIEW.
- .codex/skills/ground-truth-guard/SKILL.md whenever frozen geometry, contracts, manifests, or authority hashes are read or changed.
- .codex/skills/blender-preview-first/SKILL.md for Blender studies and rendering; default Workbench/EEVEE preview, subagents=0, and no Cycles before approval.
- .codex/skills/repo-artifact-boundary/SKILL.md for Git status, source classification, generated-artifact review, and context-size audits.

## Default Performance Rules

- Before implementation or refinement, search existing project/local work,
  official product assets, compatible model/material libraries and established
  methods. Adapt a suitable solution first; custom-build only unresolved gaps.
  For ArchViz, verify furniture shape, format, UV, material scale, renderer
  compatibility and license before claiming an external asset is usable.
  A library preview is not a successful local Cycles validation.

- Use exact task-named files; do not recursively scan renders/** or rediscover frozen Ground Truth.
- Default subagents=0; delegate only genuinely independent work.
- Preview first, render only requested decision views, and allow at most one automatic retry.
- Do not use git add .; stage explicit task-relevant paths only.
- Never auto-merge. Stop at the requested Gate or HUMAN_REVIEW.

## Portability

The RTK include uses this machine's configured path. Keep it for local Codex execution; do not treat it as a portable GitHub-runner dependency.

## Git / GitHub Review Workflow

Every substantial design task uses a task-scoped branch. Sync the approved base, read only named authority files, execute the task Gate, inspect status and diff, stage explicit task-relevant paths, commit, push, report branch/commit/PR, and stop at HUMAN_REVIEW.

Generated artifacts never enter the diff. Frozen-authority hash changes are FAIL. Do not use git add ., do not merge automatically, and do not commit unrelated source candidates. Standard completion reports include TASK STATUS, BRANCH, COMMIT, PR, FILES CHANGED, GROUND TRUTH, GENERATED ARTIFACTS, GATES, KNOWN ISSUES, and NEXT ACTION.
