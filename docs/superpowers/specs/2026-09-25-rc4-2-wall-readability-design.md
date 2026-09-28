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

The semantic classification source for render-only wall faces is
`current_existing/canonical_plan_v1.json`. The versioned DXF remains the
graphical geometry truth. Only canonical records with
`disposition == "EXISTING"` are eligible. Before creating a face, the
renderer must confirm that the canonical rectangle is covered by active wall
geometry in the versioned DXF (`S-S.WALL`, `A-WALL-EXST-CORR`, or the
parapet layer as appropriate). A canonical rectangle without active DXF
coverage is an error; the renderer must not paint it into the output. Objects
typed `railing_parapet` are rendered through the parapet style and are never
merged into the wall style.

## Rendering architecture

`scripts/task03a_render_dxf.py` keeps the existing ezdxf Matplotlib pipeline:

1. Read a versioned DXF and create the selected render profile.
2. Align each eligible canonical wall rectangle with active wall geometry in
   that DXF and fail fast on missing coverage.
3. Build render-only wall fragments from the aligned canonical rectangles.
4. For each wall, subtract the union of overlapping canonical opening/window
   rectangles using axis-aligned rectangle splitting. The result is a list of
   rectangular fragments, not a compound Matplotlib path hole. The renderer
   records the source wall area, cut area, and fragment area so the identity
   `wall area - cut area = fragment area` can be gated. A hostless fenestration
   whose opening is already a gap between active DXF wall segments is recorded
   as an `active_gap` association after checking its glazing geometry and gap
   boundaries; it is never accepted from JSON alone.
5. Draw DXF entities through the ezdxf frontend using the existing layer/type
   filters.
6. Save PNG, PDF, and a provenance sidecar that includes the source DXF hash,
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

The Matplotlib artists use explicit fixed z-orders rather than relying on
insertion order: wall fill `10`, wall outline `20`, parapet `30`, DXF
glazing/door/furniture/text `40` or higher. This keeps glazing lines from
visually overpowering the wall face when the ezdxf backend adds its artists.

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
qc/rc4_2_baseline/rc4_1_v01_presentation.png
qc/rc4_2_baseline/rc4_1_v02_f1_presentation.png
qc/rc4_2_baseline/rc4_1_v01_presentation.pdf
qc/rc4_2_baseline/rc4_1_v02_f1_presentation.pdf
qc/rc4_2_baseline/manifest.json
```

Before any RC4.2 render overwrites the existing presentation filenames, the
four RC4.1 files are copied into `qc/rc4_2_baseline/` and their SHA-256 values
are written to `manifest.json`. The current baseline values are recorded as:

```text
rc4_v01_presentation.png      37a9fb82ad7cd4219fc9cdb204b45edc7e65fcfff723394ecac3cdf3d6ef9dec
rc4_v02_f1_presentation.png   ae226d24e58dea0ae9e1269d75e8759d39df2e1ec54af25386a61a6a7f48ee53
rc4_v01_presentation.pdf      099c289079e74785de743adbcb21d77f640081d2b37dce497e045cf549623c3a
rc4_v02_f1_presentation.pdf   8200025316220af26a0d59d9fec5a0d9ba6b32701c609cb126b587cec97c4509
```

The before/after sheet contains four fixed zones: living north window,
north-balcony/guest-bath/guest-bedroom/study, dining/life-balcony/kitchen,
and the secondary-master/master-bedroom/bathroom area. The readability check
is a full-plan Presentation render with diagnostic wall IDs only; its labels
are not included in the formal V01/V02 Presentation outputs.

## Gate design

The existing gate checker is extended with five gates:

- **RC4-G14 wall-face completeness:** every eligible canonical existing wall
  aligns to active DXF wall geometry, every wall fragment is emitted in the
  render report, and each wall satisfies the area identity after registered
  opening/window subtraction. Human visual judgement is tracked separately as
  `HUMAN VISUAL REVIEW = REQUIRED`; this gate never claims that a drawing
  looks good by itself.
- **RC4-G15 wall-window hierarchy:** all 9 registered fenestration records have
  either a `wall_cut`/`parapet_cut` association or a verified `active_gap`
  association bounded by active DXF geometry, with no uncut solid overlay
  covering the opening.
- **RC4-G16 parapet hierarchy:** all four canonical parapets are reported as
  parapets, use the parapet style, and are absent from the wall-face list.
- **RC4-G17 Presentation layer hygiene:** the render sidecars report no visible
  DEMO, SURVEY_SUPERSEDED, QC, TAG, or survey-hatch layer and no HATCH or
  DIMENSION entity type.
- **RC4-G18 geometry frozen:** the live SHA-256 values must equal the frozen
  RC4.1 values for both CAD children:

  ```text
  design_v01_existing_sync.dxf = 5210557086ce08d2ca40cb5b14be909ba83608e68b22bcfd151ed73904cf6c00
  design_v02_f1_l1.dxf          = 4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d
  ```

  The gate also performs rectangle/hash comparisons for the frozen semantic
  sections (`walls`, `openings`, `windows`, `kitchen_cabinets`, `keep_items`,
  `balconies`, `split_level`, and F1 furniture). Render-only files are
  excluded from this comparison. Any DXF `saveas()` or other CAD mutation
  therefore fails immediately on the SHA check.

The new gates consume the render sidecars/report and the existing CAD manifest;
they do not regenerate or rewrite CAD. A failed gate reports the specific wall,
opening, window, layer, or hash mismatch. The report always includes an
explicit `HUMAN VISUAL REVIEW = REQUIRED` status for the reviewer to complete
after inspecting the full-plan and before/after images.

## Error handling and limits

The renderer fails fast if a required semantic wall/window field is missing,
if a wall rectangle is invalid, or if a requested versioned DXF is absent. A
A window that has no host wall may be accepted only when its opening rectangle
is covered by active glazing and bounded by active wall segments; the gate
records that association explicitly as `active_gap`. No unregistered survey
fill is used as a fallback.

## Verification

After implementation:

1. Run the renderer with the project `.venv/bin/python` so all four formal
   renders and RC4.2 audit outputs are regenerated.
2. Run `scripts/task03a_gate_check.py` and confirm all prior gates plus
   RC4-G14–G18 pass.
3. Compare the frozen baseline manifest, the exact V01/V02 DXF SHA values, and
   entity/rectangle inventories for MEASURED, V01, and V02 before and after
   rendering; the only modified tracked inputs should be the renderer, gate
   checker, design/audit documentation, and generated QC outputs that are
   already part of the RC4 artifact set.
4. Inspect the full-plan V01/V02 renders and the four-zone before/after sheet,
   focusing on the living north window, the open north balcony, the dining and
   kitchen boundary, and the two south bay-window bedrooms.
