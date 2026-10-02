"""New memory contract. Real sqlite + reducer, no LLM semantic claims."""
import unittest,tempfile,json
from pathlib import Path
try:
    from switchlab.memory.store import MemoryStore
except ImportError:
    MemoryStore=None

NOW=1800000000.
class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(MemoryStore,'persistent memory store is not implemented')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=MemoryStore(Path(self.tmp.name)/'memory.sqlite3');self.addCleanup(lambda:self.s.close())
    def say(self,text):return self.s.apply('message',{'text':text},at=NOW)['id']
    def create(self,text='以后一起玩MC',when=''):
        mid=self.say(text)
        e=self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'create','title':'一起玩MC','category':'activity','quote':text,'when':when,'accept':True}]},at=NOW)
        return e['result']['commitments'][0]
    def test_same_turn_durable_untimed_then_restart(self):
        cid=self.create();self.s.close();self.s=MemoryStore(Path(self.tmp.name)/'memory.sqlite3')
        c=self.s.commitment(cid);self.assertEqual(c['status'],'accepted');self.assertIsNone(c['due_at']);self.assertEqual(c['revision'],1)
        self.assertIn('一起玩MC',json.dumps(self.s.context('以前约好玩什么',budget_bytes=12000),ensure_ascii=False))
    def test_revision_and_cancel_invalidate_old_schedule(self):
        cid=self.create('我们约好2099-01-01T20:00:00+00:00一起玩MC','2099-01-01T20:00:00+00:00')
        mid=self.say('改到2099-01-02T21:00:00+00:00')
        self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'revise','id':cid,'expected_revision':1,'quote':'改到2099-01-02T21:00:00+00:00','when':'2099-01-02T21:00:00+00:00'}]},at=NOW)
        self.assertEqual(len(self.s.versions(cid)),2);self.assertEqual(self.s.commitment(cid)['revision'],2)
        mid=self.say('取消这个约定')
        self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'cancel','id':cid,'expected_revision':2,'quote':'取消这个约定'}]},at=NOW)
        self.assertEqual(self.s.due(9999999999.),[])
    def test_false_source_and_stale_revision_rollback_whole_packet(self):
        cid=self.create();before=self.s.projection_digest();mid=self.say('修改约定')
        before=self.s.projection_digest()
        with self.assertRaises(ValueError):self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'revise','id':cid,'expected_revision':0,'quote':'修改约定','when':''}]},at=NOW)
        self.assertEqual(before,self.s.projection_digest())
        with self.assertRaises(ValueError):self.s.apply('interpret',{'source':mid,'claims':[{'subject':'user','predicate':'favorite','value':'蓝','quote':'并未出现','scope':'personal'}],'commitments':[]},at=NOW)
        self.assertEqual(before,self.s.projection_digest())
    def test_semantic_claims_never_turn_generated_speech_into_observation(self):
        mid=self.say('书里的小明喜欢蓝色，不是我。')
        self.s.apply('interpret',{'source':mid,'claims':[{'subject':'character:小明','predicate':'favorite','value':'蓝色','quote':'小明喜欢蓝色','scope':'fiction'}],'commitments':[]},at=NOW)
        self.assertEqual(self.s.claims(scope='personal')['total'],0)
        with self.assertRaises(ValueError):self.s.apply('interpret',{'source':'M999999999','claims':[],'commitments':[]},at=NOW)
    def test_no_time_hallucination_or_boolean_timestamp(self):
        with self.assertRaises(ValueError):self.create('以后一起玩MC','2099-01-01T20:00:00+00:00')
        mid=self.say('明天下午一起玩MC')
        e=self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'create','title':'一起玩MC','category':'activity','quote':'明天下午一起玩MC','when':'明天下午','accept':True}]},at=NOW)
        c=self.s.commitment(e['result']['commitments'][0]);self.assertIsNone(c['due_at']);self.assertEqual(c['status'],'needs_clarification')
    def test_full_list_pagination_is_not_top_k(self):
        for i in range(25):self.create('以后一起玩MC'+str(i))
        page=self.s.commitments(limit=7);self.assertEqual(page['total'],25);self.assertEqual(len(page['items']),7);self.assertFalse(page['complete'])
        allrows=[];offset=0
        while True:
            p=self.s.commitments(limit=7,offset=offset);allrows+=p['items']
            if p['complete']:break
            offset=p['next_offset']
        self.assertEqual(len({c['id'] for c in allrows}),25)
    def test_context_bounded_but_source_not_discarded(self):
        mid=self.say('蓝裙子是星之海牌，编号AZ009。'+'很久以前 '*500)
        for i in range(110):self.say('无关的话题'+str(i))
        context=self.s.context('星之海 AZ009',budget_bytes=9000)
        self.assertLessEqual(len(json.dumps(context,ensure_ascii=False,separators=(',',':')).encode()),9000)
        self.assertTrue(any(x['id']==mid for x in self.s.search('星之海 AZ009')['items']))
        self.assertEqual(len(self.s.observation(mid)['text']),len('蓝裙子是星之海牌，编号AZ009。'+'很久以前 '*500))
    def test_backup_restore_preserves_identity_and_all_raw_text(self):
        cid=self.create();backup=Path(self.tmp.name)/'backup.sqlite3';self.s.backup(backup)
        restored=MemoryStore(backup)
        try:
            self.assertEqual(self.s.person_id,restored.person_id);self.assertEqual(self.s.projection_digest(),restored.projection_digest());self.assertEqual(restored.commitment(cid)['title'],'一起玩MC')
        finally:restored.close()
    def test_recorded_input_replay_rejects_rehashed_result_tamper(self):
        self.create();cp=self.s.export();other=MemoryStore.from_export(Path(self.tmp.name)/'copy.sqlite3',cp)
        self.assertEqual(self.s.projection_digest(),other.projection_digest());other.close()
        from switchlab.memory.store import rehash_export
        cp['journal'][-1]['result']['commitments']=[];rehash_export(cp)
        with self.assertRaises(ValueError):MemoryStore.from_export(Path(self.tmp.name)/'tamper.sqlite3',cp)
    def test_failed_sql_commit_does_not_claim_success(self):
        before=self.s.projection_digest()
        self.s.db.execute("CREATE TRIGGER reject_message BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT,'disk simulated failure'); END")
        with self.assertRaises(Exception):self.say('记住这件事')
        self.assertEqual(before,self.s.projection_digest())
