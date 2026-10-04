// A conservative loaded-chunk tree heuristic, not proof of world-generation origin.
const ground=new Set(['grass_block','dirt','coarse_dirt','podzol','rooted_dirt','moss_block']);
const point=p=>({x:p.x,y:p.y,z:p.z});
function walking(bot,Movements) {
  const movement=new Movements(bot);
  movement.canDig=false;movement.allow1by1towers=false;movement.scafoldingBlocks=[];movement.canOpenDoors=false;
  return movement;
}
export async function approachOwner(bot,Movements,goals) {
  const owner=bot.players.Moonlight?.entity;
  if(!owner)return {verified:false,status:'owner_not_visible'};
  const old=bot.pathfinder.movements;
  bot.pathfinder.setMovements(walking(bot,Movements));
  try {await bot.pathfinder.goto(new goals.GoalNear(owner.position.x,owner.position.y,owner.position.z,1.5));}
  finally {bot.pathfinder.setMovements(old);}
  const current=bot.players.Moonlight?.entity;
  return {verified:!!current&&bot.entity.position.distanceTo(current.position)<=3.25&&Math.abs(bot.entity.position.y-current.position.y)<=1.25,
    status:'approach_checked',navigation:'no_break_no_place'};
}
export function treeCandidate(bot,mc,range) {
  const ids=mc.WOOD_TYPES.map(t=>mc.getBlockId(`${t}_log`)).filter(v=>v!==null);
  const positions=bot.findBlocks({matching:ids,maxDistance:range,count:512});
  const candidates=[];
  for(const p of positions) {
    const base=bot.blockAt(p);
    if(!base?.name.endsWith('_log')||!ground.has(bot.blockAt(p.offset(0,-1,0))?.name))continue;
    let height=0;
    while(height<16&&bot.blockAt(p.offset(0,height,0))?.name===base.name)height++;
    if(height<3)continue;
    const leavesName=base.name.replace(/_log$/,'_leaves');
    let leaves=0;
    for(let x=-2;x<=2;x++)for(let z=-2;z<=2;z++)for(let y=height-2;y<=height+1;y++)
      if(bot.blockAt(p.offset(x,y,z))?.name===leavesName)leaves++;
    if(leaves>=5)candidates.push({block:base,height,leaves,distance:bot.entity.position.distanceTo(p)});
  }
  return candidates.sort((a,b)=>a.distance-b.distance)[0]||null;
}

export async function collectTree(bot,mc,Movements,goals,range) {
  if(bot.currentWindow||bot.inventory.selectedItem||bot.inventory.slots.slice(1,5).some(Boolean))
    return {verified:false,status:'crafting_grid_or_cursor_not_clear',recovery:'recover_inventory'};
  if(!bot.inventory.emptySlotCount())return {verified:false,status:'inventory_no_empty_slot'};
  const candidate=treeCandidate(bot,mc,range);
  if(!candidate)return {verified:false,status:'natural_tree_not_found',observation_complete:true,range,scope:'loaded_chunks_only'};
  const {block,height,leaves}=candidate;
  const amount=()=>bot.inventory.items().reduce((n,i)=>n+(i.name===block.name?i.count:0),0);
  const before=amount(),old=bot.pathfinder.movements;
  const movement=walking(bot,Movements);
  bot.pathfinder.setMovements(movement);
  let targetAfter=null;
  try {
    await bot.pathfinder.goto(new goals.GoalLookAtBlock(block.position,bot.world));
    if(bot.interrupt_code)return {verified:false,status:'interrupted'};
    if(bot.blockAt(block.position)?.name!==block.name)return {verified:false,status:'tree_target_changed'};
    // Only this reviewed trunk block is dug; navigation may not break or place blocks.
    await bot.dig(bot.blockAt(block.position));
    targetAfter=bot.blockAt(block.position)?.name;
    if(!bot.interrupt_code)await bot.pathfinder.goto(new goals.GoalNear(block.position.x,block.position.y,block.position.z,1));
    for(let n=0;n<30&&!bot.interrupt_code&&amount()<=before;n++)await new Promise(r=>setTimeout(r,100));
  } finally {bot.pathfinder.setMovements(old);}
  const gained=amount()-before;
  return {verified:targetAfter==='air'&&gained>=1,status:'tree_inventory_checked',item:block.name,gained,
    position:point(block.position),target_after:targetAfter,tree_evidence:{trunk_height:height,matching_leaves:leaves,ground:bot.blockAt(block.position.offset(0,-1,0))?.name},
    scope:'one_trunk_block_no_navigation_modification'};
}
