"""Separate executed life facts from a newly authored fictional vignette."""
FORMAT='life-v3'
FICTION_LABEL='脑海里的小剧场 · 虚构，不是发生过的事'


def fact_text(moment):
    if moment.get('actor')!='pet':raise ValueError('缺少明确的动作执行者')
    kind=moment['kind'];changes=moment['changes']
    if kind=='eat':
        food=changes['food'];hunger=changes['hunger']
        if food['before']-food['after']!=1 or hunger['after']>=hunger['before']:
            raise ValueError('进食结果不完整')
        sentence='我吃完了一份餐点，现在没那么饿了。'
    elif kind=='rest':
        energy=changes['energy']
        if energy['after']<=energy['before']:raise ValueError('休息没有恢复精力')
        sentence='我在床上休息了一会儿，精神恢复了一些。'
    else:raise ValueError('不支持的分享活动')
    if moment.get('initiator')=='user':sentence+='这次是你叫我去的。'
    elif moment.get('initiator')=='autonomous':sentence+='这次是我自己安排的。'
    if moment.get('teaching'):sentence+='用上了你教我的自理办法。'
    return sentence


def life_letter_content(moment,result):
    if not isinstance(result,dict) or result.get('format')!=FORMAT:
        raise ValueError('旧版生活散文不能作为新格式的信件发布')
    imagination=result.get('imagination')
    if not isinstance(imagination,str) or not imagination.strip() or len(imagination)>2000:
        raise ValueError('想象片段为空或太长')
    fact=fact_text(moment)
    return dict(format=FORMAT,fact_text=fact,imagination=imagination,
                text=fact+'\n\n'+FICTION_LABEL+'\n'+imagination)


def letter_for_chat(letter):
    if letter.get('withdrawn'):return None
    if letter.get('source_moment'):
        if letter.get('format')!=FORMAT:return None
        return {'id':letter['id'],'fact_text':letter['fact_text'],
                'source_moment':letter['source_moment'],
                'creative_work':'写过一个虚构小片段，情节不是现实经历。'}
    return letter
