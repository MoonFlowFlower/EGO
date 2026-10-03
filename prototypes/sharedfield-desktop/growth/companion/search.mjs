// A completed observation can be negative without being an execution failure.
export function searchBlocks(bot, mc, world, requested, range) {
  const names=requested==='wood'?mc.WOOD_TYPES.map(type=>`${type}_log`):[requested];
  if(names.some(name=>mc.getBlockId(name)===null))
    return {verified:false,status:'unknown_block',observation_complete:false};
  const block=world.getNearestBlocks(bot,names,range,1)[0]||null;
  const center=bot.entity.position;
  return {verified:!!block,status:block?'block_located':'block_not_found',
    observation_complete:true,found:!!block,
    query:{requested,block_types:names,range,scope:'loaded_chunks_only',center:{x:center.x,y:center.y,z:center.z}},
    matched_block:block?.name||null,block_position:block?.position||null,
    distance:block?center.distanceTo(block.position):null};
}
