// Run with the installed official Mindcraft checkout as the sole argument.
const assert=require('node:assert/strict');
const {createRequire}=require('node:module');
const path=require('node:path');
const req=createRequire(path.join(path.resolve(process.argv[2]),'package.json'));
const mc=req('minecraft-protocol');
// One actual wire-format recipe: name, serializer id 22, category 3.
const name=Buffer.from('minecraft:decorated_pot');
const fixture=Buffer.concat([Buffer.from([1,name.length]),name,Buffer.from([22,3])]);
const before=mc.createDeserializer({state:'play',isServer:false,version:'1.21.1'});
assert.throws(()=>before.proto.readCtx.packet_declare_recipes(fixture,0));
require('./protocol_1211.cjs')(req);
// Compiled parsing is cached. Reload the isolated serializer module so this
// test can compare before and after in one process. Live repair precedes import.
const serializerPath=req.resolve('minecraft-protocol/src/transforms/serializer');
delete req.cache[serializerPath];
const after=req(serializerPath).createDeserializer({state:'play',isServer:false,version:'1.21.1'});
const decoded=after.proto.readCtx.packet_declare_recipes(fixture,0);
assert.equal(decoded.size,fixture.length);
assert.equal(decoded.value.recipes[0].type,'minecraft:crafting_decorated_pot');
assert.equal(decoded.value.recipes[0].data.category,3);
console.log('1.21.1 real recipe id regression PASS');
