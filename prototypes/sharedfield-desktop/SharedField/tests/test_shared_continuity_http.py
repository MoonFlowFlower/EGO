import json,unittest,urllib.error
from tests import test_shared_http as fixtures
from switchlab.shared.core import SharedCore

class ContinuityHTTPTests(unittest.TestCase):
    setUp = fixtures.SharedHTTPTests.setUp
    cleanup_server = fixtures.SharedHTTPTests.cleanup_server
    req = fixtures.SharedHTTPTests.req
    def test_joint_and_memory_controls_are_exposed_not_only_library_functions(self):
        html=self.req('/')
        for ident in ('togetherBtn','waitBtn','resumeJointBtn','independentBtn','memoryTimeline','sharedConcern','importFile'):
            self.assertIn('id="'+ident+'"',html,'main UI omits '+ident)
        self.req('/api/command',{'kind':'activity','payload':{'mode':'wait'}})
        self.req('/api/auto',{'steps':8});self.s.run_once(force=True)
        state=self.req('/api/state');self.assertEqual(state['world']['tick'],0)
        self.assertEqual(state['cognition']['focus']['action']['kind'],'wait_partner')
    def test_http_import_is_verified_paused_and_requires_archive_confirmation(self):
        c=SharedCore();c.apply('agent_step',{})
        result=self.req('/api/import',{'checkpoint':c.checkpoint()})
        self.assertTrue(result['paused']);self.assertEqual(self.req('/api/state')['world']['tick'],1)
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/import',{'checkpoint':c.checkpoint()})
        result=self.req('/api/import',{'checkpoint':c.checkpoint(),'archive_current':True})
        self.assertTrue(result['paused'])
    def test_cross_origin_cannot_import_a_checkpoint(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:self.req('/api/import',{'checkpoint':SharedCore().checkpoint()},origin='https://example.invalid')
        self.assertEqual(ctx.exception.code,403)

    def test_non_object_import_is_rejected_without_losing_session(self):
        before=self.s.core.checkpoint()
        for invalid in (None,[],False,17):
            with self.assertRaises(urllib.error.HTTPError) as ctx:self.req('/api/import',{'checkpoint':invalid})
            self.assertEqual(ctx.exception.code,400)
            self.assertEqual(self.s.core.checkpoint(),before)

    def test_real_sized_checkpoint_uses_import_budget_not_model_output_budget(self):
        c=SharedCore()
        for _ in range(12):c.apply('agent_step',{})
        cp=c.checkpoint();self.assertGreater(len(json.dumps(cp)),50000)
        result=self.req('/api/import',{'checkpoint':cp})
        self.assertTrue(result['ok']);self.assertEqual(self.s.core.world.tick,12)
