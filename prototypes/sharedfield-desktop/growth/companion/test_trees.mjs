import assert from 'node:assert/strict';
import {treeCandidate,collectTree,approachOwner,approachBlock} from './trees.mjs';
class Pos {constructor(x,y,z){Object.assign(this,{x,y,z});}offset(x,y,z){return new Pos(this.x+x,this.y+y,this.z+z);}distanceTo(p){return Math.hypot(this.x-p.x,this.y-p.y,this.z-p.z);}}
const origin=new Pos(0,64,0),cells=new Map();
const key=p=>`${p.x},${p.y},${p.z}`;
const put=(p,name)=>cells.set(key(p),{name,position:p});
const bot={entity:{position:origin},findBlocks:()=>[origin],blockAt:p=>cells.get(key(p))||{name:'air',position:p}};
const mc={WOOD_TYPES:['oak'],getBlockId:()=>1};
put(origin,'oak_log');
assert.equal(treeCandidate(bot,mc,64),null); // no ground or crown
put(origin.offset(0,-1,0),'grass_block');
put(origin.offset(0,1,0),'oak_log');put(origin.offset(0,2,0),'oak_log');
assert.equal(treeCandidate(bot,mc,64),null); // a log pillar is insufficient
for(const [x,z] of [[1,0],[-1,0],[0,1],[0,-1],[1,1]])put(origin.offset(x,3,z),'oak_leaves');
assert.equal(treeCandidate(bot,mc,64).height,3);
assert.equal(treeCandidate(bot,mc,64).leaves,5);
const slots=Array(46).fill(null);let count=0,digs=0;
bot.inventory={slots,emptySlotCount:()=>30,items:()=>count?[{name:'oak_log',count}]:[]};
const old={id:'old'};
bot.pathfinder={movements:old,setMovements(v){this.movements=v;},async goto(){
  assert.equal(this.movements.canDig,false);assert.deepEqual(this.movements.scafoldingBlocks,[]);
  assert.equal(this.movements.allow1by1towers,false);assert.equal(this.movements.canOpenDoors,false);
}};
bot.dig=async b=>{digs++;assert.equal(key(b.position),key(origin));put(b.position,'air');count++;};
class Movements {}
const goals={GoalLookAtBlock:class{},GoalNear:class{}};
const r=await collectTree(bot,mc,Movements,goals,64);
assert.equal(r.verified,true);assert.equal(r.gained,1);assert.equal(digs,1);assert.equal(bot.pathfinder.movements,old);
assert.equal((await collectTree(bot,mc,Movements,goals,64)).status,'natural_tree_not_found');
bot.inventory.selectedItem={name:'oak_planks',count:1};
assert.equal((await collectTree(bot,mc,Movements,goals,64)).status,'crafting_grid_or_cursor_not_clear');
bot.players={Moonlight:{entity:{position:origin.offset(1,0,0)}}};
assert.equal((await approachOwner(bot,Movements,goals)).verified,true);
assert.equal(bot.pathfinder.movements,old);
assert.equal((await approachBlock(bot,Movements,goals,origin.offset(2,0,0))).verified,true);
assert.equal((await approachBlock(bot,Movements,goals,origin.offset(20,0,0))).verified,false);
bot.pathfinder.goto=async()=>{throw new Error('no_path');};
await assert.rejects(()=>approachBlock(bot,Movements,goals,origin),/no_path/);
assert.equal(bot.pathfinder.movements,old);assert.equal(digs,1);
console.log('tree preparation checks passed: reject bare pillars, require crown/ground, one log, no navigation modification, inventory guard');
