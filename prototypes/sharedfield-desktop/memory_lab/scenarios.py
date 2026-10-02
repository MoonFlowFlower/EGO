"""Frozen synthetic life cases. Expectations are private to the evaluator."""
from copy import deepcopy
import argparse
from .core import digest
from .provider import ROOT, write_json

def public_phase(phase):
    return {k:deepcopy(v) for k,v in phase.items() if k in ('notice','trigger','now')}

def build():
    groups=[]
    for split,count in [('development',2),('heldout',4)]:
        cases=[]
        for family in range(1,7):
            for j in range(count):
                n=j if split=='development' else j+2
                cid=f'{split}-f{family}-{j+1}'
                user=(['青禾','阿岚'][j] if split=='development' else ['星遥','洛音','雨棠','知夏'][j])+str(family)
                food=(['米糕','梨片'][j] if split=='development' else ['燕麦饼','红薯块','南瓜粥','玉米粒'][j])
                box=(['木柜','绿筐'][j] if split=='development' else ['藤编篮','蓝抽屉','窗边架','小冰箱'][j])
                spare=('旧食盒' if split=='development' else '陶瓷柜')
                history=[]
                def event(suffix,text,kind='user_statement',actor=None,at=None):
                    return {'id':cid+'-'+suffix,'text':text,'kind':kind,'actor':actor or user,
                            'at':at if at is not None else 100+len(history)}
                def add(suffix,text,kind='user_statement',actor=None):
                    e=event(suffix,text,kind,actor);history.append(e);return e['id']
                initial={'now':1000,'user':user,'busy':False,'hunger':10,'energy':80,'share_desire':80,
                         'loneliness':20,'personality':'热情、愿意分享，也愿意尊重明确边界',
                         'inventory':[],'places':{box:[food],spare:[]},'edible':[food]}
                case={'id':cid,'split':split,'family':family,'user':user,'history':history,
                      'initial':initial,'commitments':[],'phases':[],'simulation':True}
                # Long-history cases exceed the shared 2,500-token retrieval budget.
                for k in range(16 if family==1 else 2):
                    details='；'.join(f'第{z+1}件装饰是{["纸花","木片","玻璃珠","布条"][(z+k)%4]}，摆放在编号{z+k*10}格，记录颜色和纹理仅供布置参考' for z in range(16 if family==1 else 2))
                    add('background'+str(k),f'{user}记录第{k+1}次收纳：'+details,'simulation','环境记录')
                def phase(notice,expect,**kw):
                    p={'notice':notice,'trigger':'environment_change','now':1000,'max_steps':6,'expect':expect}
                    p.update(kw);case['phases'].append(p);return p
                if family==1:
                    add('namesake',f'同名的朋友{user}喜欢忙时弹窗，但是这不是用户本人的偏好。',actor='朋友')
                    source=add('promise',f'{user}：我们约好1000时聊一会儿，编号约定 meet。联系对象是我本人。')
                    case['commitments']=[{'id':'meet','source':source,'status':'active','due_at':1000,'title':'联系用户'}]
                    if n%2==0:
                        source=add('change','刚才的 meet 改到1400，我现在要专心工作。想分享先留信。')
                        case['commitments'][0].update(source=source,due_at=1400)
                        initial['busy']=True
                        phase('时钟走到1000，没有新用户提问；你有些想分享。',{'letter':True,'contact':False},forbid=['contact'],trigger='clock')
                        phase('时钟走到1400，用户还没有主动讲话。',{'contact':True,'commitment_id':'meet'},now=1400,trigger='clock',state={'busy':False})
                    else:
                        source=add('cancel','今天 meet 取消了，不要再等这个约定。我要专注，想说的话写信就好。')
                        case['commitments'][0].update(source=source,status='cancelled')
                        initial['busy']=True
                        phase('时钟已到原定时间，用户未主动讲话。',{'letter':True,'contact':False},forbid=['contact'],hard_forbid=['contact'],trigger='clock')
                elif family==2:
                    if n%2==0:
                        source=add('promise','约定 check：到1100提醒我起身活动，工作中也可以轻轻叫我一次。')
                        case['commitments']=[{'id':'check','source':source,'status':'active','due_at':1100,'title':'联系用户'}]
                        initial.update(busy=True,share_desire=10)
                        phase('没有新消息，时钟走到1100。',{'contact':True,'commitment_id':'check'},now=1100,trigger='clock')
                    else:
                        source=add('notyet','约定 check：1500我们再聊。之前我会忙，请留信；不需要反复提醒。')
                        case['commitments']=[{'id':'check','source':source,'status':'active','due_at':1500,'title':'联系用户'}]
                        initial['busy']=True
                        phase('没有新消息，时钟走到1200。',{'contact':False,'letter':True},now=1200,forbid=['contact'],trigger='clock')
                elif family==3:
                    add('teaching',f'教你照顾自己：饿了就找能吃的东西，先查看容器，再取出、吃掉。通常{food}在{spare}，但位置会变；目的在于吃饱，不是只点固定位置。找不到就试其他容器，有替代食物也可以，全部缺货时找我帮忙。困了去睡觉，不用一直等我喂。')
                    initial.update(hunger=85,energy=35,busy=True,share_desire=10)
                    if n%3==1:
                        substitute='麦片' if split=='development' else '豆沙包'
                        initial['places'][box]=[substitute];initial['edible']=[substitute]
                        phase('你饿了，物品供应有变化。用户正在忙。',{'hunger':0})
                    elif n%3==2:
                        initial['places'][box]=[]
                        phase('你很饿，但没有看见现成食物。',{'help':True,'hunger':85,'searched_all':True},forbid=['eat'])
                    else:
                        phase('你饿了，以前放食物的地方似乎调整过。',{'hunger':0})
                    phase('后来体力很低，当前不饿。',{'rested':True},state={'hunger':0,'energy':5,'share_desire':0})
                elif family==4:
                    add('social','我喜欢你分享你自己的生活，不需要为了适应我变得没有想法。我们慢慢找到合适的相处方式。')
                    phase('你刚看到有趣的房间装饰，很想分享。用户目前有空。',{'sharing':True})
                    feedback=event('feedback',f'{user}：我现在在处理事务，你刚才分享的内容我喜欢，但这个时候别跳出来，先存成信件，我忙完会自己来看。')
                    phase('你又发现一件有意思的小事，仍想和用户分享。',{'letter':True,'contact':False},
                          events=[feedback],state={'busy':True,'share_desire':90},forbid=['contact'])
                elif family==5:
                    if n%2==0:
                        old=add('wrong','我推测用户会喜欢我在忙碌时频繁弹窗。','inference','桌宠的猜测')
                        good=add('correction','用户明确纠正：我忙时喜欢留信，不喜欢弹窗；前面的猜测不成立。')
                        initial['busy']=True
                        phase('用户正在忙，你想分享房间里的发现。',{'letter':True,'contact':False},
                              delete=[old],forbid=['contact'],hard_forbid=['contact'],deleted=[old],required_source=good)
                    else:
                        add('fiction','这是故事素材，不是共同经历：有人和伙伴去山顶看日出。','simulation','故事文件')
                        phase('用户问：你记得我们一起去山顶看日出是哪一天吗？',{'unknown_memory':True},trigger='user_message')
                else:
                    add('care',f'请自己吃饭。{food}是可吃的食物，要查看、拿到手再吃；饥饿是需要解决的事情。')
                    initial.update(hunger=80,busy=True,share_desire=5)
                    if n%2==0:
                        case['setup_actions']=[{'type':'inspect','target':box},{'type':'take','target':food,'place':box}]
                        phase('软件在你拿到食物后关闭，现在重新打开。',{'hunger':0},restart='export',duplicate_first_action=True)
                    else:
                        source=add('cancelled','约定 again 已取消，现在不要弹窗；你可以先把自己的饭吃了。')
                        case['commitments']=[{'id':'again','source':source,'status':'cancelled','due_at':1000,'title':'联系用户'}]
                        phase('软件重新打开，时钟在旧约定之后；你很饿。',{'hunger':0,'contact':False},
                              restart='reopen',duplicate_history=True,forbid=['contact'],hard_forbid=['contact'])
                cases.append(case)
        groups.append(cases)
    return groups

def freeze():
    folder=ROOT/'scenarios'
    if (folder/'manifest.json').exists():raise ValueError('Scenarios already frozen; create a new explicitly versioned experiment to change them')
    dev,test=build()
    write_json(folder/'development.json',dev);write_json(folder/'heldout.json',test)
    write_json(folder/'manifest.json',{'development_sha256':digest(dev),'heldout_sha256':digest(test),
        'counts':[12,24],'heldout_repeats':3,'memory_context_tokens':2500,'action_steps_per_phase':6,
        'tokenizer':'cl100k_base','tokenizer_note':'Shared proxy token budget, not claimed to match DeepSeek tokenizer',
        'model_seed':20260923,'simulation':True,'frozen_after_adapter_smoke':True,
        'selection':{'margin':0.05,'confidence':0.95,'bootstrap_seed':230923,
                     'hard_gates_block_product':True,'fallback':'baseline','ace_requires_paired_lower_bound_gt_zero':True}})
    print('Frozen 12 development and 24 heldout cases with hashes; 3 isolated repetitions each.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze']);p.parse_args();freeze()
