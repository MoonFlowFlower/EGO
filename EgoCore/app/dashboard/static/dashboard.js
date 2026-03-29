const view = document.body.dataset.view;
const sampleId = document.body.dataset.sampleId;
const metaBar = document.getElementById("meta-bar");
const app = document.getElementById("app");
const POLL_MS = 5000;
const VIEW_ROUTES = {
  runs: "/runs",
  agency: "/agency",
  growth: "/growth",
  failures: "/failures",
};

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${Math.round(Number(value) * 100)}%`;
}

function formatFloat(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return Number(value).toFixed(digits);
}

function formatFreshness(seconds) {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "n/a";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
}

function renderMeta(buildMeta, gapSummary) {
  const items = [
    ["Total Runs", buildMeta.total_runs],
    ["Complete E4 Bundles", buildMeta.complete_runs],
    ["OE Available", buildMeta.oe_available_runs],
    ["Host-only", buildMeta.host_only_runs],
    ["Agency Records", buildMeta.agency_records ?? 0],
    ["Failure Cases", buildMeta.failure_cases],
  ];
  metaBar.innerHTML = items
    .map(
      ([label, value]) => `
        <article class="stat-card">
          <strong>${escapeHtml(value ?? 0)}</strong>
          <span>${escapeHtml(label)}</span>
        </article>
      `,
    )
    .join("");
  if (gapSummary?.continuity_status) {
    metaBar.innerHTML += Object.entries(gapSummary.continuity_status)
      .map(
        ([label, value]) => `
          <article class="stat-card">
            <strong>${escapeHtml(value)}</strong>
            <span>continuity:${escapeHtml(label)}</span>
          </article>
        `,
      )
      .join("");
  }
}

function gapTag(type) {
  if (type.includes("missing") || type.includes("gap")) return "warning";
  if (type.includes("mismatch")) return "danger";
  return "ok";
}

function actionList(actions) {
  if (!actions?.length) return "none";
  return actions.join(", ");
}

function renderRuns(records, continuity) {
  if (!records.length) {
    app.innerHTML = `<section class="panel"><div class="empty">当前没有 runs 索引。</div></section>`;
    return;
  }
  const continuityMap = new Map(continuity.map((item) => [item.scenario, item.status]));
  app.innerHTML = `
    <section class="panel">
      <h2>Live Runs</h2>
      <p>实时样本流，按只读派生索引展示 bundle 完整度、continuity 命中和关键 gap。</p>
      <div class="pill-row">
        ${[...continuityMap.entries()]
          .map(([scenario, status]) => `<span class="pill ${status === "missing" ? "warning" : "ok"}">${escapeHtml(`continuity:${scenario}=${status}`)}</span>`)
          .join("")}
      </div>
    </section>
    <section class="row-list">
      ${records
        .map(
          (record) => `
            <a class="row-link" href="/samples/${encodeURIComponent(record.sample_id)}">
              <strong>${escapeHtml(record.sample_id)}</strong>
              <span class="muted">${escapeHtml(record.timestamp)}</span>
              <div class="tag-list">
                <span class="tag ${record.bundle_complete ? "ok" : "warning"}">${record.bundle_complete ? "complete_bundle" : "partial_bundle"}</span>
                <span class="tag ${record.oe_available ? "ok" : "warning"}">${record.oe_available ? "oe_available" : "oe_unavailable"}</span>
                ${record.host_only ? `<span class="tag warning">host_only</span>` : ""}
                ${record.repair_closure ? `<span class="tag ok">repair_closure</span>` : ""}
                ${(record.continuity_tags || []).map((tag) => `<span class="tag ok">${escapeHtml(tag)}</span>`).join("")}
                ${(record.gap_types || []).map((tag) => `<span class="tag ${gapTag(tag)}">${escapeHtml(tag)}</span>`).join("")}
              </div>
            </a>
          `,
        )
        .join("")}
    </section>
  `;
}

function renderGrowth(records, summary) {
  if (!records.length) {
    app.innerHTML = `<section class="panel"><div class="empty">当前没有可用的 OE growth records。</div></section>`;
    return;
  }
  app.innerHTML = `
    <section class="panel">
      <h2>Growth Signals</h2>
      <p>只展示可审计的 OpenEmotion 结构化信号，不做“意识程度”解释。</p>
      <div class="pill-row">
        <span class="pill ok">records=${escapeHtml(summary.total_records)}</span>
        <span class="pill ${summary.reflection_trigger_count ? "ok" : "warning"}">reflection_triggers=${escapeHtml(summary.reflection_trigger_count)}</span>
        <span class="pill ${summary.repair_closure_count ? "ok" : "warning"}">repair_closure=${escapeHtml(summary.repair_closure_count)}</span>
      </div>
    </section>
    <section class="detail-grid">
      ${records
        .map(
          (record) => `
            <article>
              <h3>${escapeHtml(record.sample_id)}</h3>
              <p class="muted">${escapeHtml(record.timestamp)}</p>
              <pre>${escapeHtml(
                JSON.stringify(
                  {
                    memory_update: record.memory_update_summary,
                    appraisal_state_delta: record.appraisal_delta_summary,
                    reflection: record.reflection_summary,
                    response_tendency: record.response_tendency_summary,
                    cycle: record.cycle_summary,
                  },
                  null,
                  2,
                ),
              )}</pre>
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function renderFailures(records, gapSummary) {
  app.innerHTML = `
    <section class="panel">
      <h2>Failures & Replay</h2>
      <p>真实 failure cases 与 bundle gap 分开显示，避免把缺项误记成失败。</p>
      <pre>${escapeHtml(JSON.stringify(gapSummary, null, 2))}</pre>
    </section>
    <section class="row-list">
      ${records.length
        ? records
            .map(
              (record) => `
                <article class="row-link">
                  <strong>${escapeHtml(record.failure_id)}</strong>
                  <span class="muted">${escapeHtml(record.timestamp)}</span>
                  <div class="tag-list">
                    <span class="tag ${record.severity === "high" ? "danger" : record.severity === "medium" ? "warning" : "ok"}">${escapeHtml(record.cause_type)}</span>
                    ${record.in_regression ? `<span class="tag ok">in_regression</span>` : `<span class="tag warning">not_in_regression</span>`}
                    ${record.retested_after_fix ? `<span class="tag ok">retested</span>` : ""}
                  </div>
                  <pre>${escapeHtml(
                    JSON.stringify(
                      {
                        expected: record.expected,
                        actual: record.actual,
                        artifact_ref: record.artifact_ref,
                      },
                      null,
                      2,
                    ),
                  )}</pre>
                </article>
              `,
            )
            .join("")
        : `<div class="empty">当前没有 failure_cases 索引。</div>`}
    </section>
  `;
}

function renderSample(detail) {
  const artifactBlocks = Object.entries(detail.artifacts || {})
    .map(
      ([name, value]) => `
        <article>
          <h3>${escapeHtml(name)}</h3>
          <pre>${escapeHtml(typeof value === "string" ? value : JSON.stringify(value, null, 2))}</pre>
        </article>
      `,
    )
    .join("");
  const runRecord = detail.run_record || {};
  app.innerHTML = `
    <section class="panel">
      <h2>Sample Detail</h2>
      <p>原样回指 artifact，不在页面层做主体语义再解释。</p>
      <div class="tag-list">
        ${Object.entries(runRecord)
          .filter(([key]) => ["bundle_complete", "oe_available", "host_only", "repair_closure"].includes(key))
          .map(([key, value]) => `<span class="tag ${value ? "ok" : "warning"}">${escapeHtml(`${key}=${value}`)}</span>`)
          .join("")}
        ${(runRecord.gap_types || []).map((tag) => `<span class="tag ${gapTag(tag)}">${escapeHtml(tag)}</span>`).join("")}
      </div>
      <pre>${escapeHtml(JSON.stringify(runRecord, null, 2))}</pre>
    </section>
    <section class="detail-grid">${artifactBlocks}</section>
  `;
}

function metricCards(summary) {
  const items = [
    ["Turns", summary.turn_count],
    ["Candidate Rate", formatPercent(summary.candidate_generated_rate)],
    ["Writeback Rate", formatPercent(summary.exec_result_writeback_rate)],
    ["Trace Complete", formatPercent(summary.trace_completeness_rate)],
    ["Violations", summary.direct_execution_violations],
    ["Mean Urge", formatFloat(summary.mean_urge, 3)],
  ];
  return `
    <section class="metric-grid">
      ${items
        .map(
          ([label, value]) => `
            <article class="metric-card">
              <strong>${escapeHtml(value)}</strong>
              <span>${escapeHtml(label)}</span>
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function renderFunnel(funnel, totalTurns) {
  const steps = [
    ["idle eligible", funnel.idle_eligible_count],
    ["candidate generated", funnel.candidate_generated_count],
    ["governor approved", funnel.governor_approved_count],
    ["host action", funnel.host_action_count],
    ["writeback", funnel.writeback_count],
  ];
  return `
    <section class="panel">
      <h2>Agency Funnel</h2>
      <div class="funnel-grid">
        ${steps
          .map(
            ([label, count]) => `
              <article class="funnel-step">
                <div class="funnel-top">
                  <strong>${escapeHtml(count)}</strong>
                  <span>${escapeHtml(label)}</span>
                </div>
                <div class="mini-bar">
                  <span style="width:${Math.max(totalTurns ? (Number(count) / totalTurns) * 100 : 0, 4)}%"></span>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function buildTrendSvg(trends) {
  if (!trends.length) {
    return `<div class="empty">no trend data</div>`;
  }
  const width = 820;
  const height = 220;
  const padX = 28;
  const padY = 18;
  const scores = trends.map((item) => Number(item.urge_score || 0));
  const maxScore = Math.max(1, ...scores);
  const stepX = trends.length === 1 ? 0 : (width - padX * 2) / (trends.length - 1);
  const points = trends
    .map((item, index) => {
      const x = padX + stepX * index;
      const y = height - padY - ((Number(item.urge_score || 0) / maxScore) * (height - padY * 2));
      return { x, y, item };
    });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const candidateDots = points
    .filter((point) => point.item.candidate_generated)
    .map((point) => `<circle class="marker candidate" cx="${point.x}" cy="${point.y}" r="4"></circle>`)
    .join("");
  const writebackDots = points
    .filter((point) => point.item.writeback_applied)
    .map((point) => `<rect class="marker writeback" x="${point.x - 4}" y="${point.y - 4}" width="8" height="8" rx="2"></rect>`)
    .join("");

  return `
    <svg class="trend-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-label="urge trend">
      <line class="trend-axis" x1="${padX}" y1="${height - padY}" x2="${width - padX}" y2="${height - padY}"></line>
      <polyline class="trend-line" points="${polyline}"></polyline>
      ${candidateDots}
      ${writebackDots}
    </svg>
  `;
}

function renderDistribution(title, values) {
  const entries = Object.entries(values || {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    return `
      <article class="panel">
        <h3>${escapeHtml(title)}</h3>
        <div class="empty">no data</div>
      </article>
    `;
  }
  const maxValue = Math.max(...entries.map(([, value]) => Number(value)));
  return `
    <article class="panel">
      <h3>${escapeHtml(title)}</h3>
      <div class="distribution-list">
        ${entries
          .map(
            ([label, value]) => `
              <div class="distribution-row">
                <span class="distribution-label">${escapeHtml(label)}</span>
                <div class="distribution-bar">
                  <span style="width:${(Number(value) / maxValue) * 100}%"></span>
                </div>
                <strong>${escapeHtml(value)}</strong>
              </div>
            `,
          )
          .join("")}
      </div>
    </article>
  `;
}

function renderAgency(payload) {
  const summary = payload?.summary || {};
  const latest = payload?.latest_state;
  const trends = payload?.trends || [];
  const recentTurns = payload?.recent_turns || [];
  const distributions = payload?.distributions || {};
  const excludedCounts = payload?.excluded_counts || {};
  const hasData = Boolean(summary.turn_count);

  if (!hasData) {
    app.innerHTML = `
      <section class="panel">
        <h2>Agency</h2>
        <div class="empty">no seed_v0_2 agency evidence yet</div>
      </section>
    `;
    return;
  }

  app.innerHTML = `
    <section class="panel agency-status-panel">
      <div class="agency-status-header">
        <div>
          <h2>Agency</h2>
          <p>seed_v0_2 causal chain over read-only real artifacts.</p>
        </div>
        <div class="pill-row">
          <span class="pill ok">freshness=${escapeHtml(formatFreshness(payload.freshness_seconds))}</span>
          <span class="pill ok">profile=${escapeHtml((payload.profile_scope || []).join(", "))}</span>
          <span class="pill ${latest?.trace_completeness ? "ok" : "warning"}">trace=${escapeHtml(String(Boolean(latest?.trace_completeness)))}</span>
        </div>
      </div>
      <div class="agency-status-grid">
        <article class="metric-card">
          <strong>${escapeHtml(latest?.focus_goal || "n/a")}</strong>
          <span>current focus</span>
        </article>
        <article class="metric-card">
          <strong>${escapeHtml(actionList(latest?.candidate_actions))}</strong>
          <span>latest candidate</span>
        </article>
        <article class="metric-card">
          <strong>${escapeHtml(latest?.final_host_action || "none")}</strong>
          <span>latest final action</span>
        </article>
        <article class="metric-card">
          <strong>${escapeHtml(latest?.exec_result_type || "none")}</strong>
          <span>latest exec result</span>
        </article>
      </div>
    </section>

    ${metricCards(summary)}
    ${renderFunnel(payload.funnel || {}, summary.turn_count || 0)}

    <section class="panel">
      <h2>Urge / Candidate / Writeback</h2>
      <p class="muted">折线是 urge，圆点表示 candidate，方点表示 writeback。</p>
      ${buildTrendSvg(trends)}
    </section>

    <section class="distribution-grid">
      ${renderDistribution("Candidate Actions", distributions.candidate_actions)}
      ${renderDistribution("Governor Status", distributions.governor_status)}
      ${renderDistribution("Final Host Action", distributions.final_host_action)}
      ${renderDistribution("Suppression Reason", distributions.suppression_reason)}
    </section>

    <section class="panel">
      <h2>Recent Turns</h2>
      <div class="table-wrap">
        <table class="agency-table">
          <thead>
            <tr>
              <th>sample</th>
              <th>urge</th>
              <th>candidate</th>
              <th>governor</th>
              <th>final</th>
              <th>result</th>
              <th>focus</th>
            </tr>
          </thead>
          <tbody>
            ${recentTurns
              .map(
                (item) => `
                  <tr>
                    <td><a href="/samples/${encodeURIComponent(item.sample_id)}">${escapeHtml(item.sample_id)}</a></td>
                    <td>${escapeHtml(formatFloat(item.urge_score, 3))}</td>
                    <td>${escapeHtml(actionList(item.candidate_actions))}</td>
                    <td>${escapeHtml(item.governor_status || "unknown")}</td>
                    <td>${escapeHtml(item.final_host_action || "none")}</td>
                    <td>${escapeHtml(item.exec_result_type || "none")}</td>
                    <td>${escapeHtml(item.focus_goal || "n/a")}</td>
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
      <div class="pill-row top-gap">
        ${Object.entries(excludedCounts)
          .map(([label, value]) => `<span class="pill warning">${escapeHtml(`${label}=${value}`)}</span>`)
          .join("")}
      </div>
    </section>
  `;
}

async function refresh() {
  const health = await fetchJson("/api/dashboard/health");
  renderMeta(health.build_meta || {}, health.gap_summary || {});

  if (view === "growth") {
    const growth = await fetchJson("/api/dashboard/growth");
    renderGrowth(growth.records || [], growth.summary || {});
    return;
  }

  if (view === "failures") {
    const failures = await fetchJson("/api/dashboard/failures");
    renderFailures(failures.records || [], failures.gap_summary || {});
    return;
  }

  if (view === "agency") {
    const agency = await fetchJson("/api/dashboard/agency");
    renderAgency(agency);
    return;
  }

  if (view === "sample" && sampleId) {
    const detail = await fetchJson(`/api/dashboard/samples/${encodeURIComponent(sampleId)}`);
    renderSample(detail);
    return;
  }

  const runs = await fetchJson("/api/dashboard/runs");
  renderRuns(runs.records || [], runs.continuity || []);
}

async function start() {
  if (window.location.pathname === "/") {
    const preferredView = window.localStorage.getItem("dashboard:lastView");
    if (preferredView && VIEW_ROUTES[preferredView]) {
      window.location.replace(VIEW_ROUTES[preferredView]);
      return;
    }
  }
  if (view !== "sample" && VIEW_ROUTES[view]) {
    window.localStorage.setItem("dashboard:lastView", view);
  }
  try {
    await refresh();
    setInterval(refresh, POLL_MS);
  } catch (error) {
    app.innerHTML = `<section class="panel"><div class="empty">Dashboard load failed: ${escapeHtml(error.message)}</div></section>`;
  }
}

start();
