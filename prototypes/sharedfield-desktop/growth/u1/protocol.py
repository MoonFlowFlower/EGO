"""Public decision/consolidation protocols; no fixture answers in prompts."""
import json
from datetime import datetime

from growthlab.memory import rank
from .conventions import normalize

MEMORY_LIMIT = 2048  # Serialized UTF-8 bytes, conservative upper bound in tokens.
DECISION_ORDER = ['reason', 'interpretation', 'action', 'reply']
DECISION_SYSTEM = '''你是一个与用户聊天的助手。请根据当前说的话、给定上下文和记忆，先简短说明依据，再选择理解和行动，最后写一句回复。
只输出一个严格 JSON 对象。属性实际生成顺序必须是 reason、interpretation、action、reply。
interpretation 只能填写 interpretation_choices 的 choice_id；action 只能填写 action_choices 的 choice_id。
记忆里可能有用户过去说过的话、文字反思或经程序标出的约定。个人约定只在适用时使用；缺少信息时可选择询问。
不要捏造未提供的约定。reply 是聊天内容，不能替代选项。'''
B_SLEEP_SYSTEM = '''从给定原话中提议可复用的个人约定卡。你只提议，程序校验后才写入。
原话保留 utterance_id、speaker、session_id；只引用给定的 user 原话，不能引用助手的猜测。
每张卡写 trigger、meaning、source_ids、replaces。trigger 包含 kind、text、weekday、after、event。
原话触发用 kind=utterance，text 逐字引用触发词，weekday=-1，after 和 event 都写空串。
情境触发用 kind=situation，text 逐字引用完整情境，例如周五18:00以后上线；weekday 周一为0至周日为6，after 是 HH:MM，event 是 login。
meaning 从 user 原话中逐字引用其希望的含义，去掉外侧引号，不要改写。每条被引用原话都必须包含 trigger.text，至少一条还必须含 meaning。
只依据原话提议，不创建无关日记的约定。
两次不同场合的明确纠正也能建立约定，应引用两个场合的原话。引用不得猜造。
与已有卡相同的约定无需再提议。修改已有卡，replaces 必须填该卡 card_id，而且所引更正原话必须明确说：不再是「旧含义」，现在改成「新含义」。
没有这样明确的更正，不得替换已有卡；无法证明就返回空 proposals 列表。不要把记忆重复抄成新的更正。'''
A_SLEEP_SYSTEM = '''写一段文字反思供下一次 BM25 检索。只依据给定原话和已有记忆，保留用户约定的触发、含义和更正，不把助手的猜测当成事实。
反思用普通文字，不写约定卡；不编造新事实。只返回 JSON 对象，唯一属性 reflection_text。最多1200个字。'''


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def bounded(items):
    result = []
    for item in items:
        if len(compact(result + [item]).encode('utf-8')) <= MEMORY_LIMIT:
            result.append(item)
    return result


def obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def string(max_length=500, choices=None):
    value = {'type': 'string', 'maxLength': max_length}
    if choices is not None:
        value['enum'] = choices
    return value


def wrapped(name, schema):
    return {'type': 'json_schema', 'json_schema': {'name': name, 'strict': True, 'schema': schema}}


def decision_schema(case):
    return wrapped('u1_decision', obj({
        'reason': string(500),
        'interpretation': string(16, [x['choice_id'] for x in case['interpretation_choices']]),
        'action': string(16, [x['choice_id'] for x in case['action_choices']]),
        'reply': string(500),
    }))


def sleep_schema(arm):
    if arm == 'A':
        return wrapped('u1_reflection', obj({'reflection_text': string(2400)}))
    trigger = obj({'kind': string(16, ['utterance', 'situation']), 'text': string(150),
                   'weekday': {'type': 'integer', 'minimum': -1, 'maximum': 6},
                   'after': string(5), 'event': string(40)})
    proposal = obj({'trigger': trigger, 'meaning': string(500),
                    'source_ids': {'type': 'array', 'items': string(32), 'minItems': 1, 'maxItems': 12},
                    'replaces': string(32)})
    return wrapped('u1_consolidation', obj({'proposals': {'type': 'array', 'items': proposal, 'maxItems': 12}}))


def memory(lib, arm, query, case=None):
    if arm == 'A':
        docs = []
        for row in lib.rows():
            if row['record_kind'] == 'experience':
                body = row['body']
                if body.get('type') == 'utterance':
                    value = {'memory_kind': 'original_utterance', 'utterance_id': row['record_id'],
                             **{k: v for k, v in body.items() if k != 'type'}}
                else:
                    continue
            elif row['record_kind'] == 'reflection':
                value = {'memory_kind': 'reflection', **row['body']}
            else:
                continue
            docs.append((value, compact(value)))
        return bounded([value for value, _ in rank(query, docs)])
    cards = [{k: v for k, v in c.items() if k != 'type'} for c in lib.cards()]
    ranked = [value for value, _ in rank(query, [(c, compact(c)) for c in cards])]
    applications = lib.annotate(case['current_utterance'], case['turn_context']['occurred_at'],
                               case['turn_context']['event_labels']) if case else []
    return bounded([{'memory_kind': 'applied_convention', **a} for a in applications]
                   + [{'memory_kind': 'convention_card', **c} for c in ranked])


def decision_packet(lib, arm, case):
    context = case['turn_context']
    instant = datetime.fromisoformat(context['occurred_at'])
    # A has the same public calendar/events as B's deterministic matcher.
    calendar = '周' + '一二三四五六日'[instant.weekday()] + ' ' + instant.strftime('%H:%M')
    query = case['current_utterance'] + ' ' + compact(context) + ' ' + calendar
    if 'login' in context['event_labels']:
        query += ' 上线'
    recollection = memory(lib, arm, query, case)
    packet = {'turn_context': context, 'current_utterance': case['current_utterance'],
              'memory': recollection, 'interpretation_choices': case['interpretation_choices'],
              'action_choices': case['action_choices']}
    return [{'role': 'system', 'content': DECISION_SYSTEM}, {'role': 'user', 'content': compact(packet)}]


def parse_decision(content, case):
    if not isinstance(content, str) or not content.lstrip().startswith('{'):
        raise ValueError('decision_requires_object')
    pairs = json.loads(content, object_pairs_hook=lambda p: p)
    if not isinstance(pairs, list) or [k for k, _ in pairs] != DECISION_ORDER:
        raise ValueError('decision_property_order_or_keys')
    value = dict(pairs)
    if not all(isinstance(value[k], str) for k in DECISION_ORDER):
        raise ValueError('decision_field_type')
    if len(value['reason']) > 500 or len(value['reply']) > 500:
        raise ValueError('decision_field_length')
    if value['interpretation'] not in [x['choice_id'] for x in case['interpretation_choices']]:
        raise ValueError('interpretation_option')
    if value['action'] not in [x['choice_id'] for x in case['action_choices']]:
        raise ValueError('action_option')
    return value


def follows(value, target):
    return bool(value and all(value[k] == target[k] for k in ('interpretation', 'action')))


def keyword_score(card, fixture):
    return (all(normalize(k) in normalize(card['trigger']['text']) for k in fixture['keywords']['trigger'])
            and all(normalize(k) in normalize(card['meaning']) for k in fixture['keywords']['meaning'])
            and card['trigger'] == fixture['trigger'])
