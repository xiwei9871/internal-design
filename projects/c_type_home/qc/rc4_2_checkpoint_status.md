# RC4.2 checkpoint status

Final local verification completed from `f716527`. RC4.2 remains a
renderer-only Presentation change; human visual review is still required.

1. **Baseline freeze — PASS.** The four copied RC4.1 PNG/PDF artifacts match
   the recorded SHA-256 values in `rc4_2_baseline/manifest.json`. The manifest
   records the original CAD view boxes and pixel mapping.
2. **Geometry/input freeze — PASS.** V01 is
   `5210557086ce08d2ca40cb5b14be909ba83608e68b22bcfd151ed73904cf6c00` and V02
   is `4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d`.
   All 13 files in `rc4_2_geometry_diff.json` are byte-identical to
   `d6d8f2a`; walls, doors/openings, windows, parapets, cabinets and F1 are
   recorded as unchanged.
3. **Wall fragment builder — PASS.** Focused area cases, the unit-grid oracle,
   and canonical immutability regression pass. Both V01 and V02 report 39
   aligned existing walls (35 solid + 4 parapets), zero fragment area error,
   and nine verified DXF-backed fenestrations with zero overlay area.
4. **Parapet separation — PASS.** The four canonical parapets are routed to
   `parapet_faces` only and use the lighter/thinner parapet style.
5. **Presentation hierarchy and hygiene — PASS.** Wall fill, outline,
   parapet, openings, glazing/doors, furniture and text have fixed z-order;
   the required hidden Presentation layers/types are absent from the drawn
   entity audit.
6. **CAD_REVIEW isolation — PASS.** `draw_wall_faces()` is gated to the
   `PRESENTATION` profile. The regression test confirms a CAD_REVIEW render
   has no RC4.2 wall-face or parapet overlay, preserving the RC4.1 audit
   rendering behavior.
7. **RC4-G14 through RC4-G18 — PASS.** The complete legacy + RC4.2 run is
   `60/60 ALL PASS`; each new gate is recorded individually in
   `qc/task03a_gates.json`.
8. **Provenance — PASS.** Formal V01/V02 Presentation sidecars point to the
   unchanged V01/V02 DXF hashes. The before/after sheet records the frozen
   RC4.1 baseline PNG hashes as its top-row sources.

**HUMAN VISUAL REVIEW = REQUIRED.** Review the four before/after zones and
the full-plan Presentation outputs before any merge or next-level work.
