import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';

// Execute the production bridge with an event-only WebSocket double. No network,
// credentials, AIRI config, model, or game is accessed by this regression check.
const bootstrap=`
let count=0;
const emit=row=>process.stdout.write(JSON.stringify(row)+'\\n');
globalThis.WebSocket=class {
  static OPEN=1;
  constructor(){
    this.n=++count;this.readyState=1;
    emit({kind:'test_connection_attempt',n:this.n,at:Date.now()});
    setTimeout(()=>{
      if(this.n===1){this.onerror?.({});return} // error without close
      this.onopen?.();
    },10);
  }
  send(raw){
    const row=JSON.parse(raw);
    const message=(type,data)=>this.onmessage?.({data:JSON.stringify({type,data})});
    if(row.type==='module:authenticate')message('module:authenticated',{authenticated:true});
    if(row.type==='extension:module:announce'){
      message('registry:modules:sync',{modules:[{name:'proj-airi:stage-tamagotchi',identity:{id:'stage'}}]});
      message('extension:module:announced',{identity:{id:'ego-kernel'}});
      if(this.n===2){
        const staleError=this.onerror,staleMessage=this.onmessage;
        setTimeout(()=>{
          this.onclose?.();staleError?.({});
          staleMessage?.({data:JSON.stringify({type:'extension:module:announced',data:{identity:{id:'ego-kernel'}}})});
        },10);
      }
    }
    if(row.type==='input:text')emit({kind:'test_display',n:this.n,id:row.metadata.event.id});
  }
  close(){this.readyState=3;this.onclose?.()}
};
`;
const child=spawn(process.execPath,['--import','data:text/javascript,'+encodeURIComponent(bootstrap),fileURLToPath(new URL('./airi_bridge.mjs',import.meta.url))],{stdio:['pipe','pipe','pipe']});
const rows=[];let buffer='',errors='';
child.stdout.on('data',chunk=>{
  buffer+=chunk;
  for(let i;(i=buffer.indexOf('\n'))>=0;){
    const line=buffer.slice(0,i);buffer=buffer.slice(i+1);
    const row=JSON.parse(line);rows.push(row);
    if(row.kind==='test_connection_attempt'&&row.n===3)
      child.stdin.write(JSON.stringify({op:'publish',id:'one',text:'cached reply'})+'\n');
    if(row.kind==='test_display')child.stdin.write(JSON.stringify({op:'shutdown'})+'\n');
  }
});
child.stderr.on('data',chunk=>errors+=chunk);
const timer=setTimeout(()=>child.kill(),15000);
child.stdin.write(JSON.stringify({url:'ws://127.0.0.1:6121/ws',token:'test-local-token'})+'\n');
const exit=await new Promise((resolve,reject)=>{child.once('exit',resolve);child.once('error',reject)});
clearTimeout(timer);
assert.equal(exit,0,errors||'bridge did not shut down cleanly');
const attempts=rows.filter(r=>r.kind==='test_connection_attempt');
assert.equal(attempts.length,3,'exactly one retry per failed socket');
assert.ok(attempts[1].at-attempts[0].at>=4900,'error-only reconnect must wait');
assert.ok(attempts[2].at-attempts[1].at>=4900,'close reconnect must wait');
assert.equal(rows.filter(r=>r.kind==='bridge_connection_error').length,1);
assert.equal(rows.filter(r=>r.kind==='bridge_disconnected').length,1);
assert.equal(rows.filter(r=>r.kind==='bridge_ready').length,2,'stale callback must not revive an old socket');
assert.deepEqual(rows.filter(r=>r.kind==='test_display').map(r=>[r.n,r.id]),[[3,'one']]);
console.log('bridge reconnect checks passed: error-only, duplicate/stale events, paced retries, queued display, clean shutdown');
