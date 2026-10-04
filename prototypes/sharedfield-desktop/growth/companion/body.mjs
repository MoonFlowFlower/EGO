// Model-free body. Imports official skills, never Agent/Prompter/Coder.
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import repair1211 from '../p7/protocol_1211.cjs';
import {searchBlocks} from './search.mjs';
import {placeNextBlock} from './placement.mjs';
import {recoverInventory,craftChecked} from './inventory.mjs';
import {inspectArea,placeAt,verifyBlocks,validPosition} from './spatial.mjs';
import {collectTree,approachOwner,approachBlock} from './trees.mjs';

const lines = readline.createInterface({input:process.stdin});
const input = lines[Symbol.asyncIterator]();
const config = JSON.parse((await input.next()).value || '{}');
if (config.host !== '127.0.0.1' || config.port !== 25565) throw new Error('local_reviewed_world_only');
const root = path.resolve(config.root);
if (fs.existsSync(path.join(root,'keys.json'))) throw new Error('keys_file_refused');
for (const key of Object.keys(process.env)) if (/KEY|TOKEN|SECRET|PASSWORD/i.test(key)) delete process.env[key];
const emit = event => process.stdout.write(JSON.stringify({unix_ms:Date.now(),...event})+'\n');
for (const name of ['log','error','warn']) console[name] = (...args) => emit({kind:'technical',message:args.map(v=>v instanceof Error?v.name:String(v)).join(' ').slice(0,1500)});
const req = createRequire(path.join(root,'package.json'));
repair1211(req);
const load = relative => import(pathToFileURL(path.join(root,relative)));
const {setSettings,default:settings} = await load('src/agent/settings.js');
setSettings({minecraft_version:'1.21.1',host:config.host,port:config.port,auth:'offline',
  allow_insecure_coding:false,allow_vision:false,speak:false,render_bot_view:false,language:'en'});
Object.freeze(settings);
const mc = await load('src/utils/mcdata.js');
const skills = await load('src/agent/library/skills.js');
const world = await load('src/agent/library/world.js');
const {goals,Movements} = req('mineflayer-pathfinder');
if(config.probe) {
  emit({kind:'offline_probe',model_client_initialized:false,generated_code_enabled:false,
    protocol_patch:true,skills:['goToPlayer','goToPosition','collectBlock','craftRecipe','giveToPlayer','placeBlock'].every(k=>typeof skills[k]==='function')});
  process.exit(0);
}
const bot = mc.initBot('EgoP7');
bot.output = '';
bot.interrupt_code = false;
bot.modes = {isOn:()=>false,pause(){},unpause(){}};
let online=false, current=null, generation=0, closing=false;
const sleep = ms=>new Promise(resolve=>setTimeout(resolve,ms));
const counts = items => { const result={}; for(const item of items) if(item) result[item.name]=(result[item.name]||0)+item.count; return result; };
function snapshot() {
  if(!online||!bot.entity)return {offline:true,model_client_initialized:false,generated_code_enabled:false};
  const owner=bot.players.Moonlight?.entity;
  return {offline:false,position:bot.entity.position,health:bot.health,hunger:bot.food,
    inventory:counts(bot.inventory.items()),crafting_grid:counts(bot.inventory.slots.slice(1,5)),
    cursor:bot.inventory.selectedItem?{name:bot.inventory.selectedItem.name,count:bot.inventory.selectedItem.count}:null,
    window:bot.currentWindow?{type:bot.currentWindow.type,cursor:bot.currentWindow.selectedItem?.name||null}:null,
    owner:owner?{name:'Moonlight',position:owner.position,distance:owner.position.distanceTo(bot.entity.position),height_difference:Math.abs(owner.position.y-bot.entity.position.y)}:null,
    controls:bot.controlState,current_action:current,model_client_initialized:false,generated_code_enabled:false};
}
function interrupt() {
  generation++;
  bot.interrupt_code=true;
  try{bot.collectBlock.cancelTask()}catch{}
  try{bot.pathfinder.setGoal(null);bot.pathfinder.stop()}catch{}
  try{bot.stopDigging();bot.pvp.stop();bot.clearControlStates()}catch{}
  if(current==='follow')current=null;
}
function allowed(action) {
  const spec={inspect:[],approach:[],follow:[],stop:[],search:['block','range'],go_to_block:['block','range'],collect:['block','count'],collect_tree:['block','range'],craft:['item','count'],give:['item','count'],place:['block'],recover_inventory:[],inspect_area:['radius'],place_at:['block','position'],verify_blocks:['targets']};
  if(!action||!Object.hasOwn(spec,action.name)||!action.args||Object.keys(action).sort().join()!=['args','name'].join()||Object.keys(action.args).sort().join()!=spec[action.name].slice().sort().join())throw new Error('action_not_allowed');
  for(const [k,v] of Object.entries(action.args)) {
    if(['item','block'].includes(k)&&!(typeof v==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(v)))throw new Error('invalid_identifier');
    if(k==='count'&&!(Number.isInteger(v)&&v>=1&&v<=(action.name==='give'?16:8)))throw new Error('invalid_count');
    if(k==='range'&&!(Number.isInteger(v)&&v>=8&&v<=128))throw new Error('invalid_range');
    if(k==='radius'&&!(Number.isInteger(v)&&v>=1&&v<=4))throw new Error('invalid_radius');
    if(k==='position'&&!validPosition(v))throw new Error('invalid_position');
    if(k==='targets'&&!(Array.isArray(v)&&v.length>0&&v.length<=128&&v.every(t=>t&&Object.keys(t).sort().join()==='block,position'&&typeof t.block==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(t.block)&&validPosition(t.position))))throw new Error('invalid_targets');
  }
}
async function run(message) {
  const {id,action}=message;
  try{allowed(action)}catch{emit({kind:'receipt',id,receipt:{verified:false,status:'action_rejected'}});return}
  if(!online){emit({kind:'receipt',id,receipt:{verified:false,status:'body_offline'}});return}
  if(current&&current!=='follow'&&action.name!=='stop'){emit({kind:'receipt',id,receipt:{verified:false,status:'body_busy'}});return}
  if(action.name==='stop') {
    interrupt();await sleep(150);
    emit({kind:'receipt',id,receipt:{verified:!Object.values(bot.controlState).some(Boolean)&&!bot.targetDigBlock,status:'stopped',observed:snapshot()}});return;
  }
  if(['inspect','inspect_area','verify_blocks'].includes(action.name)) {
    const receipt=action.name==='inspect'?{verified:true,status:'observed'}:
      action.name==='inspect_area'?inspectArea(bot,action.args.radius):verifyBlocks(bot,action.args.targets);
    emit({kind:'receipt',id,receipt:{...receipt,observed:snapshot()}});return;
  }
  interrupt();bot.interrupt_code=false;
  const epoch=generation;
  current=action.name;
  const before=snapshot(); const {name,args}=action;
  let timer,timedOut=false,receipt={verified:false,status:'not_demonstrated'};
  try {
    const execute=async()=>{
      if(name==='recover_inventory')return recoverInventory(bot);
      if(name==='collect_tree') {
        if(args.block!=='wood'&&!mc.WOOD_TYPES.some(t=>`${t}_log`===args.block))return {verified:false,status:'unknown_tree_type'};
        return collectTree(bot,{...mc,WOOD_TYPES:args.block==='wood'?mc.WOOD_TYPES:[args.block.slice(0,-4)]},Movements,goals,args.range);
      }
      if(name==='place_at')return placeAt(bot,mc,skills,args.block,args.position);
      if(name==='approach') {
        return approachOwner(bot,Movements,goals);
      }
      if(name==='follow') {
        const owner=bot.players.Moonlight?.entity;
        if(!owner)return {verified:false,status:'owner_not_visible'};
        const movement=new Movements(bot);movement.canDig=false;movement.allow1by1towers=false;movement.scafoldingBlocks=[];movement.canOpenDoors=false;
        bot.pathfinder.setMovements(movement);bot.pathfinder.setGoal(new goals.GoalFollow(owner,2),true);
        return {verified:true,status:'following_started_only'};
      }
      if(name==='search')return searchBlocks(bot,mc,world,args.block,args.range);
      if(name==='go_to_block') {
        const target=searchBlocks(bot,mc,world,args.block,args.range);
        if(!target.found)return {...target,verified:false,status:'navigation_target_not_found'};
        return {...target,...await approachBlock(bot,Movements,goals,target.block_position)};
      }
      if(name==='collect') {
        if(mc.getBlockId(args.block)===null)return {verified:false,status:'unknown_block'};
        await skills.collectBlock(bot,args.block,args.count);
        const item={iron_ore:'raw_iron',deepslate_iron_ore:'raw_iron',stone:'cobblestone'}[args.block]||args.block;
        const gain=(snapshot().inventory[item]||0)-(before.inventory[item]||0);
        return {verified:gain>=args.count,status:'collection_inventory_checked',item,gained:gain};
      }
      if(name==='craft') {
        return craftChecked(bot,mc,skills,args.item,args.count);
      }
      if(name==='give') {
        if(!bot.players.Moonlight?.entity)return {verified:false,status:'owner_not_visible'};
        let collected=0;
        const onCollect=(collector,entity)=>{try{const item=entity.getDroppedItem?.();if(collector.username==='Moonlight'&&item?.name===args.item)collected+=item.count}catch{}};
        bot.on('playerCollect',onCollect);
        try{await skills.giveToPlayer(bot,args.item,'Moonlight',args.count)}finally{bot.removeListener('playerCollect',onCollect)}
        const loss=(before.inventory[args.item]||0)-(snapshot().inventory[args.item]||0);
        return {verified:loss===args.count&&collected>=args.count,status:'give_entity_and_inventory_checked',lost:loss,matching_collected:collected};
      }
      if(name==='place') {
        return placeNextBlock(bot,mc,world,skills,args.block);
      }
    };
    receipt=await Promise.race([execute(),new Promise((_,reject)=>{timer=setTimeout(()=>{timedOut=true;interrupt();reject(new Error('action_timeout'))},60000)})]);
    if(epoch!==generation)receipt={verified:false,status:'interrupted'};
  }catch(error){receipt={verified:false,status:timedOut?'action_timeout':'action_failed',error_type:error.name};interrupt()}
  finally{clearTimeout(timer);if(name!=='follow'||!receipt.verified)current=null}
  emit({kind:'receipt',id,receipt:{...receipt,observed:snapshot(),output:bot.output.slice(-1200)}});
  bot.output='';
  // A timed-out library promise might still own controls. Terminate this body
  // instead of admitting a second action alongside an unfinished promise.
  if(timedOut){bot.whisper('Moonlight','刚才的动作超过60秒，我会重新连接；进度保留，这个动作不会自动重试。');emit({kind:'action_deadline_exit'});await close()}
}
bot.on('chat',(name,text)=>{if(name==='Moonlight'&&text.trim())emit({kind:'owner_input',text})});
bot.on('whisper',(name,text)=>{if(name==='Moonlight'&&text.trim())emit({kind:'owner_input',text})});
bot.once('spawn',async()=>{await sleep(1000);online=true;emit({kind:'ready',state:snapshot()})});
bot.on('error',error=>emit({kind:'body_error',error_type:error.name}));
bot.on('end',()=>{online=false;emit({kind:'disconnected'});if(!closing)process.exit(1)});
const stateTimer=setInterval(()=>emit({kind:'state',state:snapshot()}),1000);
const spawnTimer=setTimeout(()=>{if(!online){emit({kind:'spawn_timeout'});process.exit(1)}},120000);
async function close() {
  if(closing)return;closing=true;interrupt();clearInterval(stateTimer);clearTimeout(spawnTimer);
  emit({kind:'body_closing'});try{bot.quit()}catch{};setTimeout(()=>process.exit(0),200);
}
lines.on('close',close);process.on('SIGTERM',close);
emit({kind:'body_started',pid:process.pid,model_client_initialized:false,generated_code_enabled:false});
for await(const line of input) {
  let message;try{message=JSON.parse(line)}catch{continue}
  if(message.op==='shutdown'){await close();break}
  if(message.op==='action')void run(message);
  if(message.op==='say'&&online&&typeof message.text==='string') {
    // Whisper only to the owner. Model text can never become a slash command.
    const text=message.text.replace(/[\r\n]+/g,' ').slice(0,600);
    for(const chunk of text.match(/.{1,180}/gu)||[])bot.whisper('Moonlight',chunk);
  }
}
