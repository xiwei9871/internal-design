"""Living finalization PBR library. Blender 5.2 / Cycles, scene units in metres.

CC0 scans: Powered by Poly Haven. See reports/MATERIAL_ASSET_NOTES.md.
All textured shaders read LF_PhysicalUV in METRES, then scale to a physical tile.
Use assign_uv(mesh, grain_axis='X') for grain along its local X axis. The texture
U axis is longitudinal grain. Call after geometry/scales are final, before pack.
No source objects, cameras, lighting, geometry, files, or scene settings mutate
unless assign_uv / pack_material_images is explicitly invoked by the caller.
"""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'materials'
UV_NAME = 'LF_PhysicalUV'
PREFIX = 'LF_PBR_'

# (length along grain, width across grain), metres. Scan calibration is an
# authored look-development choice; it is NOT a manufacturer specification.
TILE_METRES = {'WOOD': (1.80, .60), 'FLOOR': (2.20, 1.10),
               'FABRIC': (.16, .16), 'FABRIC_DARK': (.16, .16),
               'STONE': (1.35, 1.35), 'WALL': (1.0, 1.0),
               'CEILING': (1.0, 1.0), 'RUG': (.26, .26)}


def _asset_files(asset):
    manifest = json.loads((ASSETS / asset / 'asset-manifest.json').read_text())
    if manifest['status'] != 'complete':
        raise RuntimeError('Incomplete PBR asset: ' + asset)
    return {f['map']: ASSETS / asset / f['file'] for f in manifest['files']}


def _base(key, color, roughness=.5, metallic=0.0):
    import bpy
    name = PREFIX + key
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    out = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    out.location = (800, 0)
    bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (500, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    mat.diffuse_color = (*color, 1)
    mat['role'] = key
    return mat, bsdf, out


def _scan(key, asset, low, high, rough=(.4, .65), normal_strength=.3,
          sheen=0.0, coat=0.0):
    import bpy
    mat, bsdf, out = _base(key, high, sum(rough) / 2)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = UV_NAME
    uv.location = (-1000, 100)
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY'
    scale.location = (-800, 100)
    tile = TILE_METRES[key]
    scale.inputs[1].default_value = (1 / tile[0], 1 / tile[1], 1)
    links.new(uv.outputs['UV'], scale.inputs[0])
    maps = {}
    for i, (role, path) in enumerate(_asset_files(asset).items()):
        if not path.exists():
            raise FileNotFoundError(path)
        tex = nodes.new('ShaderNodeTexImage')
        tex.label = f'{asset} | {role} | CC0'
        tex.location = (-570, 240 - i * 270)
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        tex.image.colorspace_settings.name = 'sRGB' if role == 'diffuse' else 'Non-Color'
        tex.extension = 'REPEAT'
        tex.interpolation = 'Linear'
        links.new(scale.outputs['Vector'], tex.inputs['Vector'])
        maps[role] = tex
    # Preserve scan grain and weave, adapting hue/contrast into the approved
    # pale palette. RGB-to-BW reads decoded linear albedo, not raw JPEG values.
    bw = nodes.new('ShaderNodeRGBToBW')
    bw.location = (-260, 220)
    links.new(maps['diffuse'].outputs['Color'], bw.inputs['Color'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.label = 'Pale palette; scan variation retained'
    ramp.location = (-50, 250)
    ramp.color_ramp.elements[0].position = .03
    ramp.color_ramp.elements[0].color = (*low, 1)
    ramp.color_ramp.elements[1].position = .80
    ramp.color_ramp.elements[1].color = (*high, 1)
    links.new(bw.outputs[0], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    remap = nodes.new('ShaderNodeMapRange')
    remap.location = (-60, -70)
    remap.inputs['To Min'].default_value = rough[0]
    remap.inputs['To Max'].default_value = rough[1]
    links.new(maps['roughness'].outputs['Color'], remap.inputs['Value'])
    links.new(remap.outputs[0], bsdf.inputs['Roughness'])
    normal = nodes.new('ShaderNodeNormalMap')
    normal.space = 'TANGENT'
    normal.uv_map = UV_NAME
    normal.inputs['Strength'].default_value = normal_strength
    normal.location = (200, -270)
    links.new(maps['normal'].outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Sheen Weight'].default_value = sheen
    bsdf.inputs['Sheen Roughness'].default_value = .65
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = .32
    mat['source'] = f'https://polyhaven.com/a/{asset}'
    mat['license'] = 'CC0'
    mat['tile_metres'] = list(tile)
    mat['normal_convention'] = 'OpenGL +Y; Non-Color; tangent LF_PhysicalUV'
    return mat


def make_materials():
    """Return WOOD/FLOOR/FABRIC/... keys. Safe to call repeatedly.

    WOOD uses oak scan as ash-color joinery analogue; it is not an ash scan.
    STONE is a restrained color-adapted marble scan, not certified limestone.
    GLASS routes shadow rays through clear Transparent BSDF. Camera/glossy rays
    see genuine IOR 1.46 transmission with neutral reflection. This is a
    documented architectural glazing approximation for efficient daylight.
    """
    import bpy
    mats = {}
    mats['WOOD'] = _scan('WOOD', 'washed_grey_oak_veneer',
                        (.37, .325, .25), (.65, .59, .48), (.32, .49), .32, coat=.08)
    mats['FLOOR'] = _scan('FLOOR', 'oak_wood_planks',
                         (.34, .295, .23), (.63, .565, .455), (.32, .5), .27, coat=.07)
    mats['FABRIC'] = _scan('FABRIC', 'rough_linen',
                          (.51, .47, .395), (.72, .67, .57), (.72, .92), .24, sheen=.22)
    mats['FABRIC_DARK'] = _scan('FABRIC_DARK', 'rough_linen',
                               (.17, .18, .17), (.32, .34, .30), (.74, .93), .24, sheen=.23)
    mats['RUG'] = _scan('RUG', 'rough_linen',
                       (.40, .365, .30), (.62, .57, .48), (.82, .97), .40, sheen=.12)
    mats['STONE'] = _scan('STONE', 'marble_01',
                         (.46, .425, .37), (.68, .63, .54), (.32, .53), .13)
    mats['WALL'] = _scan('WALL', 'beige_wall_001',
                        (.70, .68, .625), (.79, .77, .715), (.77, .93), .10)
    mats['CEILING'] = _scan('CEILING', 'beige_wall_001',
                           (.75, .735, .69), (.81, .795, .755), (.80, .95), .07)
    mat, bsdf, out = _base('GLASS', (.985, .990, .995), .025)
    bsdf.inputs['Transmission Weight'].default_value = 1
    bsdf.inputs['IOR'].default_value = 1.46
    if 'Thin Wall' in bsdf.inputs:
        bsdf.inputs['Thin Wall'].default_value = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    light = nodes.new('ShaderNodeLightPath')
    light.location = (0, 250)
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.inputs['Color'].default_value = (1, 1, 1, 1)
    transparent.location = (200, 250)
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (620, 150)
    links.new(light.outputs['Is Shadow Ray'], mix.inputs[0])
    links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    links.new(transparent.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs['Surface'])
    mat['transport'] = 'neutral IOR1.46 camera/glossy transmission; clear shadow pass architectural approximation'
    mats['GLASS'] = mat
    mat, bsdf, out = _base('METAL', (.61, .50, .33), .32, metallic=1.0)
    bsdf.inputs['Anisotropic'].default_value = .25
    mats['METAL'] = mat
    mat, bsdf, out = _base('CERAMIC', (.68, .65, .57), .24)
    bsdf.inputs['Coat Weight'].default_value = .14
    bsdf.inputs['Coat Roughness'].default_value = .24
    mats['CERAMIC'] = mat
    mat, bsdf, out = _base('LEAF', (.075, .14, .055), .43)
    bsdf.inputs['Subsurface Weight'].default_value = .035
    mats['LEAF'] = mat
    return mats


def assign_uv(obj, grain_axis='X', physical_scale=1.0, offset=None):
    """Physical box UV in metres, preserves mesh positions/shape and transforms.

    U follows local grain_axis on long faces; V follows cross-grain. End faces
    use their own plane. physical_scale scalar or (U,V) multiplies projected
    metres; default 1.0 is correct. Use .5 to DOUBLE apparent grain size.
    offset defaults to stable per-object scan offset to avoid cloned knots.
    This is for solid furniture/walls. Curved fabric with a good authored
    unwrap should retain it; copy/scale it into LF_PhysicalUV instead.
    Non-uniform object/parent scale is included; metre conversion uses the
    scene unit scale_length. Grain axis refers to local mesh axes.
    """
    import bpy
    from mathutils import Vector
    if obj.type != 'MESH':
        return None
    if grain_axis.upper() not in ('X', 'Y', 'Z'):
        raise ValueError('grain_axis must be X, Y, or Z')
    # Blender can leave matrix_world stale after direct object.scale writes.
    # Resolve it before measuring physical scale, including parent transforms.
    bpy.context.view_layer.update()
    axis = 'XYZ'.index(grain_axis.upper())
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    mesh = obj.data
    uv = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
    mesh.uv_layers.active = uv
    uv.active_render = True
    length_unit = bpy.context.scene.unit_settings.scale_length or 1.0
    basis = obj.matrix_world.to_3x3()
    scales = [basis.col[i].length * length_unit for i in range(3)]
    if isinstance(physical_scale, (int, float)):
        physical_scale = (float(physical_scale), float(physical_scale))
    if offset is None:
        digest = hashlib.sha256(obj.name.encode()).digest()
        offset = (int.from_bytes(digest[:2], 'big') / 65535 * .73,
                  int.from_bytes(digest[2:4], 'big') / 65535 * 1.13)
    for face in mesh.polygons:
        normal_axis = max(range(3), key=lambda i: abs(face.normal[i]))
        # Faces at end grain cannot have grain projected through their normal.
        u_axis = axis if axis != normal_axis else next(i for i in range(3) if i != normal_axis)
        v_axis = next(i for i in range(3) if i not in (normal_axis, u_axis))
        u = Vector((0, 0, 0)); u[u_axis] = 1
        v = Vector((0, 0, 0)); v[v_axis] = 1
        sign = 1 if u.cross(v).dot(face.normal) >= 0 else -1
        for loop_index in face.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (
                co[u_axis] * scales[u_axis] * physical_scale[0] * sign + offset[0],
                co[v_axis] * scales[v_axis] * physical_scale[1] + offset[1])
    obj['LF_UV_units'] = 'metres before shader tile scaling'
    obj['LF_grain_axis'] = grain_axis.upper()
    obj['LF_UV_offset_m'] = list(offset)
    return uv


def pack_material_images():
    """Pack only this library's images; caller then saves its separate .blend."""
    import bpy
    packed = []
    for img in bpy.data.images:
        if img.source == 'FILE' and str(ASSETS) in bpy.path.abspath(img.filepath):
            if not img.packed_file:
                img.pack()
            packed.append(img.name)
    return packed
