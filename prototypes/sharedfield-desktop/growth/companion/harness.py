"""One user turn may contain many tool steps, recovery and durable checkpoints."""
import copy
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from p7.proxy import ProxyError

from .engine import Engine, STOP, confirmed_progress, completed_negative_search
from .memory import Memory
from .work import validate_action, validate_goal, create_work, save_work, incorporate, preliminary_completion, fingerprint

PROMPT = Path(__file__).with_name('harness_prompt.txt').read_text(encoding='utf-8')
RECOVERABLE = {'crafting_grid_or_cursor_not_clear', 'craft_inventory_checked', 'placement_material_missing',
               'placement_target_not_empty', 'no_placement_space', 'placed_block_checked', 'navigation_target_not_found',
               'block_approach_checked', 'approach_checked', 'owner_not_visible', 'collection_inventory_checked',
               'inventory_no_empty_slot', 'inventory_recovery_incomplete', 'action_repeated_without_progress',
               'target_out_of_reach', 'target_not_loaded', 'natural_tree_not_found', 'tree_inventory_checked', 'tree_target_changed'}


class Harness(Engine):
    def __init__(self, path, model, body, audit, *, max_decisions=64, max_seconds=900, action_policy=None):
        super().__init__(path, model, body, audit, max_decisions=max_decisions, max_seconds=max_seconds)
        self._waiting_lock = threading.Lock()
        self._waiting = 0
        self.progress = '等待输入'
        self.action_policy = action_policy
        m = Memory(path)
        try:
            old = m.goal()
            if old and old.get('work') and old['work']['status'] in ('active', 'recovering', 'yielded'):
                w = old['work']; w['status'] = 'interrupted'; w['last_problem'] = 'restart_requires_new_input_and_observation'
                save_work(m, w, [old['record_id']])
        finally:
            m.close()

    def run(self, event_id, channel, text, emit=lambda text: None):
        if channel not in ('airi', 'minecraft', 'verification') or not isinstance(text, str) or not 0 < len(text.strip()) <= 6000:
            raise ValueError('input_schema')
        text = text.strip()
        stop_receipt = self.stop() if STOP.fullmatch(text) else None
        epoch = self._epoch
        with self._waiting_lock:
            self._waiting += 1
        with self._turn_lock:
            with self._waiting_lock:
                self._waiting -= 1
            return self._work(event_id, channel, text, emit, epoch, stop_receipt)

    def _work(self, event_id, channel, text, emit, epoch, stop_receipt):
        m = Memory(self.path)
        work = None
        parents, spoken, receipts = [], [], []
        try:
            source, cached = m.begin(event_id, channel, text)
            if cached is not None:
                emit(cached)
                return cached
            old = m.goal()
            if old and old.get('work') and old['work']['status'] != 'completed':
                work = copy.deepcopy(old['work'])
            parents = list(dict.fromkeys([source, *[r['record_id'] for r in m.context()], *([old['record_id']] if old else [])]))
            annotations = m.library.annotate(text, datetime.now().astimezone().isoformat(), ('login',) if text == '上线了' else ())
            for card in m.library.cards():
                parents.extend([card['card_id'], *card['source_ids']])
            parents = list(dict.fromkeys(parents))

            def say(value):
                if value and (not spoken or spoken[-1] != value):
                    spoken.append(value); emit(value); self.body.say(value)

            def persist(status, problem=None):
                if work:
                    work['status'] = status
                    work['last_problem'] = problem
                    save_work(m, work, parents)
                self.progress = status

            def record(action, receipt, step):
                receipts.append(receipt)
                identity = m.append('experience', {'type': 'action_receipt', 'event_id': event_id, 'task_id': work['task_id'] if work else None,
                                                   'action': action, 'receipt': receipt}, parents)
                parents.append(identity)
                self.audit.write('actions.jsonl', {'event_id': event_id, 'step': step, 'action': action['name'],
                                                  'verified': receipt.get('verified', False), 'status': receipt.get('status')})

            def complete(state, step):
                if not work or not preliminary_completion(work, state)['satisfied']:
                    return False
                preliminary = preliminary_completion(work, state)
                action = {'name': 'verify_blocks', 'args': {'targets': preliminary['targets']}} if preliminary['targets'] else {'name': 'inspect', 'args': {}}
                with self._dispatch_lock:
                    if epoch != self._epoch:
                        return False
                    future = self.body.start_action(action, timeout=60)
                proof = future.result(timeout=65)
                record(action, proof, step)
                observed = proof.get('observed', self.body.snapshot())
                success = epoch == self._epoch and proof.get('verified') is True and preliminary_completion(work, observed)['satisfied']
                if success:
                    work['completion'] = {'checks': preliminary['checks'], 'world_verified': bool(preliminary['targets']), 'receipt_id': parents[-1]}
                    persist('completed')
                    say('目标已核对完成：' + work['title'] + '。')
                return success

            if epoch != self._epoch or stop_receipt is not None:
                persist('paused_by_owner', 'owner_stop')
                say('已经停下，目标和进度已保存。' if stop_receipt and stop_receipt.get('verified') else '这一轮已被停止请求取消，没有继续执行。')
            else:
                started = time.monotonic()
                seen, failures, no_action, premature = {}, 0, 0, 0
                notice = None
                state = self.body.snapshot()
                for step in range(self.max_decisions):
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'owner_stop'); say('已停止，进度已保存。'); break
                    with self._waiting_lock:
                        waiting = self._waiting
                    if waiting:
                        persist('yielded', 'new_owner_input'); say('收到新消息，我先按你的新输入调整；当前进度已保存。'); break
                    if time.monotonic() - started >= self.max_seconds:
                        persist('paused_limit', 'task_deadline'); say('这项任务到时间上限了，进度和具体剩余工作已保存。'); break
                    state = self.body.snapshot()
                    context = {'current': {'event_id': event_id, 'channel': channel, 'user': text}, 'history': m.context(),
                               'goal': m.goal(), 'work': work, 'conventions': m.library.cards(), 'annotations': annotations,
                               'recent_actions': m.recent_actions(), 'body': state, 'receipts': receipts[-6:], 'harness_notice': notice,
                               'remaining_decisions': self.max_decisions-step}
                    decision = self.model.decide(PROMPT, context)
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'late_decision_discarded'); say('已停止，迟到的决定没有执行。'); break
                    required = {'reply', 'goal', 'convention', 'forget_card', 'action', 'status'}
                    if not isinstance(decision, dict) or set(decision) != required or decision['status'] not in ('continue', 'done', 'blocked', 'chat'):
                        raise ValueError('harness_decision_schema')
                    if not isinstance(decision['reply'], str) or len(decision['reply']) > 1800:
                        raise ValueError('reply_schema')
                    m.append('reflection', {'type': 'kernel_decision', 'event_id': event_id, 'step': step, 'decision': decision}, parents)
                    if work:
                        work['decisions'] += 1
                    if decision['forget_card'] is not None:
                        if not re.search(r'^(?:请|帮我)?(?:忘掉|删除)', text):
                            raise ValueError('forget_requires_explicit_user_request')
                        m.forget(decision['forget_card']); work = None; parents = [source] if m.record(source) else []
                        say('该约定及其派生记录已从内核删除；AIRI 的显示副本仍由 AIRI 保留。'); break
                    if decision['convention'] is not None:
                        card = m.propose(decision['convention'], source); parents.append(card)
                        receipts.append({'verified': True, 'kind': 'convention_saved', 'card_id': card})
                        notice = '约定已实际写入；没有正在执行的任务时可回复确认。'
                        continue
                    if decision['goal'] is not None:
                        proposed = validate_goal(decision['goal'])
                        if work and (step > 0 or proposed['title'] == work['title'] or re.match(r'^(继续|接着)', text)):
                            if proposed['done_when'] != work['done_when']:
                                notice = '已有任务完成条件不可为提前结束而降低；请完成原条件或明确说明阻塞。'
                                premature += 1
                                if premature >= 2:
                                    persist('blocked', 'completion_contract_changed'); say('完成条件被改写，任务没有通过核对，已保留原目标。'); break
                                continue
                            work['steps'] = proposed['steps']
                        else:
                            work = create_work(proposed, state, source)
                        persist('active')
                        if step == 0:
                            say('我会连续推进：' + work['title'] + '。完成后会核对结果。')
                    action = decision['action']
                    if work and complete(state, step):
                        break
                    if action is None:
                        if not work:
                            say(decision['reply']); break
                        if decision['status'] == 'blocked':
                            persist('blocked', decision['reply'][:500]); say(decision['reply']); break
                        if decision['status'] == 'chat':
                            say(decision['reply'])
                            if work['status'] in ('blocked','interrupted','paused_limit','paused_by_owner'):
                                break
                        no_action += 1
                        notice = '目标尚未得到程序完成确认；有可执行下一步就继续，真实阻塞请 status=blocked 并说具体原因。'
                        if no_action >= 2:
                            persist('blocked', 'no_action_or_unverified_completion'); say('目标尚未通过核对，当前没有给出可执行的下一步；进度已保存。'); break
                        continue
                    if not work:
                        notice = '执行前先提供 goal 的 title、steps、done_when。'
                        no_action += 1
                        if no_action >= 2:
                            say('行动缺少可检查的目标，尚未执行。'); break
                        continue
                    validate_action(action)
                    if state.get('offline'):
                        persist('blocked', 'body_offline'); say('身体连接不可用，目标已保存；连接恢复后先观察，再决定下一步。'); break
                    key = json.dumps(action, sort_keys=True)
                    state_key = fingerprint(state)
                    previous = seen.get((key, state_key))
                    progress_action = action if action['name'] != 'place_at' else {'name': 'place', 'args': {'block': action['args']['block']}}
                    if previous is not None and not confirmed_progress(progress_action, previous):
                        receipt = {'verified': False, 'executed': False, 'status': 'action_repeated_without_progress', 'observed': state}
                    elif self.action_policy and not self.action_policy(action):
                        persist('blocked', 'acceptance_action_boundary'); say('到达本次验收动作边界，已停止。'); break
                    else:
                        with self._dispatch_lock:
                            if epoch != self._epoch:
                                persist('paused_by_owner', 'owner_stop'); break
                            future = self.body.start_action(action, timeout=60)
                        receipt = future.result(timeout=65)
                        seen[(key, state_key)] = receipt
                        work['actions'] += 1
                    record(action, receipt, step)
                    incorporate(work, action, receipt)
                    state = receipt.get('observed', self.body.snapshot())
                    no_action = 0
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'owner_stop'); say('已停止，动作结果与任务进度已保存。'); break
                    if receipt.get('verified') or completed_negative_search(action, receipt):
                        failures = 0; notice = None; persist('active')
                        if complete(state, step):
                            break
                    else:
                        failures += 1
                        notice = {'kind': 'recover_or_replan', 'failed_action': action, 'status': receipt.get('status'),
                                  'attempts_without_success': failures, 'same_state_retry_forbidden': True}
                        persist('recovering', receipt.get('status'))
                        if failures >= 3 or receipt.get('status') not in RECOVERABLE:
                            persist('blocked', receipt.get('status'))
                            reasons={'inventory_no_empty_slot':'背包没有足够空位整理材料', 'action_repeated_without_progress':'相同状态下重复尝试没有进展',
                                     'body_disconnected':'游戏连接中断', 'unsupported_container':'当前打开的容器不在整理工具支持范围内',
                                     'action_failed':'动作执行遇到尚未确认的错误'}
                            say('当前步骤受阻：' + reasons.get(receipt.get('status'),'恢复尝试仍未确认成功') + '；进度和回执已保存。'); break
                    if (step + 1) % 8 == 0:
                        work['checkpoints'] += 1; persist(work['status'], work['last_problem'])
                        self.audit.write('lifecycle.jsonl', {'event': 'task_checkpoint', 'event_id': event_id, 'step': step+1, 'continues': True})
                        say('进度已保存，正在继续处理剩余步骤。')
                    self.progress = '执行中 · ' + work['title'][:32] + ' · ' + str(step+1) + ' 次决定'
                else:
                    persist('paused_limit', 'task_decision_cap'); say('这项任务达到决定次数上限，进度与剩余工作已保存。')
            reply = '\n'.join(spoken) or '本轮进度已保存。'
            m.finish(event_id, reply, parents)
            self.audit.write('lifecycle.jsonl', {'event': 'turn_done', 'event_id': event_id, 'channel': channel,
                                               'receipt_count': len(receipts), 'task_status': work['status'] if work else None})
            return reply
        except Exception as error:
            self.body.stop()
            problem = error.code if isinstance(error, ProxyError) else type(error).__name__
            if work and parents:
                work['status'] = 'blocked'; work['last_problem'] = problem
                save_work(m, work, parents)
            result = ('本次预算不足以预留下一次请求，已停止；目标和进度已保存。' if problem == 'budget_stop'
                      else '任务遇到连接或格式问题，进度已保存；没有自动重试。')
            emit(result); self.body.say(result)
            self.audit.write('lifecycle.jsonl', {'event': 'turn_failed', 'event_id': event_id, 'error_type': type(error).__name__, 'error_code': problem})
            if 'source' in locals() and source and m.record(source):
                m.finish(event_id, result, [source])
            return result
        finally:
            m.close()
