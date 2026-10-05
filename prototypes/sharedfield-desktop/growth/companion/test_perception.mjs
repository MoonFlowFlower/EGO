import assert from 'node:assert/strict';
import {inspectArea,validAreaArgs} from './spatial.mjs';
class V {
  constructor(x,y,z){Object.assign(this,{x,y,z});}
  floored(){return new V(Math.floor(this.x),Math.floor(this.y),Math.floor(this.z));}
  offset(x,y,z){return new V(this.x+x,this.y+y,this.z+z);}
  distanceTo(p){return Math.hypot(this.x-p.x,this.y-p.y,this.z-p.z);}
}
// A constructed counterexample matching the recorded heights, not a live-world replay.
const bot={entity:{position:new V(12.505,111,-57.450)},blockAt(p){
  if(p.x===8)return null;
  if(p.x===12&&p.y===110&&p.z===-58)return {name:'oak_planks'};
  if(p.x===14&&p.z===-60)return {name:'air'}; // an actual hole stays a hole
  const top=p.z < -58?107:108;
  return {name:p.y===top?'grass_block':p.y<top?'dirt':'air'};
}};
const get=(r,x,y,z)=>r.cells.find(c=>c[0]===x&&c[1]===y&&c[2]===z)?.[3];
const old=inspectArea(bot,4,{below:1,above:2}),r=inspectArea(bot,4);
assert.equal(get(old,12,108,-58),undefined);
assert.equal(get(old,12,110,-58),'oak_planks');
assert.equal(get(r,12,108,-58),'grass_block');
assert.equal(get(r,12,107,-59),'grass_block');
assert.equal(get(r,8,108,-58),null);
assert.equal(get(r,14,108,-60),'air');
assert.equal(get(r,12,106,-58),undefined);
assert.equal(r.coverage.complete,false);
assert.equal(r.coverage.unknown,81);
assert.deepEqual(r.coverage.bounds,{min:{x:8,y:107,z:-62},max:{x:16,y:115,z:-54}});
const shifted=inspectArea(bot,1,{center:{x:10,y:109,z:-58},below:8,above:0});
assert.equal(shifted.query.center_source,'explicit');
assert.deepEqual(shifted.center,new V(10,109,-58));
assert.equal(get(shifted,10,108,-58),'grass_block');
assert.equal(inspectArea(bot,1,{center:{x:100,y:109,z:-58}}).status,'observation_center_out_of_reach');
assert.equal(inspectArea(bot,1,{below:17}).status,'invalid_observation_bounds');
for(const args of [{radius:1,below:true},{radius:1,above:-1},{radius:1,center:{x:1.5,y:100,z:0}},
  {radius:1,below:4,command:'move'},{radius:5}])assert.ok(!validAreaArgs(args));
bot.entity.position=new V(-.1,-63.5,-.1);
const negative=inspectArea(bot,1);
assert.deepEqual(negative.center,new V(-1,-64,-1));
assert.equal(negative.coverage.bounds.min.y,-64);
assert.ok(negative.cells.every(c=>c[1]>=-64));
console.log(JSON.stringify({passed:true,cases:['raised_body','slope','unknown','hole','explicit_center','bounds','negative_coordinates']}));
if(process.argv.includes('--fixture'))console.log(JSON.stringify(r));
