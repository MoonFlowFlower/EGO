function clamp01(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.max(0, Math.min(1, number));
}

function buildLive2dObserverFrame(frame) {
  const world = frame && frame.pet_world_v0 ? frame.pet_world_v0 : {};
  const needs = world.needs || {};
  const energy = clamp01(needs.energy);
  const comfort = clamp01(needs.comfort);
  return {
    schema_version: "ego_desktop.pet_live2d_observer_projection.v0",
    claim_ceiling: "renderer_observer_projection_only_not_evidence",
    evidence_authority: false,
    input_authority: false,
    source_state_hash: frame && frame.state_hash ? String(frame.state_hash) : "",
    tick_index: Number.isFinite(Number(world.tick_index)) ? Number(world.tick_index) : 0,
    live2d_params: {
      ParamEnergy: energy,
      ParamComfort: comfort,
      ParamPetBreath: 0.45 + comfort * 0.2,
      ParamPetMood: (energy + comfort) / 2,
    },
    bubble: frame && frame.user_facing_bubble ? { ...frame.user_facing_bubble } : null,
  };
}

module.exports = {
  buildLive2dObserverFrame,
};
