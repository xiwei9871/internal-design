# Latest FCStd Update Audit

Status: `HUMAN_REVIEW`

Source mtime: `1790595060.194331`
Source SHA256: `337b3b0bd533c2e03349f766b5dacb3c84c4409a74c793c41cb6a52a849d590e`
FreeCAD objects: 427
Named objects: 55

## WC front-direction verification

- Owner ensuite WC bbox: `[9693.375, 5770.71875, 10193.375, 6370.71875]`; front +Y = `-70.7 mm`; front -Y = `1120.7 mm`.
- Mother bath WC bbox: `[14483.25, 5721.125, 14983.25, 6371.125]`; front +Y = `-71.1 mm`; front -Y = `1071.1 mm`.
- The previous negative values occur under the +Y front interpretation; the opposite direction yields positive available depth. No WC was rotated or moved.

## Report-only permitted changes

- Mother bed: proposed dx = `-542.9 mm`, dy = `0.0 mm`, rotation = `0°`; not applied.
- 次卧衣柜 vs G-GB-BALC: report-only `move left` dx = `-18.1 mm`, dy = `0.0 mm`; not applied.

## New named objects

- 3kg washing machine: `[9200.5, 10353.46875, 9650.5, 10803.46875]`.
- Printer: `[15277.0, 6664.125, 15677.0, 7064.125]`.
- NAS: `[14792.875, 6664.125, 15192.875, 7064.125]`.

No object was moved, rotated, or rewritten in the source FCStd.
Blender = HOLD; formal CAD = false.
