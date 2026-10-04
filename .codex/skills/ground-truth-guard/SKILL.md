---
name: ground-truth-guard
description: Use whenever a task reads, compares, or changes frozen architectural or design authority.
---

# Ground Truth Guard

Respect this hierarchy: PHYSICAL GROUND TRUTH -> SEMANTIC GROUND TRUTH -> HUMAN DESIGN GUIDE -> DERIVED DESIGN MODEL -> PRESENTATION/RENDER. Generated content never overrides a higher layer; the Human Design Guide is mutable guidance, not physical truth.

Read the exact authority manifest named by the task and record its SHA256 before work. Recheck it after work and before commit. Any unexpected frozen hash, room boundary, opening, level, or registered fixture change is FAIL; stop and report it. Changes require an explicit user-authorized branch and a new manifest. A derived branch may preserve the frozen authority; an explicitly authorized successor (for example R5) must preserve R4, create a new manifest, and record the intentional hash/version transition.
