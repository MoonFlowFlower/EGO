'use strict';
const $=id=>document.getElementById(id);
const token=document.querySelector('meta[name="pet-token"]').content;
let state=null,tab='chat',face=false,chatBusy=false,renderKey='',lastContact=null,toastTimer,liveModel,liveApp,loadingModel;
const clock=t=>new Date(t*1000).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
const date=t=>new Date(t*1000).toLocaleDateString('zh-CN',{month:'long',day:'numeric'});
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,4800);}
async function api(path,data){const r=await fetch('/api/'+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Pet-Token':token},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw Error(j.error||'暂时连接不上小屋');return j;}
async function action(name,data={}){try{state=await api('action',{action:name,data,id:crypto.randomUUID()});render();return true;}catch(e){toast(e.message);return false;}}
function setTab(value){tab=value;renderKey='';document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));$('chat-footer').hidden=tab!=='chat';renderPanel();}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
function render(){
 if(!state)return;
 const a=state.activity,busy=!!state.busy_until;
 $('personality-label').textContent=state.personalities[state.personality].name+' · '+(state.selfcare?'在学着照顾自己':'慢慢认识彼此');
 $('hunger-label').textContent=state.hunger>65?'想吃点东西':state.hunger>35?'有一点饿':'饱饱的';
 $('energy-label').textContent=state.energy<35?'有点困了':state.energy<65?'慢悠悠的':'精神不错';
 $('hunger-bar').style.width=(100-state.hunger)+'%';$('energy-bar').style.width=state.energy+'%';$('food-count').textContent=state.food;
 $('activity-label').textContent=a?(a.walking>0?'正走过去 · ':'')+a.label:'在窗边发呆';
 $('life-mode').textContent=busy?'给彼此一点空间':'自在生活中';
 $('welcome-line').textContent=busy?'你先安心忙，我会把想说的话好好留着。':'你有你的事情，我也有我的小世界。';
 $('busy-button').querySelector('strong').textContent=busy?'我忙完，回来啦':'我先忙一会儿';
 $('busy-caption').textContent=busy?(Date.now()/1000>state.busy_until?'约好的时间已经到了':'约好 '+clock(state.busy_until)+' 再见'):'把想说的话留成信';
 $('teach-caption').textContent=state.selfcare?'已经记住，会自己安排':'饿了吃饭，累了休息';
 $('teach-button').querySelector('strong').textContent=state.selfcare?'她在学着自理':'教她照顾自己';
 $('save-status').innerHTML='<i></i> 本地保存 · '+new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
 const p=a?a.target:state.position;$('pet').style.left=p[0]+'%';$('pet').style.top=p[1]+'%';
 $('pet').classList.toggle('walking',!!a&&a.walking>0);
 const sprite=$('pet-sprite');const frames={eat:'0% 100%',rest:'100% 100%',write:'66.666% 100%',read:'33.333% 100%'};
 sprite.style.backgroundPosition=a&&a.walking===0&&frames[a.kind]?frames[a.kind]:'0% 0%';
 const thoughts={eat:'热乎乎的，慢慢吃。',rest:'让我再抱一会儿枕头…',write:busy?'想说的话，先写给你。':'有一点小事想分享给你。',read:'看看你写了些什么。',wander:'这里，也想去看看。',idle:state.selfcare?'我会试着照顾好自己的。':'安安静静地待一会儿。'};
 $('thought').textContent=thoughts[a?.kind||'idle'];$('thought').style.left=Math.max(25,Math.min(74,p[0]))+'%';$('thought').style.top=Math.max(13,p[1]-23)+'%';
 const unread=state.letters.filter(x=>!x.read&&!x.withdrawn).length;$('letter-count').textContent=unread;$('letter-count').hidden=!unread;
 const contact=state.events.find(x=>x.kind==='contact'||x.kind==='help');
 if(contact&&lastContact!==contact.id){if(lastContact!==null)toast(contact.text);lastContact=contact.id;}
 $('model-status').textContent=(state.model_status==='ready'?'按需连接 · ':'暂时离线 · ')+({qwen35:'Qwen 3.5',qwen37:'Qwen 3.7',deepseek:'DeepSeek',gemini:'Gemini Flash-Lite'}[state.model]||state.model);
 $('model-dot').style.background=state.model_status==='ready'?'#88a277':'#c6b78b';
 renderPanel();
}
function renderPanel(){
 if(!state)return;
 const data=tab==='chat'?state.messages:tab==='letters'?state.letters:tab==='diary'?state.diary:state.memories;
 const key=tab+JSON.stringify(data)+JSON.stringify(state.letter_work)+chatBusy;if(key===renderKey)return;renderKey=key;
 const panel=$('panel');const previous=panel.scrollTop;panel.replaceChildren();
 if(tab==='chat'){
  if(!data.length){const intro=el('div','intro');intro.append(el('div','leaf','✧'),el('h3','','初次见面，请多关照。'),el('p','','小屋已经准备好了。\n选一个喜欢的性格，和她打声招呼吧。'));panel.append(intro);}
  data.forEach(m=>{const row=el('div','message '+m.role);row.append(el('div','meta',(m.role==='user'?'你':'悠小喵')+' · '+clock(m.time)),el('div','bubble',m.text));panel.append(row);});
  if(chatBusy){const pending=el('div','message');pending.append(el('div','meta','悠小喵'),el('div','bubble','正在想怎么和你说…'));panel.append(pending);}
  panel.scrollTop=panel.scrollHeight;
 }else if(tab==='letters'){
  (state.letter_work||[]).filter(j=>j.status!=='done').forEach(j=>{
   const status=j.status==='error'?'没写成：'+j.error:j.status==='cancelled'?'已撤下：'+j.error:j.status==='waiting'?'读完或做完了，等她整理成信。':'正在整理成信…';
   panel.append(el('div','letter-status',j.name+' · '+status));
  });
  if(!data.length)panel.append(el('div','empty',state.life_sharing_enabled?'信箱还是空的。\n完成生活中的小事后，她会留一段记录和小小的想象。也可以写张便签给她。':'信箱还是空的。\n可以先写张便签，读完后她会把回信留在这里。'));
  [...data].reverse().forEach(l=>{
   const card=el('article','entry');card.append(el('small','',date(l.time)+' · '+clock(l.time)),el('h3','',l.title));
   if(l.withdrawn){card.append(el('p','','这封信关联的来源已删除或教学已取消，内容不再展示或用于后续交流。'));panel.append(card);return;}
   if(l.format==='life-v3'){
    card.append(el('small','letter-fact-label','刚刚在小屋里'),el('p','',l.fact_text));
    const fiction=el('section','letter-fiction');fiction.append(el('strong','','脑海里的小剧场'),el('small','','虚构想象，不是发生过的事'),el('p','',l.imagination));card.append(fiction);
   }else card.append(el('p','',l.text));
   if(l.source_note){const source=el('details','letter-source');source.append(el('summary','','她读到的便签原文'),el('p','',l.source_note.text));card.append(source);}
   if(l.source_moment){const source=el('details','letter-source'),m=l.source_moment;source.append(el('summary','','这封信来自哪件小事'),el('p','',m.text+'\n'+(m.initiator==='autonomous'?'她自己安排的活动。':m.initiator==='user'?'你邀请她做的活动。':'未记录由谁发起。')));if(m.teaching)source.append(el('p','',m.teaching.text));card.append(source);}
   if(!l.read){const b=el('button','','我读到啦 ♡');b.onclick=()=>action('letter_read',{id:l.id});card.append(b);}else card.append(el('small','','已经读过 · 好好收着'));panel.append(card);
  });panel.scrollTop=previous;
 }else if(tab==='diary'){
  if(!data.length)panel.append(el('div','empty','今天的故事才刚开始。\n完成的生活片段，会慢慢写在这里。'));
  [...data].reverse().forEach(l=>{const card=el('article','entry');card.append(el('small','',date(l.time)+' · '+clock(l.time)),el('p','',l.text));panel.append(card);});panel.scrollTop=previous;
 }else{
  if(!data.length)panel.append(el('div','empty','还没有熟悉的小习惯。\n可以告诉她你喜欢什么，或教她自己吃饭。'));
  [...data].reverse().forEach(m=>{const card=el('article','entry memory-entry');const forget=el('button','','忘掉这条');forget.onclick=async()=>{try{state=await api('forget',{source:m.source});render();toast('这条记忆已移除');}catch(e){toast(e.message);}};card.append(el('small','','来自你的原话 · '+date(m.time)),el('p','',m.text),forget);panel.append(card);});panel.scrollTop=previous;
 }
}
function loadScript(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(Error('角色渲染文件没能加载'));document.head.append(s);});}
async function loadLive2D(){
 if(liveModel)return;
 if(loadingModel)return loadingModel;
 loadingModel=(async()=>{
  try{
   await loadScript('/vendor/live2dcubismcore.min.js');await loadScript('/vendor/pixi.min.js');await loadScript('/vendor/cubism4.min.js');
   const box=$('face-view');liveApp=new PIXI.Application({view:$('live2d'),width:box.clientWidth,height:box.clientHeight,backgroundAlpha:0,antialias:true,resolution:Math.min(devicePixelRatio,1.5),autoDensity:true});
   liveModel=await PIXI.live2d.Live2DModel.from('/model/'+encodeURIComponent('悠小喵')+'/'+encodeURIComponent('悠小喵.model3.json'),{autoInteract:true});
   liveApp.stage.addChild(liveModel);const base={width:liveModel.width,height:liveModel.height};
   function resize(){const w=box.clientWidth,h=box.clientHeight;if(w<1||h<1)return;liveApp.renderer.resize(w,h);const scale=Math.min(w*.96/base.width,h*.95/base.height);liveModel.scale.set(scale);liveModel.anchor.set(.5,.5);liveModel.position.set(w*.5,h*.51);}
   resize();new ResizeObserver(resize).observe(box);
   // The supplied package explicitly provides its "1 / 水印开关" expression.
   // Use that original parameter, keep model credit, never edit textures.
   liveModel.internalModel.on('beforeModelUpdate',()=>{const core=liveModel.internalModel.coreModel;const t=performance.now()/1000;core.setParameterValueById('Param85',1);core.setParameterValueById('ParamAngleZ',Math.sin(t*.7)*2);core.setParameterValueById('ParamBreath',(Math.sin(t*1.5)+1)/2);});
   $('model-loading').hidden=true;$('face-view').dataset.loaded='true';
  }catch(e){$('model-loading').textContent='立绘暂时没加载好，小房间仍可正常使用。';console.error(e);}
 })();return loadingModel;
}
async function setFace(value){face=value;$('room-view').hidden=value;$('face-view').hidden=!value;$('room-mode').classList.toggle('selected',!value);$('face-mode').classList.toggle('selected',value);$('scene-hint').textContent=value?'现在，听你说。':'点点她，或邀请她做点什么';if(value){await loadLive2D();liveApp?.start();}else liveApp?.stop();}
$('room-mode').onclick=()=>setFace(false);$('face-mode').onclick=()=>setFace(true);$('pet').onclick=()=>{setFace(true);setTab('chat');$('chat-input').focus();};
document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action));
$('busy-button').onclick=async()=>{const wasBusy=!!state.busy_until;if(await action(wasBusy?'return':'busy',{minutes:Number($('busy-minutes').value)}))toast(wasBusy?'欢迎回来。信箱里有想和你分享的小事。':'约好啦。她会把想说的话先写下来。');};
$('teach-button').onclick=async()=>{if(await action('teach'))toast('记住了：饿了自己吃饭，累了自己休息。下一次会自己安排。');};
$('food-button').onclick=async()=>{if(await action('restock'))toast('餐桌上添了5份食物。');};
let noteVersion=null,noteBaseline='',noteSaving=false;
const noteValue=()=>JSON.stringify([$('note-name').value,$('note-text').value]);
function noteBusy(value){noteSaving=value;['note-save','note-share','note-new','note-select','note-name','note-text','note-close'].forEach(id=>$(id).disabled=value);}
function mayDiscard(){return noteValue()===noteBaseline||confirm('便签还有未保存的修改，确定放弃吗？');}
async function openNote(name){
 noteBusy(true);
 try{const n=await api('note?name='+encodeURIComponent(name));$('note-name').value=n.name;$('note-name').readOnly=true;$('note-text').value=n.text;noteVersion=n.version;noteBaseline=noteValue();$('note-status').textContent='保存到小屋的便签文件夹。请她读完后，会连接模型写一封回信。';}
 catch(e){toast(e.message);}finally{noteBusy(false);}
}
$('read-button').onclick=async()=>{
 const select=$('note-select');select.replaceChildren();
 for(const name of state.note_files){const o=el('option','',name);o.value=name;select.append(o);}
 $('note-editor').showModal();await openNote(select.value||'给悠小喵的便签.txt');
};
$('note-select').onchange=()=>{if(mayDiscard())openNote($('note-select').value);else $('note-select').value=$('note-name').value;};
$('note-new').onclick=()=>{if(!mayDiscard())return;$('note-name').readOnly=false;$('note-name').value='';$('note-text').value='';noteVersion=null;noteBaseline=noteValue();$('note-name').focus();};
$('note-close').onclick=()=>{if(!noteSaving&&mayDiscard())$('note-editor').close();};
$('note-editor').addEventListener('cancel',e=>{if(noteSaving||!mayDiscard())e.preventDefault();});
async function saveNote(share){
 if(noteSaving)return;
 if(share&&!$('note-text').value.trim()){toast('先写一点想告诉她的内容吧。');return;}
 noteBusy(true);
 try{
  const n=await api('note',{name:$('note-name').value.trim(),text:$('note-text').value,version:noteVersion});
  $('note-name').value=n.name;$('note-name').readOnly=true;noteVersion=n.version;noteBaseline=noteValue();
  if(![...$('note-select').options].some(o=>o.value===n.name)){const o=el('option','',n.name);o.value=n.name;$('note-select').append(o);}$('note-select').value=n.name;
  $('note-status').textContent='已保存。';
  if(share&&await action('read',{name:n.name,version:n.version})){$('note-editor').close();setTab('letters');toast('她会先读完，再写回信。同一版内容不会重复回信。');}
  else if(!share)toast('便签已保存。');
  await refresh();
 }catch(e){$('note-status').textContent=e.message;toast(e.message);}finally{noteBusy(false);}
}
$('note-save').onclick=()=>saveNote(false);$('note-share').onclick=()=>saveNote(true);
function settings(){
 const list=$('personality-options');list.replaceChildren();
 for(const [key,value] of Object.entries(state.personalities)){const b=el('button',key===state.personality?'selected':'');b.type='button';b.append(el('b','',value.name),el('small','',value.description));b.onclick=async()=>{if(await action('personality',{value:key})){[...list.children].forEach(x=>x.classList.toggle('selected',x===b));toast('好，那我们慢慢熟悉起来。');}};list.append(b);}
 $('workspace-path').textContent=state.workspace;$('busy-minutes').value=String(state.busy_minutes);$('sharing-mode').value=state.quiet_sharing?'quiet':'open';$('settings').showModal();
}
$('settings-button').onclick=settings;$('profile-settings').onclick=settings;$('sharing-mode').onchange=()=>action('quiet',{value:$('sharing-mode').value==='quiet'});
$('export-button').onclick=async()=>{const content=await api('export');const a=document.createElement('a');const url=URL.createObjectURL(new Blob([JSON.stringify(content,null,2)],{type:'application/json'}));a.href=url;a.download='悠小喵-相处记录-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);};
async function chat(text){
 if(chatBusy||!text.trim())return;chatBusy=true;$('send-button').disabled=true;$('chat-input').value='';
 state.messages.push({role:'user',text,time:Date.now()/1000});renderPanel();
 try{await api('chat',{text,id:crypto.randomUUID()});}catch(e){toast(e.message);$('chat-input').value=text;}
 finally{chatBusy=false;$('send-button').disabled=false;await refresh();}
}
$('chat-form').onsubmit=e=>{e.preventDefault();chat($('chat-input').value);};
$('chat-input').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();chat($('chat-input').value);}};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>chat(b.dataset.prompt));
async function refresh(){try{state=await api('state');render();}catch(e){$('save-status').textContent='小屋暂时断开 · 正在重连';}}
async function heartbeat(){try{await api('heartbeat',{});}catch(e){}}
window.addEventListener('pagehide',()=>{fetch('/api/pause',{method:'POST',headers:{'Content-Type':'application/json','X-Pet-Token':token},body:'{}',keepalive:true}).catch(()=>{});});
(async()=>{await refresh();await heartbeat();setInterval(refresh,1500);setInterval(heartbeat,2500);$('day-tag').textContent='☀ '+new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric'});})();
