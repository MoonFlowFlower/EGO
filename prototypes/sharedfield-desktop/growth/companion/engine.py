"""Single serialized thought/action loop shared by both input surfaces."""
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from .memory import Memory

CONVERSATION_ID = 'ego:Moonlight'
PROMPT = Path(__file__).with_name('prompt.txt').read_text(encoding='utf-8')
STOP = re.compile(r'^(?:请|先)?(?:停下|停止|别动|暂停|stop)[。！!\s]*$', re.I)
ACTION_FIELDS = {'inspect': set(), 'approach': set(), 'follow': set(), 'stop': set(),
                 'search': {'block', 'range'}, 'go_to_block': {'block', 'range'}, 'collect': {'block', 'count'},
                 'craft': {'item', 'count'}, 'give': {'item', 'count'}, 'place': {'block'}}


def validate_action(action):
    if not isinstance(action, dict) or set(action) != {'name', 'args'}:
        raise ValueError('action_schema')
    name, args = action['name'], action['args']
    if name not in ACTION_FIELDS or not isinstance(args, dict) or set(args) != ACTION_FIELDS[name]:
        raise ValueError('action_not_allowed')
    for key, value in args.items():
        if key in ('item', 'block') and (not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value)):
            raise ValueError('invalid_game_identifier')
        if key == 'count' and (type(value) is not int or not 1 <= value <= (16 if name == 'give' else 8)):
            raise ValueError('invalid_action_count')
        if key == 'range' and (type(value) is not int or not 8 <= value <= 128):
            raise ValueError('invalid_search_range')
    return action


def completed_negative_search(action, receipt):
    return (action['name'] == 'search' and receipt.get('status') == 'block_not_found'
            and receipt.get('observation_complete') is True and receipt.get('found') is False
            and receipt.get('query', {}).get('scope') == 'loaded_chunks_only')


class Engine:
    def __init__(self, path, model, body, audit, *, max_decisions=8, max_seconds=180):
        self.path, self.model, self.body, self.audit = path, model, body, audit
        self.max_decisions, self.max_seconds = max_decisions, max_seconds
        self._turn_lock = threading.Lock()
        self._dispatch_lock = threading.Lock()
        self._epoch = 0
        # Recovery records interrupted turns but never replays a pending action.
        memory = Memory(path)
        memory.mark_interrupted()
        memory.close()

    def stop(self):
        with self._dispatch_lock:
            self._epoch += 1
            return self.body.stop()

    def run(self, event_id, channel, text, emit=lambda text: None):
        if channel not in ('airi', 'minecraft', 'verification') or not isinstance(text, str) or not 0 < len(text.strip()) <= 6000:
            raise ValueError('input_schema')
        text = text.strip()
        stop_receipt = self.stop() if STOP.fullmatch(text) else None
        submitted_epoch = self._epoch
        with self._turn_lock:
            memory = Memory(self.path)
            try:
                source_id, cached = memory.begin(event_id, channel, text)
                if cached is not None:
                    self.audit.write('lifecycle.jsonl', {'event': 'cached_turn', 'event_id': event_id, 'channel': channel})
                    emit(cached)
                    return cached
                parents = [c['record_id'] for c in memory.context()]
                parents.extend(c['record_id'] for c in memory.recent_actions())
                if memory.goal():parents.append(memory.goal()['record_id'])
                start = time.monotonic()
                epoch = self._epoch
                receipts, spoken, seen_actions = [], [], set()
                annotations = memory.library.annotate(text, datetime.now().astimezone().isoformat(), ('login',) if text == '上线了' else ())
                for card in memory.library.cards():
                    parents.extend([card['card_id'], *card['source_ids']])
                parents = list(dict.fromkeys(parents))

                def say(value):
                    if value and (not spoken or value != spoken[-1]):
                        spoken.append(value)
                        emit(value)
                        self.body.say(value)

                if submitted_epoch != self._epoch:
                    say('排队中的这一轮已被停止请求取消，没有执行。')
                elif stop_receipt is not None:
                    receipts.append(stop_receipt)
                    old = memory.goal()
                    if old:
                        memory.update_goal(old['title'], 'paused_by_owner', parents)
                    say('已经停下了。' if stop_receipt.get('verified') else '已发出停止指令，但还没有得到身体停稳的确认。')
                else:
                    for index in range(self.max_decisions):
                        if epoch != self._epoch:
                            say('这一轮已被打断，我没有继续执行后续动作。')
                            break
                        if time.monotonic() - start >= self.max_seconds:
                            say('这一轮到时间上限了，我先暂停，待办已保留。')
                            break
                        context = {'conversation_id': CONVERSATION_ID,
                                   'current': {'event_id': event_id, 'channel': channel, 'user': text},
                                   'history': memory.context(), 'goal': memory.goal(),
                                   'recent_actions': memory.recent_actions(),
                                   'conventions': memory.library.cards(), 'annotations': annotations,
                                   'body': self.body.snapshot(), 'receipts': receipts}
                        decision = self.model.decide(PROMPT, context)
                        if epoch != self._epoch:
                            say('已停止；刚才迟到的决定没有执行。')
                            break
                        if not isinstance(decision, dict) or set(decision) != {'reply', 'goal', 'convention', 'forget_card', 'action'}:
                            raise ValueError('decision_schema')
                        if not isinstance(decision['reply'], str) or len(decision['reply']) > 1800:
                            raise ValueError('reply_schema')
                        memory.append('reflection', {'type': 'kernel_decision', 'event_id': event_id,
                                                     'step': index, 'decision': decision}, parents)
                        if decision['goal'] is not None:
                            goal = decision['goal']
                            if not isinstance(goal, dict) or set(goal) != {'title'} or not isinstance(goal['title'], str) or not 1 <= len(goal['title']) <= 400:
                                raise ValueError('goal_schema')
                            memory.update_goal(goal['title'], 'active', parents)
                        if decision['forget_card'] is not None:
                            if not re.search(r'^(?:请|帮我)?(?:忘掉|删除)', text):
                                raise ValueError('forget_requires_explicit_user_request')
                            result = memory.forget(decision['forget_card'])
                            # Rebuild references after deletion closure; do not reinsert its contents.
                            parents = [source_id] if memory.record(source_id) else []
                            say('这个约定已从内核存储及其派生记录中删除；AIRI 的界面聊天副本仍由 AIRI 保留。')
                            receipts.append(result)
                            break
                        if decision['convention'] is not None:
                            try:
                                card_id = memory.propose(decision['convention'], source_id)
                                receipts.append({'kind': 'convention_saved', 'verified': True, 'card_id': card_id})
                                parents.append(card_id)
                            except ValueError as error:
                                receipts.append({'kind': 'convention_rejected', 'verified': False, 'code': str(error)})
                                say('这条约定没有通过原话校验，我还没有记入长期约定。')
                                break
                            # A memory claim must be made after the actual write receipt.
                            continue
                        action = decision['action']
                        if action is None:
                            say(decision['reply'])
                            break
                        validate_action(action)
                        encoded = json.dumps(action, sort_keys=True)
                        if encoded in seen_actions:
                            say('同一动作已经尝试过，我先停在这里，保留任务和结果，避免反复空转。')
                            break
                        seen_actions.add(encoded)
                        with self._dispatch_lock:
                            if epoch != self._epoch:
                                break
                            future = self.body.start_action(action, timeout=60)
                        # Before-action text may promise or hallucinate completion. Do not publish it.
                        receipt = future.result(timeout=65)
                        receipts.append(receipt)
                        memory.append('experience', {'type': 'action_receipt', 'event_id': event_id,
                                                    'action': action, 'receipt': receipt}, parents)
                        self.audit.write('actions.jsonl', {'event_id': event_id, 'step': index, 'action': action['name'],
                                                          'verified': receipt.get('verified', False), 'status': receipt.get('status')})
                        # An empty search is evidence for the next decision, not an execution fault.
                        # Actual execution failures still admit one explanation and no more actions.
                        if not receipt.get('verified') and not completed_negative_search(action, receipt):
                            context['receipts'] = receipts
                            context['body'] = self.body.snapshot()
                            if index + 1 < self.max_decisions and epoch == self._epoch:
                                result = self.model.decide(PROMPT, {**context, 'execution_blocked': True})
                                memory.append('reflection', {'type': 'kernel_decision', 'event_id': event_id,
                                    'step': index + 1, 'execution_blocked': True, 'decision': result}, parents)
                                if epoch == self._epoch and isinstance(result, dict) and result.get('action') is None and isinstance(result.get('reply'), str):
                                    say(result['reply'])
                            say('这一步没有得到成功确认，动作已暂停，任务仍保留。')
                            break
                    else:
                        say('这一轮八次决定已用完，我先暂停，待办和动作结果已经保存。')
                goal = memory.goal()
                if goal and goal['goal_status'] == 'active':
                    memory.update_goal(goal['title'], 'awaiting_next_input', parents)
                reply = '\n'.join(spoken) or '这一轮已暂停，没有执行新的动作。'
                memory.finish(event_id, reply, parents)
                self.audit.write('lifecycle.jsonl', {'event': 'turn_done', 'event_id': event_id,
                                                   'conversation_id': CONVERSATION_ID, 'channel': channel,
                                                   'receipt_count': len(receipts)})
                return reply
            except Exception as error:
                self.body.stop()
                message = '这一轮遇到连接、预算或格式问题，动作已暂停；不会自动重试。'
                emit(message)
                self.body.say(message)
                self.audit.write('lifecycle.jsonl', {'event': 'turn_failed', 'event_id': event_id,
                                                   'error_type': type(error).__name__})
                if 'source_id' in locals() and source_id and memory.record(source_id):
                    memory.finish(event_id, message, [source_id])
                return message
            finally:
                memory.close()
