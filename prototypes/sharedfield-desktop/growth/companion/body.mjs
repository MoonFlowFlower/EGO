// Model-free body. Imports official skills, never Agent/Prompter/Coder.
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import repair1211 from '../p7/protocol_1211.cjs';

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
    protocol_patch:true,skills:['goToPlayer','collectBlock','craftRecipe','giveToPlayer','placeBlock'].every(k=>typeof skills[k]==='function')});
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
    inventory:counts(bot.inventory.items()),crafting_grid:counts(bot.inventory.slots.slice(0,5)),
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
  const spec={inspect:[],approach:[],follow:[],stop:[],search:['block','range'],collect:['block','count'],craft:['item','count'],give:['item','count'],place:['block']};
  if(!action||!Object.hasOwn(spec,action.name)||!action.args||Object.keys(action).sort().join()!=['args','name'].join()||Object.keys(action.args).sort().join()!=spec[action.name].slice().sort().join())throw new Error('action_not_allowed');
  for(const [k,v] of Object.entries(action.args)) {
    if(['item','block'].includes(k)&&!(typeof v==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(v)))throw new Error('invalid_identifier');
    if(k==='count'&&!(Number.isInteger(v)&&v>=1&&v<=(action.name==='give'?16:8)))throw new Error('invalid_count');
    if(k==='range'&&!(Number.isInteger(v)&&v>=8&&v<=64))throw new Error('invalid_range');
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
  interrupt();bot.interrupt_code=false;
  const epoch=generation;
  current=action.name;
  const before=snapshot(); const {name,args}=action;
  let timer,timedOut=false,receipt={verified:false,status:'not_demonstrated'};
  try {
    const execute=async()=>{
      if(name==='inspect')return {verified:true,status:'observed'};
      if(name==='approach') {
        if(!bot.players.Moonlight?.entity)return {verified:false,status:'owner_not_visible'};
        await skills.goToPlayer(bot,'Moonlight',1.5);
        const state=snapshot();
        return {verified:!!state.owner&&state.owner.distance<=3.25&&state.owner.height_difference<=1.25,status:'approach_checked'};
      }
      if(name==='follow') {
        const owner=bot.players.Moonlight?.entity;
        if(!owner)return {verified:false,status:'owner_not_visible'};
        const movement=new Movements(bot);movement.canDig=false;
        bot.pathfinder.setMovements(movement);bot.pathfinder.setGoal(new goals.GoalFollow(owner,2),true);
        return {verified:true,status:'following_started_only'};
      }
      if(name==='search') {
        if(mc.getBlockId(args.block)===null)return {verified:false,status:'unknown_block'};
        const block=world.getNearestBlock(bot,args.block,args.range);
        return {verified:!!block,status:block?'block_located':'block_not_found',block_position:block?.position};
      }
      if(name==='collect') {
        if(mc.getBlockId(args.block)===null)return {verified:false,status:'unknown_block'};
        await skills.collectBlock(bot,args.block,args.count);
        const item={iron_ore:'raw_iron',deepslate_iron_ore:'raw_iron',stone:'cobblestone'}[args.block]||args.block;
        const gain=(snapshot().inventory[item]||0)-(before.inventory[item]||0);
        return {verified:gain>=args.count,status:'collection_inventory_checked',item,gained:gain};
      }
      if(name==='craft') {
        if(Object.keys(before.crafting_grid).length||before.cursor||before.window)return {verified:false,status:'crafting_grid_or_cursor_not_clear'};
        if(mc.getItemId(args.item)===null)return {verified:false,status:'unknown_item'};
        await skills.craftRecipe(bot,args.item,args.count);
        const gain=(snapshot().inventory[args.item]||0)-(before.inventory[args.item]||0);
        const recipe=mc.getItemCraftingRecipes(args.item)?.[0];
        return {verified:!!recipe&&gain>=args.count*recipe[1].craftedCount,status:'craft_inventory_checked',gained:gain};
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
        if(mc.getBlockId(args.block)===null)return {verified:false,status:'unknown_block'};
        const pos=world.getNearestFreeSpace(bot,1,4);
        if(!pos)return {verified:false,status:'no_placement_space'};
        await skills.placeBlock(bot,args.block,pos.x,pos.y,pos.z);
        return {verified:bot.blockAt(pos)?.name===args.block,status:'placed_block_checked',position:pos};
      }
    };
    receipt=await Promise.race([execute(),new Promise((_,reject)=>{timer=setTimeout(()=>{timedOut=true;interrupt();reject(new Error('action_timeout'))},60000)})]);
    if(epoch!==generation)receipt={verified:false,status:'interrupted'};
  }catch(error){receipt={verified:false,status:'action_failed',error_type:error.name};interrupt()}
  finally{clearTimeout(timer);if(name!=='follow'||!receipt.verified)current=null}
  emit({kind:'receipt',id,receipt:{...receipt,observed:snapshot(),output:bot.output.slice(-1200)}});
  bot.output='';
  // A timed-out library promise might still own controls. Terminate this body
  // instead of admitting a second action alongside an unfinished promise.
  if(timedOut){emit({kind:'action_deadline_exit'});await close()}
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
