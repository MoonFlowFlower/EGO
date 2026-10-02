#!/usr/bin/env python3
"""Portable entrypoint. Studio language transport is opt-in; old lab stays offline."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
if sys.version_info<(3,10):raise SystemExit('Python 3.10 or newer is required.')
import argparse
import json
import time
import tempfile
import sqlite3
from switchlab.runtime import Session,save_json,load_json,verify_trace
from switchlab.world import Config
from switchlab.agent import AgentConfig,POLICIES,ABLATIONS


def export_run(s,out):
    from switchlab.reports import session_report
    out=Path(out);trace=s.export_trace()
    save_json(out/'trace.json',trace);save_json(out/'checkpoint.json',s.checkpoint())
    verification=verify_trace(trace);save_json(out/'verification.json',verification)
    session_report(trace,out/'report.html')
    summary={'steps':s.world.observe()['tick'],'return':s.world.total_reward,
             'completed':s.world.observe()['completed'],'missed':s.world.observe()['missed'],
             'memory_events':len(s.agent.memory),'goals_adopted':s.agent.goal_counter,
             'trace_verified':verification['semantic_replay'],'output':str(out.resolve()),
             'mechanism_status':'NOT_ESTABLISHED'}
    save_json(out/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))


def main(argv=None):
    parser=argparse.ArgumentParser(description='SwitchLab offline persistent adaptive-control experiment')
    sub=parser.add_subparsers(dest='command')
    for command in ('run','serve'):
        p=sub.add_parser(command)
        p.add_argument('--seed',type=int,default=41);p.add_argument('--steps',type=int,default=96)
        p.add_argument('--scenario',choices=('standard','quiet','stress'),default='standard')
        p.add_argument('--policy',choices=POLICIES,default='candidate')
        p.add_argument('--planner',choices=('rollout','two_step'),default='rollout')
        p.add_argument('--ablation',choices=ABLATIONS,default='none')
        if command=='run':p.add_argument('--out',default=str(ROOT/'outputs'/'run'))
        else:
            p.add_argument('--port',type=int,default=8765);p.add_argument('--no-browser',action='store_true')
            p.add_argument('--resume')
    p=sub.add_parser('verify');p.add_argument('artifact')
    p=sub.add_parser('resume');p.add_argument('checkpoint');p.add_argument('--steps',type=int,default=12)
    p.add_argument('--out',default=str(ROOT/'outputs'/'resumed'))
    p=sub.add_parser('benchmark');p.add_argument('--seeds',type=int,default=8)
    p.add_argument('--stress-seeds',type=int,default=4);p.add_argument('--jobs',type=int,default=1)
    p.add_argument('--steps',type=int,default=96);p.add_argument('--out',default=str(ROOT/'outputs'/'benchmark'))
    p=sub.add_parser('test');p.add_argument('--out',default=str(ROOT/'outputs'/'tests'))
    p=sub.add_parser('studio',help='local persistent language workbench')
    p.add_argument('--port',type=int,default=8771);p.add_argument('--no-browser',action='store_true')
    p.add_argument('--data-dir',default=str(ROOT/'user_data'/'adaptive'))
    p=sub.add_parser('studio-verify',help='recompute downstream state from recorded language inputs')
    p.add_argument('checkpoint')
    p=sub.add_parser('studio-import',help='validate and import into an EMPTY data directory')
    p.add_argument('checkpoint');p.add_argument('--data-dir',required=True)
    p=sub.add_parser('studio-migrate-v02',help='verify old data with original code; import historical context into a NEW directory')
    p.add_argument('checkpoint');p.add_argument('--data-dir',required=True)
    p=sub.add_parser('cognitive-benchmark',help='bounded synthetic online learning and causal-history probes; no model API')
    p.add_argument('--seeds',type=int,default=4);p.add_argument('--training',type=int,default=160)
    p.add_argument('--testing',type=int,default=64);p.add_argument('--out',default=str(ROOT/'outputs'/'cognitive_benchmark'))
    p=sub.add_parser('shared',help='shared exploration and source-grounded self reports')
    p.add_argument('--port',type=int,default=8773);p.add_argument('--no-browser',action='store_true')
    p.add_argument('--data-dir',default=str(ROOT/'user_data'/'shared'))
    p=sub.add_parser('shared-verify',help='recompute shared environment and cognitive state from recorded inputs')
    p.add_argument('checkpoint')
    p=sub.add_parser('shared-import',help='restore same-version shared state into a NEW directory')
    p.add_argument('checkpoint');p.add_argument('--data-dir',required=True)
    p=sub.add_parser('memory',help='persistent memory + oral commitments + in-app prospective cognition')
    p.add_argument('--port',type=int,default=8774);p.add_argument('--no-browser',action='store_true')
    p.add_argument('--data-dir',default=str(ROOT/'user_data'/'memory'))
    p=sub.add_parser('memory-verify',help='recompute recorded inputs with the current or frozen legacy runtime');p.add_argument('checkpoint')
    p=sub.add_parser('memory-import',help='import into a NEW memory directory');p.add_argument('checkpoint');p.add_argument('--data-dir',required=True)
    p=sub.add_parser('memory-restore',help='restore a same-version SQLite backup into a NEW directory');p.add_argument('backup');p.add_argument('--data-dir',required=True)
    args=parser.parse_args(argv if argv is not None else (sys.argv[1:] or ['memory']))
    try:
        if args.command=='memory':
            from switchlab.memory.http import serve as memory_serve
            memory_serve(args.data_dir,args.port,not args.no_browser)
        elif args.command=='memory-verify':
            from switchlab.memory.store import MemoryStore
            data=load_json(args.checkpoint)
            if data.get('schema')=='sharedfield.memory.v6':
                from switchlab.memory.store import code_fingerprint
                if data.get('initial',{}).get('source_sha256')!=code_fingerprint():
                    from switchlab.memory.migration_v06 import verify_v06
                    verified=verify_v06(data)
                    print(json.dumps({k:v for k,v in verified.items() if k!='projection'},ensure_ascii=False,indent=2))
                    return 0
                with tempfile.TemporaryDirectory(prefix='memory_verify_') as t:
                    c=MemoryStore.from_export(Path(t)/'memory.sqlite3',data)
                    try:r={'recorded_input_replay':True,'journal_events':len(data['journal']),'person_id':c.person_id,'projection_sha256':c.projection_digest(),
                           'privacy_checkpoint':bool(c._meta('initial').get('privacy_projection')),'language_rerun':False}
                    finally:c.close()
            else:
                from switchlab.memory.migration import verify_legacy
                r=verify_legacy(data)['report']
            print(json.dumps(r,ensure_ascii=False,indent=2))
        elif args.command=='memory-import':
            from switchlab.memory.service import MemoryService
            target=Path(args.data_dir)
            if (target/'memory.sqlite3').exists():raise ValueError('不能覆盖已有记忆目录')
            service=MemoryService(target)
            try:r=service.import_checkpoint(load_json(args.checkpoint))
            finally:service.close()
            print(json.dumps(r,ensure_ascii=False,indent=2))
        elif args.command=='memory-restore':
            from switchlab.memory.store import MemoryStore
            from switchlab.studio.service import DirectoryLock
            target=Path(args.data_dir);target.mkdir(parents=True,exist_ok=True);lock=DirectoryLock(target)
            try:
                if (target/'memory.sqlite3').exists():raise ValueError('不能覆盖已有记忆目录')
                if not Path(args.backup).is_file():raise ValueError('找不到备份文件')
                from switchlab.memory.migration import restore_sqlite_backup
                restore_sqlite_backup(args.backup,target/'memory.sqlite3')
            finally:lock.close()
            print('Restored into new directory; execution paused: '+str(target.resolve()))
        elif args.command=='shared':
            from switchlab.shared.http import serve as shared_serve
            shared_serve(args.data_dir,args.port,not args.no_browser)
        elif args.command in ('shared-verify','shared-import'):
            from switchlab.shared.core import SharedCore
            data=load_json(args.checkpoint)
            c=SharedCore.from_v04(data) if data.get('schema')=='switchlab.shared.v4' else SharedCore.restore(data)
            if args.command=='shared-import':
                from switchlab.studio.service import DirectoryLock
                target=Path(args.data_dir);target.mkdir(parents=True,exist_ok=True);lock=DirectoryLock(target)
                try:
                    if (target/'session.json').exists():raise ValueError('目标目录已有个体，不覆盖；请选择新目录。')
                    save_json(target/'session.json',c.checkpoint())
                finally:lock.close()
            print(json.dumps({'recorded_input_replay':True,'events':len(c.events),'world_tick':c.world.tick,
                'learned_events':c.mind.learned_events,'remote_model_rerun':False,
                'origin_version':data['metadata']['version'],
                'numeric_comparison':'finite JSON numbers at 12 decimals; integer float equivalence, original v04 hash strings checked',
                'scope':'bounded local record replay; not sentience or semantic quality evidence'},ensure_ascii=False,indent=2))
        elif args.command=='studio':
            from switchlab.studio.http import serve as studio_serve
            studio_serve(args.data_dir,args.port,not args.no_browser)
        elif args.command=='studio-migrate-v02':
            from switchlab.studio.migration import migrate_v02
            print(json.dumps(migrate_v02(args.checkpoint,args.data_dir),ensure_ascii=False,indent=2))
        elif args.command=='cognitive-benchmark':
            from switchlab.studio.experiments import run_all
            print(json.dumps(run_all(args.out,args.seeds,args.training,args.testing),ensure_ascii=False,indent=2))
        elif args.command=='studio-verify':
            from switchlab.studio.core import Core
            data=load_json(args.checkpoint)
            from switchlab.studio.adaptive_core import AdaptiveCore
            c=(AdaptiveCore if data.get('schema')=='switchlab.studio.v3' else Core).restore(data)
            print(json.dumps({'recorded_input_replay':True,'remote_model_rerun':False,
                  'events':len(c.events),'goals':len(c.state['goals']),'artifacts':len(c.state['artifacts']),
                  'head':c.head,'scope':'recorded language inputs; not proof of model authorship or content truth'},ensure_ascii=False,indent=2))
        elif args.command=='studio-import':
            from switchlab.studio.core import Core
            from switchlab.studio.service import DirectoryLock
            data=load_json(args.checkpoint)
            from switchlab.studio.adaptive_core import AdaptiveCore
            if data.get('schema')!='switchlab.studio.v3':raise ValueError('v0.2 requires studio-migrate-v02 into a NEW directory; default runtime is v0.3')
            c=AdaptiveCore.restore(data);directory=Path(args.data_dir)
            directory.mkdir(parents=True,exist_ok=True);lock=DirectoryLock(directory)
            try:
                target=directory/'session.json'
                if target.exists():raise ValueError('data directory already contains a life; select a new directory')
                save_json(target,c.checkpoint())
            finally:lock.close()
            print('Imported, initially paused: '+str(directory.resolve()))
        elif args.command in ('run','serve'):
            if args.command=='serve' and args.resume:s=Session.from_checkpoint(load_json(args.resume))
            else:s=Session(Config(seed=args.seed,horizon=args.steps,scenario=args.scenario),
                           AgentConfig(policy=args.policy,ablation=args.ablation,planner=args.planner))
            if args.command=='serve':
                from switchlab.server import serve
                serve(s,args.port,not args.no_browser)
            else:
                for _ in range(args.steps):s.step()
                export_run(s,args.out)
        elif args.command=='verify':
            data=load_json(args.artifact)
            trace=data['trace'] if data.get('schema')=='switchlab.checkpoint.v1' else data
            print(json.dumps(verify_trace(trace),ensure_ascii=False,indent=2))
        elif args.command=='resume':
            if not 0<=args.steps<=2000:raise ValueError('resume steps must be 0..2000')
            s=Session.from_checkpoint(load_json(args.checkpoint))
            for _ in range(min(args.steps,s.world.config.horizon-s.world.observe()['tick'])):s.step()
            export_run(s,args.out)
        elif args.command=='benchmark':
            from switchlab.experiments import run_benchmark
            def progress(n,total,row):
                if n==1 or n%16==0 or n==total:print(f'{n}/{total} independent life-method runs completed',flush=True)
            summary=run_benchmark(args.out,args.seeds,args.stress_seeds,args.jobs,args.steps,progress)
            print('Evidence saved:',Path(args.out).resolve());print('Mechanism status:',summary['mechanism_status'])
        elif args.command=='test':
            import unittest
            start=time.perf_counter();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
            result=unittest.TextTestRunner(verbosity=2).run(suite)
            summary={'tests_run':result.testsRun,'failures':[str(t) for t,_ in result.failures],
                     'errors':[str(t) for t,_ in result.errors],'skipped':[str(t) for t,_ in result.skipped],
                     'successful':result.wasSuccessful(),'seconds':time.perf_counter()-start,
                     'python':sys.version,'scope':'engineering tests, not mechanism validation'}
            save_json(Path(args.out)/'result.json',summary)
            return 0 if result.wasSuccessful() else 1
        else:parser.print_help();return 2
        return 0
    except (ValueError,KeyError,TypeError,OSError,sqlite3.Error) as error:
        print('ERROR:',str(error),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
