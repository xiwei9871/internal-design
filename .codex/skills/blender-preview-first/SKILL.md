---
name: blender-preview-first
description: Use for Blender geometry, spatial studies, and rendering tasks with a human decision gate.
---

# Blender Preview First

Work in stages: Geometry -> Workbench/EEVEE low-resolution Preview -> HUMAN_REVIEW gate -> Material/lookdev -> Cycles final render. Default \`subagents=0\`; delegate only genuinely independent work. Do not run Cycles before explicit human approval or an explicit final-render request.

Render only the minimum decision views requested. Keep source geometry immutable and use a separate branch/file. Allow at most one automatic retry per failed output; then stop or mark the failure. Do not create extra views or polish unrelated rooms for completeness.
