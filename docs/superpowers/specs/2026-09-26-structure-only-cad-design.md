# Structure Only CAD Output Design

## Goal

Produce a CAD-first structure drawing for the C-type home that removes furniture
and the second-level leisure/platform overlay while preserving every retained
wall and source entity from the direct 世纪欣园 CAD conversion.

## Source priority

1. `projects/c_type_home/source/世纪欣园FF.dwg` is the owner source binary.
2. `projects/c_type_home/cad/measured_working.dxf` is its recorded direct DXF
   conversion and is the graphical source for this output.
3. `cad/design_v01_existing_sync.dxf`, V02, canonical JSON, and concept data
   are review or design overlays only. They are not copied into the
   structure-only output.
4. `cad/C型_原始户型数字化基准图.dxf` is a reconstructed task01 reference;
   it is used only for a coordinate/name cross-check, not as a source for new
   wall geometry.

## Output contract

Create:

- `projects/c_type_home/cad/structure_only_source_sync.dxf`
- `projects/c_type_home/qc/structure_only_cad_report.json`
- `projects/c_type_home/qc/structure_only_cad.png`
- `projects/c_type_home/qc/structure_only_cad.pdf`
- `projects/c_type_home/qc/structure_only_cad.render.json`
- `projects/c_type_home/qc/lounge_entity_audit.json`
- `projects/c_type_home/qc/lounge_entity_audit.png`

The DXF is a derived CAD deliverable, not a presentation overlay. Its retained
wall, column, door, window, stair, sanitary and source annotation entities are
copied from `measured_working.dxf`. The output may differ in file bytes because
the furniture deletion is serialized, but every retained entity must match the
source geometry and layer exactly within 0.01 mm.

## Deletion scope

The output uses an explicit exclusion registry. The approved lounge/platform
source handles are `30830F`, `308310`, and `308311` on `S-楼梯`; they form the
vertical/quarter-arc/horizontal fan-shaped boundary. The straight two-riser
stair handles `308341`, `308342`, `308343`, and `308345` remain.

Furniture exclusions include source `F-FURN` entities and the `S-S.WALL`
`INSERT 307F68`, whose `bing` block contains nested `F-FURN` geometry. No
unlisted wall, window, door, column, or retained stair entity may be deleted or
synthesized.

The source conversion contains no platform or leisure-room geometry. Any
`休闲厅`, `平台`, `LANDING`, `LOUNGE`, or `RAMP` text/overlay encountered in a
derived input is excluded from the structure-only output. This removes the
second-level扇形休闲厅/platform presentation without changing source walls.

## Verification

The report must record:

- source DWG, source DXF, output DXF and output artifact SHA-256 values;
- source/output entity counts by layer and type;
- deleted handles/layers and deletion reasons;
- retained wall entity signatures and exact coordinate differences;
- extra/missing wall handles, coordinate mismatches, and furniture residues;
- explicit status for the green-box regions, checked against source `S-S.WALL`
  linework;
- explicit lounge entity audit with handle, layer, DXF type, bbox, geometry and
  source layer determination;
- `lounge_geometry_remaining = 0` and exact registry handle matching;
- explicit confirmation that the nine registered windows remain source-backed
  and that standard windows do not erase surrounding wall geometry.

## Rendering

The CAD preview is rendered directly from the derived DXF with the ezdxf
frontend. It must not call the RC4.2 synthetic wall-face overlay. The PNG/PDF
are evidence for inspecting the CAD output; the DXF and match report remain the
authoritative deliverables.
