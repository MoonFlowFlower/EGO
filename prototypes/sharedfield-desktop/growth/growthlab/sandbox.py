"""Closed AST language, NOT Python exec with a blacklist.

Untrusted source is data interpreted in a disposable process. No imports,
attributes, subscripts, user variables, definitions or arbitrary call targets.
Only act(str), observe(), seen(str), count(str), need(str), comparisons,
if, while and for _ in range(literal up to 32). Source never enters eval/exec.
"""
import ast
import hashlib
import multiprocessing as mp
import time


class Denied(Exception): pass


def parse(source):
    if type(source) is not str or len(source.encode()) > 8192: raise Denied('source_size')
    try: tree = ast.parse(source)
    except (SyntaxError, RecursionError): raise Denied('syntax')
    nodes=list(ast.walk(tree))
    if len(nodes)>512: raise Denied('node_limit')
    allowed=(ast.Module,ast.Expr,ast.Call,ast.Name,ast.Load,ast.Store,ast.Constant,
             ast.If,ast.While,ast.For,ast.Compare,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE)
    for n in nodes:
        if not isinstance(n,allowed): raise Denied('syntax_denied')
        if isinstance(n,ast.Constant) and (type(n.value) not in (str,int,bool) or len(str(n.value))>128): raise Denied('literal_denied')
        if isinstance(n,ast.Name) and n.id not in ('act','observe','seen','count','need','range','_'): raise Denied('name_denied')
        if isinstance(n,ast.Call):
            if not isinstance(n.func,ast.Name) or n.func.id not in ('act','observe','seen','count','need','range') or n.keywords: raise Denied('call_denied')
            argc=0 if n.func.id=='observe' else 1
            if len(n.args)!=argc or any(not isinstance(x,ast.Constant) for x in n.args): raise Denied('argument_denied')
            if argc:
                value=n.args[0].value
                if n.func.id=='range':
                    if type(value) is not int or not 0<=value<=32: raise Denied('loop_limit')
                elif type(value) is not str: raise Denied('argument_denied')
        if isinstance(n,ast.For) and (not isinstance(n.target,ast.Name) or n.target.id!='_' or
            not isinstance(n.iter,ast.Call) or not isinstance(n.iter.func,ast.Name) or n.iter.func.id!='range' or n.orelse): raise Denied('loop_denied')
        if isinstance(n,ast.While) and n.orelse: raise Denied('loop_denied')
    return tree


def worker(pipe,source):
    # No Python execution of source. Interpreter operations below are exhaustive.
    def rpc(op,arg=None):
        pipe.send((op,arg)); reply=pipe.recv()
        if reply[0]!='ok': raise Denied(reply[1])
        return reply[1]
    def value(n):
        if isinstance(n,ast.Constant): return n.value
        if isinstance(n,ast.Call):
            op=n.func.id; arg=n.args[0].value if n.args else None
            if op=='range': return range(arg)
            if op=='act': return rpc('act',arg)
            obs=rpc('observe')
            if op=='observe': return obs
            if op=='seen': return any(c['material']==arg or c['entity']==arg for c in obs['cells'])
            if op=='count': return obs['inventory'].get(arg,0)
            if op=='need': return obs['needs'].get(arg,0)
        if isinstance(n,ast.Compare):
            values=[value(n.left)]+[value(x) for x in n.comparators]
            for a,b,op in zip(values,values[1:],n.ops):
                if not {ast.Eq:lambda:a==b,ast.NotEq:lambda:a!=b,ast.Lt:lambda:a<b,
                        ast.LtE:lambda:a<=b,ast.Gt:lambda:a>b,ast.GtE:lambda:a>=b}[type(op)](): return False
            return True
        raise Denied('expression_denied')
    def block(nodes):
        for n in nodes:
            if isinstance(n,ast.Expr): value(n.value)
            elif isinstance(n,ast.If): block(n.body if value(n.test) else n.orelse)
            elif isinstance(n,ast.While):
                while value(n.test): block(n.body)
            elif isinstance(n,ast.For):
                for _ in value(n.iter): block(n.body)
            else: raise Denied('statement_denied')
    try:
        block(parse(source).body); pipe.send(('finished',None))
    except Exception:
        pipe.send(('denied','program_rejected'))
    finally: pipe.close()


def run(source, observe, act, *, max_steps=32, timeout_s=2.):
    start=time.perf_counter(); steps=0
    record={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'steps':0}
    try: parse(source)
    except Denied as e:
        return dict(record,status='denied',reason=str(e),seconds=time.perf_counter()-start)
    ctx=mp.get_context('spawn'); parent,child=ctx.Pipe()
    p=ctx.Process(target=worker,args=(child,source),daemon=True); p.start(); child.close()
    status='timeout'; reason='wall_clock_limit'
    try:
        while time.perf_counter()-start < timeout_s:
            if not parent.poll(min(.02,max(0,timeout_s-(time.perf_counter()-start)))):
                if not p.is_alive(): status,reason='denied','worker_exit'; break
                continue
            op,arg=parent.recv()
            if op=='finished': status,reason='completed',None; break
            if op=='denied': status,reason='denied','program_rejected'; break
            if op=='observe': parent.send(('ok',observe()))
            elif op=='act':
                if steps>=max_steps: status,reason='step_limit','environment_step_limit'; break
                try: result=act(arg)
                except ValueError: status,reason='denied','action_denied_or_episode_finished'; break
                steps+=1; parent.send(('ok',result))
            else: status,reason='denied','protocol_denied'; break
    except (EOFError,BrokenPipeError): status,reason='denied','worker_disconnected'
    finally:
        if p.is_alive(): p.terminate()
        p.join(timeout=2); parent.close()
    return dict(record,status=status,reason=reason,steps=steps,seconds=time.perf_counter()-start)
