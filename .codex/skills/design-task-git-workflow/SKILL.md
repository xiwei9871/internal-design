---
name: design-task-git-workflow
description: Use for substantial project changes that must leave a task-scoped Git/GitHub review boundary.
---

# Design Task Git Workflow

Use one task branch per substantial change. Read only named authority files, run the task Gate, then inspect the diff.

## Preflight Write Gate

Before scanning or modeling, confirm repository readability, ordinary workspace write access, Git metadata/branch-creation access, requested output-directory write access, and readable Git status. If any write or branch operation returns Operation not permitted, permission denied, auth_unavailable, or an approval-service 5xx, set TASK STATUS to BLOCKED_WORKSPACE_PERMISSION and stop. Do not spend time scanning, modeling, or rendering after that failure.

Stage explicit task paths only; never use \`git add .\`. Keep renders, retries, proxies, caches, textures, and backups out of the diff. Commit with a task-specific message, push the branch, create or update a PR, report branch/commit/PR, and stop at HUMAN_REVIEW. Never merge automatically.

If frozen-authority hashes change unexpectedly, fail and stop. Do not commit until \`git diff --cached --check\`, staged-file scope, and generated-artifact exclusion pass.

If local commit and push succeed but PR creation fails because GitHub authentication is unavailable, report HUMAN_REVIEW_PR_BLOCKED with branch, commit, pushed remote ref, and exact blocker; the local task is not otherwise invalidated.
