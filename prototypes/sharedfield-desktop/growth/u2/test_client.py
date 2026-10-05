import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from companion.budget import DailyLedger
from p7.proxy import ProxyError
from . import client as module
from .client import Client, Stop, append
from .protocol import MODEL


class ClientTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(dir=module.ROOT/'runs');self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.folder=self.root/'lane';self.folder.mkdir()
        ledger=DailyLedger(self.root/'budget.sqlite')
        with patch.object(module,'ROOT',self.root),patch.object(module,'read_key',return_value='offline-dummy'),patch.object(module,'DEFAULT_BUDGET',self.root/'budget.sqlite'):
            self.client=Client(self.folder)
        self.patcher=patch.object(module,'ROOT',self.root);self.patcher.start();self.addCleanup(self.patcher.stop)
        self.client.check=lambda:None
        self.delays=[];self.client.wait=lambda target:self.delays.append(target)
        self.requests=[]

    def model(self,failures):
        def complete(request,**kwargs):
            self.requests.append(copy.deepcopy(request))
            charge=self.client.transport.ledger.reserve(.05)
            append(self.folder/'routing.jsonl',{'charge_id':charge,'outcome':'http_error','retry_after_s':31})
            if len(self.requests)<=len(failures):raise ProxyError(failures[len(self.requests)-1],503,charge_id=charge)
            self.client.transport.ledger.settle(charge,{'cost':.001})
            return {'reason':'r','interpretation':'i','action':'o1','reply':'x'},{'cost_usd':.001,'charge_id':charge}
        self.client.model=SimpleNamespace(complete=complete)

    def test_exactly_one_retry_same_payload_unknown_hold_retained(self):
        self.model(['upstream_http_503'])
        output,_=self.client.call([{'role':'user','content':'隔离故障测试'}],{'test':True})
        self.assertEqual(len(self.requests),2);self.assertEqual(self.requests[0],self.requests[1])
        self.assertEqual(output['action'],'o1');self.assertAlmostEqual(self.client.cost(),.051)

    def test_second_failure_stops_no_third_attempt(self):
        self.model(['upstream_http_429','upstream_connection_error'])
        with self.assertRaisesRegex(Stop,'upstream_connection_error'):
            self.client.call([{'role':'user','content':'same'}],{})
        self.assertEqual(len(self.requests),2);self.assertAlmostEqual(self.client.cost(),.10)

    def test_nonretryable_error_no_retry(self):
        self.model(['upstream_http_400'])
        with self.assertRaisesRegex(Stop,'upstream_http_400'):
            self.client.call([{'role':'user','content':'same'}],{})
        self.assertEqual(len(self.requests),1)

    def test_reasoning_flags_and_two_invalid_stop(self):
        self.model([])
        self.client.call([{'role':'user','content':'plain'}],{})
        self.client.call([{'role':'user','content':'organize'}],{},reasoning=True)
        self.assertEqual(self.requests[0]['reasoning'],{'enabled':False})
        self.assertEqual(self.requests[1]['reasoning']['effort'],'low')
        self.client.parsed(False)
        with self.assertRaisesRegex(Stop,'two_consecutive_invalid_outputs'):self.client.parsed(False)


if __name__=='__main__':unittest.main()
