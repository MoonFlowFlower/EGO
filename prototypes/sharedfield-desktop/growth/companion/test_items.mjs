import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {observeItems,pickupItems,trackPickups} from './items.mjs';
let checks=0;
const check=(condition)=>{assert.ok(condition);checks++};
function fixture(mode='success') {
  const bot=new EventEmitter();let amount=0;
  bot.entity={id:1,position:{x:0,y:64,z:0}};
  const item={id:41,name:'item',position:{x:3,y:64,z:0},getDroppedItem:()=>({name:'oak_log',count:8})};
  bot.entities={41:item};bot.inventory={items:()=>amount?[{name:'oak_log',count:amount}]:[]};
  bot.interrupt_code=false;
  bot.pathfinder={movements:{old:true},setMovements(m){this.movements=m},setGoal(){},async goto(){
    check(this.movements.canDig===false&&this.movements.scafoldingBlocks.length===0&&this.movements.canOpenDoors===false);
    if(mode==='path_error')throw new Error('blocked');
    if(mode==='cancel'){bot.interrupt_code=true;return}
    if(mode!=='no_inventory')amount=8;
    if(mode!=='no_event')bot.emit('playerCollect',{id:mode==='other_player'?2:1},item);
    delete bot.entities[41];
  }};
  return bot;
}
class Movements {}
class GoalNear {constructor(x,y,z,r){Object.assign(this,{x,y,z,r})}}
const args={entity_ids:[41],item:'wood',count:8};
const options={wait:async()=>{},pathTimeout:30};
for(const mode of ['success','other_player','no_inventory','no_event','path_error','cancel']) {
  const bot=fixture(mode),old=bot.pathfinder.movements;
  const tracker=trackPickups(bot,'session');
  const observation=observeItems(bot,16,'session');
  check(observation.items[0].entity_id===41&&observation.items[0].count===8);
  check(observation.scope==='visible_entities_only'&&observation.origin==='dropper_unknown');
  const receipt=await pickupItems(bot,Movements,{GoalNear},args,'session',options);
  check(receipt.verified===(mode==='success'));
  if(mode==='success') {
    check(receipt.gained===8&&receipt.pickup_events[0].entity_key==='session:41');
    check(tracker.snapshot()[0].collector_id===1);
  }
  if(mode==='other_player')check(tracker.snapshot().length===0&&receipt.pickup_events.length===0);
  if(mode==='no_inventory'||mode==='no_event')check(receipt.pickup_events.length===0);
  check(bot.pathfinder.movements===old);
  tracker.close();check(bot.listenerCount('playerCollect')===0);
}
for(const change of ['missing','far','wrong_item']) {
  const bot=fixture();
  if(change==='missing')delete bot.entities[41];
  if(change==='far')bot.entities[41].position.x=50;
  const receipt=await pickupItems(bot,Movements,{GoalNear},{...args,item:change==='wrong_item'?'diamond':'wood'},'session',options);
  check(receipt.status==='pickup_target_missing'&&!receipt.verified);
  check(bot.listenerCount('playerCollect')===0);
}
console.log(JSON.stringify({checks,status:'passed',minecraft:false}));
