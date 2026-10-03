// Transport compatibility only. Verified against Mojang 1.21.1 RecipeSerializer
// registration order and the entire captured declare_recipes packet.
module.exports = function repair1211(requireFromMindcraft) {
  const data = requireFromMindcraft('minecraft-data')('1.21.1').protocol;
  let found=0;
  function visit(value) {
    if (!value || typeof value!=='object') return;
    if(Array.isArray(value) && value[0]==='mapper' && value[1]?.mappings?.['11']==='minecraft:crafting_special_banneraddpattern') {
      const old=value[1].mappings;
      if(old['10']!=='minecraft:crafting_special_bannerduplicate' || old['23']!=='minecraft:crafting_decorated_pot') throw new Error('unexpected_recipe_mapping');
      value[1].mappings=Object.fromEntries(Object.entries(old).filter(([id])=>Number(id)!==11).map(([id,name])=>[String(Number(id)>11?Number(id)-1:Number(id)),name]));
      found++;
    }
    for(const child of Object.values(value))visit(child);
  }
  visit(data.play.toClient.types.packet_declare_recipes);
  if(found!==1)throw new Error('expected_one_1211_recipe_mapping');
};
