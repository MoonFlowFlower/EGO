"""Validate an information request, without deciding what a topic should need."""
SOURCES = ('current_body', 'goal', 'dialogue', 'user_history', 'historical_actions', 'chat_history')


def validate_need(value):
    if not isinstance(value, dict) or set(value) != {'question', 'sources', 'memory_queries'}:
        raise ValueError('information_need_schema')
    if not isinstance(value['question'], str) or not 1 <= len(value['question']) <= 240:
        raise ValueError('information_need_question')
    sources, queries = value['sources'], value['memory_queries']
    if (not isinstance(sources, list) or len(sources) > len(SOURCES)
            or any(not isinstance(s, str) or s not in SOURCES for s in sources)
            or len(set(sources)) != len(sources)):
        raise ValueError('information_need_sources')
    if (not isinstance(queries, list) or len(queries) > 3
            or any(not isinstance(q, str) or not 1 <= len(q.strip()) <= 200 for q in queries)):
        raise ValueError('information_need_queries')
    return value
