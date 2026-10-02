"""Action receipt + deliberately narrow natural-language contradiction guard.

This is not an independent semantic verifier. It recognizes explicit near-term
statements about the finite sandbox actions, repairs recognized contradictions,
and discloses repairs. Novel paraphrases, feelings and narrative truth are not
certified. Original output remains recorded as an exogenous event payload.
"""
from __future__ import annotations
from copy import deepcopy
import re
from .world import ROOM_NAMES

LABELS={'move':'前往','scan':'观察路况','survey':'调查这里','calibrate':'校准自己的工具','rest':'休整恢复',
        'repair':'维护工具','sleep':'暂时休息','wait_partner':'等你准备好'}

def action_words(action):
    label=LABELS[action['kind']]
    return label+('「'+ROOM_NAMES[action['target']]+'」' if 'target' in action else '')


def contract(report):
    f=report['report']['focus']
    return {'decision_id':f['id'],'state_id':report['id'],'goal_id':f['goal']['id'],
            'action':deepcopy(f['action']),'action_words':action_words(f['action']),
            'basis':f['basis'],'world_tick':report['world_tick'],
            'status':'selected_not_executed','conditional_on':'remaining authorized steps and no new observation invalidating plan',
            'not_selected_alternatives':[{'action':deepcopy(c['action']),'status':'not_selected'}
                 for c in f.get('candidates',[]) if c['action']!=f['action']][:2]}

# Look for near-term self-commitments, not arbitrary action words in recollections.
CUES=re.compile(r'(?:我(?:打算|准备|决定|会|想先|要先|先)|接下来(?:我)?|下一步|暂时停下|先做一次|先用传感|先把)')
VERBS=[('calibrate',r'校准'),('scan',r'扫描|扫一下|扫清楚|观察.{0,4}路况|检查路况'),
       ('survey',r'测绘|调查这里|调查脚下|调查当前'),('rest',r'休整|歇回来|恢复体力'),
       ('repair',r'维护工具|修理工具'),('wait_partner',r'等你|等待你|停下等'),
       ('move',r'动身|走向|前往|走到|往.{0,10}走|去「?[^，。；！？]{0,8}')]
UNCERTAIN_CHOICE=re.compile(r'(?:还没|尚未|没有)(?:完全)?(?:决定|定下来|选好)')


def guard_speech(raw,intent,historical=False):
    parts=re.split(r'(?<=[。！？!?])|\n+',raw);kept=[];issues=[]
    for sentence in parts:
        if not sentence:continue
        cue=CUES.search(sentence);bad=None
        if (re.search(r'我(?:还没|尚未|没有)(?:完全)?(?:决定|定下来|选好)',sentence)
            and not re.search(r'[？?]|你说|你问|如果',sentence)):
            bad='selected_plan_reported_as_undecided'
        if cue:
            segment=sentence[cue.start():]
            # Explicitly hypothetical/later alternatives are not a current promise.
            if not re.search(r'^(?:如果|以后|之后|将来)|可以考虑|或许|也许',sentence[:cue.start()+4]):
                matches=[]
                for kind,pattern in VERBS:
                    hit=re.search(pattern,segment)
                    if hit:
                        prefix=segment[max(0,hit.start()-5):hit.start()]
                        if not re.search(r'不(?:会|想|再|要)?$|而不是$',prefix):matches.append((hit.start(),kind,hit))
                if matches:
                    _,kind,hit=min(matches,key=lambda x:x[0])
                    if historical:bad='future_commitment_from_old_snapshot'
                    elif kind!=intent['action']['kind']:bad='unselected_action_announced'
                    elif kind in ('move','scan'):
                        mentioned=[i for i,n in enumerate(ROOM_NAMES) if n in segment[hit.start():hit.end()+18]]
                        if mentioned and intent['action'].get('target') not in mentioned:bad='wrong_target_announced'
        if bad:issues.append(bad)
        else:kept.append(sentence)
    if issues:
        next_line=('提问时我准备'+intent['action_words']+'；期间已有新观测，接下来会依据更新后的计划。' if historical
                   else '在允许继续行动时，我下一步准备'+intent['action_words']+'。')
        kept.append(next_line)
    return ''.join(kept),{'corrected':bool(issues),'issues':issues,
                         'scope':'finite-action near-term phrasing only; NOT full semantic fidelity verification'}
