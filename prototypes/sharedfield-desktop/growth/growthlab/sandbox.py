"""Closed AST v2, never Python eval/exec. One worker per outer call.
Parent owns versions, observations, actions, call stack and shared budgets.
This is a closed-language boundary, not an OS sandbox for arbitrary Python.
"""
import ast
import hashlib
import multiprocessing as mp
import time


class Denied(ValueError): pass


def parse(source, *, condition=False):
    if type(source) is not str or len(source.encode()) > 8192: raise Denied('source_size')
    try: tree = ast.parse(source, mode='eval' if condition else 'exec')
    except (SyntaxError, RecursionError): raise Denied('syntax') from None
    nodes = list(ast.walk(tree))
    if len(nodes) > 512: raise Denied('node_limit')
    allowed = (ast.Module, ast.Expression, ast.Expr, ast.Call, ast.Name, ast.Load, ast.Store,
               ast.Constant, ast.If, ast.While, ast.For, ast.Compare, ast.Eq, ast.NotEq,
               ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not)
    calls = ('seen', 'count', 'need') if condition else ('act', 'goto', 'observe', 'seen', 'count', 'need', 'range', 'run')
    for node in nodes:
        if not isinstance(node, allowed): raise Denied('syntax_denied')
        if isinstance(node, ast.Constant) and (type(node.value) not in (str, int, bool) or len(str(node.value)) > 128): raise Denied('literal_denied')
        if isinstance(node, ast.Name) and node.id not in (*calls, '_'): raise Denied('name_denied')
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in calls or node.keywords: raise Denied('call_denied')
            argc = 0 if node.func.id == 'observe' else 1
            if len(node.args) != argc or any(not isinstance(x, ast.Constant) for x in node.args): raise Denied('argument_denied')
            if argc:
                arg = node.args[0].value
                if node.func.id == 'range':
                    if type(arg) is not int or not 0 <= arg <= 32: raise Denied('loop_limit')
                elif type(arg) is not str: raise Denied('argument_denied')
        if isinstance(node, ast.For) and (not isinstance(node.target, ast.Name) or node.target.id != '_' or
            not isinstance(node.iter, ast.Call) or node.iter.func.id != 'range' or node.orelse): raise Denied('loop_denied')
        if isinstance(node, ast.While) and node.orelse: raise Denied('loop_denied')
    return tree


def evaluate(node, call):
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.Call): return call(node.func.id, node.args[0].value if node.args else None)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And): return all(evaluate(x, call) for x in node.values)
        return any(evaluate(x, call) for x in node.values)
    if isinstance(node, ast.UnaryOp): return not evaluate(node.operand, call)
    if isinstance(node, ast.Compare):
        left = evaluate(node.left, call)
        for op, other in zip(node.ops, node.comparators):
            right = evaluate(other, call)
            if not {ast.Eq: lambda: left == right, ast.NotEq: lambda: left != right,
                    ast.Lt: lambda: left < right, ast.LtE: lambda: left <= right,
                    ast.Gt: lambda: left > right, ast.GtE: lambda: left >= right}[type(op)](): return False
            left = right
        return True
    raise Denied('expression_denied')


def read_value(obs, op, arg):
    if op == 'observe': return obs
    if op == 'seen': return any(c['material'] == arg or c['entity'] == arg for c in obs['cells'])
    if op == 'count': return obs['inventory'].get(arg, 0)
    if op == 'need': return obs['needs'].get(arg, 0)
    raise Denied('query_denied')


def completed(condition, obs):
    value = evaluate(parse(condition, condition=True).body, lambda op, arg: read_value(obs, op, arg))
    if type(value) is not bool: raise Denied('completion_must_be_boolean')
    return value


def references(source):
    return {n.args[0].value for n in ast.walk(parse(source)) if isinstance(n, ast.Call) and n.func.id == 'run'}


def validate_graph(library):
    def walk(name, stack):
        if name in stack: raise Denied('recursive_skill')
        if len(stack) >= 3: raise Denied('depth_limit')
        if name not in library: raise Denied('missing_skill')
        for child in references(library[name]['source']): walk(child, [*stack, name])
    for name in library: walk(name, [])


def worker(pipe, source):
    def rpc(op, arg=None):
        pipe.send((op, arg)); reply = pipe.recv()
        if reply[0] != 'ok': raise Denied('rpc_denied')
        return reply[1]
    def call(op, arg):
        if op == 'range': return range(arg)
        if op in ('act', 'goto'): return rpc(op, arg)
        if op == 'run':
            child = rpc('begin', arg)
            if not child['skip']:
                block(parse(child['source']).body); rpc('end')
            return None
        return read_value(rpc('observe'), op, arg)
    def block(nodes):
        for node in nodes:
            if isinstance(node, ast.Expr): evaluate(node.value, call)
            elif isinstance(node, ast.If): block(node.body if evaluate(node.test, call) else node.orelse)
            elif isinstance(node, ast.While):
                while evaluate(node.test, call): block(node.body)
            elif isinstance(node, ast.For):
                for _ in evaluate(node.iter, call): block(node.body)
            else: raise Denied('statement_denied')
    try:
        block(parse(source).body); pipe.send(('finished', None))
    except Exception: pipe.send(('denied', 'program_rejected'))
    finally: pipe.close()


def run(source, observe, act, *, max_steps=32, timeout_s=2., cancel=None,
        library=None, name=None, completion=None, on_step=None):
    start = time.perf_counter(); steps = 0; stack = []; calls = []; navigation = []
    record = {'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'steps': 0}
    resolve = (lambda n: library.current()[n]) if hasattr(library, 'current') else (lambda n: (library or {})[n])
    def begin(skill_name, skill):
        if skill_name in [c['name'] for c in stack]: raise Denied('recursive_skill')
        if len(stack) >= 3: raise Denied('depth_limit')
        parse(skill['source'])
        skip = completed(skill['completion'], observe()) if skill.get('completion') else False
        entry = {'name': skill_name, 'version': skill.get('version'), 'record_id': skill.get('id'),
                 'depth': len(stack)+1, 'start_step': steps, 'start_s': time.perf_counter()-start,
                 'completion': skill.get('completion'), 'outcome': 'not_needed' if skip else None}
        calls.append(entry)
        if skip: entry.update(steps=0, seconds=0.)
        else: stack.append(entry)
        return skip
    def end(outcome_status):
        entry = stack.pop()
        try: achieved = completed(entry['completion'], observe()) if entry['completion'] else False
        except (ValueError, TypeError): achieved = False
        entry.update(outcome=('success' if achieved else 'unsuccessful'),
                     execution_status=outcome_status, steps=steps-entry['start_step'],
                     seconds=time.perf_counter()-start-entry['start_s'])
    try:
        parse(source)
        if name:
            skill = resolve(name); source = skill['source']; record['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        else: skill = {'source': source, 'completion': completion, 'version': None}
        if begin(name or '<inline>', skill):
            return dict(record, status='not_needed', reason=None, calls=calls, seconds=time.perf_counter()-start)
    except (Denied, KeyError, TypeError) as error:
        return dict(record, status='denied', reason=str(error) if isinstance(error, Denied) else 'missing_or_invalid_skill', calls=calls, seconds=time.perf_counter()-start)
    ctx = mp.get_context('spawn'); parent, child = ctx.Pipe()
    process = ctx.Process(target=worker, args=(child, source), daemon=True); process.start(); child.close()
    status, reason = 'timeout', 'wall_clock_limit'
    try:
        while time.perf_counter()-start < timeout_s:
            if cancel is not None and cancel.is_set(): status, reason = 'cancelled', 'owner_takeover'; break
            if not parent.poll(min(.02, max(0, timeout_s-(time.perf_counter()-start)))):
                if not process.is_alive(): status, reason = 'denied', 'worker_exit'; break
                continue
            op, arg = parent.recv()
            if op == 'finished': status, reason = 'completed', None; break
            if op == 'denied': status, reason = 'denied', 'program_rejected'; break
            if op == 'observe': parent.send(('ok', observe()))
            elif op == 'begin':
                skill = resolve(arg); skip = begin(arg, skill)
                parent.send(('ok', {'skip': skip, 'source': skill['source']}))
            elif op == 'end':
                if len(stack) <= 1: raise Denied('call_stack')
                end('completed'); parent.send(('ok', None))
            elif op == 'act':
                if steps >= max_steps: status, reason = 'step_limit', 'environment_step_limit'; break
                before = observe()
                if before['done']: status, reason = 'episode_finished', 'episode_finished'; break
                result = act(arg); steps += 1
                if on_step: on_step(before, result, arg)
                if result['needs']['health'] < before['needs']['health']:
                    status, reason = 'injured', 'health_lost'; break
                parent.send(('ok', result))
            elif op == 'goto':
                from .navigation import goto
                result = goto(arg, observe, act, max_steps=max_steps-steps,
                              deadline=start+timeout_s, cancel=cancel, on_step=on_step)
                steps += result['steps']; navigation.append(result)
                if result['status'] != 'arrived':
                    status, reason = result['status'], result['reason']; break
                parent.send(('ok', result))
            else: raise Denied('protocol_denied')
    except (KeyError, ValueError, TypeError) as error:
        status, reason = 'denied', str(error) if isinstance(error, Denied) else 'action_or_skill_denied'
    except (EOFError, BrokenPipeError): status, reason = 'denied', 'worker_disconnected'
    finally:
        if process.is_alive(): process.terminate()
        process.join(timeout=2); parent.close()
        while stack: end(status)
    return dict(record, status=status, reason=reason, steps=steps, calls=calls, navigation=navigation, seconds=time.perf_counter()-start)
