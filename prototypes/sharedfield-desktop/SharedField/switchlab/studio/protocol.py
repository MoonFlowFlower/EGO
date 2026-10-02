"""Strict, intentionally small action contract. Text does not create authority."""
from __future__ import annotations
import json
from switchlab.world import ACTIONS

TOOLS = ('draft', 'inspect', 'lab_step', 'lab_action', 'lab_think', 'consolidate', 'ask')
STRATEGIES = ('outline', 'compare', 'direct')
MAX_TEXT = 12000


def text(value, name='text', maximum=MAX_TEXT, allow_empty=False):
    if not isinstance(value, str) or len(value) > maximum or ('\x00' in value):
        raise ValueError(f'{name}: invalid string or exceeds {maximum} characters')
    if not allow_empty and not value.strip():
        raise ValueError(f'{name}: must not be empty')
    return value.strip()


def obj(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError('unexpected or missing object fields')
    return value


def arr(value, maximum, name='list'):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f'{name}: list bound {maximum}')
    return value


def parse_json(raw, max_chars=50000):
    raw = text(raw, 'JSON input', max_chars)
    if raw.startswith('```') and raw.endswith('```'):
        if '\n' not in raw: raise ValueError('malformed fenced JSON')
        raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result: raise ValueError('duplicate JSON key')
            result[k] = v
        return result
    def reject(x): raise ValueError('non-finite JSON number')
    try: data = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    except (json.JSONDecodeError, RecursionError) as exc: raise ValueError('model must return one complete JSON object') from exc
    if not isinstance(data, dict): raise ValueError('model must return an object')
    return data


def basis(value, evidence):
    refs = arr(value, 8, 'basis')
    if not refs or any(not isinstance(r, str) or r not in evidence for r in refs):
        raise ValueError('unknown/missing evidence ID; a model cannot invent observations')
    return list(dict.fromkeys(refs))


def steps(value):
    out = []
    for s in arr(value, 6, 'steps'):
        obj(s, ('tool', 'instruction', 'action'), ('tool', 'instruction'))
        if s['tool'] not in TOOLS: raise ValueError('unauthorized tool')
        clean = {'tool':s['tool'], 'instruction':text(s['instruction'], 'instruction', 2500)}
        if s['tool'] == 'lab_action':
            if s.get('action') not in ACTIONS: raise ValueError('unknown sandbox action')
            clean['action'] = s['action']
        elif 'action' in s: raise ValueError('action only belongs to lab_action')
        out.append(clean)
    if not out: raise ValueError('a goal needs a finite plan')
    return out


def turn_packet(value, evidence, goals):
    obj(value, ('speech', 'memories', 'goals', 'revisions'), ('speech',))
    clean = {'speech':text(value['speech'], 'speech', 8000, True), 'memories':[], 'goals':[], 'revisions':[]}
    for m in arr(value.get('memories', []), 5, 'memories'):
        obj(m, ('kind','key','text','basis'), ('kind','key','text','basis'))
        if m['kind'] not in ('reported','preference','hypothesis'): raise ValueError('memory kind is not authority')
        clean['memories'].append({'kind':m['kind'], 'key':text(m['key'],'key',120),
             'text':text(m['text'],'memory',1600),'basis':basis(m['basis'],evidence)})
    for g in arr(value.get('goals', []), 3, 'goals'):
        obj(g, ('title','reason','success','basis','steps'), ('title','reason','success','basis','steps'))
        clean['goals'].append({'title':text(g['title'],'title',160),'reason':text(g['reason'],'reason',1000),
          'success':text(g['success'],'success',1200),'basis':basis(g['basis'],evidence),'steps':steps(g['steps'])})
    seen = set()
    for r in arr(value.get('revisions', []), 4, 'revisions'):
        obj(r, ('goal_id','action','reason','basis','steps'), ('goal_id','action','reason','basis'))
        if r['goal_id'] not in goals or r['goal_id'] in seen: raise ValueError('unknown/duplicate revised goal')
        seen.add(r['goal_id'])
        if r['action'] not in ('cancel','revise','resume','pause'): raise ValueError('model cannot declare human success')
        x = {'goal_id':r['goal_id'],'action':r['action'],'reason':text(r['reason'],'reason',1000),
             'basis':basis(r['basis'],evidence)}
        if r['action'] == 'revise': x['steps'] = steps(r.get('steps'))
        elif 'steps' in r: raise ValueError('only revise accepts steps')
        clean['revisions'].append(x)
    return clean


SYSTEM = '''你是 SwitchLab Studio 中的语言推理模块，不是整个系统。用自然中文合作、交流与提出可执行假设。不要扮演有主观感受的人，不用人格台词冒充机制。不需要自称机械，也不刻意反对。用户审美是偏好；用户事实陈述是有来源的陈述；赞同、压力和重复不是新物理证据。可靠新证据应改变判断。
你只得到公共观测和历史。不要虚构看过网页、操作了电脑或已完成工具工作。你的输出是候选，实际执行结果由内核另行记录。不得请求 shell、网络搜索、发送消息、任意文件路径、外部权限。允许工具只作用于本地工作区和数值玩具世界。对现实中的事实不确定要说明；这里没有联网查证。
持续目标可以来自用户承诺、已有目标的障碍、真实实验异常；不是每句聊天都创建目标，不是空闲就找事，不要把用户的随口感慨改成自动任务。普通讨论可以只 speech，不必规划。目标要具体、有成功条件、有有限计划；缺少真正必要的信息可 ask 然后等待。一个草稿需要用户验收，不可自封成功。不要输出私有逐步思维链，仅给简短决定理由、可检查假设和结果。
记录记忆时必须指向本次上下文中的真实 evidence ID；模型记忆摘要只是 unverified 表达。不同陈述可能是变更或冲突，保留来源，不改写历史。禁止把模拟或重复回放当成新观测。
永远输出一个完整 JSON 对象，无 Markdown 包裹、无额外字段。'''

TURN_FORMAT = '''本轮输出结构：
{"speech":"对用户的自然回复；尚未执行的只能说计划，不能说已经完成", "memories":[{"kind":"reported|preference|hypothesis", "key":"稳定的主题键", "text":"短内容", "basis":["E000001"]}], "goals":[{"title":"新的持久目标", "reason":"为什么现在值得做", "success":"如何验收", "basis":["E000001"], "steps":[{"tool":"draft", "instruction":"要生成什么"}]}], "revisions":[{"goal_id":"G0001", "action":"revise", "reason":"修改依据", "basis":["E000002"], "steps":[{"tool":"draft", "instruction":"修订工作"}]}]}
通常只需要 speech，其余列表可为空。不得重复创建上下文已有目标，变更已有目标用 revisions。action 可为 cancel/revise/resume/pause，只有 revise 带 steps。speech 8000字以内；新目标最多3个、每目标最多6步。
可用 step.tool：draft（生成并保存真实草稿，最后等待用户验收）、inspect（读取当前工作区）、lab_step（数值控制器实际执行一步）、lab_action（在玩具世界执行指定 action）、lab_think（仅规划，不伪造观测）、consolidate（重建经验统计，不升级真值）、ask（向用户提问并停止）。lab_action 另有 action 字段：e0/e1/c0/c1/hand_energy/hand_coolant/work/probe_e/probe_c/calibrate/repair/wait/noise。其他 step 不带 action 字段。新目标只能使用这些工具，不得发明工具。一般自然语言任务使用 draft 或 ask。真实世界行动只能提出建议，不能声称已做。'''

WORK_FORMAT = '''执行当前已采纳目标的一个语言步骤。你要产出的内容将由内核写入本地草稿或显示为问题，不是外部行动。结合已有约束、可见旧稿、验收失败原因和实际工具观测，不要忽略此前条件。执行 job.strategy 对应的方法：outline=先组织结构再补内容；compare=先比较竞争选项与反例再选择；direct=直接完成当前交付。它是由过往验收选择的工作方法，不是成功保证；任务约束始终优先。不需再生成目标。只输出 {"content":"完整内容"}。draft 要给真正可阅读的交付，不是说你将会去写。ask 要给一个必要问题。不要宣称经过未执行的测试。'''
