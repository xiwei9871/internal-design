import unittest
import numpy as np

class RenderQCTests(unittest.TestCase):
    def test_identical_edges_and_empty_input(self):
        from scheme_a_v14.qc import compare_edges
        a=np.zeros((100,100),bool); a[20:80,30]=True
        score=compare_edges(a,a,tolerance=2)
        self.assertEqual(score['recall'],1)
        self.assertEqual(score['precision'],1)
        with self.assertRaises(ValueError): compare_edges(np.zeros_like(a),a)

    def test_added_and_moved_structure_is_penalized(self):
        from scheme_a_v14.qc import compare_edges
        a=np.zeros((100,100),bool); a[20:80,30]=True
        extra=a.copy(); extra[20:80,70]=True
        self.assertLess(compare_edges(a,extra,tolerance=2)['precision'],1)
        moved=np.roll(a,10,axis=1)
        self.assertEqual(compare_edges(a,moved,tolerance=2)['recall'],0)

    def test_candidate_never_auto_releases_without_semantic_review(self):
        from scheme_a_v14.qc import can_publish
        meta={'design_sha256':'a','camera_signature':'b'}
        self.assertFalse(can_publish(meta,meta,{}, {'f1':.99},None))
        review={k:True for k in ['openings','equipment_order','furniture_orientation','no_unapproved_objects']}
        self.assertTrue(can_publish(meta,meta,review,{'f1':.99,'evaluation_size':[1000,700],'tolerance_px':5,'reference_sha256':'x'},None))
        self.assertFalse(can_publish(meta,dict(meta,design_sha256='c'),review,{'f1':.99},None))
        self.assertFalse(can_publish(meta,meta,review,{'f1':.70},{'f1':.8}))

    def test_invalid_or_incomparable_scores_cannot_publish(self):
        from scheme_a_v14.qc import can_publish
        meta={'design_sha256':'a','camera_signature':'b'}
        review={k:True for k in ['openings','equipment_order','furniture_orientation','no_unapproved_objects']}
        base={'f1':.8,'evaluation_size':[1000,700],'tolerance_px':5,'reference_sha256':'x'}
        for score in [dict(base,f1=float('nan')),dict(base,f1=2),dict(base,evaluation_size=[500,350]),dict(base,reference_sha256='y')]:
            self.assertFalse(can_publish(meta,meta,review,score,base))
