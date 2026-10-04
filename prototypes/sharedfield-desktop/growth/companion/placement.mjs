// Fixed official placement skill with evidence of an actual world change.
export async function placeNextBlock(bot, mc, world, skills, block) {
  if(mc.getBlockId(block)===null)return {verified:false,status:'unknown_block'};
  const count=()=>bot.inventory.items().reduce((n,item)=>n+(item?.name===block?item.count:0),0);
  const inventoryBefore=count();
  if(inventoryBefore<1)return {verified:false,status:'placement_material_missing'};
  const pos=world.getNearestFreeSpace(bot,1,4);
  if(!pos)return {verified:false,status:'no_placement_space'};
  const beforeBlock=bot.blockAt(pos)?.name;
  // The official skill can break an occupied target; this adapter must not.
  if(beforeBlock!=='air')return {verified:false,status:'placement_target_not_empty',position:pos};
  await skills.placeBlock(bot,block,pos.x,pos.y,pos.z,'bottom',true);
  const afterBlock=bot.blockAt(pos)?.name, inventoryAfter=count();
  const placement={before_block:beforeBlock,after_block:afterBlock??null,
    inventory_before:inventoryBefore,inventory_after:inventoryAfter,consumed:inventoryBefore-inventoryAfter};
  return {verified:afterBlock===block&&placement.consumed===1,
    status:'placed_block_checked',position:pos,placement};
}
