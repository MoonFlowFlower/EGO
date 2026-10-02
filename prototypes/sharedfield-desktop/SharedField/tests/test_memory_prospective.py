import unittest,tempfile
from pathlib import Path
from tests.test_memory_store import NOW
from switchlab.memory.store import MemoryStore
from switchlab.memory.timeutil import resolve_when

class ProspectiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=MemoryStore(Path(self.tmp.name)/'m.db');self.addCleanup(self.s.close)
    def say(self,text,at=NOW):return self.s.apply('message',{'text':text},at=at)['id']
    def commitment(self,at=NOW):
        source=self.say('我1分钟后回家',at)
        e=self.s.apply('interpret',{'source':source,'claims':[],'commitments':[{'op':'create','title':'预计回家','category':'checkin','quote':'我1分钟后回家','when':'1分钟后','accept':True}]},at=at)
        return self.s.commitment(e['result']['commitments'][0])
    def deliver(self,c,at=NOW+70):
        r=self.s.apply('consider',{'id':c['id'],'revision':c['revision']},at=at)['result']
        if r['action']=='wait':
            at=r['until']+1;r=self.s.apply('consider',{'id':c['id'],'revision':c['revision']},at=at)['result']
        self.assertEqual(r['action'],'consider_contact')
        key=r['contact']['key'];self.s.apply('expression',{'text':'测试夹具：现在方便联系吗','source':None,'evidence':[c['source']],'contact':key,'transport':'fixture'},at=at+1)
        return key
    def test_real_clock_due_not_recent_context(self):
        c=self.commitment()
        for i in range(80):self.say('新话题'+str(i))
        self.assertEqual(self.s.due(NOW+59),[]);self.assertEqual(self.s.due(NOW+61)[0]['id'],c['id'])
        key=self.deliver(c);self.assertEqual(self.s.due(NOW+6000),[])
        with self.assertRaises(ValueError):self.s.apply('consider',{'id':c['id'],'revision':1},at=NOW+90)
    def test_cancel_before_delivery_rejects_inflight_expression(self):
        c=self.commitment();r=self.s.apply('consider',{'id':c['id'],'revision':1},at=NOW+70)['result'];key=r['contact']['key']
        mid=self.say('不用联系我了')
        self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'cancel','id':c['id'],'expected_revision':1,'quote':'不用联系我了'}]},at=NOW+71)
        with self.assertRaises(ValueError):self.s.apply('expression',{'text':'该被丢弃','source':None,'evidence':[c['source']],'contact':key},at=NOW+72)
    def test_actual_busy_report_changes_same_clock_decision(self):
        c=self.commitment();mid=self.say('我忙到今天23:00')
        self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[],'availability':{'quote':'我忙到今天23:00','until':'今天23:00'}},at=NOW)
        r=self.s.apply('consider',{'id':c['id'],'revision':1},at=NOW+70)['result']
        self.assertEqual(r['action'],'wait');self.assertEqual(self.s.pending_contacts(),[])
    def test_feedback_learning_changes_future_choice_and_freeze_blocks_update(self):
        for i in range(8):
            t=NOW+i*200;c=self.commitment(t);key=self.deliver(c,t+70);mid=self.say('这次我正忙，不方便回复',t+72)
            self.s.apply('feedback',{'source':mid,'contact':key,'outcome':'busy'},at=t+72)
        c=self.commitment(NOW+2000)
        self.assertEqual(self.s.apply('consider',{'id':c['id'],'revision':1},at=NOW+2070)['result']['action'],'wait')
        model=self.s.model();examples=self.s.outcome_count()
        self.s.apply('setting',{'learning':False},at=NOW+2071);self.s.apply('replay',{},at=NOW+2072)
        self.assertEqual(self.s.model(),model);self.assertEqual(examples,self.s.outcome_count())
    def test_replay_changes_weights_not_independent_evidence_count(self):
        c=self.commitment();key=self.deliver(c);mid=self.say('这次方便')
        self.s.apply('feedback',{'source':mid,'contact':key,'outcome':'available'},at=NOW+72);old=self.s.model();n=self.s.outcome_count()
        r=self.s.apply('replay',{},at=NOW+73)['result']
        self.assertEqual(r['new_external_evidence'],0);self.assertGreater(self.s.model()['updates'],old['updates']);self.assertEqual(self.s.outcome_count(),n)
        with self.assertRaises(ValueError):self.s.apply('feedback',{'source':mid,'contact':key,'outcome':'available'},at=NOW+74)
    def test_time_anchor_and_vague_date_and_dst(self):
        self.assertEqual(resolve_when('1分钟后',NOW),NOW+60)
        self.assertIsNone(resolve_when('明天下午',NOW))
        self.assertIsNone(resolve_when('2027-03-14 02:30',NOW,'America/New_York'))
        self.assertIsNone(resolve_when('2027-11-07 01:30',NOW,'America/New_York'))
        self.assertEqual(resolve_when('2099-01-01T20:00:00+08:00',NOW),4070952000.)
