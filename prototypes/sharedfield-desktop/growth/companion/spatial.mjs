// Local observations and explicit coordinates; no generated building code.
export const validPosition=p=>p&&Object.keys(p).sort().join()==='x,y,z'&&Object.values(p).every(Number.isInteger)
  &&Math.abs(p.x)<=29999984&&Math.abs(p.z)<=29999984&&p.y>=-64&&p.y<=319;
export function inspectArea(bot,radius) {
  const center=bot.entity.position.floored(),cells=[];
  for(let dx=-radius;dx<=radius;dx++)for(let dz=-radius;dz<=radius;dz++)for(let dy=-1;dy<=2;dy++) {
    const p=center.offset(dx,dy,dz),b=bot.blockAt(p);
    cells.push([p.x,p.y,p.z,b?.name??null]);
  }
  return {verified:true,status:'local_area_observed',scope:'loaded_chunks_only',cells,center};
}
export function verifyBlocks(bot,targets) {
  const blocks=targets.map(t=>{
    const p=bot.entity.position.floored();p.x=t.position.x;p.y=t.position.y;p.z=t.position.z;
    const block=bot.blockAt(p);
    return {...t,observed_block:block?.name??null,matches:block?.name===t.block};
  });
  return {verified:blocks.length>0&&blocks.every(b=>b.matches),status:'goal_blocks_checked',blocks};
}
export async function placeAt(bot,mc,_skills,block,position,navigation=null) {
  if(!validPosition(position)||block==='air'||mc.getBlockId(block)===null)return {verified:false,status:'unknown_block_or_position'};
  const pos=bot.entity.position.floored();Object.assign(pos,position);
  if(bot.entity.position.distanceTo(pos)>16)return {verified:false,status:'target_out_of_reach'};
  const beforeBlock=bot.blockAt(pos)?.name;
  if(beforeBlock==null)return {verified:false,status:'target_not_loaded'};
  if(beforeBlock!=='air')return {verified:false,status:'placement_target_not_empty',position};
  const count=()=>bot.inventory.items().reduce((n,i)=>n+(i?.name===block?i.count:0),0);
  const before=count();
  if(before<1)return {verified:false,status:'placement_material_missing'};
  const old=bot.pathfinder?.movements;
  try {
    const move=async goal=>{
      const movement=new navigation.Movements(bot);
      movement.canDig=false;movement.allow1by1towers=false;movement.scafoldingBlocks=[];movement.canOpenDoors=false;
      bot.pathfinder.setMovements(movement);await bot.pathfinder.goto(goal);
    };
    const overlaps=()=>[bot.entity.position,bot.entity.position.offset(0,1,0)].some(p=>p.distanceTo(pos)<1.1);
    if(overlaps()) {
      if(!navigation)return {verified:false,status:'placement_body_occupies_target',position};
      await move(new navigation.goals.GoalInvert(new navigation.goals.GoalNear(pos.x,pos.y,pos.z,2)));
    }
    if(bot.entity.position.distanceTo(pos)>4.5) {
      if(!navigation)return {verified:false,status:'target_out_of_reach',position};
      await move(new navigation.goals.GoalNear(pos.x,pos.y,pos.z,3.5));
    }
    if(bot.interrupt_code)return {verified:false,status:'interrupted',position};
    let reference,face;
    for(const [x,y,z] of [[0,-1,0],[0,1,0],[0,0,-1],[0,0,1],[1,0,0],[-1,0,0]]) {
      const neighbor=bot.blockAt(pos.offset(x,y,z));
      if(neighbor?.boundingBox==='block') {
        reference=neighbor;face=new pos.constructor(-x,-y,-z);break;
      }
    }
    if(!reference)return {verified:false,status:'placement_no_support',position};
    const item=bot.inventory.items().find(i=>i?.name===block);
    if(!item)return {verified:false,status:'placement_material_missing',position};
    await bot.equip(item,'hand');await bot.lookAt(reference.position.offset(.5,.5,.5));
    if(bot.interrupt_code)return {verified:false,status:'interrupted',position};
    if(bot.blockAt(pos)?.name!=='air')return {verified:false,status:'placement_target_not_empty',position};
    try {await bot.placeBlock(reference,face)} catch { /* Actual world/inventory readback decides effect. */ }
    for(let i=0;i<10&&(bot.blockAt(pos)?.name!==block||before-count()!==1)&&!bot.interrupt_code;i++)
      await new Promise(resolve=>setTimeout(resolve,100));
  } catch(error) {
    return {verified:false,status:'placement_path_failed',position,error_type:error.name};
  } finally {
    if(navigation&&old)bot.pathfinder.setMovements(old);
  }
  const after=count(),afterBlock=bot.blockAt(pos)?.name;
  return {verified:afterBlock===block&&before-after===1,status:'placed_block_checked',position,
    placement:{before_block:beforeBlock,after_block:afterBlock??null,inventory_before:before,inventory_after:after,consumed:before-after}};
}

export async function placeMany(bot,mc,skills,targets,navigation=null,onPlacement=()=>{}) {
  const placements=[];
  for(const target of targets) {
    if(bot.interrupt_code)return {verified:false,status:'interrupted',placements};
    const p=bot.entity.position.floored();Object.assign(p,target.position);
    const receipt=bot.blockAt(p)?.name===target.block?
      {verified:true,status:'target_already_matches',position:target.position}:
      await placeAt(bot,mc,skills,target.block,target.position,navigation);
    placements.push({target,receipt});
    onPlacement({target,receipt});
    if(!receipt.verified)return {verified:false,status:'placement_batch_partial',problem:receipt.status,placements};
  }
  return {verified:true,status:'placement_batch_checked',placements};
}
