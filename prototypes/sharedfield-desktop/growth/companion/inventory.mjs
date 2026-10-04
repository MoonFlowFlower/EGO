// Fixed inventory recovery. Never clicks result slots or drops cursor items.
const totals = win => {
  const items = [...win.slots.slice(1,win.inventoryStart===9?5:10),
    ...win.slots.slice(win.inventoryStart,win.inventoryEnd),win.selectedItem];
  const result={};
  for(const item of items)if(item)result[item.name]=(result[item.name]||0)+item.count;
  return Object.fromEntries(Object.entries(result).sort());
};
const gridEnd = win=>win.inventoryStart===9?5:10;
const emptyGrid = win=>!win.selectedItem&&!win.slots.slice(1,gridEnd(win)).some(Boolean);
export async function syncInventory(bot) {
  if(typeof bot._syncWindow!=='function')throw new Error('inventory_sync_unavailable');
  await bot._syncWindow(bot.currentWindow||bot.inventory);
}
export async function recoverInventory(bot) {
  const win=bot.currentWindow||bot.inventory;
  if(win!==bot.inventory&&!win.type.startsWith('minecraft:crafting'))return {verified:false,status:'unsupported_container'};
  const stale=JSON.stringify(totals(win));
  await syncInventory(bot);
  const before=totals(win), synchronized=stale!==JSON.stringify(before);
  const inputs=win.slots.slice(1,gridEnd(win)).filter(Boolean).length;
  const empty=[];
  for(let i=win.inventoryStart;i<win.inventoryEnd;i++)if(!win.slots[i])empty.push(i);
  if(empty.length<inputs+(win.selectedItem?1:0))return {verified:false,status:'inventory_no_empty_slot',moved_stacks:0};
  let moved=0;
  const check=()=>{if(bot.interrupt_code)throw new Error('inventory_recovery_cancelled');};
  async function putCursor() {
    if(!win.selectedItem)return;
    check();
    const slot=empty.shift();
    if(slot===undefined||win.slots[slot])throw new Error('inventory_empty_slot_changed');
    await bot.clickWindow(slot,0,0);
    await syncInventory(bot);
    if(win.selectedItem)throw new Error('inventory_cursor_not_cleared');
    moved++;
  }
  await putCursor();
  for(let slot=1;slot<gridEnd(win);slot++) {
    if(!win.slots[slot])continue;
    check();await bot.clickWindow(slot,0,0);await syncInventory(bot);await putCursor();
  }
  const clear=emptyGrid(win);
  if(clear&&bot.currentWindow) {check();await bot.closeWindow(bot.currentWindow);await syncInventory(bot);}
  const after=totals(bot.currentWindow||bot.inventory);
  const conserved=JSON.stringify(before)===JSON.stringify(after);
  return {verified:clear&&conserved&&!bot.currentWindow,
    status:clear&&conserved?'inventory_recovered':'inventory_recovery_incomplete',
    synchronized,moved_stacks:moved,conserved,contents_before:before,contents_after:after};
}
export async function craftChecked(bot, mc, skills, item, count) {
  await syncInventory(bot);
  const win=bot.currentWindow||bot.inventory;
  if(bot.currentWindow||!emptyGrid(win))return {verified:false,status:'crafting_grid_or_cursor_not_clear',recovery:'recover_inventory'};
  if(mc.getItemId(item)===null)return {verified:false,status:'unknown_item'};
  const available={};
  for(const stack of bot.inventory.items())if(stack)available[stack.name]=(available[stack.name]||0)+stack.count;
  const recipes=mc.getItemCraftingRecipes(item)||[];
  const missing=recipe=>Object.fromEntries(Object.entries(recipe[0]).map(([name,n])=>[name,Math.max(0,n*count-(available[name]||0))]).filter(([,n])=>n>0));
  const recipe=recipes.find(r=>Object.keys(missing(r)).length===0);
  if(!recipe) {
    const alternatives=[];
    if(item.endsWith('_planks'))for(const wood of mc.WOOD_TYPES||[]) {
      const output=wood+'_planks';
      if((mc.getItemCraftingRecipes(output)||[]).some(r=>Object.keys(missing(r)).length===0))alternatives.push(output);
    }
    return {verified:false,executed:false,status:recipes.length?'missing_ingredients':'unknown_recipe',item,count,
      missing_options:recipes.map(missing),available_plank_alternatives:alternatives};
  }
  const amount=()=>bot.inventory.items().reduce((n,v)=>n+(v?.name===item?v.count:0),0);
  const before=amount();
  let error=null;
  try {await skills.craftRecipe(bot,item,count);}catch(e){error=e.name;}
  await syncInventory(bot);
  const gained=amount()-before;
  return {verified:!!recipe&&gained>=count*recipe[1].craftedCount,
    status:'craft_inventory_checked',gained,item,error_type:error,
    recovery:!emptyGrid(bot.inventory)||bot.currentWindow?'recover_inventory':null};
}
