import assert from 'node:assert/strict';
import {stageTarget,displayRoute} from './bridge_protocol.mjs';
assert.equal(stageTarget([{name:'unrelated',identity:{id:'x'}}]),null);
assert.equal(stageTarget([{name:'proj-airi:stage-tamagotchi',identity:{id:'one'}},{name:'proj-airi:stage-tamagotchi',identity:{id:'two'}}]),'one');
assert.deepEqual(displayRoute('one'),{delivery:{mode:'broadcast'},destinations:[{type:'instance',instances:['one']}]});
assert.throws(()=>displayRoute(null));
console.log('4 bridge routing checks passed; one native destination, no bypass');
