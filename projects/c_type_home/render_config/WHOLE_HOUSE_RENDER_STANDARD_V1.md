# WHOLE_HOUSE_RENDER_STANDARD_V1

Authority: PRESENTATION only, over `CONSOLE400_THREE_BATH_MIRRORS.blend` / `console400-three-bath-mirrors-review-1`. Source/frozen geometry never changes. The adjacent JSON is the executable specification.

| Parameter | Frozen baseline |
| --- | --- |
| HERO camera | 1.55 m above finished floor; 36 mm sensor; 28 mm default |
| Living / bedroom / study | 28–32 / 28–35 / 26–32 mm |
| Kitchen / small bathrooms / detail | 24–28 / 20–24 / 35–50 mm |
| Verticals / DOF | Horizontal camera; Lens Shift for framing; DOF off |
| Daylight | Soft afternoon; Sun elevation 35°, southwest azimuth 225°, angular diameter 5°, strength 0.15 |
| World | Packed courtyard HDRI, strength 0.45, rotation 0° |
| Fill | Visually verified window/room fill powers retained; neutral daylight RGB and restrained warm fill; practical target 2900 K |
| White balance | 5200 K, tint 0 |
| Color | AgX / Medium High Contrast / exposure +0.5 EV / gamma 1 |
| Camera gate | 960×540 Workbench, geometry/composition only |
| Lighting preview | Cycles 32 samples, 960×540 |
| Final | Cycles 256 samples, adaptive threshold 0.01, 1920×1080, OIDN, 8 bounces, indirect clamp 3 |
| Materials | Ash 0.45–0.65; fabric 0.65–0.85; wall 0.8; matte tile 0.5; stone 0.42 |

Sun/World/CCT/look stay identical across rooms. Record local power changes and exposure overrides (default zero, max ±0.3 EV). Source fixtures do not currently provide a complete lighting design; the existing room fill helpers remain presentation aids, not invented physical fixtures.

Every approved VIEW freezes matrix, lens, sensor, shift, viewport and source revision. FAITHFUL/DESIGNER/CREATIVE use the same camera record. AI editing is a visual study, not a numerical geometry guarantee; compare openings, furniture envelopes and edge alignment before acceptance.

Review cameras room by room, beginning with living. Reviewed V3 camera matrices were approved by the user on 2026-10-07; the per-view records take precedence over suggested numeric ranges. Keep earlier images intact as previews. Never use output-file existence alone to promote previews to finals. Only Image2 calls load the API/key via the persistent global Image2 launcher. Credentials are absent from this standard and Blender files.
