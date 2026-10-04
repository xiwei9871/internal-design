---
name: design-task-git-workflow
description: Use for substantial project changes that must leave a task-scoped Git/GitHub review boundary.
---

# Design Task Git Workflow

Use one task branch per substantial change. Read only named authority files, run the task Gate, then inspect the diff.

Stage explicit task paths only; never use \`git add .\`. Keep renders, retries, proxies, caches, textures, and backups out of the diff. Commit with a task-specific message, push the branch, create or update a PR, report branch/commit/PR, and stop at HUMAN_REVIEW. Never merge automatically.

If frozen-authority hashes change unexpectedly, fail and stop. Do not commit until \`git diff --cached --check\`, staged-file scope, and generated-artifact exclusion pass.
