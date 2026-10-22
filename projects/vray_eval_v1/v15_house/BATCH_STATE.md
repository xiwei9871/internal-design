# V15 Whole-House V-Ray Batch

- Source: `projects/c_type_home/design/secondary_mirror_v15/WHOLE_HOUSE_SECONDARY_MIRROR_FINAL_V15.blend` (copied to V15_WORK.blend; original untouched)
- Params: progressive, subdivs 48, threshold 0.005, maxTime 14min, GI on, 1280x720
- Material pass: auto-convert + keyword-mapped VRayNodeMetaImageTexture (ash/linen-ivory/floor/rug/art/marble); linen_warm.png baked via numpy retint
- Queue: 75 cameras (15 rooms x VIEW_01..05), all VIEW_01 first, then 02-05
- Resume-safe: skips existing PNGs; per-frame log in manifest.json
- Denoise: `oidn_denoise.py` (Blender background, no license) — run per-file after batch
- Validated: couple_bedroom_view01.png 851s — warm ivory bedding + ash nightstands correct
- Living reference: b_hero_final.png / b_closeup_final.png (from earlier living pass)
