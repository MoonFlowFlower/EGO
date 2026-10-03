// Adapter around the unmodified official v0.1.4 Agent. No MindServer listener.
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {EventEmitter} from 'node:events';

if (!process.argv.includes('--private-pipe') || process.stdout.isTTY) throw new Error('private_pipe_required');
const lines = readline.createInterface({input: process.stdin});
const queue = lines[Symbol.asyncIterator]();
const first = await queue.next();
const input = JSON.parse(first.value || '{}');
const root = path.resolve(input.root || '');
const here = path.dirname(fileURLToPath(import.meta.url));
const token = input.local_token;
if (typeof token !== 'string' || token.length < 32 || token.startsWith('sk-')) throw new Error('local_token_required');
if (input.host !== '127.0.0.1' || !Number.isInteger(input.port) || input.port < 1024 || input.port > 65535)
  throw new Error('reviewed_loopback_target_required');
if (fs.existsSync(path.join(root, 'keys.json'))) throw new Error('keys_file_override_refused');
const emit = value => process.stdout.write(JSON.stringify({unix_ms:Date.now(), ...value}).replaceAll(token, '[LOCAL_TOKEN_REDACTED]')+'\n');
for (const name of Object.keys(process.env)) if (/KEY|TOKEN|SECRET|PASSWORD/i.test(name) || name === 'INSECURE_CODING') delete process.env[name];
process.env.OPENAI_API_KEY = token;
process.chdir(root);
for (const method of ['log','warn','error']) console[method] = (...args) => emit({kind:'official_'+method,text:args.map(x=>x instanceof Error ? x.name+': '+x.message : typeof x==='string'?x:JSON.stringify(x)).join(' ')});
const load = relative => import(pathToFileURL(path.join(root,relative)).href);
const [{default:defaults},{default:settings,setSettings},{serverProxy},{Coder}] = await Promise.all([
  load('settings.js'),load('src/agent/settings.js'),load('src/agent/mindserver_proxy.js'),load('src/agent/coder.js')]);
const planned = JSON.parse(fs.readFileSync(path.join(here,'mindcraft_settings.json'),'utf8'));
const profile = JSON.parse(fs.readFileSync(path.join(here,'mindcraft_profile.json'),'utf8'));
setSettings({...defaults,...planned,host:input.host,port:input.port,profile});
// Freeze the setting object; official Prompter still fills profile defaults.
Object.freeze(settings.blocked_actions);
Object.freeze(settings.only_chat_with);
Object.freeze(settings);
if (settings.allow_insecure_coding !== false || settings.allow_vision !== false || settings.speak !== false
    || settings.language !== 'en' || settings.render_bot_view !== false || !settings.blocked_actions.includes('!newAction'))
  throw new Error('unsafe_settings');
for (const name of ['generateCode','_stageCode']) Object.defineProperty(Coder.prototype,name,{value:async()=>{throw new Error('generated_code_disabled')},writable:false,configurable:false});
const bus = new EventEmitter();
bus.on('bot-output',(name,message)=>emit({kind:'bot_output',name,message}));
Object.assign(serverProxy,{socket:bus,connected:true,name:profile.name,agents:[{name:profile.name,in_game:true}],
  login(){emit({kind:'login',name:profile.name})},shutdown(){process.exit(0)}});
const {blacklistCommands,commandExists} = await load('src/agent/commands/index.js');
blacklistCommands(settings.blocked_actions);
if (commandExists('!newAction')) throw new Error('generated_action_still_enabled');
let mutationBlocked=false;
try {settings.allow_insecure_coding=true} catch {mutationBlocked=true}
if (!mutationBlocked) throw new Error('settings_mutable');
if (input.probe) {
  let codeBlocked=false;
  try {await Coder.prototype.generateCode()} catch(e) {codeBlocked=e.message==='generated_code_disabled'}
  emit({kind:'offline_probe',mutationBlocked,codeBlocked,newActionPresent:commandExists('!newAction'),controlServerStarted:false,
    minecraft_version:settings.minecraft_version,model:profile.model,embedding:profile.embedding});
  process.exit(codeBlocked?0:1);
}
const {Agent} = await load('src/agent/agent.js');
const {getFullState} = await load('src/agent/library/full_state.js');
const agent = new Agent();
serverProxy.setAgent(agent);
let closing=false;
const close=()=>{if(closing)return;closing=true;try{agent.requestInterrupt();agent.shutUp();agent.bot?.clearControlStates();agent.bot?.quit()}catch{};setTimeout(()=>process.exit(0),250)};
lines.on('close',close);
process.on('SIGTERM',close);
process.on('SIGINT',close);
await agent.start(false,null,0);
const prompts={follow:'跟着我走',tree:'砍一棵树，收集至少一块原木',pickaxe:'做一把木镐',stop:'停下'};
const used=new Set();
function snapshot(){
  if(!agent.bot?.entity || !agent.respondFunc)return null;
  try{
    const value=getFullState(agent);
    const owner=agent.bot.players.Moonlight?.entity;
    return {...value,owner:owner?{position:owner.position,distance:owner.position.distanceTo(agent.bot.entity.position)}:null,
      controls:agent.bot.controlState,digging:!!agent.bot.targetDigBlock,generated_code_enabled:settings.allow_insecure_coding};
  }catch{return null}
}
const timer=setInterval(()=>emit({kind:'state',state:snapshot()}),1000);
emit({kind:'started',pid:process.pid,controlServerStarted:false});
try{
  for await(const line of queue){
    let command;try{command=JSON.parse(line)}catch{emit({error:'invalid_json'});continue}
    if(command.op==='shutdown')break;
    if(command.op==='status'){emit({kind:'status',state:snapshot()});continue}
    if(command.op!=='task'||!Object.hasOwn(prompts,command.id)){emit({error:'unknown_fixed_task'});continue}
    if(!snapshot()){emit({error:'agent_not_ready'});continue}
    if(used.has(command.id)){emit({error:'task_already_sent_no_rerun'});continue}
    used.add(command.id);
    emit({kind:'task_sent',task:command.id,prompt:prompts[command.id],operator:'codex_fixture',initial_state:snapshot()});
    // Same public Agent message path used by the official MindServer adapter.
    agent.respondFunc('Moonlight',prompts[command.id]);
  }
}finally{clearInterval(timer);close()}
