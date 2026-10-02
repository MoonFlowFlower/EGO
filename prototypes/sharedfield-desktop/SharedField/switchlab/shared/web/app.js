'use strict';
const $=id=>document.getElementById(id),TOKEN=document.querySelector('meta[name="studio-token"]').content;
let state=null,selected=null,polling=false,lastEvent=-1,lastMessage='',manualID=null,toastTimer;
const kinds={flora:['✧','苔光植物'],echo:['◉','回声'],ruins:['⌂','古老构造'],water:['≈','水纹']};
const actions={move:'前往',survey:'调查',scan:'观察路况',calibrate:'校准工具',rest:'休整',repair:'维护工具',sleep:'休息',wait_partner:'等你准备好'};
const goals={explore:'探索',investigate:'调查路况',join:'会合',rejoin:'恢复会合',wait_partner:'共同等待',calibrate:'校准自身',rest:'恢复',repair:'维护',sleep:'休息',wait_partner:'等你准备好'};
function el(tag,cls,txt){let n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;}
function toast(t){$('toast').textContent=t;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,6000);}
async function api(path,body){const opt={headers:{'X-SwitchLab-Token':TOKEN}};if(body!==undefined){opt.method='POST';opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(body);}const r=await fetch(path,opt);let data;try{data=await r.json();}catch{throw Error('服务器没有返回JSON；检查命令行窗口是否仍在运行。');}if(!r.ok)throw Error(data.error||String(r.status));return data;}
async function execute(fn){try{await fn();await refresh();}catch(e){toast(e.message);}}
async function cmd(kind,payload={}){return api('/api/command',{kind,payload});}
function roomName(n){return state.world.visible_rooms.find(r=>r.id===n)?.name||`地点 ${n}`;}
function fmt(x,d=2){return Number(x).toFixed(d);}
function actionText(a){return (actions[a.kind]||a.kind)+(a.target!==undefined?' · '+roomName(a.target):'');}
function renderMap(){
 const map=$('worldMap'),known=new Map(state.world.visible_rooms.map(r=>[r.id,r]));map.replaceChildren();
 for(let i=0;i<12;i++){
  const r=known.get(i),near=state.player.neighbors.some(n=>n.id===i),b=el('button','room'+(!r?' fog':'')+(r?.surveyed?' visited':'')+(near?' adjacent':'')+(selected===i?' selected':''));
  b.type='button';b.dataset.room=i;b.setAttribute('aria-label',r?`${r.name}${near?'，可前往':''}`:'未观察地点');b.disabled=!r;
  b.append(el('span','glyph',r?kinds[r.kind][0]:'·'),el('span','roomTitle',r?r.name:'未观察'),el('span','roomKind',r?(r.surveyed?'已调查':kinds[r.kind][1]):'未知'));
  const holders=el('span','occupants');if(state.player.position===i)holders.append(el('span','actor user','你'));if(state.world.position===i)holders.append(el('span','actor',state.name.slice(0,1)));b.append(holders);
  b.onclick=()=>{selected=i;renderMap();};map.append(b);
 }
 const adjacent=state.player.neighbors.some(n=>n.id===selected);$('moveBtn').disabled=!adjacent;$('scanBtn').disabled=!adjacent;
 $('selectedPlace').textContent=selected===null?'点选一个邻接地点，再移动或观察路况。':`已选：${roomName(selected)}${adjacent?' · 可以走过去，也可以先观察路况。':' · 当前不能直接走到这里。'}`;
 $('locationText').textContent=`你：${state.player.room.name} / ${state.name}：${state.world.room.name}`;
 $('expeditionText').textContent=`第 ${state.expedition} 次探索`;$('worldTick').textContent=state.world.tick;$('mindTick').textContent=state.cognition.internal_ticks;$('obsTick').textContent=state.observations;
 $('yourEnergy').value=state.player.stamina;$('herEnergy').value=state.world.stamina;$('discoveries').textContent=`${12-state.remaining_discoveries} / 12 处发现`;
}
function renderMind(){
 const c=state.cognition,f=c.focus;$('avatar').textContent=state.name.slice(0,2);document.querySelectorAll('.agentName').forEach(n=>n.textContent=state.name);
 $('feelingWords').textContent=c.state_words;$('focusText').textContent=f?.reason||'正在观察';
 $('nextAction').textContent=f?`下一步：${actionText(f.action)} · 当前目标 ${f.goal.id} · 依据 ${f.basis}`:'';
 const bars=$('affectBars');bars.replaceChildren();for(const [key,label] of [['valence','积极 / 消极'],['arousal','关注激活'],['frustration','受挫倾向']]){
  let row=el('div','affectRow');let bar=el('progress');bar.max=1;bar.value=key==='valence'?(c.affect[key]+1)/2:c.affect[key];row.append(el('span','',label),bar,el('span','',fmt(c.affect[key])));bars.append(row);
 }
 $('learningText').textContent=`已处理 ${c.learned_events} 条可学习物理事件；自身工具成功估计 ${fmt(c.self_model.tool_success_estimate*100,1)}%，含设计先验与 ${c.self_model.calibration_observations} 次本阶段独立校准。最近预测误差 ${fmt(c.attention.prediction_error,3)}。`;
 $('interestList').replaceChildren();for(const v of Object.values(c.interests)){$('interestList').append(el('div','metricRow',`${v.name} · 预期信息收益 ${fmt(v.expected_information)} · ${v.observed_findings} 次发现`));}
 $('candidateList').replaceChildren();for(const r of f?.candidates||[]){const n=el('div','candidate');n.append(el('span','',`${goals[r.type]||r.type} / ${actionText(r.action)}`),el('span','',fmt(r.score,3)));$('candidateList').append(n);}
 $('basisList').replaceChildren();if(!c.basis.length)$('basisList').append(el('p','fine','尚无行动经历；初始目标来自公开的设计先验。'));
 for(const a of c.basis){const n=el('div','basisRow');n.append(el('b','',a.source+' '),document.createTextNode(a.why));$('basisList').append(n);}
 $('otherList').replaceChildren();if(!state.other_reports.length)$('otherList').append(el('p','fine','还没有关于你的有来源报告；不会从沉默自动推断你难过或离开。'));
 for(const r of [...state.other_reports].reverse().slice(0,15)){
  const n=el('div','otherRow');n.append(el('span','',`${r.holder} / ${r.domain}：${r.value} · ${r.kind==='explicit'?'明确自述的解释':'不确定推断'} ${fmt(r.confidence*100,0)}%${r.withdrawn?' · 已撤回':''}`));
  if(!r.withdrawn){const b=el('button','','解释不对，撤回');b.onclick=()=>execute(()=>cmd('withdraw_report',{id:r.id}));n.append(b);}n.append(el('blockquote','',r.quote));$('otherList').append(n);
 }
 $('goalHistory').replaceChildren();for(const g of state.goal_history.slice(-8).reverse())$('goalHistory').append(el('div','basisRow',`${g.id} ${goals[g.type]||g.type} · ${g.status} · ${g.closed_by||g.basis}`));
 $('ablationSelect').value=c.mode;
}
function renderJoint(){
 const c=state.cognition,a=c.activity||{mode:'independent'},names={independent:'各自探索',together:'一起走',wait:'等你准备好'};
 $('activityMode').textContent=names[a.mode]||a.mode;
 $('activityStatus').textContent=a.mode==='together'?'保留共同目标；领先时等待，观察到受阻时考虑会合。你仍控制自己的动作。':a.mode==='wait'?'已保留约定并等待，不刷休整动作、不消耗世界步骤。准备好后恢复。':'可以各自探索和分享发现；看见你受阻不等于擅自替你决定。';
 $('togetherBtn').classList.toggle('selectedMode',a.mode==='together');$('waitBtn').classList.toggle('selectedMode',a.mode==='wait');
 $('resumeJointBtn').disabled=a.mode!=='wait';
 const issue=c.shared_concerns?.at(-1),box=$('sharedConcern');box.hidden=!issue;box.replaceChildren();
 if(issue){box.append(el('strong','','有一件共同活动里的事值得留意'),el('p','',`你刚才有移动没有走通。可以邀请她一起看，也可以继续各自探索；她不会由此断定你的情绪。来源 ${issue.sources.slice(-3).join(' / ')}`));}
 $('memoryTimeline').replaceChildren();
 const memories=c.memory_cards||[];
 if(!memories.length)$('memoryTimeline').append(el('p','fine','还没有可以回看的发现、失败或检查经历。'));
 for(const m of [...memories].reverse().slice(0,5)){
  const row=el('div','memoryItem');row.append(el('small','',`第 ${m.expedition} 次探索 · ${m.source}${m.joint?' · 当时在一起':''}`),el('div','',m.summary));$('memoryTimeline').append(row);
 }
 $('experienceThreads').replaceChildren();
 for(const t of (c.experience_threads||[]).slice(-3))$('experienceThreads').append(el('div','threadItem',`${t.type==='partner_route'?'共同路况问题':'自身 / 路况的未决解释'} · ${t.status==='resolved'?'已经到达目标':t.status==='open'?'仍保留不确定性':'旧探索已归档'} · 实际检查 ${t.checks.length} 次 · ${t.source}${t.closed_by?' → '+t.closed_by:''}`));
 const p=c.partner_choice_model;
 $('partnerPrediction').textContent=p?`实际在线更新 ${p.updates} 次；这是受路线与测试方式影响的选择预测，不是读心。${Object.entries(p.category_tendencies).map(([k,v])=>kinds[k][1]+' '+fmt(v*100,0)+'%').join(' / ')}`:'';
 const notice=state.migration_notice;$('migrationNotice').hidden=!notice;
 if(notice)$('migrationNotice').textContent=`已接续旧版第 ${notice.physical_tick} 步，保留 ${notice.old_events} 条旧事件。${notice.unfinished_questions.length?'有 '+notice.unfinished_questions.length+' 个导出时未完成的问题，未自动重发。':'旧版没有待重发的问题。'}`;
}

async function showReport(id){const r=await api('/api/report?id='+encodeURIComponent(id));$('reportContent').textContent=JSON.stringify(r,null,2);$('reportDialog').showModal();}
function renderChat(){
 const key=state.messages.map(m=>m.id+':'+(m.intention?.status||'')).join('|')+state.name;if(key===lastMessage)return;lastMessage=key;
 if(!state.messages.length){if($('chatLog').querySelector('.welcome'))return;$('chatLog').replaceChildren(el('div','welcome','开始一段共同经历。你可以直接问她的感觉、思考和意愿。'));return;}
 const log=$('chatLog'),atBottom=log.scrollHeight-log.scrollTop-log.clientHeight<100;log.replaceChildren();
 for(const m of state.messages){const n=el('div','message '+m.role);let source=m.role==='user'?'你':state.name+(m.kind==='local_state_report'?' · 本地状态报告':' · 语言表达');
  n.append(el('div','messageMeta',source+' · '+m.id),el('div','bubble',m.text));if(m.state_id){n.append(el('br'));let b=el('button','',`说话前的状态 ${m.state_id} ↗`);b.onclick=()=>execute(()=>showReport(m.state_id));n.append(b);}
  if(m.intention){
   const r=m.intention,status={selected_not_executed:'待实际行动',executed:r.success?'已经执行':'已经尝试 · 未达预期',revised_on_new_observation:'有新证据，计划已修改',superseded_before_delivery:'回复使用较早快照'};
   n.append(el('div','intentionReceipt',`${actionText(r.action)} · ${status[r.status]||r.status}${r.result_event?' · '+r.result_event:''}`));
  }
  if(m.temporal_status==='earlier_snapshot')n.append(el('div','receiptNote',`回复对应较早快照（第 ${m.intention.world_tick} 步）。期间位置或共同约定已变化；当前决定不会被回滚。`));
  if(m.speech_guard?.corrected)n.append(el('div','receiptNote','行动承诺已按已选计划校正 · 有限措辞检查，不代表全文语义验证'));
  log.append(n);
 }
 if(atBottom||state.messages.at(-1)?.role==='user')log.scrollTop=log.scrollHeight;
}
function renderEvents(){
 $('eventCount').textContent=`${state.events} 个事件`;$('eventLog').replaceChildren();
 for(const e of [...state.last_events].reverse()){
  let t=e.result.transition,s=e.result.kind;if(t){s=`${t.actor==='agent'?state.name:'你'} · ${actionText(t.action)} · ${t.success?'成功':'未达到预期'}`;if(t.finding?.new)s+=` · 新发现的信息收益 ${fmt(t.finding.richness)}`;}
  const n=el('div','event');n.append(el('small','',e.id+' '),document.createTextNode(s));$('eventLog').append(n);
 }
}
function renderRuntime(){
 const r=state.runtime;$('runtimeStatus').textContent=r.status;$('errorBox').hidden=!r.error;$('errorBox').textContent=r.error||'';
 $('runBadge').textContent=r.busy?'语言处理中':r.manual_request?'等手动交换':r.auto_remaining?`可继续 ${r.auto_remaining} 步`:'已暂停 / 等待';
 $('saveStatus').textContent=r.session_saved?'已保存到本地':'未开始';
 const modes={local:'本地状态报告',manual:'手动语言交换',api:'已配置模型API'};$('connectionBadge').textContent=modes[r.options.language_mode];
 $('callCount').textContent=r.options.language_mode==='local'?'本地报告 · 不调用模型':`语言请求 ${state.calls} / ${r.provider.max_calls} · 供应商报告 tokens ${state.usage.input_tokens} / ${state.usage.output_tokens}`;
 $('manualBanner').hidden=!r.manual_request;$('manualPhase').textContent=r.manual_request?` · ${r.manual_request.phase==='interpret'?'解释输入':'表达状态'}`:'';
 if(r.manual_request&&manualID!==r.manual_request.id){manualID=r.manual_request.id;$('manualPrompt').value=r.manual_request.prompt;$('manualResult').value='';}
 if(!r.manual_request){manualID=null;if($('manualDialog').open)$('manualDialog').close();}
}
async function refresh(){if(polling)return;polling=true;try{state=await api('/api/state');renderRuntime();if(state.events!==lastEvent){lastEvent=state.events;renderMap();renderMind();renderJoint();renderChat();renderEvents();}}catch(e){$('runtimeStatus').textContent='连接本地服务失败：'+e.message;}finally{polling=false;}}
async function sendMessage(){const text=$('messageInput').value.trim();if(!text)return;await api('/api/chat',{text});$('messageInput').value='';await refresh();}
$('chatForm').onsubmit=e=>{e.preventDefault();execute(sendMessage);};$('messageInput').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();execute(sendMessage);}};
document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>execute(async()=>{$('messageInput').value=b.dataset.question;await sendMessage();}));
$('moveBtn').onclick=()=>execute(()=>cmd('player_action',{action:{kind:'move',target:selected}}));$('scanBtn').onclick=()=>execute(()=>cmd('player_action',{action:{kind:'scan',target:selected}}));
$('surveyBtn').onclick=()=>execute(()=>cmd('player_action',{action:{kind:'survey'}}));$('restBtn').onclick=()=>execute(()=>cmd('player_action',{action:{kind:'rest'}}));$('inviteBtn').onclick=()=>execute(()=>cmd('invite'));
$('stepBtn').onclick=()=>execute(()=>api('/api/advance',{}));$('autoBtn').onclick=()=>execute(()=>api('/api/auto',{steps:Number($('autoSteps').value)}));$('pauseBtn').onclick=()=>execute(()=>api('/api/pause',{}));$('reflectBtn').onclick=()=>execute(()=>cmd('reflect'));
$('ablationSelect').onchange=()=>execute(()=>cmd('ablation',{mode:$('ablationSelect').value}));
for(const [id,kind] of [['stormBtn','storm'],['faultBtn','tool_fault'],['repairBtn','repair']])$(id).onclick=()=>execute(()=>cmd('intervene',{kind}));
$('nextIslandBtn').onclick=()=>execute(async()=>{if(confirm('保留学得的类型收益、能力估计、对话和来源记录，换一个环境并暂停。继续？')){await cmd('new_expedition');selected=null;}});
$('newLifeBtn').onclick=()=>execute(async()=>{if(confirm('将当前个体完整归档，并开始空白状态？旧数据不会删除。')){await api('/api/new',{});$('settingsDialog').close();lastMessage='';selected=null;}});
$('exportBtn').onclick=()=>execute(async()=>{
 if(!confirm('导出含对话、记忆和实验数据，不含配置中的API密钥。请勿公开未检查的文件。继续？'))return;
 // Preserve server JSON bytes. Parsing then stringify erased 0.0 and broke v04 replay.
 const r=await fetch('/api/export',{headers:{'X-SwitchLab-Token':TOKEN}});
 if(!r.ok)throw Error('导出失败');const text=await r.text();
 const u=URL.createObjectURL(new Blob([text],{type:'application/json'}));const a=el('a');a.href=u;a.download='SharedField_v05_checkpoint.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);
});
$('importBtn').onclick=()=>$('importFile').click();
$('importFile').onchange=()=>execute(async()=>{
 const file=$('importFile').files[0];$('importFile').value='';if(!file)return;
 if(file.size>16*1024*1024)throw Error('界面导入上限16MiB；更大记录请使用命令行。');
 if(!confirm('验证并导入这份探索？当前个体有数据时先归档；导入后暂停，不调用模型，不删除旧文件。'))return;
 toast('正在用对应版本的代码验证并恢复探索……');
 const checkpoint=JSON.parse(await file.text());await api('/api/import',{checkpoint,archive_current:true});
 selected=null;lastEvent=-1;lastMessage='';toast('已接续旧经历，当前暂停；密钥仍需在模型连接中配置。');
});
for(const [id,mode] of [['togetherBtn','together'],['waitBtn','wait'],['resumeJointBtn','resume'],['independentBtn','independent']])$(id).onclick=()=>execute(()=>cmd('activity',{mode}));
$('helpBtn').onclick=()=>$('helpDialog').showModal();document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
function openSettings(){if(!state)return;const p=state.runtime.provider,o=state.runtime.options;
 $('agentNameInput').value=state.name;$('languageMode').value=o.language_mode;$('baseURL').value=p.base_url;$('modelID').value=p.model;$('apiKey').value='';$('apiKey').placeholder=p.key_present?'已有进程内密钥；留空保留':'密钥只留在当前进程';$('clearKey').checked=false;
 $('maxCalls').value=p.max_calls;$('maxTokens').value=p.max_output_tokens;$('timeout').value=p.timeout;$('tokenParameter').value=p.token_parameter;$('jsonMode').checked=p.json_mode;$('networkConsent').checked=p.network_consent;$('narrate').checked=o.narrate;$('interval').value=o.interval;$('settingsResult').textContent='';$('settingsDialog').showModal();}
$('connectBtn').onclick=openSettings;
$('saveSettingsBtn').onclick=()=>execute(async()=>{
 const mode=$('languageMode').value;const config={mode:mode==='api'?'api':'manual',base_url:$('baseURL').value.trim(),model:$('modelID').value.trim(),json_mode:$('jsonMode').checked,max_output_tokens:Number($('maxTokens').value),timeout:Number($('timeout').value),token_parameter:$('tokenParameter').value,network_consent:$('networkConsent').checked,max_calls:Number($('maxCalls').value)};
 await api('/api/config',{config,key:$('apiKey').value,clear_key:$('clearKey').checked});
 await api('/api/options',{language_mode:mode,narrate:$('narrate').checked,interval:Number($('interval').value)});
 if($('agentNameInput').value.trim()!==state.name)await cmd('name',{name:$('agentNameInput').value.trim()});
 $('apiKey').value='';$('settingsResult').textContent='已保存并暂停。主动发送消息或允许探索后才继续。';toast('连接设置已保存；尚未调用模型。');
});
$('checkProtocolBtn').onclick=()=>execute(async()=>{if(!confirm('使用已保存的API设置，最多发送2次真实请求，可能计费。只检查协议，不改变当前个体的学习。继续？'))return;const r=await api('/api/protocol-check',{});$('settingsResult').textContent='两阶段协议通过；真实语义表现仍由你测试。'+JSON.stringify(r);});
$('manualBtn').onclick=()=>$('manualDialog').showModal();$('copyPromptBtn').onclick=()=>execute(async()=>{try{if(!navigator.clipboard?.writeText)throw Error('clipboard unavailable');await navigator.clipboard.writeText($('manualPrompt').value);toast('已复制完整阶段请求。');}catch{ $('manualPrompt').focus();$('manualPrompt').select();toast('请求已选中；请按 Ctrl+C（手机长按复制）。');}});
$('submitManualBtn').onclick=()=>execute(async()=>{await api('/api/manual',{request_id:manualID,text:$('manualResult').value});$('manualDialog').close();});
refresh();setInterval(refresh,800);
