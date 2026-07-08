(function () {
  const statusEl = document.getElementById("pet-status");
  const needsEl = document.getElementById("pet-needs");
  const bubbleEl = document.getElementById("pet-bubble");
  const traceEl = document.getElementById("pet-trace");
  const feedButton = document.getElementById("pet-feed");
  const touchButton = document.getElementById("pet-touch");
  const ablationButton = document.getElementById("pet-ablation");

  function api() {
    return window.egoDesktop && window.egoDesktop.petMode ? window.egoDesktop.petMode : null;
  }

  function renderMeter(label, value) {
    const clamped = Math.max(0, Math.min(1, Number(value) || 0));
    return [
      `<div class="pet-meter">`,
      `<span>${label}</span>`,
      `<span style="--value:${Math.round(clamped * 100)}%"></span>`,
      `<span>${Math.round(clamped * 100)}%</span>`,
      `</div>`,
    ].join("");
  }

  function renderFrame(frame) {
    if (!frame) {
      return;
    }
    const world = frame.pet_world_v0 || {};
    const needs = world.needs || {};
    statusEl.textContent = `python kernel frame: tick ${world.tick_index ?? frame.step_id}`;
    needsEl.innerHTML = [
      renderMeter("energy", needs.energy),
      renderMeter("comfort", needs.comfort),
    ].join("");
    bubbleEl.textContent = frame.user_facing_bubble ? frame.user_facing_bubble.text : "no user-facing bubble emitted";
    traceEl.textContent = JSON.stringify({
      state_hash: frame.state_hash,
      kernel_adoption_v0: frame.kernel_adoption_v0,
      bubble_suppression: frame.bubble_suppression,
    }, null, 2);
  }

  async function tick(count = 1) {
    const pet = api();
    if (!pet) {
      statusEl.textContent = "pet bridge unavailable";
      return;
    }
    const result = await pet.tick({ count });
    renderFrame(result.latest_frame);
  }

  async function sendInput(eventType, payload) {
    const pet = api();
    if (!pet) {
      statusEl.textContent = "pet bridge unavailable";
      return;
    }
    const result = await pet.sendInput({
      event_type: eventType,
      tick_index: 0,
      payload,
    });
    renderFrame(result.frame);
  }

  async function boot() {
    const pet = api();
    if (!pet) {
      statusEl.textContent = "pet mode is disabled unless EgoDesktop is launched with --ego-pet-mode";
      return;
    }
    const unsubscribe = pet.onStateFrame ? pet.onStateFrame(renderFrame) : null;
    if (unsubscribe) {
      window.addEventListener("beforeunload", unsubscribe, { once: true });
    }
    renderFrame(await pet.getSnapshot());
    window.setInterval(() => tick(1).catch((error) => {
      statusEl.textContent = `pet tick unavailable: ${error.message}`;
    }), 1500);
  }

  feedButton.addEventListener("click", () => sendInput("feed", { portion: "small" }).catch((error) => {
    statusEl.textContent = error.message;
  }));
  touchButton.addEventListener("click", () => sendInput("pet", { intensity: "gentle" }).catch((error) => {
    statusEl.textContent = error.message;
  }));
  ablationButton.addEventListener("click", () => {
    const nextEnabled = ablationButton.dataset.enabled !== "true";
    ablationButton.dataset.enabled = nextEnabled ? "true" : "false";
    sendInput("ablation_toggle", { ablation_enabled: nextEnabled }).catch((error) => {
      statusEl.textContent = error.message;
    });
  });

  boot().catch((error) => {
    statusEl.textContent = `pet boot unavailable: ${error.message}`;
  });
}());
