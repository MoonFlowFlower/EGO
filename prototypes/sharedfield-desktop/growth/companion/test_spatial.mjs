import assert from 'node:assert/strict';
import {placeAt,placeMany,verifyBlocks,inspectArea,validPosition} from './spatial.mjs';
class V {
  constructor(x,y,z){Object.assign(this,{x,y,z});}
  floored(){return new V(Math.floor(this.x),Math.floor(this.y),Math.floor(this.z));}
  offset(x,y,z){return new V(this.x+x,this.y+y,this.z+z);}
  distanceTo(p){return Math.hypot(this.x-p.x,this.y-p.y,this.z-p.z);}
}
const key=p=>[p.x,p.y,p.z].join(','),p=(x,y=64,z=0)=>({x,y,z});
const target=(x,y=64,z=0)=>({block:'oak_planks',position:p(x,y,z)});
const mc={getBlockId:n=>n==='oak_planks'?1:null};
const skills={placeBlock(){throw Error('unsafe_official_placement_must_not_run');}};
function fixture(stock=8){
  const blocks=new Map(),old={original:true},moves=[];
  const bot={entity:{position:new V(0,64,0)},stock,calls:0,
    inventory:{items:()=>bot.stock?[{name:'oak_planks',count:bot.stock}]:[]},
    blockAt:pos=>({name:blocks.get(key(pos))??(pos.y<64?'stone':'air'),position:new V(pos.x,pos.y,pos.z),
      boundingBox:(blocks.get(key(pos))??(pos.y<64?'stone':'air'))==='air'?'empty':'block'}),
    equip:async()=>{},lookAt:async()=>{},
    placeBlock:async(ref,face)=>{bot.calls++;bot.stock--;blocks.set(key(ref.position.offset(face.x,face.y,face.z)),'oak_planks');},
    pathfinder:{movements:old,setMovements(v){this.movements=v;},async goto(g){moves.push({goal:g,movement:this.movements});
      bot.entity.position=g.inner?new V(g.inner.x-3,64,g.inner.z):new V(g.x-2,64,g.z);}}
  };
  class Movements{}
  class GoalNear{constructor(x,y,z,r){Object.assign(this,{x,y,z,r});}}
  class GoalInvert{constructor(inner){this.inner=inner;}}
  return {bot,blocks,old,moves,nav:{Movements,goals:{GoalNear,GoalInvert}}};
}
let checks=0;const check=x=>{assert.ok(x);checks++;};
let f=fixture();
check((await placeAt(f.bot,mc,skills,'oak_planks',p(2))).verified);
check(verifyBlocks(f.bot,[target(2)]).verified);
check((await placeAt(f.bot,mc,skills,'oak_planks',p(2))).status==='placement_target_not_empty');
check(f.bot.calls===1&&f.bot.stock===7);
check((await placeAt(f.bot,mc,skills,'oak_planks',p(20))).status==='target_out_of_reach');
check(!validPosition(p(1.1))&&!validPosition(p(true)));
check(inspectArea(f.bot,1).cells.length===81);
check((await placeAt(f.bot,mc,skills,'air',p(3))).status==='unknown_block_or_position');
check((await placeAt(f.bot,mc,skills,'oak_planks',p(3,66))).status==='placement_no_support');
f.blocks.set(key(p(2,66)),'stone');
check((await placeAt(f.bot,mc,skills,'oak_planks',p(3,66))).verified);
f=fixture(0);
check((await placeAt(f.bot,mc,skills,'oak_planks',p(2))).status==='placement_material_missing'&&f.bot.calls===0);
f=fixture();
check((await placeAt(f.bot,mc,skills,'oak_planks',p(0))).status==='placement_body_occupies_target');
check((await placeAt(f.bot,mc,skills,'oak_planks',p(0),f.nav)).verified);
check(f.moves.length===1&&f.bot.pathfinder.movements===f.old);
check(f.moves.every(m=>m.movement.canDig===false&&m.movement.allow1by1towers===false&&m.movement.canOpenDoors===false&&m.movement.scafoldingBlocks.length===0));
f=fixture();
check((await placeAt(f.bot,mc,skills,'oak_planks',p(8),f.nav)).verified&&f.moves.length===1);
f=fixture();f.bot.pathfinder.goto=async()=>{throw new Error('no_path');};
check((await placeAt(f.bot,mc,skills,'oak_planks',p(8),f.nav)).status==='placement_path_failed'&&f.bot.calls===0&&f.bot.pathfinder.movements===f.old);
f=fixture();f.bot.equip=async()=>f.blocks.set(key(p(2)),'stone');
check((await placeAt(f.bot,mc,skills,'oak_planks',p(2))).status==='placement_target_not_empty'&&f.bot.calls===0);
f=fixture();f.blocks.set(key(p(3)),'stone');
let result=await placeMany(f.bot,mc,skills,[target(2),target(3),target(4)]);
check(!result.verified&&result.status==='placement_batch_partial'&&result.placements.length===2);
check(result.placements[0].receipt.placement.consumed===1&&f.bot.calls===1&&!f.blocks.has(key(p(4))));
f=fixture();f.blocks.set(key(p(2)),'oak_planks');
result=await placeMany(f.bot,mc,skills,[target(2),target(3)]);
check(result.verified&&result.placements[0].receipt.status==='target_already_matches'&&f.bot.calls===1&&f.bot.stock===7);
f=fixture();const original=f.bot.placeBlock;f.bot.placeBlock=async(...args)=>{await original(...args);f.bot.interrupt_code=true;};
const partial=[];
result=await placeMany(f.bot,mc,skills,[target(2),target(3)],null,value=>partial.push(value));
check(!result.verified&&result.status==='interrupted'&&result.placements.length===1&&f.bot.calls===1);
check(partial.length===1&&partial[0].receipt.verified&&partial[0].receipt.placement.consumed===1);
f=fixture();f.bot.blockAt=()=>null;
check(!verifyBlocks(f.bot,[{block:'air',position:p(2)}]).verified);
check((await placeAt(f.bot,mc,skills,'oak_planks',p(2))).status==='target_not_loaded');
console.log(JSON.stringify({spatial_assertions:checks,passed:true}));
