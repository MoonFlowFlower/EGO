// Fixed entity observation/pickup. No model, generated code, digging or placing.
const logs = new Set(['oak_log','spruce_log','birch_log','jungle_log','acacia_log','dark_oak_log','mangrove_log','cherry_log']);
const matches = (wanted, item) => wanted === item || wanted === 'wood' && logs.has(item);
const point = p => ({x:p.x,y:p.y,z:p.z});
const distance = (a,b) => Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
const counts = bot => {
  const result={}; for(const item of bot.inventory.items()) result[item.name]=(result[item.name]||0)+item.count;
  return result;
};
export function trackPickups(bot, session) {
  const events=[];
  const listener=(collector,entity)=>{
    if(collector?.id!==bot.entity?.id)return;
    let item;try{item=entity.getDroppedItem?.()}catch{return}
    if(!item||typeof item.name!=='string'||!Number.isInteger(item.count)||item.count<=0||!entity.position)return;
    events.push({entity_id:entity.id,entity_key:`${session}:${entity.id}`,item:item.name,count:item.count,
      position:point(entity.position),collected_at:Date.now(),collector_id:collector.id});
    if(events.length>64)events.shift();
  };
  bot.on('playerCollect',listener);
  return {snapshot:()=>events.filter(e=>Date.now()-e.collected_at<=120000).map(e=>({...e})),
    close:()=>bot.removeListener('playerCollect',listener)};
}
export function observeItems(bot, range=16, session='unknown') {
  const center=point(bot.entity.position),items=[];
  for(const entity of Object.values(bot.entities||{})) {
    if(entity.name!=='item'||!Number.isInteger(entity.id)||distance(center,entity.position)>range)continue;
    let item;try{item=entity.getDroppedItem?.()}catch{continue}
    if(!item||typeof item.name!=='string'||!Number.isInteger(item.count)||item.count<=0)continue;
    items.push({entity_id:entity.id,entity_key:`${session}:${entity.id}`,item:item.name,count:item.count,
      position:point(entity.position),distance:distance(center,entity.position)});
  }
  items.sort((a,b)=>a.distance-b.distance||a.entity_id-b.entity_id);
  return {sampled_at:Date.now(),range,center,scope:'visible_entities_only',origin:'dropper_unknown',
    items:items.slice(0,64),truncated:items.length>64};
}

export async function pickupItems(bot, Movements, goals, args, session, {wait=ms=>new Promise(r=>setTimeout(r,ms)),pathTimeout=10000}={}) {
  const observed=observeItems(bot,16,session);
  const selected=args.entity_ids.map(id=>observed.items.find(e=>e.entity_id===id));
  if(selected.some(e=>!e||!matches(args.item,e.item)))return {verified:false,status:'pickup_target_missing',observation_complete:true};
  const before=counts(bot),events=[],seen=new Set(),old=bot.pathfinder.movements;
  const listener=(collector,entity)=>{
    if(collector?.id!==bot.entity.id)return;
    const target=selected.find(e=>e.entity_id===entity.id);
    if(!target||seen.has(target.entity_key))return;
    // Re-read actual stack metadata when available; otherwise the bound pre-action observation.
    let item;try{item=entity.getDroppedItem?.()}catch{}
    if(item&&(item.name!==target.item||!Number.isInteger(item.count)||item.count<=0))return;
    seen.add(target.entity_key);events.push({entity_id:target.entity_id,entity_key:target.entity_key,
      item:target.item,count:item?.count||target.count,collector_id:collector.id});
  };
  bot.on('playerCollect',listener);
  const movement=new Movements(bot);
  movement.canDig=false;movement.allow1by1towers=false;movement.scafoldingBlocks=[];movement.canOpenDoors=false;
  bot.pathfinder.setMovements(movement);
  let problem=null;
  try {
    for(const target of selected) {
      if(bot.interrupt_code){problem='interrupted';break}
      if(seen.has(target.entity_key))continue;
      const entity=bot.entities[target.entity_id];
      if(!entity){problem='pickup_target_missing';break}
      // A target may have moved/merged since observation. Never chase outside the bounded region.
      if(distance(bot.entity.position,entity.position)>16){problem='pickup_target_missing';break}
      let timer;
      try {
        await Promise.race([bot.pathfinder.goto(new goals.GoalNear(entity.position.x,entity.position.y,entity.position.z,0.7)),
          new Promise((_,reject)=>{timer=setTimeout(()=>{bot.pathfinder.setGoal(null);reject(new Error('pickup_path_deadline'))},pathTimeout)})]);
      } catch {problem=bot.interrupt_code?'interrupted':'pickup_path_failed';break}
      finally {clearTimeout(timer)}
      for(let i=0;i<10&&!bot.interrupt_code&&!seen.has(target.entity_key);i++)await wait(100);
    }
    for(let i=0;i<10&&!bot.interrupt_code;i++) {
      const now=counts(bot);
      if(events.every(e=>(now[e.item]||0)-(before[e.item]||0)>=events.filter(x=>x.item===e.item).reduce((n,x)=>n+x.count,0)))break;
      await wait(100);
    }
  } finally {
    bot.removeListener('playerCollect',listener);
    bot.pathfinder.setGoal(null);
    bot.pathfinder.setMovements(old);
  }
  const after=counts(bot),gained={};
  for(const item of new Set(events.map(e=>e.item)))gained[item]=(after[item]||0)-(before[item]||0);
  const supported=events.filter(e=>gained[e.item]>=events.filter(x=>x.item===e.item).reduce((n,x)=>n+x.count,0));
  const picked=supported.reduce((n,e)=>n+e.count,0);
  const verified=!bot.interrupt_code&&!problem&&picked>=args.count;
  return {verified,status:verified?'pickup_checked':problem||'pickup_partial',
    evidence:'self_collect_events_and_inventory',pickup_events:supported,inventory_gained:gained,
    gained:picked,origin:'dropper_unknown_spatially_bound_entities',navigation:'no_break_no_place'};
}
