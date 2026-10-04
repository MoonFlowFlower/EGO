"""Project durable records into current facts and explicitly historical evidence."""
import copy
from datetime import datetime


def user_history(memory):
    # Generated replies are retained for replay/audit, never recycled as observations.
    return [{**row, 'authority': 'past_user_utterance_not_current_observation'}
            for row in memory.context() if row['role'] == 'user']


def historical_actions(memory):
    result = []
    for row in memory.recent_actions():
        receipt = row.get('receipt', {})
        result.append({'record_id': row['record_id'], 'event_id': row.get('event_id'),
                       'authority': 'past_action_result_not_current_body', 'action': row.get('action'),
                       'result': {key: copy.deepcopy(receipt[key]) for key in
                                  ('verified', 'executed', 'status', 'gained', 'lost', 'position') if key in receipt}})
    return result


def conversation_context(memory, text, mode, state, *, capability_notice=None):
    online = state.get('offline') is False
    current = {'available': online, 'sampled_at': datetime.now().astimezone().isoformat(),
               'source': 'body.snapshot', 'state': copy.deepcopy(state) if online else
               {'offline': True, 'reason': state.get('reason', 'body_offline')},
               'semantics': 'empty/null are observed empty; missing fields are unknown; only this snapshot describes the current body'}
    saved = memory.goal()
    goal = None
    if saved:
        work = saved.get('work', {})
        goal = {'record_id': saved['record_id'], 'title': saved['title'], 'status': saved['goal_status'],
                'task_id': work.get('task_id'), 'source_id': work.get('source_id'),
                'done_when': work.get('done_when'), 'steps': work.get('steps'),
                'verified_progress': {key: copy.deepcopy(work[key]) for key in
                                      ('placed', 'delivered', 'follow_started', 'actions', 'completion') if key in work},
                'last_attempt_problem': work.get('last_problem'),
                'semantics': 'durable task progress; last_attempt_problem is historical, not proof of a current body defect'}
    return {'current_user': text, 'mode': mode, 'current_body': current, 'goal': goal,
            'user_history': user_history(memory), 'conventions': memory.library.cards(),
            'historical_actions': historical_actions(memory), 'capability_notice': capability_notice}
