"""Self-contained HTML evidence reports. No CDN, external font, or JS dependency."""
from __future__ import annotations
from pathlib import Path
from html import escape
import json

STYLE='''body{font:15px/1.65 system-ui,"Microsoft YaHei",sans-serif;margin:36px auto;max-width:1180px;padding:0 22px;color:#1f2937;background:#f5f7fb}h1{font-size:30px}h2{margin-top:32px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:9px 12px;border-bottom:1px solid #dde3ec;text-align:left;font-variant-numeric:tabular-nums}th{background:#e9eef7}code,pre{background:#e7edf6;padding:3px 6px;overflow:auto}small{color:#58687c}.notice{background:#fff5df;border-left:4px solid #c58318;padding:15px}.scroll{overflow-x:auto}a{color:#314fb8}'''

def _write(path,title,body):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(title)+'</title><style>'+STYLE+'</style><body>'+body+'</body></html>',encoding='utf-8')

def session_report(trace,path):
    a=trace['final']['agent'];w=trace['final']['world'];o=w['public']
    body='<h1>SwitchLab · 单次运行证据</h1><div class="notice">这是一段真实执行的离线 toy-world 轨迹，不是学习型主体或真实自主的证明。神经训练、社会推理与技能发现未实现。</div>'
    body+=f'<p>步数 <b>{o["tick"]}</b> · 净环境回报 <b>{w["total_reward"]:.3f}</b> · 完成交付 <b>{o["completed"]}</b> · 错过交付 <b>{o["missed"]}</b> · 经验 {len(a["memory"])}</p>'
    body+='<p>配置：<code>'+escape(json.dumps(trace['metadata'],ensure_ascii=False))+'</code></p>'
    body+='<p>哈希只能检出编辑；请执行 <code>python run.py verify trace.json</code> 重算策略、环境、学习和最终状态。</p>'
    body+='<div class="scroll"><table><tr><th>时刻</th><th>目标</th><th>行动 / 结果</th><th>能量 / 冷却</th><th>回报</th><th>意外程度</th></tr>'
    for event in trace['events']:
        if event['op']['kind']!='step':continue
        r=event['result'];t=r['transition'];d=r['decision'];s=t['after']
        body+=f'<tr><td>{s["tick"]}</td><td>{escape(d["domain"])}</td><td>{escape(t["action"])} → {escape(t["outcome"])}</td><td>{s["energy"]:.2f} / {s["coolant"]:.2f}</td><td>{t["reward"]:.2f}</td><td>{r["learning"]["surprise_nats"]:.3f}</td></tr>'
    body+='</table></div>'
    _write(path,'SwitchLab 运行证据',body)


def benchmark_report(summary,path):
    body='<h1>SwitchLab · 基线与消融实测</h1><div class="notice"><b>机制优越性：未确立。</b> 简单基线、负结果及零差异保留。测试通过不代表候选优于基线。置信区间是描述性的、未作多重比较校正。</div>'
    body+='<p>Source SHA-256: <code>'+escape(summary['source_sha256'])+'</code></p>'
    body+='<div class="scroll"><table><tr><th>情境</th><th>方法</th><th>生命周期</th><th>平均回报</th><th>交付</th><th>短缺步</th><th>诊断 / 维修</th><th>想象节点</th></tr>'
    for r in summary['aggregate']:
        body+=f'<tr><td>{r["scenario"]}</td><td>{r["label"]}</td><td>{r["lives"]}</td><td>{r["mean_return"]:.3f}</td><td>{r.get("mean_completed",0):.2f}</td><td>{r.get("mean_shortage_steps",0):.2f}</td><td>{r.get("mean_diagnostics",0):.2f} / {r.get("mean_repairs",0):.2f}</td><td>{r.get("mean_nodes",0):.0f}</td></tr>'
    body+='</table></div><h2>配对差异：candidate − 对照</h2><div class="scroll"><table><tr><th>情境</th><th>对照</th><th>差值</th><th>描述性 95% 区间</th></tr>'
    for r in summary['paired']:
        ci=r['descriptive_normal_95_interval'];label='样本不足' if ci is None else f'[{ci[0]:.3f}, {ci[1]:.3f}]'
        body+=f'<tr><td>{r["scenario"]}</td><td>{r["comparison"]}</td><td>{r["mean_delta"]:.3f}</td><td>{label}</td></tr>'
    body+='</table></div><h2>同一观察流上的预测检查</h2><p>此表不像 on-policy surprise 那样受到策略选择不同观测的混淆；越低越好。</p><pre>'+escape(json.dumps(summary.get('prediction_panel_mean_nll',{}),indent=2))+'</pre>'
    body+='<h2>未覆盖与停止边界</h2><p>'+escape('；'.join(summary['missing_baselines']))+'</p>'
    for warning in summary['warnings']:body+='<p>'+escape(warning)+'</p>'
    _write(path,'SwitchLab 基线与消融实测',body)
