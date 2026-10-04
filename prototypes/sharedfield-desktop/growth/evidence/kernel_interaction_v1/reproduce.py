"""Offline defect witnesses for 476e76ab; not model or Minecraft acceptance.

Run from growth: python evidence/kernel_interaction_v1/reproduce.py
Only temporary test databases and a deterministic body are used. No credentials,
provider calls, official owner database writes, or game actions occur.
Assertions intentionally describe the defective baseline, not desired behavior.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from companion.context import conversation_context
from companion.harness import Harness
from companion.intent import route_input
from companion.memory import Memory
from companion.test_harness import Body, Model, decision, goal, place
from companion.test_kernel import Audit
from companion.work import create_work, fingerprint, preliminary_completion, save_work


def main():
    results = []
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'state.sqlite'
        body = Body()
        memory = Memory(path)
        source, _ = memory.begin('old_house', 'verification', '放置八块木板')
        old = create_work(goal(8), body.snapshot(), source)
        old['status'] = 'blocked'
        save_work(memory, old, [source])
        memory.finish('old_house', '施工受阻。', [source])
        memory.close()
        model = Model(decision(action={'name': 'approach', 'args': {}}), place())
        harness = Harness(path, model, body, Audit(), max_decisions=2,
                          input_router=lambda *args: {'mode': 'task', 'task_kind': 'ordinary'})
        harness.run('come', 'verification', '过来一下')
        memory = Memory(path)
        current = memory.goal()['work']
        names = [action['name'] for action in body.actions]
        assert names == ['approach', 'place'] and current['task_id'] == old['task_id']
        results.append({'id': 'D1', 'defect_observed': True,
                        'actions_after_come': names, 'same_old_task': True,
                        'note': 'Scripted model decision witnesses missing task ownership guard; no new model inference.'})

        state = body.snapshot()
        state['owner']['distance'] = 95
        context = conversation_context(memory, '原木在这里，你去哪儿啊', 'chat', state)
        assert 'current_body' not in context and 'goal' not in context
        results.append({'id': 'D2', 'defect_observed': True, 'chat_context_keys': sorted(context),
                        'body_distance_supplied_to_projection': 95})
        router = Model({'mode': 'chat', 'task_kind': 'ordinary', 'request_quote': ''})
        route_input(router, '这儿', memory.goal(), [])
        assert set(router.contexts[0]) == {'current_user', 'pending_title', 'matched_conventions'}
        results.append({'id': 'D3', 'defect_observed': True,
                        'router_context_keys': sorted(router.contexts[0]),
                        'note': 'Projection witness only; live route choices are separately preserved in owner records.'})
        memory.close()

        moved_owner = copy.deepcopy(state)
        moved_owner['owner']['distance'] = 1
        assert fingerprint(state) == fingerprint(moved_owner)
        results.append({'id': 'D4', 'defect_observed': True,
                        'owner_distances': [95, 1], 'same_dedup_fingerprint': True})

        pickup_goal = {'title': '捡起用户丢的八个原木', 'steps': ['捡起并核对'],
                       'done_when': [{'kind': 'gained', 'item': 'oak_log', 'count': 8}]}
        inventory_work = create_work(pickup_goal, state, 'test_source')
        arbitrary_gain = copy.deepcopy(state)
        arbitrary_gain['inventory']['oak_log'] += 8
        assert preliminary_completion(inventory_work, arbitrary_gain)['satisfied']
        results.append({'id': 'D5', 'defect_observed': True,
                        'gained_accepts_without_pickup_or_source_receipts': True,
                        'note': 'Potential false acceptance in contract; live pickup did not complete.'})

        second_body = Body()
        question = '你丢的原木具体在哪里？'
        second_model = Model(
            decision(reply=question, goal=goal(8), action={'name': 'inspect', 'args': {}}),
            decision(reply='缺少目标位置。', status='blocked'))
        second_harness = Harness(Path(directory) / 'question.sqlite', second_model, second_body, Audit(),
                                 max_decisions=2,
                                 input_router=lambda *args: {'mode': 'task', 'task_kind': 'ordinary'})
        second_harness.run('question', 'verification', '捡一下我丢的原木')
        assert question not in second_body.speech and second_model.calls == 2
        results.append({'id': 'D6', 'defect_observed': True,
                        'action_accompanying_question_emitted': False,
                        'decisions_without_user_answer': second_model.calls})
    print(json.dumps({'kind': 'offline_defect_witnesses', 'baseline': '476e76ab',
                      'model_calls': 0, 'game_actions': 0, 'results': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
