import unittest


class DesignModelTests(unittest.TestCase):
    def test_opening_infill_is_centered_on_segment(self):
        from design_model import opening_infill_rect
        horizontal=opening_infill_rect([10,20,110,20],120)
        vertical=opening_infill_rect([10,20,10,120],120)
        self.assertAlmostEqual(horizontal[1]+horizontal[3]/2,20)
        self.assertAlmostEqual(vertical[0]+vertical[2]/2,10)
        self.assertAlmostEqual(horizontal[3]*9.82,120)
    def test_confirmed_bookcase_and_door(self):
        from design_model import load_design
        d = load_design()
        bookcase = next(f for f in d['furniture'] if '儿童窗边书柜' in f['name'])
        self.assertEqual(bookcase['height_m'], 1.1)
        door = next(x for x in d['doors'] if x['name'] == '次卫门')
        self.assertEqual(door['type'], 'pocket_sliding')
        self.assertIsNone(door['structural_opening_mm'])
        self.assertEqual(door['pocket_status'], 'pending_site_verification')

    def test_unique_ids_and_service_chain(self):
        from design_model import load_design
        d = load_design()
        ids = [x['id'] for k in ['walls','windows','doors','furniture','zones'] for x in d[k]]
        self.assertEqual(len(ids), len(set(ids)))
        bays = d['design']['service_wall']['bays']
        self.assertAlmostEqual(sum(b['width_mm'] for b in bays), 234 * 9.82)
        self.assertEqual([b['id'] for b in bays], ['fridge', 'oven', 'laundry'])

    def test_coordinates_and_door_shape(self):
        from design_model import world_mm, load_design, door_leaf_rect
        self.assertEqual(world_mm(200, 1337), (0.0, 0.0))
        d = next(x for x in load_design()['doors'] if x['name'] == '次卫门')
        r = door_leaf_rect(d)
        self.assertLess(r[2], 6)
        self.assertAlmostEqual(r[3], 76)

    def test_semantics_preserve_openings_and_mounting(self):
        from design_model import load_design
        d = load_design()
        self.assertTrue(all(w['sill_mm'] == 0 for w in d['windows'] if w['type'] == 'sliding_glass'))
        self.assertTrue(all(f['front_axis'] == '+X' for f in d['furniture'] if f['kind'] == 'wc'))
        mirror = next(f for f in d['furniture'] if f['id'] == 'FURN-028')
        self.assertGreaterEqual(mirror['z_mm'], 1000)
        for bay in d['design']['service_wall']['bays']:
            f = next(f for f in d['furniture'] if f['id'] == bay['furniture_id'])
            self.assertEqual(f['height_m']*1000, d['design']['service_wall']['height_mm'])


if __name__ == '__main__':
    unittest.main()
