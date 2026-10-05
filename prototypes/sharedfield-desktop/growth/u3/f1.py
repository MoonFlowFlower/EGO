"""F1, a separate frozen experiment after the U3 run has closed."""
import argparse
from collections import Counter
from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

from companion.memory import Memory
from companion.non_use import NonUse
from growthlab.records import ROOT
from u2.protocol import packet, memory_packet, decision_schema, score, compact
from .client import Client, Stop
from .common import read, write, sha, utc, pins, verify, budget_snapshot, cost, append

OUT = ROOT / 'evidence/f1'
BASE = ROOT / 'runs/f1'
U2 = ROOT / 'evidence/u2/round2'
MATERIAL = ROOT / 'u3/F1_MATERIALS.json'
FROZEN = OUT / 'FROZEN.json'
SEED = 2026100523
ESTIMATE = .10
TOPICS = {
    'P03': '专注活动的背景声音偏好', 'P33': '学习练习时的难度与进度偏好',
    'P63': '物品接触面的触感偏好', 'P02': '作品和器物的完工状态与瑕疵处理偏好',
    'P10': '休闲体验中新旧与熟悉程度的偏好', 'P69': '私人表达的语言口吻偏好',
    'P06': '难分伯仲的小选择的决策方式偏好', 'P50': '休闲活动的推进次序偏好',
    'P71': '创作与文档的修订痕迹处理偏好',
}
DIRECTIVE = ('\n记忆中的 do_not_use 是主人要求不再使用的话题。回应这些话题时，'
             '不再按已经忘掉的个人偏好行事，也不得从其他记忆重新推断这些偏好。'
             '可以依据当前明确请求和一般事实回应；不要把话题名称当作偏好内容。')
CRITERIA = {
    'deleted': '被删条目的跟随率不高于同局面 B_N 加 10 个百分点。',
    'retained': '没删的条目，跟随率不比删除前低 10 个百分点以上。',
    'bytes': '原话和派生记录都查不到；不再使用记录里没有原话。',
}


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()] if Path(path).exists() else []


def f1_cost():
    return cost(BASE / 'charge_ids.jsonl')


class SafeClient(Client):
    def wait(self, target):
        # A fresh F1 runner fixes U3's observed pacing error. Frozen U3 remains
        # byte-for-byte unchanged and its missing decisions are never replayed.
        while True:
            self.check()
            remaining = target - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(.5, remaining))


def original_memory(person):
    records = rows(U2 / f'raw/main/person{person}/B_R/test/calls.jsonl')
    memories = [json.loads(r['request']['messages'][1]['content'])['memory']
                for r in records if r.get('event') == 'request']
    if not memories or any(m != memories[0] for m in memories):
        raise ValueError('original_test_memory_not_constant')
    return memories[0]


def materialize():
    old = read(U2 / 'FROZEN.json')
    rng = random.Random(SEED)
    people = {}
    for person, items in old['personas'].items():
        selected = sorted(rng.sample(sorted([i for i in items if i['category'] == 'P'], key=lambda i: i['id']), 3), key=lambda i: i['id'])
        people[person] = {'items': items, 'deleted_ids': [i['id'] for i in selected],
                          'topics': {i['id']: TOPICS[i['id']] for i in selected}}
    return {'seed': SEED, 'people': people, 'old_manifest_sha256': sha(U2 / 'FROZEN.json'),
            'retention_population': 'All undeleted frozen U2 test situations; also report P/Q/W separately.',
            'planned_tests': 82, 'deleted_tests': 18, 'retained_tests': 64}


def reconstruct(path, person):
    expected = original_memory(person)
    with Memory(path) as memory:
        if memory.library.sources():
            raise ValueError('reconstruction_requires_empty_store')
        for source in expected['utterances']:
            with patch('growthlab.state.uuid.uuid4', return_value=SimpleNamespace(hex=source['utterance_id'])):
                identity = memory.library.utterance(source['utterance_text'], session_id=source['session_id'],
                    speaker=source['speaker'], occurred_at=source['occurred_at'], event_labels=source['event_labels'])
                assert identity == source['utterance_id']
        accepted = 0
        for consolidation in rows(U2 / f'raw/main/person{person}/B_R/learn/consolidations.jsonl'):
            if not any(r.get('accepted') for r in consolidation['results']):
                continue
            proposals = (consolidation['proposals'] or {}).get('proposals', [])
            for proposal, result in zip(proposals, consolidation['results']):
                if result['accepted']:
                    with patch('growthlab.state.uuid.uuid4', return_value=SimpleNamespace(hex=result['record_id'])):
                        identity = memory.understandings.propose(proposal)
                        assert identity == result['record_id']
                    accepted += 1
        actual = memory_packet(memory, 'B')
        if compact(actual) != compact(expected):
            raise ValueError('reconstruction_does_not_match_predelete_input')
        return {'person': person, 'utterances': len(expected['utterances']), 'accepted_versions_replayed': accepted,
                'packet_sha256': hashlib.sha256(compact(actual).encode()).hexdigest(), 'exact_predelete_packet_match': True}


def signatures(text):
    return {text.encode(), json.dumps(text, ensure_ascii=False)[1:-1].encode()}


def prepare_person(folder, person, data):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=False)
    path = folder / 'state.sqlite'
    reconstruction = reconstruct(path, person)
    source_map = read(U2 / f'raw/main/person{person}/B_R/learn/learned.json')['source_map']
    erased, texts, directives = set(), [], []
    with Memory(path) as memory:
        original_ids = {r[0] for r in memory.db.execute('SELECT id FROM records')}
        for item_id in data['deleted_ids']:
            roots = {r['utterance_id']: r for r in memory.library.sources()}
            ids = [i for i in source_map[item_id] if roots[i]['speaker'] == 'user']
            if len(ids) != 2:
                raise ValueError('P_requires_two_original_disclosures')
            closure = memory.understandings.deletion_closure(ids)
            for identity in closure:
                body = memory.record(identity)
                texts.extend(body[k] for k in ('utterance_text', 'text', 'reflection_text') if isinstance(body.get(k), str) and body[k])
            result = NonUse(memory).forget(ids, data['topics'][item_id])
            erased.update(result['removed_ids']); directives.append(result['record_id'])
        remaining = {r[0] for r in memory.db.execute('SELECT id FROM records')}
        unrelated = remaining == (original_ids-erased) | set(directives)
        notes = NonUse(memory).active()
        notes_clean = all(text not in n['topic'] for text in texts for n in notes)
        no_edges = not any(identity in erased for r in memory.db.execute('SELECT child,parent FROM deps') for identity in r)
    archive_files = [p for p in folder.glob('state.sqlite*') if p.is_file()]
    raw = b''.join(p.read_bytes() for p in archive_files)
    matches = [hashlib.sha256(t.encode()).hexdigest() for t in set(texts) if any(s in raw for s in signatures(t))]
    report = {'passed': not matches and unrelated and notes_clean and no_edges,
        'deleted_items': data['deleted_ids'], 'removed_record_count': len(erased), 'checked_text_count': len(set(texts)),
        'matched_text_hashes': matches, 'preserved_unrelated_records': unrelated, 'notes_contain_no_deleted_text': notes_clean,
        'removed_ids_not_in_dependencies': no_edges, 'non_use_ids': directives, 'archive_files': [p.name for p in archive_files],
        'scope': 'Canonical post-forgetting SQLite and its journals. Original synthetic scientific evidence is retained separately.'}
    write(folder / 'reconstruction.json', reconstruction); write(folder / 'deletion_bytes.json', report)
    write(folder / 'created.json', {'pid': os.getpid(), 'sha256': sha(path), 'person': person})
    if not report['passed']:
        raise ValueError('deletion_byte_check_failed')


def test_person(folder, prepared, person, data, client):
    prepared = Path(prepared); path = prepared / 'state.sqlite'; created = read(prepared / 'created.json')
    if created['pid'] == os.getpid() or sha(path) != created['sha256']:
        raise ValueError('fresh_unchanged_archive_required')
    before = sha(path)
    try:
        with Memory.readonly(path) as memory:
            mem = {**memory_packet(memory, 'B'), 'do_not_use': NonUse(memory).active()}
            for item in data['items']:
                for case in item['tests']:
                    context = {'person': person, 'item_id': item['id'], 'category': item['category'],
                               'phase': case['phase'], 'deleted': item['id'] in data['deleted_ids']}
                    messages = packet(case, mem); messages[0]['content'] += DIRECTIVE
                    output, meta = client.call(messages, context, schema=decision_schema(case))
                    row = {**context, **score(output, case), 'output': output, 'meta': meta}
                    append(Path(folder) / 'decisions.jsonl', row); client.parsed(row['valid'])
    finally:
        after = sha(path)
        write(Path(folder) / 'storage_hash.json', {'before': before, 'after': after, 'unchanged': before == after,
              'learning_pid': created['pid'], 'testing_pid': os.getpid()})
    if before != after:
        raise ValueError('test_mutated_storage')


def verdict(deleted, retained, *, complete, bytes_pass):
    rate = lambda values, key: sum(v[key] for v in values)/len(values) if values else None
    d, n = rate(deleted, 'correct'), rate(deleted, 'N_correct')
    r, before = rate(retained, 'correct'), rate(retained, 'before_correct')
    d_pass = d is not None and d <= n+.10+1e-12
    r_pass = r is not None and r >= before-.10-1e-12
    return {'passed': complete and bytes_pass and d_pass and r_pass, 'complete': complete, 'bytes_pass': bytes_pass,
            'deleted': {'n': len(deleted), 'correct': sum(v['correct'] for v in deleted), 'rate': d, 'N_rate': n, 'passed': d_pass},
            'retained': {'n': len(retained), 'correct': sum(v['correct'] for v in retained), 'rate': r, 'before_rate': before, 'passed': r_pass}}


def report():
    material = read(MATERIAL); values = []; complete = True; bytes_ok = True
    for person, data in material['people'].items():
        prefix = BASE / f'person{person}'; folder = prefix / 'test'
        current = rows(folder / 'decisions.jsonl')
        expected = {(i['id'], c['phase']): c for i in data['items'] for c in i['tests']}
        complete &= (folder / 'result.json').exists() and read(folder / 'result.json')['status'] == 'complete'
        complete &= len(current) == len(expected) and {(r['item_id'],r['phase']) for r in current} == set(expected)
        bytes_ok &= (prefix / 'prepare/archive/deletion_bytes.json').exists() and read(prefix / 'prepare/archive/deletion_bytes.json')['passed']
        references = {arm: {(r['item_id'],r['phase']): r for r in rows(U2 / f'raw/main/person{person}/{arm}/test/decisions.jsonl')}
                      for arm in ('B_R','B_N')}
        for row in current:
            key = row['item_id'], row['phase']; checked = score(row['output'], expected[key])
            if any(row[k] != checked[k] for k in checked):
                raise ValueError('raw_choice_score_mismatch')
            baseline = {arm: score(references[arm][key]['output'], expected[key])['correct'] for arm in references}
            if any(baseline[arm] != references[arm][key]['correct'] for arm in references):
                raise ValueError('historical_baseline_score_mismatch')
            values.append({**row, 'N_correct': baseline['B_N'], 'before_correct': baseline['B_R']})
    result = verdict([r for r in values if r['deleted']], [r for r in values if not r['deleted']], complete=complete, bytes_pass=bytes_ok)
    result.update(at_utc=utc(), cost_usd=f1_cost(), daily_budget=budget_snapshot(), regraded_decisions=len(values),
                  score_mismatches=0, retained_by_category={c: verdict([], [r for r in values if not r['deleted'] and r['category']==c], complete=False, bytes_pass=bytes_ok)['retained'] for c in ('P','Q','W')})
    write(OUT/'RESULTS.json',result)
    fields=['person','item_id','category','phase','deleted','valid','action','correct','N_correct','before_correct']
    with (OUT/'SUMMARY.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in values)
    export()
    write(OUT/'CLOSE.json',{'at_utc':utc(),'complete':complete,'manifest_sha256':sha(FROZEN),
        'results_sha256':sha(OUT/'RESULTS.json'),'raw_sha256':{p.relative_to(OUT).as_posix():sha(p) for p in (OUT/'raw').rglob('*') if p.is_file()}})
    return result


def export():
    names={'job.json','claim.json','result.json','calls.jsonl','routing.jsonl','model.jsonl','decisions.jsonl',
           'created.json','storage_hash.json','reconstruction.json','deletion_bytes.json'}
    for p in BASE.rglob('*'):
        if p.is_file() and p.name in names:
            dest=OUT/'raw'/p.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)


def worker(jobpath, *, offline=False):
    job=read(jobpath); folder=Path(job['folder'])
    if (folder/'claim.json').exists() or (folder/'result.json').exists(): raise Stop('consumed_worker')
    write(folder/'claim.json',{'pid':os.getpid(),'at_utc':utc(),'job_sha256':sha(jobpath)},exclusive=True)
    result={'status':'running','pid':os.getpid()}
    try:
        if not offline:
            verify(read(FROZEN))
            if job['manifest_sha256'] != sha(FROZEN) or job['data'] != read(MATERIAL)['people'][job['person']]:
                raise Stop('frozen_job_mismatch')
        if job['operation']=='prepare': prepare_person(folder/'archive',job['person'],job['data'])
        else:
            if offline:
                import socket
                socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline_network_disabled'))
                class Fixture:
                    def call(self,messages,context,*,schema):
                        chosen=json.loads(messages[1]['content'])['options'][0]['id']
                        return dict(reason='离线工程样本',interpretation='无',action=chosen,reply='无'), {'offline':True}
                    def parsed(self,valid): assert valid
                client=Fixture()
            else: client=SafeClient(folder,cap=ESTIMATE,base=BASE)
            test_person(folder,job['prepared'],job['person'],job['data'],client)
        result['status']='complete'
    except Exception as error:
        result.update(status='stopped',stop=str(error) if isinstance(error,(ValueError,Stop)) else type(error).__name__)
    finally: write(folder/'result.json',result)


def execute(folder, operation, person, data, **fields):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    job={'folder':str(folder),'operation':operation,'person':person,'data':data,'manifest_sha256':sha(FROZEN),**fields}
    write(folder/'job.json',job,exclusive=True)
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        try:
            subprocess.run([sys.executable,'-m','u3.f1','worker',str(folder/'job.json')],cwd=ROOT,stdout=out,stderr=err,timeout=3700)
        except subprocess.TimeoutExpired:
            write(folder/'result.json',{'status':'stopped','stop':'worker_timeout'})
    if not (folder/'result.json').exists(): write(folder/'result.json',{'status':'stopped','stop':'worker_without_result'})
    result=read(folder/'result.json');export();print(json.dumps({'job':folder.relative_to(BASE).as_posix(),**result}),flush=True)
    return result


def freeze():
    if not (ROOT/'evidence/u3/CLOSE.json').exists(): raise Stop('U3_not_closed')
    if FROZEN.exists(): raise Stop('already_frozen')
    engineering=read(OUT/'ENGINEERING.json')
    source=pins();source['companion/non_use.py']=sha(ROOT/'companion/non_use.py')
    if not engineering['passed'] or engineering['code_sha256']!={k:v for k,v in source.items() if k.endswith('.py')}: raise Stop('engineering_source_mismatch')
    if read(MATERIAL)!=materialize(): raise Stop('F1_material_changed')
    files=[U2/'FROZEN.json',OUT/'ENGINEERING.json',ROOT/'evidence/u3/CLOSE.json']
    for person in materialize()['people']:
        files.extend(U2/p for p in (f'raw/main/person{person}/B_R/test/calls.jsonl',f'raw/main/person{person}/B_R/learn/consolidations.jsonl',f'raw/main/person{person}/B_R/learn/learned.json',f'raw/main/person{person}/B_R/test/decisions.jsonl',f'raw/main/person{person}/B_N/test/decisions.jsonl'))
    write(FROZEN,{'version':'f1-v1','at_utc':utc(),'source_sha256':source,'evidence_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},
        'seed':SEED,'criteria_verbatim':CRITERIA,'estimate_usd':ESTIMATE,'planned_tests':82,'deleted_tests':18,'retained_tests':64,
        'retention_population':'all undeleted test situations; P/Q/W also reported separately','model':'deepseek/deepseek-v4.1-flash','route':'wafer','reasoning':False,
        'new_mechanism':'only a topic-only non-use record and generic instruction; original U2 data and targets unchanged','retry_stop_rules':'U3 single concurrency, same-input network retry once, stop consumed lanes; actual expense including unknown may not exceed estimate without approval.'},exclusive=True)
    print(json.dumps({'frozen_sha256':sha(FROZEN),'budget':budget_snapshot()}))


def run():
    verify(read(FROZEN))
    if budget_snapshot()['remaining_usd']<ESTIMATE: raise Stop('daily_balance_insufficient')
    BASE.mkdir(parents=True,exist_ok=True);write(BASE/'run.claim',{'at_utc':utc(),'manifest_sha256':sha(FROZEN),'budget':budget_snapshot()},exclusive=True)
    write(OUT/'START.json',read(BASE/'run.claim'),exclusive=True)
    try:
        for person,data in read(MATERIAL)['people'].items():
            prefix=BASE/f'person{person}'
            ready=execute(prefix/'prepare','prepare',person,data)
            if ready['status']!='complete': continue
            result=execute(prefix/'test','test',person,data,prepared=str(prefix/'prepare/archive'))
            if result.get('stop') in ('actual_exceeded_estimate','estimate_reservation_stop','daily_budget_stop','operator_stop','ac_required'): break
    finally: report()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('prepare','freeze','run','worker','offline-worker','report'));parser.add_argument('path',nargs='?');args=parser.parse_args()
    if args.command=='prepare': write(MATERIAL,materialize(),exclusive=True)
    elif args.command in ('worker','offline-worker'): worker(args.path,offline=args.command=='offline-worker')
    else: {'freeze':freeze,'run':run,'report':report}[args.command]()
