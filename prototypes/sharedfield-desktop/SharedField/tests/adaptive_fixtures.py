"""Explicit language-output fixtures; not samples from a real model."""
def proposal(source,goals=False):
    goal={'title':'检验当前约束','reason':'来源中有待处理的问题','success':'得到可验收的本地草稿',
          'basis':[source],'steps':[{'tool':'draft','instruction':'给出两种有限方案，保留原始约束'}]}
    return {'summary':'测试提案，不是实际模型表现','claims':[],'memories':[],
            'candidates':[{'id':'compare','intent':'比较已有约束下的两个方案','skill':'compare',
                           'kind':'plan' if goals else 'reply','basis':[source],
                           'expected':'用户能检查方案差异','goals':[goal] if goals else [],'revisions':[]},
                          {'id':'clarify','intent':'询问缺少的信息','skill':'clarify','kind':'reply',
                           'basis':[source],'expected':'获得信息','goals':[],'revisions':[]}]}
