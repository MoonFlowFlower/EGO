"""Final evaluation is gated on the complete 20-run manifest and engineering validity."""
import sys,json,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from e2_train import load_frozen
from evolab.config import setup
from evolab.rollout import rollout
from evolab.statistics import decide,paired_difference
from evolab.evaluate import mean_ci
from evolab.render import render

CONDITIONS=['static_holdout','drift_fast','drift_slow']
ARMS=['gru_fixed','gru_mb_plastic']
REGIMES=['static','drift']

def manifests():
    records=[]
    for regime in REGIMES:
        for arm in ARMS:
            for seed in range(5):
                options=list(Path('evidence/summaries').glob(f'{arm}_{regime}_seed{seed}_attempt*.json'))
                completed=[json.loads(p.read_text()) for p in options if json.loads(p.read_text())['status']=='COMPLETE']
                if len(completed)!=1:raise RuntimeError(f'Require exactly one completed run: {arm}/{regime}/{seed}')
                records.append(completed[0])
    return records

def main():
    setup();c,sha=load_frozen();records=manifests()
    assert all(r['config_sha256']==sha and r['generation']==400 for r in records)
    gates=[]
    for regime in REGIMES:
        for arm in ARMS:
            group=sorted([r for r in records if r['regime']==regime and r['arm']==arm],key=lambda r:r['seed'])
            x=torch.tensor([r['training_survival'] for r in group])[:,None,:]
            y=torch.tensor([r['random_survival'] for r in group])[:,None,:]
            x_ci=paired_difference(x,torch.zeros_like(x),label=f'validity {regime} {arm}')
            y_ci=paired_difference(y,torch.zeros_like(y),label=f'validity R {regime} {arm}')
            gates.append({'arm':arm,'regime':regime,'final':x_ci,'random':y_ci,'pass':x_ci['ci95'][0]>y_ci['ci95'][1]})
    Path('evidence/e2_training_validity.json').write_text(json.dumps(gates,indent=2),encoding='utf-8',newline='\n')
    if not all(g['pass'] for g in gates):
        failed=[g['arm']+'/'+g['regime'] for g in gates if not g['pass']]
        report='# EVOLAB-001A E2 报告\n\n判定：**工程无效；不作科学正/部分/负判定**。\n\n20次训练完成，但以下实验臂（汇总5个种子）在训练世界的存活95% CI未与随机基线分离：\n\n'+''.join('- '+x+'\n' for x in failed)
        report+='\n未访问保留集。详细训练均值与随机基线、逐代曲线见 evidence/summaries/。GPU任务墙钟时间合计 '+str(sum(r['wall_seconds'] for r in records)/3600)+' 小时（非CUDA kernel独占计时）。\n\n本结果不能证明可塑性有效或无效，也不能证明生命、意识、情感、主观能动性或桌宠迁移。\n'
        Path('evidence/E2_REPORT.md').write_text(report,encoding='utf-8',newline='\n')
        Path('evidence/e2_decision.json').write_text(json.dumps({'status':'ENGINEERING_INVALID','failed_training_gates':failed,'holdout_accessed':False},indent=2),encoding='utf-8',newline='\n')
        return
    marker=Path('runs/holdout_started.json')
    with marker.open('x',encoding='utf-8') as f:json.dump({'config_sha256':sha,'labels':[r['label'] for r in records]},f)
    start=time.perf_counter();scores={};rows=[]
    for r in records:
        cp=torch.load(Path('runs')/r['label']/'final_mean.pt',weights_only=True)
        assert cp['generation']==400 and cp['config_sha256']==sha
        arm_list=[r['arm']]+(['gru_mb_frozen'] if r['arm']=='gru_mb_plastic' else [])
        for arm in arm_list:
            key=(r['regime'],arm,r['seed']);scores[key]=[]
            for condition in CONDITIONS:
                score,_=rollout(c,condition,arm,1024,r['seed'],'holdout',0,cp['mean'][None].cuda(),use_graph=True,final_evaluation=True)
                value=score.flatten().cpu();scores[key].append(value)
                row={'trained_regime':r['regime'],'arm':arm,'seed':r['seed'],'condition':condition,**mean_ci(value)}
                rows.append(row);print(row,flush=True)
                torch.save(value,Path('runs')/f'holdout_{r["regime"]}_{arm}_{r["seed"]}_{condition}.pt')
    for arm in ('R','H'):
        for seed in range(5):
            for condition in CONDITIONS:
                score,_=rollout(c,condition,arm,1024,seed,'holdout',final_evaluation=True)
                rows.append({'trained_regime':'reference','arm':arm,'seed':seed,'condition':condition,**mean_ci(score)})
    def tensor(regime,arm,conditions):
        return torch.stack([torch.stack([scores[(regime,arm,s)][i] for i in conditions]) for s in range(5)])
    result=decide(tensor('drift',ARMS[0],[1,2]),tensor('drift',ARMS[1],[1,2]),tensor('drift','gru_mb_frozen',[1,2]),
                  tensor('static',ARMS[0],[0]),tensor('static',ARMS[1],[0]))
    # Representative is chosen by seed number, never by performance.
    representative=next(r for r in records if r['regime']=='drift' and r['arm']=='gru_mb_plastic' and r['seed']==0)
    cp=torch.load(Path('runs')/representative['label']/'final_mean.pt',weights_only=True)
    _,frames=rollout(c,'drift_fast','gru_mb_plastic',1024,0,'holdout',genomes=cp['mean'][None].cuda(),trace=True,final_evaluation=True)
    render(frames,'evidence/e2_plastic_drift.gif')
    result.update(status='VALID',config_sha256=sha,rows=rows,training_task_wall_hours=sum(r['wall_seconds'] for r in records)/3600,
                  evaluation_wall_hours=(time.perf_counter()-start)/3600)
    Path('evidence/e2_decision.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
    meanings={'positive':'正结果：在 Room-v0 测试规模下，演化出的三因子可塑性在漂移环境中带来存活优势，且优势依赖可塑性本身、只在漂移时出现。',
              'partial_static':'部分结果：B 在静态世界中也有优势，降级为结构效应，不支持可塑性结论。',
              'partial_ablation':'部分结果：B 更好，但关闭可塑性后优势基本保留，不支持可塑性结论。',
              'negative':'负结果：在这个规模下，演化出的可塑性没有超过循环网络的上下文内适应。不重调、不追加救援实验。'}
    report='# EVOLAB-001A E2 报告\n\n'+meanings[result['outcome']]+'\n\n'
    report+=f"H1={result['H1']}，H2={result['H2']}（H1不成立时不适用），H3={result['H3']}。\n\n"
    report+='配置SHA-256：`'+sha+'`。训练选择严格为第400代均值，20次完整运行通过工程门槛。\n\n'
    for field in ('drift_B_minus_A','drift_B_minus_B0','static_B_minus_A'):
        report+=f'- {field}: {result[field]}\n'
    report+='\n|训练世界|臂|种子|条件|平均存活|回合bootstrap 95% CI|\n|---|---|---|---|---|---|\n'
    for row in rows:report+=f"|{row['trained_regime']}|{row['arm']}|{row['seed']}|{row['condition']}|{row['mean']:.6f}|{row['ci95']}|\n"
    report+=f"\n训练GPU任务墙钟 {result['training_task_wall_hours']:.3f} 小时；评估 {result['evaluation_wall_hours']:.3f} 小时。包括GPU同步、随机输入与CPU控制开销，不是CUDA kernel独占时间。\n\n"
    report+='两个漂移条件等权平均；差值CI使用配对分层自助法10000次。逐代数据摘要见 summaries/；代表个体固定为B/drift/seed0/episode0，GIF见 e2_plastic_drift.gif。\n\n本结果不能证明生命、意识、情感、主观体验、主观能动性、自我或桌宠/真实用户迁移，只涉及Room-v0测试规模内的控制性质。\n'
    Path('evidence/E2_REPORT.md').write_text(report,encoding='utf-8',newline='\n')

if __name__=='__main__':main()
