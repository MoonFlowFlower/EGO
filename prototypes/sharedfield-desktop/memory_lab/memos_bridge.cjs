// JSON-lines bridge to the pinned native plugin, not its OpenClaw host entry.
require('./vendor/MemOS/apps/memos-local-openclaw/node_modules/tsx/dist/cjs/index.cjs');
const { initPlugin } = require('./vendor/MemOS/apps/memos-local-openclaw/src/index.ts');
const fs=require('fs'); const path=require('path');
const {createInterface}=require('readline');
const root=__dirname;
const token=fs.readFileSync(path.join(root,'state/gateway-token.txt'),'utf8');
const endpoint='http://127.0.0.1:18765';
const inference=JSON.parse(fs.readFileSync(path.join(root,'state/gateway.json'),'utf8')).profile;
let plugin;
let errors=[];
const logger=Object.fromEntries(['debug','info','warn','error'].map(level=>[level,(...args)=>{
  if(level==='error') errors.push(args.map(String).join(' '));
  process.stderr.write(`[${level}] ${args.join(' ')}\n`);
}]));
async function handle(msg){
  if(msg.op==='init') {
    plugin=initPlugin({stateDir:msg.directory,workspaceDir:msg.directory,log:logger,config:{
      telemetry:{enabled:false},sharing:{enabled:false},skillEvolution:{enabled:false,autoInstall:false},
      storage:{dbPath:path.join(msg.directory,'memos.db')},
      summarizer:{provider:'openai',endpoint:endpoint+'/memos/v1/chat/completions',apiKey:token,
        model:inference.model,timeoutMs:200000,temperature:0},
      embedding:{provider:'openai',endpoint:endpoint+'/v1/embeddings',apiKey:token,
        model:'BAAI/bge-m3',dimensions:1024,batchSize:4,retry:0,timeoutMs:200000}
    }}); return {ready:true};
  }
  if(msg.op==='retain') {
    for(const e of msg.events) plugin.onConversationTurn([{role:'user',content:JSON.stringify(e)}],e.id,'agent:main');
    await plugin.flush();
    if(errors.length){const e=errors;errors=[];throw Error(e.join(';'));}
    return {ok:true};
  }
  if(msg.op==='flush'){await plugin.flush();return {ok:true};}
  if(msg.op==='recall') return await plugin.tools.find(t=>t.name==='memory_search').handler({query:msg.query,maxResults:12,minScore:0.35});
  if(msg.op==='close'){await plugin.shutdown();return {ok:true};}
  throw Error('Unknown bridge operation');
}
const rl=createInterface({input:process.stdin,crlfDelay:Infinity});
(async()=>{for await(const line of rl){try {const result=await handle(JSON.parse(line));process.stdout.write(JSON.stringify({result,metrics:{peak_rss_bytes:process.resourceUsage().maxRSS*1024}})+'\n');}
catch(e){process.stdout.write(JSON.stringify({error:String(e)})+'\n');}}})();
