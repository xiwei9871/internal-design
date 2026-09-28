# D1.2 Existing Professional Layout Prior Feasibility

## LEGO-Net

- Repository commit: `198ac4978ef73f64aabb3d9074e2ca364d1b389d`
- Code and README are reachable.
- Official living-room inference requires the released Google Drive weight and preprocessed `3DFRONT_65347` data.
- The repository includes no weight file and no 3D-FRONT scene data.
- Current workspace Python has no `torch`, `torchvision`, `trimesh`, `h5py`, or `simple_3dviz`.
- Status: `FEASIBILITY_ONLY`; official example and C-type adaptation were not run.

## ATISS

- Repository commit: `0909ce0000e52bf1bf300a6a558109f7f8383fd9`
- README and selected config/preprocess files are recorded in `sources/ATISS/`.
- Official generation requires 3D-FRONT, 3D-FUTURE, preprocessed scene data, and a model weight file.
- Those files are not present; no access control was bypassed and no download was attempted.
- Status: `FEASIBILITY_ONLY`.

## 3D-FRONT

- Dataset page is publicly discoverable but acquisition is a separate download/terms step.
- No dataset files were present locally.
- Retrieval count: `0`.
- No README image was treated as a professional layout sample.

## Decision

D1.2 stops before model adaptation. There are no LP-A/LP-B/LP-C DXF candidates because official-example and data-access gates did not pass. This is recorded as unavailable evidence rather than a synthetic result.
