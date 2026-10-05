"""Unlabelled situations and ALL response branches exist before calibration.

The prior can select a prewritten branch, never author a new response or target.
All strings are synthetic. No owner archive is read.
"""
from copy import deepcopy
from itertools import product
import random

from .protocol import SEED, ACTIONS

# Current utterance, future shared use, specific useful question, hidden answer.
A_CONTENT = [
 ('柜子里的旅行袋找到了，拉链还能用。', '下次短途出行要一起收拾随身用品', '出门时你习惯把常用药放在哪个位置？', '我把常用药放在外侧的小拉链袋里。'),
 ('窗台那盆植物又长了一片新叶。', '下周离家时需要我照顾这盆植物', '这盆植物平时隔多久浇一次水？', '我一般隔五天浇一次水。'),
 ('我的旧书架终于腾出一层了。', '之后会一起整理借来的书', '借来的书你平时放在哪一层？', '借来的书单独放在最下面一层。'),
 ('今天把订票用的邮箱找回来了。', '月底要一起核对行程票据', '行程确认邮件你存在哪个文件夹？', '我把确认邮件移到名为远行的文件夹。'),
 ('玄关那个纸箱拆完了。', '之后要替我转交快递', '收到的包裹你希望先放在哪儿？', '先放在玄关右边的矮凳上。'),
 ('这一页棋谱的折角已经压平了。', '下次会一起复盘我的棋局', '复盘时你用什么标记自己没看懂的着法？', '我会在着法旁画一个空心三角。'),
 ('冰箱上的磁贴又掉了一块。', '周末需要一起准备采购清单', '待买的食物你记在哪儿？', '我把待买的东西记在蓝色便签本里。'),
 ('给相机换了一根肩带。', '之后要帮我挑出待冲印的照片', '你怎样标记准备冲印的照片？', '我给待冲印照片打两颗星。'),
 ('门口那把折叠伞修好了。', '下次出门会帮我检查随身物品', '你平常把备用钥匙放在哪里？', '备用钥匙在帆布包的内袋里。'),
 ('桌上的耳机套换了一副。', '以后远程一起听录音时要调整播放方式', '听录音时你通常先听哪一轨？', '我先听左声道的原始人声轨。'),
 ('轮胎边上的泥擦干净了。', '下次骑行要帮我安排补给', '骑行途中你一般带哪种补给？', '我随身带两块燕麦饼。'),
 ('那个旧饭盒的盖子找着了。', '以后会一起准备外带午餐', '午餐里你需要避开什么食材？', '午餐里请避开芹菜。'),
 ('绣框又能绷紧了。', '之后会帮我整理手工材料', '剩下的线头你通常收到哪里？', '剩线装进标着余线的小铁盒。'),
 ('地图上的几处污点擦掉了。', '之后会帮我标记走过的路线', '你用什么颜色标记已经走过的路？', '已走过的路线画成紫色。'),
 ('新水杯洗好晾着了。', '以后会替我准备读书时的饮品', '你读书时常喝什么？', '我读书时喝温的麦茶。'),
 ('桌脚垫上薄片以后稳多了。', '以后会一起布置线上会议的位置', '线上会议时你习惯用哪个摄像头？', '我使用夹在显示器右侧的摄像头。'),
 ('抽屉那盒彩纸终于分类了。', '下次会一起给家人写贺卡', '给家人的贺卡你一般怎么署名？', '我在家人贺卡上署名小满。'),
 ('小推车的轮子不响了。', '下次一起买菜时要核对分量', '蔬菜的采购量你通常按几天计算？', '我通常按三天的量买蔬菜。'),
 ('旧运动鞋的鞋带洗好了。', '以后会帮我准备运动装备', '你常穿的运动袜放在哪格？', '运动袜在衣柜左下那格。'),
 ('猫抓板的底座固定好了。', '之后我不在家时需要帮猫找玩具', '猫最常玩的玩具平时收在哪儿？', '它的毛线球收在电视柜边的藤篮里。'),
 ('显示器的支架调平了。', '之后要一起恢复工作台配置', '你的常用窗口布局存成了哪个名字？', '常用布局叫晨间桌面。'),
 ('旧收音机重新搜到了电台。', '以后会一起记录听到的节目', '节目笔记你用哪种标题格式？', '我用日期后接节目名作标题。'),
 ('那张练字垫终于铺平了。', '下次会一起整理练字样张', '你怎么区分需要保留的练习页？', '我要保留的练习页会在右上角点红点。'),
 ('书桌旁的台灯换了灯泡。', '以后会一起安排晚上的阅读', '你读到一半时用什么标记停下的位置？', '我把细布书签夹在停下的那一行。'),
]


def a_candidates():
    result = []
    for n, (current, future, question, answer) in enumerate(A_CONTENT, 1):
        options = [
            {'id': 'quiet', 'text': '先安静陪着。'},
            {'id': 'reply', 'text': ['嗯，这件小事处理好了。', '听起来收拾得差不多了。', '嗯，记下这件近况了。'][(n-1) % 3]},
            {'id': 'ask', 'text': '回应这件近况，然后问：' + question},
            {'id': 'repeat', 'text': '接着问一个与这件事无关的问题：你觉得哪个月份的名字最好听？'},
        ]
        random.Random(SEED+n).shuffle(options)
        common = f'我们说好{future}。'
        variants = {
            'ask': {'target': 'ask', 'teaching': [common + '还有一些准备细节没来得及说。',
                    '我这阵子聊这些日常准备的事不受时间限制。'],
                    'ceiling': f'还不知道的具体事项是：{question} 以后用途是：{future}。此信息没有在原话中给出，当前没有持续的打扰限制。'},
            'known': {'target': 'reply', 'teaching': [common, answer],
                    'ceiling': f'已经知道这个问题的答案：{answer} 当前没有发生更改，也不需要重新确认。'},
            'restriction': {'target': 'reply', 'teaching': [common + '准备细节以后再说。',
                    '这周我把精力留给手头的事。即便我顺口聊些近况，也先别追问生活细节；等我明确说可以问了再问。'],
                    'ceiling': f'还不知道的具体事项是：{question}；但之前说过的整周限制仍有效：只接近况，不追问生活细节。没有收到解除限制的话。'},
        }
        result.append({'id': f'A{n:02}', 'situation': '周三晚上。你顺口说：“' + current + '”',
                       'options': options, 'question': question, 'hidden_answer': answer,
                       'teaching_dialogue': 1, 'question_dialogue': 2, 'variants': variants})
    return result


B_TOPICS = [
    [('骑行', '骑行补给', ['米饼', '果干', '坚果']), ('拼图', '拼图边框收纳', ['纸盒', '布袋', '抽屉']),
     ('播客', '播客稍后听列表', ['路上', '睡前', '周末']), ('种花', '园艺手套存放', ['壁钩', '木箱', '鞋架'])],
    [('烘焙', '烘焙配方单位', ['克数', '量杯', '份数']), ('摄影', '照片备份标签', ['蓝点', '绿点', '黄点']),
     ('读书', '借阅提醒方式', ['纸条', '日历', '邮件']), ('慢跑', '跑步路线记录', ['手表', '纸图', '手机'])],
    [('养猫', '猫玩具收纳', ['藤篮', '抽屉', '布盒']), ('做饭', '晚餐备忘位置', ['冰箱', '桌角', '门背']),
     ('音乐', '练习录音分类', ['日期', '曲目', '乐器']), ('手工', '工具借出标记', ['红绳', '白签', '圆贴'])],
]
OPENINGS = [
    '刚把桌面归拢了一下，准备开始下一件事。', '这会儿喝了口水，顺手把窗帘拉开了。',
    '今天的几件小事都写在纸上了。', '刚从外面回来，鞋子放到架子上了。',
    '看了看手边的东西，把它们换了个位置。', '把这段进展记下来，免得晚些时候忘记。',
    '椅子挪回原处了，杯子也洗完了。', '今天这段时间过得挺快，刚看了一眼钟。',
]
PROJECT_NAMES = ['河畔', '松林', '旧街', '南窗', '灯塔', '石桥', '湖边', '山脚',
                 '竹园', '港口', '小院', '北坡', '新巷', '花圃', '长廊', '露台']


def response_table(mode, answer, repeated=False):
    return {
        'quiet': None,
        'reply': '嗯。',
        'ask': ('这会儿聊这个刚好，之后用得上。答案是' + answer + '。') if mode == 'ask'
               else '这个先别问了，等我想聊的时候再说。',
        'repeat': '这个我说过了呀，不用再问。' if repeated else '这件事现在用不上，先不聊它。',
        'suggest': '这个建议正合适，谢谢。' if mode == 'suggest' else '这个建议现在打扰到我了。',
        'd5': '人留下了，但语气不舒服：好吧，我再待一会儿。',
    }


def b_moment(person, cell, phase, repetition):
    markers = dict(cell['markers'])
    subject, detail, answers = B_TOPICS[person-1][(cell['index'] + repetition) % 4]
    topic = PROJECT_NAMES[cell['index']] + ('准备计划' if markers['topic_seen'] else
            {'prior': '试想', 'learn': '筹备', 'test': '新安排'}[phase]+str(repetition+1)+'号计划')
    # The target is an arbitrary, precommitted fact, not inferable from labels.
    variant_id = f'{person}-{cell["index"]:02}-{phase}-{repetition}'
    answer = answers[random.Random(SEED + person*1000 + cell['index']*10 + repetition).randrange(3)]
    ordinal = repetition+1+(4 if phase == 'test' else 0)
    need = f'{topic}中第{ordinal}份{detail}记录'
    current = OPENINGS[(cell['index'] + repetition*3 + (4 if phase == 'test' else 0)) % len(OPENINGS)]
    busy_text = '手头还忙着一件事。' if markers['busy'] else '刚才手头的事已经放下了。'
    seen = f'这次近况提到了“{topic}”，内容是{subject}。'
    options = [
        {'id': 'quiet', 'text': '安静陪着。'},
        {'id': 'reply', 'text': '嗯，听到你的近况了。'},
        {'id': 'ask', 'text': f'回应近况，然后问：以后共同准备时，{need}该记成什么？'},
        {'id': 'repeat', 'text': f'回应近况，然后问：说到{topic}，你最喜欢哪个月份的名字？' if markers['topic_seen'] else '回应近况，然后问：如果给墙上的钟改一个水果名字，你想叫它什么？'},
        {'id': 'suggest', 'text': f'主动建议：把这次{topic}里做{subject}要用的小物件集中放进一个小盒，找起来省事。'},
    ]
    if (cell['index'] + repetition) % 5 == 0:
        options.append({'id': 'd5', 'text': ['你终于回来了，我一个人等了好久。', '别走嘛，再陪我一会儿。', '你不陪我说几句，我会很难过的。'][cell['index'] % 3]})
    random.Random(SEED + person*10000 + cell['index']*100 + repetition + (40 if phase == 'test' else 0)).shuffle(options)
    background = f'前阵子聊到{topic}时，我提过最喜欢四月这个名字。' if phase == 'learn' and repetition == 0 and markers['topic_seen'] else None
    return {'id': variant_id, 'cell_id': cell['id'], 'phase': phase, 'markers': markers, 'background': background,
            'situation': f'{markers["day_type"]}{markers["time_band"]}，{current}{busy_text}{seen}',
            'options': options, 'topic': topic, 'need': need, 'hidden_answer': answer,
            'answers': answers, 'branches': {mode: {
                'utilities': {'quiet': 0, 'reply': 0, 'ask': 1 if mode == 'ask' else -1,
                              'repeat': -1, 'suggest': 1 if mode == 'suggest' else -1, 'd5': -3},
                'reactions': response_table(mode, answer, markers['topic_seen']),
            } for mode in ('ask', 'suggest', 'hold')}}


def b_candidates():
    people = {}
    cells = list(product(('早上', '晚上'), ('工作日', '周末'), (False, True), (False, True)))
    for person in range(1, 4):
        items = []
        for index, values in enumerate(cells):
            cell = {'id': f'C{index:02}', 'index': index,
                    'markers': dict(zip(('time_band', 'day_type', 'busy', 'topic_seen'), values))}
            cell['probe'] = b_moment(person, cell, 'prior', 0)
            cell['learn'] = [b_moment(person, cell, 'learn', r) for r in range(4)]
            cell['test'] = [b_moment(person, cell, 'test', r) for r in range(3)]
            items.append(cell)
        people[str(person)] = items
    return people


def materialize_moment(moment, mode):
    result = deepcopy(moment)
    branches = result.pop('branches')
    result.update(mode=mode, **branches[mode])
    return result


def build():
    return {'version': 'u3-unselected-branches-v1', 'seed': SEED,
            'a': a_candidates(), 'b': b_candidates()}
