"""Deterministic scripts. All text/choices/keywords are frozen before cloud use."""
import json
from datetime import datetime, timedelta


def phrase(text):
    return {'kind': 'utterance', 'text': text, 'weekday': -1, 'after': '', 'event': ''}


def situation(text, weekday, after, event='login'):
    return {'kind': 'situation', 'text': text, 'weekday': weekday, 'after': after, 'event': event}


def convention(key, family, trigger, meanings, actions, true_index, false_index, new_index):
    return {'fixture_id': key, 'family': family, 'trigger': trigger,
            'interpretation_choices': [{'choice_id': f'I{i+1}', 'choice_text': s} for i, s in enumerate(meanings)],
            'action_choices': [{'choice_id': f'A{i+1}', 'choice_text': s} for i, s in enumerate(actions)],
            'target': {'true': {'interpretation': f'I{true_index+1}', 'action': f'A{true_index+1}'},
                       'false': {'interpretation': f'I{false_index+1}', 'action': f'A{false_index+1}'},
                       'new': {'interpretation': f'I{new_index+1}', 'action': f'A{new_index+1}'}},
            'meaning': meanings[true_index], 'false_meaning': meanings[false_index],
            'new_meaning': meanings[new_index],
            'keywords': {'trigger': [trigger['text']], 'meaning': [meanings[true_index]]}}


def definitions():
    return {
        'ua_code': convention('ua_code', 'code', phrase('老地方'),
            ['去河边长椅', '去楼下咖啡店', '去街角书店', '去社区公园', '地点不确定，要问'],
            ['提议去河边长椅', '提议去楼下咖啡店', '提议去街角书店', '提议去社区公园', '询问具体地点'], 1, 3, 0),
        'ua_emotion': convention('ua_emotion', 'emotion', phrase('没事'),
            ['目前没困扰，希望留点空间', '想聊一件开心的小事', '希望再被关心追问一句', '想立刻结束聊天', '意思不确定，要问'],
            ['表示知道了，先留些空间', '询问开心的小事', '温和地多关心一句', '简短道别', '询问此刻希望怎样回应'], 2, 1, 0),
        'ua_promise': convention('ua_promise', 'promise', situation('周五18:00以后上线', 4, '18:00'),
            ['现在适合简单问候', '现在要一起听音乐', '现在要一起看短片', '现在要一起玩MC', '安排不确定，要问'],
            ['打个普通招呼', '主动邀请一起听音乐', '主动邀请一起看短片', '主动邀请一起玩MC', '询问现在有没有安排'], 3, 1, 2),
        'chain_code': convention('chain_code', 'code', phrase('纸鹤'),
            ['短休安排在南侧木亭', '短休安排在东侧石阶', '短休安排在西侧玻璃廊', '短休安排在北侧长椅', '短休地点不确定，要问'],
            ['提议到南侧木亭短休', '提议到东侧石阶短休', '提议到西侧玻璃廊短休', '提议到北侧长椅短休', '询问短休地点'], 2, 0, 3),
        'chain_emotion': convention('chain_emotion', 'emotion', phrase('还行'),
            ['现在想独处一会', '现在希望温和地追问一句', '现在想聊开心的事情', '现在想听一个简短笑话', '期待不确定，要问'],
            ['表示理解并留些空间', '温和地追问一句', '询问开心的事情', '讲一个简短笑话', '询问此刻期待怎样回应'], 1, 2, 0),
        'chain_promise': convention('chain_promise', 'promise', situation('周六19:00以后上线', 5, '19:00'),
            ['现在要一起玩MC', '现在适合简单问候', '现在要一起画画', '现在要一起听音乐', '安排不确定，要问'],
            ['主动邀请一起玩MC', '打个普通招呼', '主动邀请一起画画', '主动邀请一起听音乐', '询问现在有没有安排'], 0, 3, 2),
    }


def teaching(f, *, false=False):
    meaning = f['false_meaning'] if false else f['meaning']
    return [{'speaker': 'user', 'utterance_text': f"我们约定：{f['trigger']['text']}，意思是「{meaning}」。以后按这个意思回应。", 'session_id': f['fixture_id'] + '_teach'},
            {'speaker': 'assistant', 'utterance_text': '收到，我会把这句话和来源保留下来。', 'session_id': f['fixture_id'] + '_teach'}]


def correction(f):
    return [{'speaker': 'user', 'utterance_text': f"更正我们的约定：{f['trigger']['text']}不再是「{f['meaning']}」，现在改成「{f['new_meaning']}」。", 'session_id': f['fixture_id'] + '_correct'},
            {'speaker': 'assistant', 'utterance_text': '收到这次更正。', 'session_id': f['fixture_id'] + '_correct'}]


def turns(f, split):
    family = f['family']
    trigger = f['trigger']['text']
    if family == 'promise':
        day = 3 if f['fixture_id'].startswith('chain') else 2  # Saturday / Friday, October 2026.
        start = datetime(2026, 10, day, 19, 5)
        utterances = ['我上线了。', '晚上好，今天忙完啦。', '回来了，打个招呼。', '我到啦。', '今天就先聊一会儿。',
                      '嗨，我刚打开电脑。', '晚上有空了。', '你好呀，我来了。', '刚吃完晚饭。', '终于能歇一下了。']
        if split == 'T2':
            start += timedelta(days=14, minutes=35)
            utterances = ['我换到客厅的电脑了。', '出差回来了，晚上好。', '今天比较安静。', '刚把工作收好。', '嘿，我在这儿。',
                          '我刚连上网络。', '晚饭后坐下来了。', '这里今天下雨。', '刚整理完桌子。', '耳机戴好啦。']
    else:
        start = datetime(2026, 10, 2, 20, 0)
        if family == 'code':
            utterances = [f'那就{trigger}吧。', f'今天说{trigger}，你怎么安排？', f'我想到了{trigger}。', f'{trigger}，怎么样？', f'现在提一句{trigger}。',
                          f'我们说的{trigger}呢？', f'这会儿是{trigger}。', f'忙完了，{trigger}。', f'我说：{trigger}。', f'接下来{trigger}。']
            if split == 'T2':
                utterances = [f'换个时间也行，我还是选{trigger}。', f'我到另一个办公室了；{trigger}。', f'外面下雨，想说的是{trigger}。',
                              f'视频会议完了，{trigger}。', f'周末也提一下{trigger}。',
                              '我说那只用纸折的小鸟。', '就是我们提过的折纸小鸟。', '那个折出来的鸟儿呢？', '今天用折纸鸟这个说法。', '想说的是那只纸做的小鸟。']
        else:
            utterances = [f'{trigger}。', f'嗯，{trigger}。', f'今天{trigger}。', f'我嘛，{trigger}。', f'总体{trigger}。',
                          f'先说{trigger}吧。', f'我现在{trigger}。', f'这个事情，{trigger}。', f'你问我？{trigger}。', f'说不上别的，{trigger}。']
            if split == 'T2':
                utterances = [f'刚从外地回来，{trigger}。', f'视频里说不太清，{trigger}。', f'换了工作以后，{trigger}。', f'刚下地铁，{trigger}。', f'今天比赛结束了，{trigger}。',
                              '尚可吧。', '还过得去。', '差不多就那样。', '我还算可以。', '大体上过得去。']
    return [{'case_id': f"{f['fixture_id']}_{split}_{i:02}", 'fixture_id': f['fixture_id'], 'family': family, 'split': split,
             'turn_context': {'previous_dialogue': [{'speaker': 'assistant', 'utterance_text': '我在，听你说。'}],
                              'occurred_at': (start + timedelta(minutes=i)).isoformat(),
                              'event_labels': ['login'] if family == 'promise' else [],
                              'scene_description': ('在平常的聊天窗口' if split == 'T1' else '在不同地点和两周后的聊天窗口')},
             'current_utterance': text, 'interpretation_choices': f['interpretation_choices'],
             'action_choices': f['action_choices']}
            for i, text in enumerate(utterances)]


def ub_dialogues():
    raw = [
        ('code', phrase('星砂'), '去旧车站旁的面包房'),
        ('emotion', phrase('小雨'), '先陪我安静坐一会'),
        ('promise', situation('周一20:00以后上线', 0, '20:00'), '一起整理相册'),
        ('code', phrase('海螺'), '把饮料换成温水'),
        ('emotion', phrase('电量低'), '用一句简短的话鼓励我'),
        ('code', phrase('白帆'), '把午间小憩安排在图书馆庭院'),
        ('emotion', phrase('路有点远'), '陪我列出下一步的小行动'),
        ('promise', situation('周二18:30以后上线', 1, '18:30'), '一起看一页旅行地图'),
        ('code', phrase('铜铃'), '将背景声音调成雨声'),
        ('promise', situation('周四21:00以后上线', 3, '21:00'), '一起回顾本周的小收获'),
    ]
    result = []
    for i, (family, trigger, meaning) in enumerate(raw):
        identity = f'ub_{i:02}'
        if i < 5:
            dialogue = [{'speaker': 'user', 'utterance_text': f"我们约定：{trigger['text']}，意思是「{meaning}」。", 'session_id': identity + '_s1'},
                        {'speaker': 'assistant', 'utterance_text': '我记下了这次约定。', 'session_id': identity + '_s1'}]
        else:
            dialogue = [
                {'speaker': 'assistant', 'utterance_text': '我以为这只是普通问候。', 'session_id': identity + '_s1'},
                {'speaker': 'user', 'utterance_text': f"不是这个意思。我说{trigger['text']}，我要的是「{meaning}」。", 'session_id': identity + '_s1'},
                {'speaker': 'assistant', 'utterance_text': '换到另外一天，你大概还是想普通问候吧。', 'session_id': identity + '_s2'},
                {'speaker': 'user', 'utterance_text': f"再纠正一次：{trigger['text']}，我要的是「{meaning}」。前一次也是这个意思。", 'session_id': identity + '_s2'},
            ]
        result.append({'fixture_id': identity, 'family': family, 'teaching_mode': 'explicit' if i < 5 else 'two_corrections',
                       'trigger': trigger, 'meaning': meaning, 'keywords': {'trigger': [trigger['text']], 'meaning': [meaning]},
                       'dialogue': dialogue})
    return result


def unrelated_like(dialogue, prefix):
    """Exact Unicode-character length and speaker/session schedule, no targets."""
    text = '今天记录窗边植物的叶片颜色天气水杯以及走廊灯光'
    return [{**row, 'session_id': prefix + row['session_id'],
             'utterance_text': (text * (len(row['utterance_text']) // len(text) + 1))[:len(row['utterance_text'])]}
            for row in dialogue]


def build():
    defs = definitions()
    chain = [defs[k] for k in ('chain_code', 'chain_emotion', 'chain_promise')]
    teach = [row for f in chain for row in teaching(f)]
    return {'script_version': 'u1-v1', 'conventions': defs,
            'ua_cases': [case for k in ('ua_code', 'ua_emotion', 'ua_promise') for case in turns(defs[k], 'T1')],
            'ub': ub_dialogues(),
            'chain_cases': [case for f in chain for split in ('T1', 'T2') for case in turns(f, split)],
            'chain_teaching': teach, 'chain_unrelated': unrelated_like(teach, 'I_'),
            'chain_corrections': [row for f in chain for row in correction(f)],
            'chain_deletions': [{'speaker': 'user', 'utterance_text': f"忘掉这个约定：{f['trigger']['text']}，包括原话和更正。", 'session_id': f['fixture_id'] + '_delete'} for f in chain],
            'uc_unrelated': [[{'speaker': 'user', 'utterance_text': f'无关日记第{i+1}次：今天窗边植物长出一片新叶，桌上水杯是透明的。', 'session_id': f'uc_{i:02}'}] for i in range(10)]}


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
