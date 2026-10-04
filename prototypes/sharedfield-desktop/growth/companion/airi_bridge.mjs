// Plain JSON is an officially accepted AIRI channel protocol encoding.
// This process has a local WebSocket token only, never a model or cloud key.
import readline from 'node:readline';
import {randomUUID,createHash} from 'node:crypto';
import {stageTarget,displayRoute} from './bridge_protocol.mjs';
const lines=readline.createInterface({input:process.stdin});
const input=lines[Symbol.asyncIterator]();
const cfg=JSON.parse((await input.next()).value||'{}');
if(cfg.url!=='ws://127.0.0.1:6121/ws'||typeof cfg.token!=='string'||!cfg.token)throw new Error('local_channel_required');
const emit=value=>process.stdout.write(JSON.stringify({unix_ms:Date.now(),...value})+'\n');
const identity={id:'ego-kernel',extension:{id:'ego-kernel',version:'1.0.0',sessionId:randomUUID()}};
let ws,ready=false,closed=false,retry,target=null;
const heartbeat=setInterval(()=>{if(ready)send('transport:connection:heartbeat',{kind:'ping',message:'🩵',at:Date.now()})},30000);
const pending=[];
function send(type,data,id=randomUUID(),route){
  if(ws?.readyState!==WebSocket.OPEN)return false;
  ws.send(JSON.stringify({type,data,route,metadata:{source:{kind:'plugin',...identity,plugin:{id:'ego-kernel'}},event:{id}}}));return true;
}
function publish(message){
  if(!ready||!target){if(pending.length<20)pending.push(message);else emit({kind:'mirror_queue_full',id:message.id});return}
  send('input:text',{text:message.text},message.id,displayRoute(target));
  emit({kind:'mirror_sent',id:message.id,single_stage_destination:true});
}
function flush(){if(ready&&target)while(pending.length)publish(pending.shift())}
function reconnect(socket,kind){
  if(closed||socket!==ws)return;
  ready=false;target=null;ws=null;
  socket.onopen=socket.onmessage=socket.onerror=socket.onclose=null;
  emit({kind});
  try{socket.close()}catch{}
  clearTimeout(retry);retry=setTimeout(connect,5000);
}
function connect(){
  if(closed)return;
  const socket=ws=new WebSocket(cfg.url);
  socket.onopen=()=>{if(!closed&&socket===ws)send('module:authenticate',{token:cfg.token})};
  socket.onmessage=event=>{
    if(closed||socket!==ws)return;
    let row;try{row=JSON.parse(event.data);row=row.json||row}catch{return}
    if(row.type==='registry:modules:sync'){
      target=stageTarget(row.data?.modules||[]);emit({kind:'stage_destination',available:!!target});flush();
    }
    if(row.type==='module:authenticated'&&row.data?.authenticated){
      send('extension:module:announce',{name:'ego-kernel',identity,possibleEvents:['input:text'],dependencies:[]});
    }
    if(row.type==='extension:module:announced'&&row.data?.identity?.id===identity.id){
      ready=true;emit({kind:'bridge_ready'});flush();
    }
    if(row.type==='transport:connection:heartbeat'&&row.data?.kind==='ping')send(row.type,{kind:'pong',message:'💛',at:Date.now()});
    if(row.type==='output:gen-ai:chat:complete'||row.type==='output:gen-ai:chat:message')
      emit({kind:'airi_output',type:row.type,sha256:createHash('sha256').update(JSON.stringify(row.data)).digest('hex')});
    if(row.type?.includes('error'))emit({kind:'bridge_protocol_error',type:row.type});
  };
  socket.onerror=()=>reconnect(socket,'bridge_connection_error');
  socket.onclose=()=>reconnect(socket,'bridge_disconnected');
}
function close(){closed=true;clearTimeout(retry);clearInterval(heartbeat);ws?.close();setTimeout(()=>process.exit(0),150)}
lines.on('close',close);process.on('SIGTERM',close);connect();
for await(const line of input){let m;try{m=JSON.parse(line)}catch{continue}
  if(m.op==='shutdown'){close();break}
  if(m.op==='publish'&&typeof m.text==='string'&&m.text.length<=6500)publish(m);
}
