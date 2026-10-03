// AIRI's public route.delivery + instance destination schema. Never use bypass.
export function stageTarget(modules) {
  return modules.find(m=>m.name==='proj-airi:stage-tamagotchi'&&typeof m.identity?.id==='string')?.identity.id||null;
}
export function displayRoute(target) {
  if(typeof target!=='string'||!target)throw new Error('stage_target_required');
  return {delivery:{mode:'broadcast'},destinations:[{type:'instance',instances:[target]}]};
}
