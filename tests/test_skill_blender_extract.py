"""Runs extract_plan_geometry.py inside real Blender on a generated scene.
Covers: hidden parent collection, object transforms, source SHA/version, read-only source."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR = ROOT / '.codex/skills/blender-plan-geometry-extraction/scripts/extract_plan_geometry.py'
BLENDER = shutil.which('blender')

BUILD = r'''
import bpy, sys, math
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def plane(name, size, loc, rot_z=0.0, coll=None, flip=False):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=(math.pi if flip else 0, 0, rot_z))
    o = bpy.context.active_object; o.name = name
    if coll:
        for c in o.users_collection: c.objects.unlink(o)
        coll.objects.link(o)
    return o
parent = bpy.data.collections.new('HIDDEN_PARENT'); sc.collection.children.link(parent)
child = bpy.data.collections.new('VISIBLE_CHILD'); parent.children.link(child)
parent.hide_render = True
plane('FLOOR_HIDDEN_BY_PARENT', 2.0, (10, 10, 0), coll=child)
f = plane('FLOOR_MOVED', 2.0, (0, 0, 0))
f.location = (3.0, 1.0, 0.45); f.rotation_euler[2] = math.radians(90); f.scale = (2.0, 1.0, 1.0)
plane('CEILING_A', 4.0, (0, 0, 2.8), flip=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
'''


def blender(*args):
    return subprocess.run([BLENDER, '-b', *args], capture_output=True, text=True, timeout=600)


@unittest.skipIf(BLENDER is None, 'blender not on PATH')
class BlenderExtractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.blend = cls.tmp / 'scene.blend'
        build = cls.tmp / 'build.py'; build.write_text(BUILD)
        r = blender('--factory-startup', '-P', str(build), '--', str(cls.blend))
        assert cls.blend.exists(), r.stdout[-2000:] + r.stderr[-2000:]
        cls.sha_before = hashlib.sha256(cls.blend.read_bytes()).hexdigest()
        cfg = cls.tmp / 'cfg.json'
        cfg.write_text(json.dumps({'floor': '^FLOOR_', 'ceiling': '^CEILING_'}))
        cls.out = cls.tmp / 'extract.json'
        r = blender(str(cls.blend), '-P', str(EXTRACTOR), '--', 'extract', str(cfg), str(cls.out))
        assert cls.out.exists(), r.stdout[-2000:] + r.stderr[-2000:]
        cls.data = json.loads(cls.out.read_text())

    def test_hidden_parent_collection_excludes_object(self):
        self.assertNotIn('FLOOR_HIDDEN_BY_PARENT', self.data['floor'])
        self.assertIn('FLOOR_MOVED', self.data['floor'])

    def test_world_transform_applied(self):
        tris = self.data['floor']['FLOOR_MOVED']['tris']
        xs = [p[0] for t in tris for p in t[:3]]; ys = [p[1] for t in tris for p in t[:3]]
        # 2x2 plane scaled x2 then rotated 90 deg: 2 m in X, 4 m in Y, centred at (3000, 1000)
        self.assertAlmostEqual(min(xs), 2000, delta=1); self.assertAlmostEqual(max(xs), 4000, delta=1)
        self.assertAlmostEqual(min(ys), -1000, delta=1); self.assertAlmostEqual(max(ys), 3000, delta=1)
        self.assertTrue(all(t[3] == 450 for t in tris))

    def test_ceiling_reads_down_facing_faces(self):
        tris = self.data['ceiling']['CEILING_A']['tris']
        self.assertTrue(tris)
        self.assertTrue(all(t[3] == 2800 for t in tris))

    def test_source_version_recorded_and_source_unchanged(self):
        self.assertEqual(self.data['blend_sha256'], self.sha_before)
        self.assertTrue(self.data['blender_version'])
        self.assertEqual(self.data['extractor'], 'extract_plan_geometry.py/2')
        self.assertEqual(hashlib.sha256(self.blend.read_bytes()).hexdigest(), self.sha_before)


if __name__ == '__main__':
    unittest.main()
