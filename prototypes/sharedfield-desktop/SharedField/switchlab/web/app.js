'use strict';
const $=id=>document.getElementById(id);
const token=document.querySelector('meta[name="switchlab-token"]').content;
const names={energy:'补充能量',coolant:'补充冷却',delivery:'兑现交付承诺',identify_energy:'调查能量机制',identify_coolant:'调查冷却机制',identify_self:'校准自身能力',restore_capability:'恢复工具能力',rest:'暂缓行动',irrelevant_signal:'读取无关信号'};
const actions={e0:'采集 E0',e1:'采集 E1',c0:'采集 C0',c1:'采集 C1',hand_energy:'手工获取能量',hand_coolant:'手工获取冷却',work:'推进交付',probe_e:'调查能量源',probe_c:'调查冷却源',calibrate:'校准自身工具',repair:'维修工具',wait:'等待',noise:'读取纯噪声'};
const outcomes={yield:'成功产出',dry:'未产出；延迟故障成本',worked:'交付推进',blocked:'条件不足',manual:'手工产出',repaired:'已执行维修',waited:'等待完成','0':'信号 0','1':'信号 1'};
const events={adopted:'采纳',continued:'继续',revised:'修订',completed_then_adopted:'完成后采纳',none:'无显式目标层',abandoned_then_adopted:'放弃失效目标后采纳',budget_exhausted_then_adopted:'预算耗尽后重新比较'};
let current=null,playing=false,timer=null,busy=false,history=new Map(),lastIdentity=null;
function text(id,value){$(id).textContent=value;}
function format(value,n=2){return typeof value==='number'&&Number.isFinite(value)?value.toFixed(n):'—';}
function stop(){playing=false;clearTimeout(timer);text('play','▶ 运行');}
async function fetchState(){const r=await fetch('/api/state');if(!r.ok)throw new Error('无法读取本地状态');render(await r.json());}
async function command(data){
 if(busy)return;busy=true;$('error').hidden=true;
 try{const r=await fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json','X-SwitchLab-Token':token},body:JSON.stringify(data)});const v=await r.json();if(!r.ok)throw new Error(v.error||'命令失败');render(v);}
 catch(e){stop();text('error',e.message);$('error').hidden=false;}
 finally{busy=false;}
}
async function loop(){if(!playing)return;await command({command:'step',count:1});if(playing)timer=setTimeout(loop,Number($('speed').value));}
$('play').addEventListener('click',()=>{if(playing){stop();return;}if(current?.done)return;playing=true;text('play','Ⅱ 暂停');loop();});
$('step').addEventListener('click',()=>{stop();command({command:'step',count:1});});
$('batch').addEventListener('click',()=>{stop();command({command:'step',count:12});});
$('think').addEventListener('click',()=>{stop();command({command:'compute'});});
$('replay').addEventListener('click',()=>{stop();command({command:'replay'});});
for(const b of document.querySelectorAll('[data-kind]'))b.addEventListener('click',()=>{stop();command({command:'intervene',kind:b.dataset.kind});});
$('reset').addEventListener('click',()=>{stop();if(current?.observation.tick>0&&!confirm('重新开始会清空当前未导出的运行。已导出需要的轨迹或状态了吗？'))return;history.clear();command({command:'reset',seed:Number($('seed').value),horizon:Number($('horizon').value),scenario:$('scenario').value,policy:$('policy').value,planner:$('planner').value});});
function cells(row,values){for(const value of values){const td=document.createElement('td');td.textContent=value;row.appendChild(td);}return row;}
function render(s){
 current=s;const o=s.observation;
 const identity=s.config.seed+':'+s.config.scenario+':'+s.agent_config.policy+':'+s.agent_config.planner;
 if(lastIdentity!==identity){history.clear();lastIdentity=identity;$('seed').value=s.config.seed;$('horizon').value=s.config.horizon;$('scenario').value=s.config.scenario;$('policy').value=s.agent_config.policy;$('planner').value=s.agent_config.planner;}
 if(s.done)stop();
 text('status',s.done?'本次生命周期结束':(s.workspace_ready?'已思考，下一动作将读取缓存':'本地模拟运行 · 无外部权限'));
 text('tick',`${o.tick} / ${s.config.horizon}`);text('reward',format(s.total_reward));text('contracts',`${o.completed} / ${o.missed}`);text('memory',s.memory_count);text('goals',s.goal_counter);text('nodes',s.planning_nodes.toLocaleString());
 $('energy').value=o.energy;$('coolant').value=o.coolant;text('energy-text',format(o.energy));text('coolant-text',format(o.coolant));
 text('contract-detail',o.deadline===null?'当前没有外部交付任务':`交付 ${o.contract_id}：${o.progress} / 3 · 截止 ${o.deadline}`);
 text('pending',o.pending.length?`${o.pending.length} 项延迟成本尚未发生`:'没有待发生的故障成本');
 for(const [key,id,bar] of [['energy_mode_1','belief-e','be'],['coolant_mode_1','belief-c','bc'],['tool_healthy','belief-self','bs']]){const p=s.marginals[key];text(id,p==null?'未显式建模':format(p*100,1)+'%');$(bar).value=p??0;}
 text('entropy',format(s.entropy_bits,3)+' bit');text('surprise',s.learning?format(s.learning.surprise_nats,3)+' nat':'—');
 text('learning-detail',s.learning?`真实经历 ${s.memory_count} 条；最近结果的事前预测概率 ${format(s.learning.predicted_probability*100,1)}%。学习更新发生在结果之后，预测记录在执行之前。`:'尚无新经历。已知的是模型类别与先验，不是隐藏环境的答案。');
 text('workspace',s.workspace_ready?'内部工作区：已有计算结果；下一动作会实际读取，不重复计入新证据。':`内部计算 ${s.internal_computations} 次 · 精确记忆重放 ${s.replay_count} 次；重放不增加独立样本。`);
 text('truth',`能量源 E${s.evaluator_truth.energy_mode} / 冷却源 C${s.evaluator_truth.coolant_mode} / 工具${s.evaluator_truth.tool_healthy?'正常':'故障'}`);
 const g=s.goal;
 text('goal-title',g?(names[g.domain]||g.domain):'没有显式承诺目标');
 text('goal-detail',g?`目标 #${g.id} · 目标值 ${g.target} · 在第 ${g.adopted_tick} 步采纳；目标模式是工程先验，具体选择依赖学到的信念。`:'候选将在决策时采纳目标；直接规划等基线可以没有独立目标记录。');
 const d=s.preview_plan||s.decision;
 text('action',d?(actions[d.action]||d.action):'—');text('goal-event',d?events[d.goal_event]||'内部候选，尚未执行':'');
 text('planner-label',d?.method==='particle_rollout_mpc'?`模型内 ${d.planning_horizon} 步 × ${d.particles} 粒子`:'有限后果评估');
 const rows=$('candidate-rows');rows.replaceChildren();
 if(d?.candidates?.length){for(const c of d.candidates.slice(0,6))rows.appendChild(cells(document.createElement('tr'),[names[c.domain]||c.domain,actions[c.first_action]||c.first_action,format(c.score,3)]));}
 else rows.appendChild(cells(document.createElement('tr'),['此策略没有显式候选比较。','','']));
 const branches=$('branches');branches.replaceChildren();
 for(const b of d?.branches||[]){const box=document.createElement('div');const title=document.createElement('b');title.textContent=`${outcomes[b.outcome]||b.outcome} · ${format(b.probability*100,1)}%`;box.append(title,document.createTextNode('随后可能：'+(actions[b.next_action]||'重新规划')));branches.appendChild(box);}
 const timeline=$('timeline-rows');timeline.replaceChildren();
 for(const e of [...s.events].reverse()){
  if(e.op.kind==='step'){const r=e.result,t=r.transition;timeline.appendChild(cells(document.createElement('tr'),[t.after.tick,events[r.decision.goal_event]||r.decision.goal_event,actions[t.action],outcomes[t.outcome]||t.outcome,`r ${format(t.reward)} / ε ${format(r.learning.surprise_nats,3)}`]));history.set(t.before.tick,t.before);history.set(t.after.tick,t.after);}
  else{const labels={compute:'内部计算：世界未推进',replay_memory:'记忆重算：没有新证据',intervene:'外部测试干预：'+(e.op.intervention||'')};timeline.appendChild(cells(document.createElement('tr'),['—',labels[e.op.kind]||e.op.kind,'','','']));}
 }
 if(!s.events.length)timeline.appendChild(cells(document.createElement('tr'),['—','尚未执行','','','']));
 history.set(o.tick,o);drawChart();text('digest','当前事件链：'+s.head+' · 哈希不证明作者身份。');
 for(const id of ['step','batch','think'])$(id).disabled=s.done;
}
function drawChart(){
 const canvas=$('chart'),rect=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;canvas.width=Math.floor(rect.width*dpr);canvas.height=Math.floor(145*dpr);const c=canvas.getContext('2d');c.scale(dpr,dpr);const w=rect.width,h=145;const points=[...history.values()].sort((a,b)=>a.tick-b.tick).slice(-96);if(!points.length)return;
 c.font='10px system-ui';c.lineWidth=1;c.strokeStyle='#29364a';c.fillStyle='#8192a9';
 for(const value of [0,6,12]){const y=12+(12-value)/12*(h-34);c.beginPath();c.moveTo(23,y);c.lineTo(w-8,y);c.stroke();c.fillText(String(value),4,y+3);}
 const min=points[0].tick,max=Math.max(min+1,points[points.length-1].tick);
 for(const [key,color] of [['energy','#a99aff'],['coolant','#6bd9c7']]){c.strokeStyle=color;c.lineWidth=2;c.beginPath();points.forEach((p,i)=>{const x=23+(p.tick-min)/(max-min)*(w-33),y=12+(12-p[key])/12*(h-34);i?c.lineTo(x,y):c.moveTo(x,y);});c.stroke();}
 c.fillStyle='#8192a9';c.fillText(String(min),23,h-3);c.fillText('t '+points[points.length-1].tick,w-45,h-3);
}
window.addEventListener('resize',drawChart);
fetchState().catch(e=>{text('error',e.message);$('error').hidden=false;});
