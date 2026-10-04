---
name: ground-truth-guard
description: Use whenever a task reads, compares, or changes frozen architectural or design authority.
---

# Ground Truth Guard

Respect this hierarchy: physical Ground Truth -> semantic/design contracts -> active design model -> generated previews/renders. Generated content never overrides a higher layer.

Read the exact authority manifest named by the task and record its SHA256 before work. Recheck it after work and before commit. Any unexpected frozen hash, room boundary, opening, level, or registered fixture change is FAIL; stop and report it. Changes require an explicit user-authorized branch and a new manifest.
