# Living finalization PBR materials

The independent library is `scripts/materials_library.py`. All 15 map files from five Poly Haven assets were downloaded with upstream verification and their SHA-256 values were rechecked locally. These are CC0 scans, **Powered by Poly Haven**; no catalog photographs, Image2 outputs or private credentials are used.

```python
import materials_library as ml
mats = ml.make_materials()
obj.data.materials.clear()
obj.data.materials.append(mats['WOOD'])
ml.assign_uv(obj, grain_axis='X')  # local joinery axis; actual metre scale
ml.pack_material_images()        # pack before saving the separate working blend
```

`make_materials()` returns WOOD, FLOOR, FABRIC, FABRIC_DARK, STONE, WALL, CEILING, GLASS, METAL, CERAMIC, RUG and LEAF. All textured materials require `LF_PhysicalUV`. That UV layer stores projected **metres**, not normalized 0–1 coordinates. The shader applies each recorded physical tile size. Texture U follows `grain_axis`, V follows cross-grain. Both oak scans were numerically measured and their grain is horizontal in U. Per-object stable UV offsets vary the sampled grain. Parent/object scale and scene length units are respected. Shared mesh data is copied before UV changes, so instances do not alter one another. The positions and shape are unchanged.

For proper rounded cloth unwraps, preserve their existing unwrap and copy/scale it into LF_PhysicalUV to represent metres. Use box projection on solid timber/floor/stone/wall pieces; avoid using it as a substitute for a good cloth unwrap. Fabric tile160mm maps dominant frequency candidates to approximately0.43–0.65mm thread pitch. This is authored physical appearance calibration, not a manufacturer measurement.

WOOD uses washed grey oak veneer adapted into a pale ash-colored wood-wax palette. It is an oak scan analogue rather than a botanical ash scan. FLOOR uses actual scanned oak boards. STONE uses a subdued pale warm marble scan and restrained honed response; it is not a certified limestone asset. Woven scan structure, real board grain and scanned plaster remain visible; broad palettes are adapted through low-contrast linear-color ramps. Normal strengths are restrained so fabric does not resemble coarse hessian and plaster does not resemble damaged concrete.

Diffuse images are sRGB. Roughness and +Y OpenGL normal maps are Non-Color. Normal maps connect through a tangent Normal Map node that names LF_PhysicalUV. AO is deliberately omitted. There is no true displacement or generic Noise-only wood/fabric shader. METAL, CERAMIC and LEAF use physically distinct Principled responses; their small secondary forms need no scanned bitmap.

GLASS uses neutral IOR1.46 transmission, roughness0.025 and Blender5.2 Thin Wall, with Transparent BSDF only for shadow rays. This efficient architectural transport approximation allows daylight into the room while preserving clear-camera transmission and reflections. It introduces no opaque blue glazing or volume absorption. Full-scene glass exposure and sun transport remain a render validation task.

Fresh factory-startup Blender5.2.1 built all12 shaders and loaded all15 maps; this technical check passed. All wood/linen/stone maps are4K; plaster is2K. The linen asset is4096×4105 rather than square; both axes still follow the physical tile contract. The physical-scale assertion also passed: a1.8m×0.6m board maps to1.8×0.6 metre UV extents; the helper resolves Blender’s stale transform matrices before projection. Shader validation is saved at `materials/SHADER_VALIDATION.json`. The full living-room rendered result has not been visually validated by this material subtask.

For integration, use Cycles daylight with enough transmission/transparent bounces to see through clear glazing; for example transmission8 and transparent8. Set AgX explicitly and judge warm-white color with neutral daylight before tuning exposure. Do not compensate for blocked windows by excessive fill lights. No scene, geometry or lighting changes were authored here.

## Source assets and provenance

- beige_wall_001 (2k, CC0): https://polyhaven.com/a/beige_wall_001
  Manifest: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/beige_wall_001/asset-manifest.json`
  diffuse: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/beige_wall_001/beige_wall_001_diffuse_2k.jpg`
  roughness: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/beige_wall_001/beige_wall_001_roughness_2k.png`
  normal: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/beige_wall_001/beige_wall_001_normal_2k.png`
- marble_01 (4k, CC0): https://polyhaven.com/a/marble_01
  Manifest: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/marble_01/asset-manifest.json`
  diffuse: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/marble_01/marble_01_diffuse_4k.jpg`
  roughness: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/marble_01/marble_01_roughness_4k.png`
  normal: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/marble_01/marble_01_normal_4k.png`
- oak_wood_planks (4k, CC0): https://polyhaven.com/a/oak_wood_planks
  Manifest: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/oak_wood_planks/asset-manifest.json`
  diffuse: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/oak_wood_planks/oak_wood_planks_diffuse_4k.jpg`
  roughness: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/oak_wood_planks/oak_wood_planks_roughness_4k.png`
  normal: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/oak_wood_planks/oak_wood_planks_normal_4k.png`
- rough_linen (4k, CC0): https://polyhaven.com/a/rough_linen
  Manifest: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/rough_linen/asset-manifest.json`
  diffuse: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/rough_linen/rough_linen_diffuse_4k.jpg`
  roughness: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/rough_linen/rough_linen_roughness_4k.png`
  normal: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/rough_linen/rough_linen_normal_4k.png`
- washed_grey_oak_veneer (4k, CC0): https://polyhaven.com/a/washed_grey_oak_veneer
  Manifest: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/washed_grey_oak_veneer/asset-manifest.json`
  diffuse: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/washed_grey_oak_veneer/washed_grey_oak_veneer_diffuse_4k.jpg`
  roughness: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/washed_grey_oak_veneer/washed_grey_oak_veneer_roughness_4k.png`
  normal: `/Users/xiwei/interior_design/projects/c_type_home/design/living_finalize_v1/materials/washed_grey_oak_veneer/washed_grey_oak_veneer_normal_4k.png`

The complete file list, checksums, map color spaces, scales and caveats are in `reports/MATERIAL_ASSET_NOTES.json`. The R4 mother and FreeCAD sources remain untouched.
