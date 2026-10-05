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
from .intent import route_input, chat_reply
from .context import conversation_context, user_history, historical_actions
from .work import validate_action, validate_goal, create_work, save_work, incorporate, preliminary_completion, fingerprint
from .interaction import input_event, dialogue, bind_request, steer_work, goal_problem, action_problem, observation_key, reconcile_pickups, normalize_transition, OBSERVATIONS
from .recall import recall, matched_cards
from .model import DecisionError
from .stall import question as stalled_question

PROMPT = Path(__file__).with_name('harness_prompt.txt').read_text(encoding='utf-8')
RECOVERABLE = {'crafting_grid_or_cursor_not_clear', 'craft_inventory_checked', 'placement_material_missing',
               'placement_target_not_empty', 'no_placement_space', 'placed_block_checked', 'navigation_target_not_found',
               'block_approach_checked', 'approach_checked', 'owner_not_visible', 'collection_inventory_checked',
               'inventory_no_empty_slot', 'inventory_recovery_incomplete', 'action_repeated_without_progress',
               'target_out_of_reach', 'target_not_loaded', 'natural_tree_not_found', 'tree_inventory_checked', 'tree_target_changed', 'missing_ingredients',
               'pickup_partial', 'pickup_target_missing', 'pickup_path_failed', 'pickup_requires_current_entity_observation',
               'pickup_requires_owner_spatial_anchor', 'pickup_outside_indicated_area', 'action_outside_current_request', 'pickup_item_mismatch'}
RECOVERABLE.update({'placement_batch_partial','placement_no_support','placement_path_failed','placement_body_occupies_target'})


class Harness(Engine):
    def invalidate(self, reason):
        with self._dispatch_lock:
            self._cancel_reason=reason
            self._epoch+=1

    def __init__(self, path, model, body, audit, *, max_decisions=64, max_seconds=900, action_policy=None, input_router=None):
        super().__init__(path, model, body, audit, max_decisions=max_decisions, max_seconds=max_seconds)
        self._waiting_lock = threading.Lock()
        self._waiting_changed = threading.Condition(self._waiting_lock)
        self._waiting = 0
        self._execution_generation = 0
        self.progress = '等待输入'
        self.action_policy = action_policy
        self.input_router = input_router
        m = Memory(path)
        try:
            old = m.goal()
            if old and old.get('work') and old['work']['status'] in ('active', 'recovering', 'yielded'):
                w = old['work']; w['status'] = 'interrupted'; w['last_problem'] = 'restart_requires_new_input_and_observation'
                save_work(m, w, [old['record_id']])
        finally:
            m.close()

    def run(self, event_id, channel, text, emit=lambda text: None, *, input_state=None):
        if channel not in ('airi', 'minecraft', 'verification') or not isinstance(text, str) or not 0 < len(text.strip()) <= 6000:
            raise ValueError('input_schema')
        text = text.strip()
        event = input_event(event_id, channel, text, input_state if input_state is not None else self.body.snapshot())
        stop_receipt = self.stop() if STOP.fullmatch(text) else None
        epoch = self._epoch
        with self._dispatch_lock:
            with self._waiting_lock:
                self._waiting += 1
        with self._turn_lock:
            with self._waiting_lock:
                self._waiting -= 1
                self._waiting_changed.notify_all()
            return self._work(event_id, channel, text, emit, epoch, stop_receipt, event)

    def _work(self, event_id, channel, text, emit, epoch, stop_receipt, event):
        m = Memory(self.path)
        work = None
        execution_granted = False
        parents, spoken, receipts = [], [], []
        action_records=[]
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
            cards = matched_cards(m, annotations)
            for card in cards:
                parents.extend([card['card_id'], *card['source_ids']])
            parents = list(dict.fromkeys(parents))

            def say(value):
                if value and (not spoken or spoken[-1] != value):
                    spoken.append(value); emit(value); self.body.say(value)

            def cancelled():
                return ('身体正在重新连接；进度已保存，迟到的决定没有执行。'
                        if self._cancel_reason=='body_reconnect' else '已停止，进度已保存，后续决定没有执行。')

            def persist(status, problem=None):
                if status=='paused_by_owner' and self._cancel_reason=='body_reconnect':
                    status,problem='interrupted','body_reconnect'
                if work:
                    work['status'] = status
                    work['last_problem'] = problem
                    save_work(m, work, parents)
                self.progress = status

            def yield_to_inputs(generation):
                """Suspend this stack, drain inputs, then revalidate its authority.

                The original loop keeps its deadline, counters, receipts and seen
                failures. No synthetic user message or persisted replay token exists.
                """
                nonlocal work
                with self._waiting_lock:
                    if not self._waiting:
                        return True
                previous_status = work['status'] if work else None
                previous_problem = work.get('last_problem') if work else None
                persist('yielded', 'new_owner_input')
                self.audit.write('lifecycle.jsonl', {'event': 'task_yielded', 'event_id': event_id,
                                                    'task_id': work['task_id'] if work else None})
                while True:
                    self._turn_lock.release()
                    try:
                        with self._waiting_changed:
                            self._waiting_changed.wait_for(lambda: self._waiting == 0)
                    finally:
                        self._turn_lock.acquire()
                    with self._waiting_lock:
                        if not self._waiting:
                            break
                current = m.goal()
                current_work = current.get('work') if current else None
                same_task = bool(work and current_work and current_work['task_id'] == work['task_id'])
                if same_task:
                    work = copy.deepcopy(current_work)
                    parents.extend(i['source_id'] for i in work.get('inputs', []) if i.get('source_id') and i['source_id'] not in parents)
                if epoch != self._epoch:
                    if same_task and work['status'] == 'yielded':
                        persist('paused_by_owner', 'owner_stop')
                    say(cancelled())
                    return False
                if generation != self._execution_generation:
                    return False
                if work and (not same_task or work['status'] != 'yielded'):
                    return False
                if work:
                    persist(previous_status, previous_problem)
                self.audit.write('lifecycle.jsonl', {'event': 'task_resumed_after_conversation', 'event_id': event_id,
                                                    'task_id': work['task_id'] if work else None})
                return True

            def wait_for_user(question, problem):
                if work:
                    work['awaiting'] = {'question': question, 'event_id': event_id}
                persist('waiting_user', problem)
                say(question)

            def record(action, receipt, step):
                receipts.append(receipt)
                identity = m.append('experience', {'type': 'action_receipt', 'event_id': event_id, 'task_id': work['task_id'] if work else None,
                                                   'task_revision': work.get('revision', 0) if work else None,
                                                   'task_title': work['title'] if work else None,
                                                   'action': action, 'receipt': receipt}, parents)
                parents.append(identity)
                action_records.append({'record_id':identity,'action':copy.deepcopy(action),
                    'sampled_at':receipt.get('observed',{}).get('sampled_at'),
                    'receipt':{k:copy.deepcopy(v) for k,v in receipt.items() if k!='observed'},
                    'authority':'past tool result, not new authorization or a replacement for current body'})
                self.audit.write('actions.jsonl', {'event_id': event_id, 'step': step, 'action': action['name'],
                                                  'verified': receipt.get('verified', False), 'status': receipt.get('status')})

            def complete(state, step):
                reconcile_pickups(work, state)
                if not work or not preliminary_completion(work, state)['satisfied']:
                    return False
                preliminary = preliminary_completion(work, state)
                action = {'name': 'verify_blocks', 'args': {'targets': preliminary['targets']}} if preliminary['targets'] else {'name': 'inspect', 'args': {}}
                with self._dispatch_lock:
                    if epoch != self._epoch or self._waiting:
                        return False
                    future = self.body.start_action(action, timeout=60)
                proof = future.result(timeout=65)
                record(action, proof, step)
                observed = proof.get('observed', self.body.snapshot())
                success = epoch == self._epoch and not self._waiting and proof.get('verified') is True and preliminary_completion(work, observed)['satisfied']
                if success:
                    work['completion'] = {'checks': preliminary['checks'], 'world_verified': bool(preliminary['targets']), 'receipt_id': parents[-1]}
                    persist('completed')
                    say('目标已核对完成：' + work['title'] + '。')
                return success

            if epoch != self._epoch or stop_receipt is not None:
                persist('paused_by_owner', 'owner_stop')
                say('已经停下，目标和进度已保存。' if stop_receipt and stop_receipt.get('verified') else '这一轮已被停止请求取消，没有继续执行。')
            else:
                event['source_id'] = source
                situation = {'current_body': self.body.snapshot(), 'input_event': event, 'dialogue': dialogue(m),
                             'pending_work': work, 'memory_candidates': recall(m, text)}
                intent=(self.input_router(text, old, annotations) if self.input_router else
                        route_input(self.model, text, old, annotations, situation=situation))
                proposed_intent = intent
                intent = normalize_transition(intent, work)
                if proposed_intent != intent:
                    self.audit.write('lifecycle.jsonl', {'event':'input_transition_normalized','event_id':event_id,
                        'proposed':proposed_intent,'applied':intent,'reason':'primitive_has_distinct_completion_contract'})
                self.audit.write('lifecycle.jsonl',{'event':'input_routed','event_id':event_id,'mode':intent['mode'],'task_kind':intent['task_kind']})
                m.append('reflection',{'type':'input_route','event_id':event_id,'route':intent},[source])
                requested_memories = [recall(m, query) for query in
                                      intent.get('information_need', {}).get('memory_queries', [])]
                for retrieval in requested_memories:
                    for candidate in retrieval['candidates']:
                        parents.extend([candidate['record_id'], *candidate.get('source_ids', [])])
                parents = list(dict.fromkeys(parents))
                if epoch != self._epoch:
                    say(cancelled())
                    reply='\n'.join(spoken);m.finish(event_id,reply,parents);return reply
                if intent['mode'] == 'steer' and work:
                    steer_work(work, event)
                    persist(work['status'], work.get('last_problem'))
                    self.audit.write('lifecycle.jsonl', {'event': 'task_steered', 'event_id': event_id,
                        'task_id': work['task_id'], 'revision': work['revision']})
                    if work['status'] == 'yielded':
                        say('收到，你的新信息已经记进当前任务；我会重新观察再行动。')
                        reply='\n'.join(spoken);m.finish(event_id,reply,parents)
                        return reply
                if intent['mode'] not in ('chat', 'status'):
                    # A new execution/memory request takes ownership. Pure dialogue
                    # is the only input that can return control to a suspended turn.
                    self._execution_generation += 1
                    if intent['mode'] == 'memory' and work and work['status'] == 'yielded':
                        persist('interrupted', 'input_requires_explicit_resume')
                if intent['mode'] in ('chat','status'):
                    # This path has no tool schema and cannot create/replace a goal.
                    context = conversation_context(m, text, intent['mode'], self.body.snapshot(),
                                                   information_need=intent['information_need'])
                    self.audit.write('lifecycle.jsonl', {'event':'response_information_loaded', 'event_id':event_id,
                        'information_need':intent['information_need'], 'loaded_fields':list(context)})
                    answer=chat_reply(self.model, context)
                    if epoch != self._epoch:answer=cancelled()
                    say(answer);self.progress='等待输入' if not old else '待办保留 · '+old['goal_status']
                    reply='\n'.join(spoken);m.finish(event_id,reply,parents)
                    self.audit.write('lifecycle.jsonl',{'event':'conversation_done','event_id':event_id,'body_actions':0,'goal_changed':False})
                    return reply
                execution_granted = intent['mode'] in ('task','resume','steer')
                if intent['mode'] in ('resume','steer') and work and (
                        work.get('requires_new_contract') or goal_problem(intent['task_kind'], work)):
                    question = '旧任务的完成条件不能核对你当前要的结果。请重新说明这次要做什么、对象在哪里，我会建立对应的核对条件。'
                    work['requires_new_contract'] = True
                    work['awaiting'] = {'question': question, 'event_id': event_id}
                    persist('waiting_user', 'legacy_contract_requires_reinterpretation')
                    say(question)
                    reply='\n'.join(spoken);m.finish(event_id,reply,parents)
                    return reply
                if intent['mode'] == 'task':
                    if work:
                        persist('suspended', 'new_request_has_separate_goal')
                    work = None
                elif work and intent['mode'] == 'resume':
                    work.setdefault('inputs', []).append(copy.deepcopy(event))
                    work['inputs'] = work['inputs'][-8:]
                if work and execution_granted:
                    persist('active')
                generation = self._execution_generation
                started = time.monotonic()
                seen, failures, no_action, premature = {}, 0, 0, 0
                observations, repeated_observations, observations_without_effect = set(), 0, 0
                notice = None
                previous_decision = None
                invalid_decisions = 0
                state = self.body.snapshot()
                for step in range(self.max_decisions):
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'owner_stop'); say(cancelled()); break
                    if not yield_to_inputs(generation):
                        break
                    if time.monotonic() - started >= self.max_seconds:
                        persist('paused_limit', 'task_deadline'); say('这项任务到时间上限了，进度和具体剩余工作已保存。'); break
                    state = self.body.snapshot()
                    latest = (work.get('inputs') or [event])[-1] if work else event
                    context = {'current': latest, 'original_request': work.get('request', event) if work else event,
                               'dialogue': dialogue(m), 'history': user_history(m),
                               'goal': m.goal() if work else None, 'work': work, 'conventions': cards, 'annotations': annotations,
                               'request_kind': work.get('task_kind', intent['task_kind']) if work else intent['task_kind'],
                               'recent_actions': historical_actions(m), 'body': state,
                               'information_need': intent.get('information_need'), 'memory_candidates': requested_memories,
                               'receipts': [{k:v for k,v in r.items() if k != 'observed'} for r in receipts[-6:]], 'harness_notice': notice,
                               'remaining_decisions': self.max_decisions-step}
                    if previous_decision is not None or isinstance(notice,dict) and notice.get('kind')=='invalid_model_output':
                        context['execution_feedback']={'previous_decision':previous_decision,
                            'event_id':event_id,'step':step,'receipts':context['receipts'],
                            'harness_notice':notice,'current_body':state,'work':work,
                            'semantics':'continuation after the preceding decision; not a new user request or new authorization'}
                    try:
                        decision = self.model.decide(PROMPT, context)
                    except DecisionError as error:
                        invalid_decisions+=1
                        notice={'kind':'invalid_model_output','code':error.code,
                                'effect':'no decision executed; provide one concise valid decision using existing evidence, or state the actual blocker'}
                        self.audit.write('lifecycle.jsonl',{'event':'model_output_rejected','event_id':event_id,
                                                          'error_code':error.code,'attempt':invalid_decisions})
                        if invalid_decisions>=3:
                            persist('blocked',error.code);say('连续三次模型输出不完整，已停止；没有执行这些无效输出。');break
                        continue
                    previous_decision = copy.deepcopy(decision)
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'late_decision_discarded'); say(cancelled()); break
                    with self._waiting_lock:
                        waiting = self._waiting
                    if waiting:
                        self.audit.write('lifecycle.jsonl', {'event': 'decision_deferred_for_input', 'event_id': event_id, 'step': step})
                        if not yield_to_inputs(generation):
                            break
                        # Count the spent decision; do not execute it against a
                        # snapshot taken before the intervening conversation.
                        continue
                    if time.monotonic() - started >= self.max_seconds:
                        persist('paused_limit', 'task_deadline'); say('这项任务到时间上限了，进度和具体剩余工作已保存。'); break
                    required = {'reply', 'goal', 'convention', 'forget_card', 'action', 'status'}
                    if not isinstance(decision, dict) or set(decision) != required or decision['status'] not in ('continue', 'done', 'blocked', 'chat', 'waiting_user'):
                        invalid_decisions += 1
                        notice={'kind':'invalid_decision','code':'harness_decision_schema','required_top_level_fields':sorted(required),
                                'effect':'nothing executed; repair the JSON structure without changing the task'}
                        self.audit.write('lifecycle.jsonl',{'event':'decision_rejected','event_id':event_id,
                                                          'error_code':'harness_decision_schema','attempt':invalid_decisions})
                        if invalid_decisions>=3:
                            persist('blocked','harness_decision_schema');say('连续三次决定格式不完整，已停止；没有执行这些无效决定。');break
                        continue
                    invalid_decisions=0
                    if not isinstance(decision['reply'], str) or len(decision['reply']) > 1800:
                        raise ValueError('reply_schema')
                    if intent['mode']=='memory' and (decision['goal'] is not None or decision['action'] is not None):
                        raise ValueError('memory_input_cannot_act_or_change_goal')
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
                    observing_before_goal = (not work and isinstance(decision['action'],dict)
                        and decision['action'].get('name') in OBSERVATIONS and isinstance(decision['goal'],dict)
                        and any(isinstance(c,dict) and c.get('kind')=='blocks' for c in decision['goal'].get('done_when',[])))
                    if decision['goal'] is not None and observing_before_goal:
                        # Observation cannot commit an ungrounded spatial contract.
                        # Keep the proposal in the decision audit, and let the
                        # observed scene inform a later executable goal.
                        self.audit.write('lifecycle.jsonl',{'event':'goal_deferred_for_observation','event_id':event_id})
                    if decision['goal'] is not None and not observing_before_goal:
                        try:
                            proposed = validate_goal(decision['goal'])
                        except ValueError as error:
                            notice = {'kind':'invalid_goal_contract', 'code':str(error)}
                            premature += 1
                            if premature >= 3:
                                say('目标的核对条件仍有矛盾或缺项，尚未执行。'); break
                            continue
                        contract_problem = goal_problem(work.get('task_kind', 'ordinary') if work else intent['task_kind'], proposed)
                        if contract_problem:
                            notice = contract_problem; premature += 1
                            if premature >= 2:
                                say('当前目标的核对条件还不符合你的请求，尚未执行。'); break
                            continue
                        if work:
                            if proposed['done_when'] != work['done_when']:
                                notice = '已有任务完成条件不可为提前结束而降低；请完成原条件或明确说明阻塞。'
                                premature += 1
                                if premature >= 2:
                                    persist('blocked', 'completion_contract_changed'); say('完成条件被改写，任务没有通过核对，已保留原目标。'); break
                                continue
                            work['steps'] = proposed['steps']
                        else:
                            work = create_work(proposed, state, source)
                            bind_request(work, event, intent['task_kind'])
                        persist('active')
                        if step == 0:
                            say('我会连续推进：' + work['title'] + '。完成后会核对结果。')
                    action = decision['action']
                    if decision['status'] == 'waiting_user':
                        if not decision['reply'].strip():
                            raise ValueError('waiting_requires_question')
                        if work:
                            work['awaiting'] = {'question': decision['reply'], 'event_id': event_id}
                            persist('waiting_user', 'needs_owner_information')
                        say(decision['reply']); break
                    if intent['mode']=='memory':
                        if action is not None:raise ValueError('memory_input_cannot_act')
                        say(decision['reply']);break
                    if work and complete(state, step):
                        break
                    if action and action.get('name') == 'recall':
                        validate_action(action)
                        result = recall(m, action['args']['query'])
                        for candidate in result['candidates']:
                            parents.extend([candidate['record_id'], *candidate.get('source_ids', [])])
                        record(action, {'verified': True, 'status': 'memory_candidates', **result}, step)
                        no_action += 1
                        if no_action >= 4:
                            wait_for_user('找到的记忆还不足以确定下一步，请补充这次要做的具体事情。', 'recall_without_actionable_information'); break
                        continue
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
                    if not work and action.get('name') not in OBSERVATIONS:
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
                    problem = action_problem(work, action, state) if work else None
                    if problem:
                        receipt = {'verified': False, 'executed': False, 'status': problem, 'observed': state}
                    elif action['name'] not in OBSERVATIONS and previous is not None and not confirmed_progress(progress_action, previous):
                        receipt = {'verified': False, 'executed': False, 'status': 'action_repeated_without_progress', 'observed': state}
                    elif self.action_policy and not self.action_policy(action):
                        persist('blocked', 'acceptance_action_boundary'); say('到达本次验收动作边界，已停止。'); break
                    else:
                        with self._dispatch_lock:
                            if epoch != self._epoch:
                                persist('paused_by_owner', 'owner_stop'); break
                            if self._waiting:
                                continue
                            self.audit.write('lifecycle.jsonl', {'event': 'action_authorized', 'event_id': event_id,
                                'task_id': work['task_id'] if work else None, 'revision': work.get('revision', 0) if work else 0, 'action': action['name']})
                            if decision['reply']:
                                say(decision['reply'])
                            future = self.body.start_action(action, timeout=60)
                        receipt = future.result(timeout=65)
                        seen[(key, state_key)] = receipt
                        if work:work['actions'] += 1
                    record(action, receipt, step)
                    incorporate(work, action, receipt)
                    state = receipt.get('observed', self.body.snapshot())
                    no_action = 0
                    if epoch != self._epoch:
                        persist('paused_by_owner', 'owner_stop'); say(cancelled()); break
                    if receipt.get('verified') or completed_negative_search(action, receipt):
                        if action['name'] in OBSERVATIONS:
                            observations_without_effect += 1
                            observed_key = observation_key(receipt)
                            repeated_observations += int(observed_key in observations)
                            observations.add(observed_key)
                            if repeated_observations >= 4 or observations_without_effect >= 12:
                                question='这些观察还没找到可用的新线索。请指出目标位置或补充你指的对象。'
                                if step+1<self.max_decisions and time.monotonic()-started<self.max_seconds:
                                    try:
                                        if work:work['decisions']+=1
                                        question=stalled_question(self.model,latest['user'],work,self.body.snapshot(),action_records,
                                                                  'observation_without_new_actionable_information')
                                    except (ValueError,DecisionError):
                                        self.audit.write('lifecycle.jsonl',{'event':'stall_explanation_invalid','event_id':event_id})
                                    if epoch!=self._epoch:
                                        persist('paused_by_owner','late_decision_discarded');say(cancelled());break
                                wait_for_user(question, 'observation_without_new_actionable_information'); break
                        else:
                            failures = 0
                            observations_without_effect = repeated_observations = 0
                            observations.clear()
                        notice = None; persist('active')
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
                                     'action_failed':'动作执行遇到尚未确认的错误', 'action_timeout':'动作超过60秒，身体将重新连接；此动作不会自动重试'}
                            say('当前步骤受阻：' + reasons.get(receipt.get('status'),'恢复尝试仍未确认成功') + '；进度和回执已保存。'); break
                    if work and (step + 1) % 8 == 0:
                        work['checkpoints'] += 1; persist(work['status'], work['last_problem'])
                        self.audit.write('lifecycle.jsonl', {'event': 'task_checkpoint', 'event_id': event_id, 'step': step+1, 'continues': True})
                        say('进度已保存，正在继续处理剩余步骤。')
                    self.progress = ('执行中 · ' + work['title'][:32] if work else '观察与规划中') + ' · ' + str(step+1) + ' 次决定'
                else:
                    persist('paused_limit', 'task_decision_cap'); say('这项任务达到决定次数上限，进度与剩余工作已保存。')
            reply = '\n'.join(spoken) or '本轮进度已保存。'
            # A queued forget request may have deleted the suspended turn's
            # source/dependencies. Do not recreate its removed derived text.
            if not m.record(source) or any(not m.record(p) for p in parents):
                reply, parents = '这项任务的来源已删除，执行已结束。', []
            else:
                parents = [p for p in parents if m.record(p)]
            m.finish(event_id, reply, parents)
            self.audit.write('lifecycle.jsonl', {'event': 'turn_done', 'event_id': event_id, 'channel': channel,
                                               'receipt_count': len(receipts), 'task_status': work['status'] if work else None})
            return reply
        except Exception as error:
            if not execution_granted:
                self._execution_generation += 1
                if work and work['status'] == 'yielded':
                    persist('interrupted', 'input_requires_explicit_resume')
            if execution_granted and epoch==self._epoch:self.body.stop()
            problem = error.code if isinstance(error, (ProxyError,DecisionError)) else type(error).__name__
            if execution_granted and work and parents:
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
