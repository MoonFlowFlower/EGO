import assert from 'node:assert/strict';
import {recoverInventory,craftChecked} from './inventory.mjs';
let checks=0;
const check=(value)=>{assert.ok(value);checks++;};
function fake() {
  const inventory={slots:Array(46).fill(null),inventoryStart:9,inventoryEnd:45,selectedItem:null,
    items(){return this.slots.slice(9,45).filter(Boolean)}};
  return {inventory,currentWindow:null,interrupt_code:false,clicks:[],
    async _syncWindow(){},async clickWindow(slot,button,mode){
      assert.ok(slot>=1&&slot<45);assert.equal(button,0);assert.equal(mode,0);
      this.clicks.push(slot);const old=inventory.slots[slot];inventory.slots[slot]=inventory.selectedItem;inventory.selectedItem=old;
    }};
}
const item=(name,count)=>({name,count});
{
  const b=fake();const r=await recoverInventory(b);check(r.verified);check(r.moved_stacks===0);check(r.conserved);
}
{
  const b=fake();b.inventory.selectedItem=item('oak_planks',4);b.inventory.slots[1]=item('oak_log',1);
  b.inventory.slots[0]=item('oak_planks',4); // virtual output must never be taken or counted
  const r=await recoverInventory(b);check(r.verified);check(r.moved_stacks===2);check(r.conserved);
  check(!b.inventory.selectedItem);check(b.inventory.slots[1]===null);check(!b.clicks.includes(0));
  check(r.contents_after.oak_planks===4&&r.contents_after.oak_log===1);
}
{
  const b=fake();for(let i=9;i<45;i++)b.inventory.slots[i]=item('stone',64);
  b.inventory.selectedItem=item('oak_log',1);
  const r=await recoverInventory(b);check(!r.verified);check(r.status==='inventory_no_empty_slot');check(b.clicks.length===0);
}
{
  const b=fake();b.inventory.selectedItem=item('oak_log',1);b.interrupt_code=true;
  await assert.rejects(()=>recoverInventory(b),/cancelled/);checks++;check(b.clicks.length===0);
}
{
  const b=fake();b.inventory.selectedItem=item('oak_planks',4);
  b._syncWindow=async()=>{b.inventory.selectedItem=null;b.inventory.slots[9]=item('oak_log',3);};
  const r=await recoverInventory(b);check(r.verified);check(r.synchronized);check(r.moved_stacks===0);
}
{
  const b=fake();b.inventory.slots[1]=item('oak_log',1);
  const r=await craftChecked(b,{}, {},'oak_planks',1);check(r.status==='crafting_grid_or_cursor_not_clear');check(b.clicks.length===0);
}
{
  const b=fake();b.inventory.slots[9]=item('acacia_log',1);let crafts=0;
  const mc={getItemId:()=>1,WOOD_TYPES:['oak','acacia'],getItemCraftingRecipes:name=>name.endsWith('_planks')?[[{[name.replace('_planks','_log')]:1},{craftedCount:4}]]:null};
  const skills={async craftRecipe(bot,name){crafts++;bot.inventory.slots[9]=item(name,4);}};
  const absent=await craftChecked(b,mc,skills,'oak_planks',1);
  check(absent.status==='missing_ingredients');check(!absent.executed);check(crafts===0);
  check(absent.missing_options[0].oak_log===1);check(JSON.stringify(absent.available_plank_alternatives)==='["acacia_planks"]');
  const tooMany=await craftChecked(b,mc,skills,'acacia_planks',2);check(tooMany.status==='missing_ingredients');check(crafts===0);
  const actual=await craftChecked(b,mc,skills,'acacia_planks',1);check(actual.verified);check(actual.gained===4);check(crafts===1);
}
console.log(JSON.stringify({inventory_assertions:checks,passed:true}));
