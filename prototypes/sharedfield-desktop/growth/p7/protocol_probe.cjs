// Bounded transport diagnostic. No model, chat, game actions or secret input.
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
Error.stackTraceLimit=100;
const root = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
const req = createRequire(path.join(root, 'package.json'));
const proto = req('minecraft-protocol');
const {FullPacketParser} = req('protodef');
fs.mkdirSync(out, {recursive:true});
if (process.argv.includes('--capture')) {
  const original = FullPacketParser.prototype.parsePacketBuffer;
  FullPacketParser.prototype.parsePacketBuffer = function(buffer) {
    try { return original.call(this, buffer); }
    catch (error) {
      fs.writeFileSync(path.join(out,'failed-packet.bin'),buffer);
      fs.writeFileSync(path.join(out,'failed-packet-error.txt'),error.stack);
      console.log(JSON.stringify({capture:true,bytes:buffer.length,message:error.message}));
      setTimeout(()=>client.end('bounded diagnostic complete'),50);
      throw error;
    }
  };
  const client = proto.createClient({host:'127.0.0.1',port:25565,version:'1.21.1',username:'EgoP7',auth:'offline'});
  const timeout = setTimeout(()=>client.end('10 second diagnostic limit'),10000);
  client.on('error',e=>console.log(JSON.stringify({error:e.message})));
  client.on('end',()=>{clearTimeout(timeout);process.exit(0)});
} else {
  if(process.argv.includes('--repair')) {
    require('./protocol_1211.cjs')(req);
  }
  const parser = proto.createDeserializer({state:'play',isServer:false,version:'1.21.1'});
  const buffer = fs.readFileSync(path.join(out,'failed-packet.bin'));
  try {
    const packet=parser.parsePacketBuffer(buffer);
    if(packet.metadata.size!==buffer.length)throw new Error('incomplete_packet_consumption');
    console.log(JSON.stringify({packet:packet.data.name,bytes:buffer.length,consumed:packet.metadata.size,complete:buffer.length===packet.metadata.size,recipes:packet.data.params.recipes?.length}));
  } catch(e) {console.error(e.stack);process.exitCode=1;}
}
