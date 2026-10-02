"""Continue only after measured pilot fits the frozen budget; never retry failures silently."""
import json,time,traceback
from pathlib import Path
from e2_train import load_frozen,run,log_failure
from e2_eval import main as evaluate

def main():
    c,sha=load_frozen()
    pilot_path=Path('evidence/summaries/gru_mb_plastic_drift_seed0_attempt0.json')
    pilot=json.loads(pilot_path.read_text())
    assert pilot['status']=='COMPLETE' and pilot['generation']==400 and pilot['config_sha256']==sha
    estimate=pilot['wall_seconds']*20
    # A one-hour evaluation reserve is explicit and conservative, not measured evaluation time.
    budget={'pilot_seconds':pilot['wall_seconds'],'twenty_run_hours':estimate/3600,
            'evaluation_reserve_hours':1.0,'estimated_total_hours':estimate/3600+1,
            'cap_hours':24,'config_sha256':sha}
    Path('evidence/e2_budget.json').write_text(json.dumps(budget,indent=2),encoding='utf-8',newline='\n')
    if estimate+3600>86400:
        log_failure('E2 预算停止，待用户确认缩小方案',f'- 实测完整B/drift/seed0 {pilot["wall_seconds"]:.2f}秒，20次外推{estimate/3600:.2f}小时，另留评估1小时。\n- 方案：保留20运行、400代、最终均值和全部预注册判定，仅将种群256降至128、每候选8回合降至4；批准后再重新冻结配置并重跑完整预算预跑。此处未实施缩小，未继续训练，未访问保留集。')
        print('BUDGET_STOP',budget,flush=True);return
    log_failure('E2 完整预算预跑通过，继续正式矩阵',f'- B/drift/seed0完成400代，实测{pilot["wall_seconds"]:.2f}秒；20次外推{estimate/3600:.3f}小时，加评估预留1小时，未超24小时。\n- 配置{sha}。原始runs/{pilot["label"]}/，摘要{pilot_path.as_posix()}；不选中途最佳。继续其余19次，最终先检查训练工程有效性，再保留集。')
    matrix=[(a,r,s) for r in ('static','drift') for a in ('gru_fixed','gru_mb_plastic') for s in range(5)]
    actual=0.
    for arm,regime,seed in matrix:
        path=Path('evidence/summaries')/f'{arm}_{regime}_seed{seed}_attempt0.json'
        if path.exists():
            summary=json.loads(path.read_text());assert summary['status']=='COMPLETE' and summary['config_sha256']==sha
        else:
            # Account all complete/failed task time, not only runs visited in this ordering.
            statuses=[json.loads(p.read_text()) for p in Path('runs').glob('*_attempt*/status.json')]
            spent=sum(s.get('wall_seconds',0) for s in statuses)
            remaining=86400-spent
            if remaining<3600:
                log_failure('E2 预算停止','- 剩余不足评估预留1小时；不再启动训练。未访问保留集。');return
            summary=run(arm,regime,seed,budget_seconds=remaining-3600)
        actual+=summary['wall_seconds']
        print('MATRIX_PROGRESS',arm,regime,seed,'training_hours',actual/3600,flush=True)
    print('ALL_20_COMPLETE; validating training gates before holdout',flush=True)
    evaluate()
    result=json.loads(Path('evidence/e2_decision.json').read_text())
    log_failure('E2 矩阵与判定结束',f'- 20/20训练完成；训练GPU任务墙钟合计{actual/3600:.3f}小时。判定状态 {result["status"]}，科学结果 {result.get("outcome","不适用：工程无效")}。\n- 证据 evidence/E2_REPORT.md、e2_decision.json、e2_training_validity.json及summaries/。无阈值修改、无最佳检查点替换。')
    print('E2_DONE',result['status'],result.get('outcome'),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        log_failure('E2 执行器停止', '- 失败未忽略：\n```\n'+traceback.format_exc()+'\n```\n- 检查runs状态与日志后再决定恢复；不得删除失败记录。')
        raise
