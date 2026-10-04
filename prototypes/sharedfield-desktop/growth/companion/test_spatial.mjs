import assert from 'node:assert/strict';
import {placeAt,verifyBlocks,inspectArea,validPosition} from './spatial.mjs';
class V {constructor(x,y,z){Object.assign(this,{x,y,z});} floored(){return new V(Math.floor(this.x),Math.floor(this.y),Math.floor(this.z));} offset(x,y,z){return new V(this.x+x,this.y+y,this.z+z);} distanceTo(p){return Math.hypot(this.x-p.x,this.y-p.y,this.z-p.z);}}
const blocks=new Map();let stock=2,calls=0;
const b={entity:{position:new V(0,64,0)},inventory:{items:()=>[{name:'oak_planks',count:stock}]},blockAt:p=>({name:blocks.get(JSON.stringify(p))||'air'})};
const mc={getBlockId:()=>1};const skills={placeBlock:async(_b,name,x,y,z,face,noCheat)=>{assert.equal(noCheat,true);calls++;stock--;blocks.set(JSON.stringify(new V(x,y,z)),name);}};
let checks=0;const check=x=>{assert.ok(x);checks++;};
const position={x:1,y:64,z:0};
check((await placeAt(b,mc,skills,'oak_planks',position)).verified);
check(verifyBlocks(b,[{block:'oak_planks',position}]).verified);
check(!(await placeAt(b,mc,skills,'oak_planks',position)).verified);check(calls===1);
check((await placeAt(b,mc,skills,'oak_planks',{x:20,y:64,z:0})).status==='target_out_of_reach');check(calls===1);
check(!validPosition({x:1.1,y:64,z:0}));check(inspectArea(b,1).cells.length===36);
blocks.clear();check(!verifyBlocks(b,[{block:'oak_planks',position}]).verified);
console.log(JSON.stringify({spatial_assertions:checks,passed:true}));
