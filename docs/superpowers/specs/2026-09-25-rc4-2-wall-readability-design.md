# RC4.2 Presentation Wall Readability Design

## Goal

Improve the human readability of the RC4.1 Presentation renders while keeping
the versioned CAD geometry, canonical geometry, and all frozen design content
unchanged.

## Scope and invariants

This change is limited to the Presentation renderer and its audit outputs.
The source DWG, `cad/measured_working.dxf`, V01, V02, canonical JSON,
fenestration, doors, parapets, cabinets, furniture, and ramp geometry remain
immutable. The renderer may create Matplotlib artists in memory and may write
PNG/PDF/JSON QC outputs; it must never save a modified DXF.

The formal inputs remain:

```text
cad/design_v01_existing_sync.dxf
cad/design_v02_f1_l1.dxf
```

The semantic source for render-only wall faces is
`current_existing/current_existing_v1.json`. Only records with
`disposition == "EXISTING"` are eligible. Objects typed
`railing_parapet` are rendered through the parapet style and are never merged
into the wall style.

## Rendering architecture

`scripts/task03a_render_dxf.py` keeps the existing ezdxf Matplotlib pipeline:

1. Read a versioned DXF and create the selected render profile.
2. Build render-only wall artists from canonical existing wall rectangles.
3. Cut every canonical opening and registered window rectangle that overlaps a
   wall rectangle. The cut is an in-memory path hole, so glazing is read as an
   opening placed in a wall rather than as a solid wall overlay.
4. Draw DXF entities through the ezdxf frontend using the existing layer/type
   filters.
5. Save PNG, PDF, and a provenance sidecar that includes the source DXF hash,
   profile, hidden layers/types, wall face IDs, parapet IDs, and opening cuts.

The display order is:

```text
wall fill
wall outline
parapet
opening/glazing/door linework
cabinet and furniture linework
text and labels
```

Presentation styling uses a dark, heavier exterior wall poche, a lighter
interior wall poche, and a still lighter/thinner parapet style. Glazing and
opening layers are toned down in memory so wall continuity remains the first
visual cue. The existing Presentation filters continue to hide DEMO,
SURVEY_SUPERSEDED, SURVEY_HATCH, QC, TAG, legacy furniture/text layers,
HATCH, and DIMENSION entities.

## Outputs

The renderer regenerates the existing V01/V02 Presentation PNG/PDF pairs and
adds:

```text
qc/rc4_2_wall_display_before_after.png
qc/rc4_2_wall_readability_check.png
qc/rc4_2_wall_readability_check.pdf
qc/rc4_render_report.json
```

The before/after sheet contains four fixed zones: living north window,
north-balcony/guest-bath/guest-bedroom/study, dining/life-balcony/kitchen,
and the secondary-master/master-bedroom/bathroom area. The readability check
is a full-plan Presentation render with diagnostic wall IDs only; its labels
are not included in the formal V01/V02 Presentation outputs.

## Gate design

The existing gate checker is extended with five gates:

- **RC4-G14 wall readability:** every canonical existing wall face is emitted
  in the render report, and the required review zones contain continuous wall
  coverage except for registered openings/windows.
- **RC4-G15 wall-window hierarchy:** all 9 registered fenestration records have
  an opening cut associated with a wall or an explicitly registered parapet
  host, with no uncut solid overlay covering the opening.
- **RC4-G16 parapet hierarchy:** all four canonical parapets are reported as
  parapets, use the parapet style, and are absent from the wall-face list.
- **RC4-G17 Presentation layer hygiene:** the render sidecars report no visible
  DEMO, SURVEY_SUPERSEDED, QC, TAG, or survey-hatch layer and no HATCH or
  DIMENSION entity type.
- **RC4-G18 geometry frozen:** SHA- and rectangle-based comparisons against
  the RC4.1 parent verify that source DXFs and all frozen semantic sections
  (`walls`, `openings`, `windows`, `kitchen_cabinets`, `keep_items`,
  `balconies`, `split_level`, and F1 furniture) are unchanged. Render-only
  files are excluded from this comparison.

The new gates consume the render sidecars/report and the existing CAD manifest;
they do not regenerate or rewrite CAD. A failed gate reports the specific wall,
opening, window, layer, or hash mismatch.

## Error handling and limits

The renderer fails fast if a required semantic wall/window field is missing,
if a wall rectangle is invalid, or if a requested versioned DXF is absent. A
window that has no host wall may still be accepted when its opening rectangle
is covered by a canonical existing wall or parapet; the gate records that
association explicitly. No unregistered survey fill is used as a fallback.

## Verification

After implementation:

1. Run the renderer with the bundled workspace Python so all four formal
   renders and RC4.2 audit outputs are regenerated.
2. Run `scripts/task03a_gate_check.py` and confirm all prior gates plus
   RC4-G14–G18 pass.
3. Compare hashes and entity/rectangle inventories for MEASURED, V01, and V02
   before and after rendering; the only modified tracked inputs should be the
   renderer, gate checker, design/audit documentation, and generated QC
   outputs that are already part of the RC4 artifact set.
4. Inspect the full-plan V01/V02 renders and the four-zone before/after sheet,
   focusing on the living north window, the open north balcony, the dining and
   kitchen boundary, and the two south bay-window bedrooms.
