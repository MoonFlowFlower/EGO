// Offline diagnostic only: no server, model, or bot connection is created.
// Compare the installed official inventory reporter with recipe eligibility.
const assert = require('node:assert/strict');
const path = require('node:path');
const { createRequire } = require('node:module');
const { pathToFileURL } = require('node:url');
const { EventEmitter } = require('node:events');

async function main() {
  assert.ok(process.argv[2], 'pass the installed official Mindcraft directory');
  const root = path.resolve(process.argv[2]);
  const requireOfficial = createRequire(path.join(root, 'package.json'));
  const data = requireOfficial('minecraft-data')('1.21.1');
  const Item = requireOfficial('prismarine-item')(data);
  const windows = requireOfficial('prismarine-windows')('1.21.1');
  const injectCraft = requireOfficial('mineflayer/lib/plugins/craft');
  const { getInventoryCounts } = await import(pathToFileURL(path.join(root, 'src/agent/library/world.js')));

  function inspect(slot) {
    const bot = new EventEmitter();
    bot.registry = data;
    bot.inventory = windows.createWindow(0, 'minecraft:inventory', 'Offline fixture');
    injectCraft(bot);
    bot.inventory.updateSlot(slot, new Item(data.itemsByName.oak_log.id, 12));
    return {
      slot,
      reported_logs: getInventoryCounts(bot).oak_log ?? 0,
      usable_inventory_logs: bot.inventory.count(data.itemsByName.oak_log.id, null),
      eligible_plank_recipes: bot.recipesFor(data.itemsByName.oak_planks.id, null, 1, null).length,
    };
  }

  const inventory = inspect(9);
  const craftingGrid = inspect(1);
  assert.equal(inventory.reported_logs, 12);
  assert.equal(inventory.usable_inventory_logs, 12);
  assert.ok(inventory.eligible_plank_recipes > 0);
  assert.equal(craftingGrid.reported_logs, 12);
  assert.equal(craftingGrid.usable_inventory_logs, 0);
  assert.equal(craftingGrid.eligible_plank_recipes, 0);
  console.log(JSON.stringify({
    kind: 'offline_inventory_scope_mismatch_reproduced',
    version: '1.21.1', inventory, crafting_grid: craftingGrid,
    live_slot_distribution_verified: false,
    runtime_source_changed: false,
  }));
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
