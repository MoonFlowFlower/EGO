'use strict';
const $=id=>document.getElementById(id), token=document.querySelector('meta[name=session-token]').content;
let state=null,runtime=null,lastSignature='',loading=false,manualId=null;
const drafts=new Map();
function preserveDrafts(){for(const card of document.querySelectorAll('[data-activity],[data-comparison]')){const id=card.dataset.activity||card.dataset.comparison;card.querySelectorAll('textarea,input,select').forEach((n,i)=>drafts.set(id+':'+i,n.value));}}
function restoreDrafts(){for(const card of document.querySelectorAll('[data-activity],[data-comparison]')){const id=card.dataset.activity||card.dataset.comparison;card.querySelectorAll('textarea,input,select').forEach((n,i)=>{const key=id+':'+i;if(drafts.has(key))n.value=drafts.get(key);});}}
const names={queued:'等待读取',read:'读过了，等你一起讨论',reflecting:'正在根据纠正重读',revised:'新方法等你决定',learned:'方法已留下来',cancelled:'已取消',awaiting_scores:'两份答案已准备好',evaluated:'评价已保存'};
const e=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
async function api(path,body){const o={headers:{'X-SwitchLab-Token':token}};if(body!==undefined){o.method='POST';o.headers['Content-Type']='application/json';o.body=JSON.stringify(body);}const r=await fetch(path,o),v=await r.json();if(!r.ok)throw Error(v.error||'请求失败');return v;}
async function action(fn){try{$('error').hidden=true;await fn();await refresh();}catch(err){$('error').textContent=err.message;$('error').hidden=false;}}
function button(label,fn){const b=e('button',label);b.type='button';b.onclick=()=>action(fn);return b;}
function field(label,node){const l=e('label',label);l.append(node);return l;}
function input(tag,max,placeholder){const n=e(tag);n.required=true;n.maxLength=max;if(placeholder)n.placeholder=placeholder;return n;}
function materials(selected){const n=e('select');for(const m of state.materials){const o=e('option',m.title);o.value=m.id;n.append(o);}if(selected)n.value=selected;return n;}
function artifact(a,target){target.append(e('p',a.summary,'answer'));for(const f of a.findings){const q=e('div',undefined,'citation');q.append(e('strong',f.text),e('p','「'+f.quote+'」'),e('small',f.paragraph+' · 引用已核对，判断仍可纠正'));target.append(q);}target.append(e('p',a.question));}
function render(){
 preserveDrafts();
 const old=$('material').value;$('material').replaceChildren(...materials(old).children);
 $('activities').replaceChildren();
 for(const a of [...state.activities].reverse()){
  const card=e('article',undefined,'card');card.dataset.activity=a.id;card.append(e('span',names[a.status]||a.status,'badge'),e('h3',a.question));
  const m=state.materials.find(x=>x.id===a.material_id);card.append(e('small',(m?.title||'')+' · '+a.goal));
  if(a.reading)artifact(a.reading,card);
  if(a.feedback)card.append(e('p','你的纠正：'+a.feedback.text));
  if(a.status==='read'||a.status==='revised'||a.status==='learned'){
   const form=e('form'),text=input('textarea',3000,'告诉我哪里理解偏了，或者还漏了什么。');text.rows=3;form.append(field('一起讨论与纠正',text),e('button','据此重新读一遍'));
   form.onsubmit=ev=>{ev.preventDefault();action(async()=>{await api('/api/reading',{op:'feedback',activity_id:a.id,text:text.value});text.value='';});};card.append(form);
  }
  if(a.proposed_method&&a.status==='revised'){
   const box=e('div',undefined,'citation');box.append(e('h3','我想把这个方法留下来'),e('p',a.proposed_method.instruction),e('p','适用：'+a.proposed_method.scope),e('p','边界：'+a.proposed_method.limits));
   box.append(button('采纳到之后的同类阅读',()=>api('/api/reading',{op:'adopt',activity_id:a.id})));card.append(box);
  }
  if(a.status==='learned'){
   const form=e('form'),select=materials(),q=input('textarea',1800,'对这份新材料提出同类问题');q.rows=2;
   form.append(field('换一份还没读过的新材料',select),field('要检查的问题',q),e('button','生成两份答案，检查迁移'));
   form.onsubmit=ev=>{ev.preventDefault();action(()=>api('/api/reading',{op:'compare',activity_id:a.id,material_id:select.value,question:q.value}));};card.append(form);
  }
  if(a.status!=='cancelled')card.append(button('结束这次活动',()=>api('/api/reading',{op:'cancel',activity_id:a.id})));
  const detail=e('details'),sum=e('summary','查看实际读过的原文');detail.append(sum,e('pre',m?.text||''));card.append(detail);$('activities').append(card);
 }
 if(!state.activities.length)$('activities').append(e('p','先留下材料，再从一个真实问题开始。','empty'));
 $('methods').replaceChildren();for(const m of state.methods){const card=e('div',undefined,'card method');card.append(e('span',(m.active?'使用中':'已撤回')+' · 第'+m.version+'版','badge'),e('p',m.instruction),e('small','适用：'+m.scope+'；边界：'+m.limits));if(m.active)card.append(button('暂时不用这个方法',()=>api('/api/reading',{op:'withdraw',method_id:m.id})));$('methods').append(card);}
 if(!state.methods.length)$('methods').append(e('p','你的纠正经实际重读、由你采纳后，才会成为可复用方法。','empty'));
 $('comparisons').replaceChildren();for(const c of [...state.comparisons].reverse()){
  const card=e('article',undefined,'card');card.dataset.comparison=c.id;card.append(e('span',names[c.status]||c.status,'badge'),e('h3',c.question));const pair=e('div',undefined,'pair');
  for(const label of ['A','B']){const box=e('div');box.append(e('h3','答案 '+label));if(c.answers[label])artifact(c.answers[label],box);else box.append(e('p','尚未完成'));pair.append(box);}card.append(pair);
  if(c.status==='awaiting_scores'){
   const form=e('form'),scores={};for(const label of ['A','B']){const row=e('div');row.append(e('h3','评价 '+label));scores[label]=[];for(const metric of ['忠于原文','回应问题','处理条件与边界']){const sel=e('select');sel.required=true;const blank=e('option','请选择');blank.value='';sel.append(blank);for(const [v,t] of [[0,'0 · 未做到'],[1,'1 · 部分做到'],[2,'2 · 做到了']]){const o=e('option',t);o.value=v;sel.append(o);}scores[label].push(sel);row.append(field(metric,sel));}form.append(row);}
   const notes=input('textarea',3000,'说明具体哪一点更好，或为什么没有差异');form.append(field('评价依据',notes),e('button','保存评价并揭示方案'));
   form.onsubmit=ev=>{ev.preventDefault();action(()=>api('/api/reading',{op:'score',comparison_id:c.id,scores:Object.fromEntries(['A','B'].map(l=>[l,scores[l].map(n=>Number(n.value))])),notes:notes.value}));};card.append(form);
  }
  if(c.status==='evaluated'){card.append(e('p',Object.entries(c.assignments).map(([k,v])=>k+'：'+(v==='method'?'相同历史 + 采纳的方法':'相同原始历史')).join('；')),e('p','本次方法方案分差：'+c.delta+'。'+(!c.same_model?'模型或调用配置相同尚未确认，不能作公平增益比较。':'')+(!c.real_model_run?'这是手动交换或测试夹具，模型运行身份未由API记录确认。':'')),e('p',c.notes),e('small','这是一次有来源的评价，不代表长期或普遍能力提升。'));}
  $('comparisons').append(card);
 }
 restoreDrafts();
}
async function refresh(){if(loading)return;loading=true;try{const [s,v]=await Promise.all([api('/api/reading'),api('/api/state')]);state=s;runtime=v.runtime;const sig=JSON.stringify(s);if(sig!==lastSignature){render();lastSignature=sig;}$('status').textContent=runtime.status+' 待处理阅读：'+s.pending_jobs;$('resume').disabled=runtime.busy||s.pending_jobs===0;if(runtime.error){$('error').textContent=runtime.error;$('error').hidden=false;}
 const r=runtime.manual_request;$('manual').hidden=!r;if(r){if(manualId!==r.id){manualId=r.id;$('manualPrompt').value=r.prompt;$('manualReply').value='';}}else manualId=null;
}catch(err){$('error').textContent=err.message;$('error').hidden=false;}finally{loading=false;}}
$('file').onchange=()=>action(async()=>{const f=$('file').files[0];if(!f)return;if(f.size>90000)throw Error('文件超过90KB，请选一段材料');const text=await f.text();if(text.length>24000)throw Error('材料超过24000字符，请分段');$('text').value=text;$('title').value=f.name.replace(/\.(md|txt)$/i,'');});
$('materialForm').onsubmit=ev=>{ev.preventDefault();action(async()=>{await api('/api/reading',{op:'material',title:$('title').value,text:$('text').value});$('text').value='';$('title').value='';});};
$('startForm').onsubmit=ev=>{ev.preventDefault();action(()=>api('/api/reading',{op:'start',material_id:$('material').value,question:$('question').value,goal:$('goal').value}));};
$('pause').onclick=()=>action(()=>api('/api/pause',{}));$('resume').onclick=()=>action(()=>api('/api/reading',{op:'resume'}));
$('copy').onclick=()=>action(()=>navigator.clipboard.writeText($('manualPrompt').value));$('sendManual').onclick=()=>action(()=>api('/api/manual',{request_id:manualId,text:$('manualReply').value}));
refresh();setInterval(refresh,1500);
