# Repository Boundary Audit

Read-only inventory and ignore-policy governance pass. No design model, render, Blender process, deletion, or relocation was performed.

## Before baseline

- tracked files: 1,524
- visible status entries: 3,336
- visible untracked bytes: 2,729,846,367 (~2.73 GB)
- branch: feat/c-type-task03a-measured-concept
- HEAD: f3ea1b0320518f0b082227acbf410a686e284893

## After applying the local ignore policy

- visible git status short untracked entries: 1,472 total, consisting of 1,471 untracked files plus the modified .gitignore
- visible untracked bytes: 772,722,364 bytes (~736.9 MiB)
- ignored files: 13,546
- ignored bytes: 3,119,322,469 bytes (~2.91 GiB)
- source-like files remain visible for human review; generated image trees, material payloads, retries, caches and backups are ignored

The visible count is not intended to reach zero: the repository has no existing source baseline for most historical project assets. Remaining visible entries require manual source-vs-authority decisions before a baseline commit.

## Classification

- SOURCE: scripts, contracts, manifests, human records, workflows, AGENTS.md, and .gitignore.
- AUTHORITATIVE_BINARY: named R4/B0/kitchen/frozen-base models; hashes are recorded, not staged.
- REFERENCE: site photos, CAD/PDF source material, catalogs, and reference manifests.
- GENERATED_ARTIFACT: render batches, AI candidates, proxies, contact sheets, retries, and texture payloads.
- CACHE/TEMP: Playwright captures, Python caches, logs, API responses, and Blender backups.
- UNCERTAIN: remaining untracked source-looking files require human review.

## Large known directories

| Path | Files | Bytes |
|---|---:|---:|
| projects/c_type_home/renders/r4_option_a/whole_house_ai_v1 | 1,483 | 1,071,927,227 |
| projects/c_type_home/design/living_finalize_v1/materials | 21 | 427,287,069 |
| projects/c_type_home/renders/r4_option_a/living_layout_exploration_v2 | 158 | 121,445,954 |
| projects/c_type_home/design/leisure_compare_v1 | 64 | 46,696,008 |
| projects/c_type_home/renders/r4_option_a/living_light_seating_v3 | 41 | 20,850,862 |
| projects/c_type_home/renders/r4_option_a/living_with_sideboard_v4 | 37 | 20,132,628 |

## Policy

.gitignore excludes generated artifact trees and caches by directory/pattern without globally ignoring all PNG/JPG files. Authority manifests, scripts, reports, contracts, and AGENTS.md remain reviewable.

See REPO_SOURCE_BOUNDARY_V1.json for complete inventory, hashes, Git state, and policy.
