"""Generate a clearly labeled replay fixture using recorded, authored model packets.
No remote model is queried. This is downstream integration evidence, not a language benchmark.
"""
from pathlib import Path
import json
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from switchlab.studio.service import Service
from switchlab.studio.core import Core, fingerprint
from switchlab.runtime import save_json


def main():
    with tempfile.TemporaryDirectory() as directory:
        s=Service(directory)
        s.submit('这是交付夹具演练：请实际校准一次工具，记录观测和当前概率估计，不要声称已经知道真实隐藏状态。')
        s.run_once(force=True);r=s.manual_request;eid=r['source_event']
        packet={'speech':'我先执行一次本地校准，然后把实际观测和概率估计写成草稿。',
                'memories':[], 'goals':[{'title':'实际校准工具并报告有界估计',
                    'reason':'以实际实验而不是主观猜测回答当前问题。','success':'列出实际观测、后验概率和不能推断的部分。',
                    'basis':[eid],'steps':[{'tool':'lab_action','action':'calibrate','instruction':'进行一次真实玩具世界校准'},
                                            {'tool':'draft','instruction':'根据返回的实际观测写概率报告，并明确这是夹具。'}]}], 'revisions':[]}
        s.accept_manual(r['id'],json.dumps(packet,ensure_ascii=False))
        s.run_once(force=True)  # actual local calibration; numerical model updated by outcome
        for _ in range(4):
            s.run_once(force=True);r=s.manual_request
            if not r:break
            if r['phase']=='turn':
                p={'speech':'新观测改变了当前概率估计；这并不能排除全部其他解释。','memories':[],'goals':[],'revisions':[]}
            else:
                b=s.core.lab.agent.model.marginals()
                p={'content':f'# 校准后报告（记录输入夹具）\n\n一次真实数值动作后，工具有效概率为 {b["tool_healthy"]:.4f}。\n\n这是有限模型族内的估计，不是真实状态的直接读取。本段由交付脚本根据实际状态填写，不是服务商模型测试。'}
            s.accept_manual(r['id'],json.dumps(p,ensure_ascii=False))
            if s.core.state['artifacts']:break
        assert len(s.core.state['artifacts'])==1
        a=s.core.state['artifacts'][0]
        s.command('feedback',{'artifact_id':a['id'],'kind':'criteria_failed','text':'还应区分自身工具异常和资源环境变化，给出下一步区分办法。'})
        s.run_once(force=True);r=s.manual_request;assert r['phase']=='work'
        assert '区分自身工具异常' in r['prompt'];assert r['job']['strategy']!='outline'
        p={'content':a['content']+'\n\n## 修订：替代解释与下一步\n资源环境变化和工具状态变化不能简单混为一谈。当前校准动作主要提供工具相关观测；资源模式应通过对应探测再判断。下一步可以进行资源探测，而不是把所有失败归咎于工具。\n\n这仍是记录输入的交付演练，不是对模型开放语言能力的独立验证。'}
        s.accept_manual(r['id'],json.dumps(p,ensure_ascii=False));s.pause()
        checkpoint=s.core.checkpoint();head=s.core.head
        save_json(ROOT/'examples/studio_sample.json',checkpoint)
        s.close();s=Service(directory)
        assert s.core.head==head and s.auto_remaining==0 and not s.run_once()
        restored=Core.restore(checkpoint)
        save_json(ROOT/'evidence_v02/example_verification.json',{'successful':True,'events':len(restored.events),
            'artifacts':len(restored.state['artifacts']),'head':head,'source_sha256':fingerprint(),
            'actual_numerical_steps':restored.lab.world.observe()['tick'], 'restart_paused':True,
            'learning_statistics_changed':restored.state['strategy_stats']['outline']['beta']==2,
            'recorded_input_replay':True,'remote_model_rerun':False,'language_source':'authored fixture packets; no live model evaluation'})
        s.close()
    print('Recorded-input example and actual restart/replay checks written.')

if __name__=='__main__':main()
