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
export async function placeAt(bot,mc,skills,block,position) {
  if(!validPosition(position)||mc.getBlockId(block)===null)return {verified:false,status:'unknown_block_or_position'};
  const pos=bot.entity.position.floored();Object.assign(pos,position);
  if(bot.entity.position.distanceTo(pos)>16)return {verified:false,status:'target_out_of_reach'};
  const beforeBlock=bot.blockAt(pos)?.name;
  if(beforeBlock==null)return {verified:false,status:'target_not_loaded'};
  if(beforeBlock!=='air')return {verified:false,status:'placement_target_not_empty',position};
  const count=()=>bot.inventory.items().reduce((n,i)=>n+(i?.name===block?i.count:0),0);
  const before=count();
  if(before<1)return {verified:false,status:'placement_material_missing'};
  await skills.placeBlock(bot,block,pos.x,pos.y,pos.z,'bottom',true);
  const after=count(),afterBlock=bot.blockAt(pos)?.name;
  return {verified:afterBlock===block&&before-after===1,status:'placed_block_checked',position,
    placement:{before_block:beforeBlock,after_block:afterBlock??null,inventory_before:before,inventory_after:after,consumed:before-after}};
}
