import datetime, hashlib, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def status_rows(ignored=False):
    args = ['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']
    if ignored:
        args.append('--ignored')
    raw = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, check=True).stdout
    rows = []
    for item in raw.decode('utf-8', 'surrogateescape').split(chr(0)):
        if item:
            status, rel = item[:2], item[3:]
            path = ROOT / rel
            rows.append({'status': status, 'path': rel, 'size_bytes': path.stat().st_size if path.is_file() else 0})
    return rows

def dir_summary(rel):
    path = ROOT / rel
    files = [p for p in path.rglob('*') if p.is_file()] if path.exists() else []
    return {'path': rel, 'file_count': len(files), 'bytes': sum(p.stat().st_size for p in files)}

tracked = subprocess.run(['git', 'ls-files'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
visible = status_rows(False)
all_status = status_rows(True)
untracked = [r for r in visible if r['status'] == '??']
ignored = [r for r in all_status if r['status'] == '!!']
known = ['projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend', 'projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend', 'projects/c_type_home/design/blender_b0/B0_FREEZE_MANIFEST.json', 'projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend', 'projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json', 'projects/c_type_home/design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend', 'projects/c_type_home/design/leisure_compare_v1/LEISURE_COMPARE_OPTION_A.blend', 'projects/c_type_home/design/leisure_compare_v1/LEISURE_COMPARE_OPTION_B.blend']
authoritative = []
for rel in known:
    path = ROOT / rel
    authoritative.append({'path': rel, 'exists': path.is_file(), 'size_bytes': path.stat().st_size if path.is_file() else None, 'sha256': sha256(path) if path.is_file() else None})
summaries = [dir_summary(x) for x in ['projects/c_type_home/renders/r4_option_a/whole_house_ai_v1', 'projects/c_type_home/design/living_finalize_v1/materials', 'projects/c_type_home/renders/r4_option_a/living_layout_exploration_v2', 'projects/c_type_home/design/leisure_compare_v1', 'projects/c_type_home/renders/r4_option_a/living_light_seating_v3', 'projects/c_type_home/renders/r4_option_a/living_with_sideboard_v4']]
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
lfs_version = subprocess.run(['git', 'lfs', 'version'], cwd=ROOT, text=True, capture_output=True).returncode == 0
lfs_attrs = ROOT / '.gitattributes'
lfs_configured = lfs_attrs.is_file() and any('filter=lfs' in line or 'lfs' in line for line in lfs_attrs.read_text(errors='replace').splitlines())
git = {'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip(), 'branch': subprocess.run(['git', 'branch', '--show-current'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip(), 'tracked_files': len(tracked), 'visible_untracked_files': len(untracked), 'visible_untracked_bytes': sum(r['size_bytes'] for r in untracked), 'ignored_files': len(ignored), 'ignored_bytes': sum(r['size_bytes'] for r in ignored), 'git_lfs_available': lfs_version, 'git_lfs_configured': lfs_configured}
obj = {'schema': 'REPO_SOURCE_BOUNDARY_V1', 'generated_at': now, 'git': git, 'authoritative_files': authoritative, 'known_artifact_dirs': summaries, 'classification': {'SOURCE': ['AGENTS.md', '.gitignore', 'projects/c_type_home/design/**/*.py', 'projects/c_type_home/design/**/*.md', 'projects/c_type_home/workflow/**', 'projects/c_type_home/semantics/**'], 'AUTHORITATIVE_BINARY': ['Named R4/B0/kitchen/frozen-base binaries above; do not auto-add'], 'REFERENCE': ['Site photos, CAD/PDF source material, catalog references, and reference manifests'], 'GENERATED_ARTIFACT': ['projects/c_type_home/renders/**', '**/contact_sheet/**', '**/proxies/**', '**/raw/**', '**/reports/initial/**', '**/reports/corrections/**', '**/reports/rejected/**', 'living_finalize_v1/materials/**'], 'CACHE/TEMP': ['.playwright-cli/**', '**/__pycache__/**', '*.pyc', '*.log', '*.resp.json', '*.blend1'], 'UNCERTAIN': ['Remaining untracked source-looking files not named by an authority manifest; manual review before commit']}, 'policy': {'no_deletion': True, 'no_move': True, 'no_blender_run': True, 'no_rendering': True, 'no_auto_commit': True, 'no_push': True}}
(ROOT / 'REPO_SOURCE_BOUNDARY_V1.json').write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10))
rows = ''.join('| '+s['path']+' | '+format(s['file_count'], ',d')+' | '+format(s['bytes'], ',d')+' |'+chr(10) for s in summaries)
(ROOT / 'REPO_BOUNDARY_AUDIT.md').write_text('# Repository Boundary Audit'+chr(10)+chr(10)+'Read-only inventory and ignore-policy governance pass. No design model, render, Blender process, deletion, or relocation was performed.'+chr(10)+chr(10)+'## Before baseline'+chr(10)+chr(10)+'- tracked files: 1,524'+chr(10)+'- visible status entries: 3,336'+chr(10)+'- visible untracked bytes: 2,729,846,367 (~2.73 GB)'+chr(10)+'- branch: '+git['branch']+chr(10)+'- HEAD: '+git['head']+chr(10)+chr(10)+'## Classification'+chr(10)+chr(10)+'- SOURCE: scripts, contracts, manifests, human records, workflows, AGENTS.md, and .gitignore.'+chr(10)+'- AUTHORITATIVE_BINARY: named R4/B0/kitchen/frozen-base models; hashes are recorded, not staged.'+chr(10)+'- REFERENCE: site photos, CAD/PDF source material, catalogs, and reference manifests.'+chr(10)+'- GENERATED_ARTIFACT: render batches, AI candidates, proxies, contact sheets, retries, and texture payloads.'+chr(10)+'- CACHE/TEMP: Playwright captures, Python caches, logs, API responses, and Blender backups.'+chr(10)+'- UNCERTAIN: remaining untracked source-looking files require human review.'+chr(10)+chr(10)+'## Large known directories'+chr(10)+chr(10)+'| Path | Files | Bytes |'+chr(10)+'|---|---:|---:|'+chr(10)+rows+chr(10)+'## Policy'+chr(10)+chr(10)+'.gitignore excludes generated artifact trees and caches by directory/pattern without globally ignoring all PNG/JPG files. Authority manifests, scripts, reports, contracts, and AGENTS.md remain reviewable.'+chr(10)+chr(10)+'See REPO_SOURCE_BOUNDARY_V1.json for complete inventory, hashes, Git state, and policy.'+chr(10))
hash_lines = ''.join('- '+a['path']+' — '+str(a['size_bytes'] if a['exists'] else 'MISSING')+' bytes — '+str(a['sha256'] or 'MISSING')+chr(10) for a in authoritative)
(ROOT / 'REPO_SOURCE_BOUNDARY_V1.md').write_text('# REPO SOURCE BOUNDARY V1'+chr(10)+chr(10)+'Generated: '+now+chr(10)+chr(10)+'## Git baseline after ignore policy'+chr(10)+chr(10)+'- tracked files: '+str(git['tracked_files'])+chr(10)+'- visible untracked files: '+str(git['visible_untracked_files'])+chr(10)+'- visible untracked bytes: '+format(git['visible_untracked_bytes'], ',d')+chr(10)+'- ignored files: '+str(git['ignored_files'])+chr(10)+'- ignored bytes: '+format(git['ignored_bytes'], ',d')+chr(10)+'- Git LFS configured: no (recommendation only; no policy change made)'+chr(10)+chr(10)+'## Authoritative hashes'+chr(10)+chr(10)+hash_lines+chr(10)+'## Review rule'+chr(10)+chr(10)+'Only SOURCE and explicitly named authority files should enter source review. Generated artifacts and caches remain on disk and accessible by original paths, but are ignored by default. See REPO_BOUNDARY_AUDIT.md for classification and known directory sizes.'+chr(10))
print(json.dumps({'before_untracked': 3336, 'before_bytes': 2729846367, 'after_visible_untracked': git['visible_untracked_files'], 'after_visible_untracked_bytes': git['visible_untracked_bytes'], 'ignored_files': git['ignored_files'], 'ignored_bytes': git['ignored_bytes'], 'authoritative_files': len(authoritative)}))
