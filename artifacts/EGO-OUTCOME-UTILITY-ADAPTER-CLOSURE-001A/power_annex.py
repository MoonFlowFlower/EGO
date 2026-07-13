#!/usr/bin/env python3
"""Power annex generator for EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.

Closed-form two-sample power analysis for a hypothetical randomized
epsilon-abstain (no_action) arm vs action arm in the Ego runtime, computed
over a transparent assumption grid.

IMPORTANT PROPERTIES
- No RNG, no measured data input. Every number is an ANALYTIC BOUND over
  DECLARED assumptions, not a measurement (do not present as measured cost).
- Deterministic: fixed grid order, sorted JSON keys, no timestamps inside
  artifacts. Double-run must produce byte-identical power_annex.json.

MODEL
- Outcome scores bounded in [0,1]; standardized effect d = delta / sigma.
  Worst-case sigma = 0.5, so d = 0.3 corresponds to a raw score gap of
  ~0.15 on [0,1].
- Two-sample z approximation, two-sided alpha = 0.05, power = 0.80:
      need 1/n1 + 1/n2 <= d^2 / K,   K = (z_{1-alpha/2} + z_{power})^2
- With D eligible decision points/day, abstain rate eps, horizon T days:
      n_abstain = eps*D*T,  n_action = (1-eps)*D*T
      => T >= K / (d^2 * eps*(1-eps) * D)          [pooled comparison]
- Context-stratified estimate (k strata, equal traffic splits): T_strat ~= k * T.
  Stratification can expose context-dependent effects, but the current
  candidate and an equal-access count_table control both encode context/action
  cells. Reaching power therefore does not distinguish them by itself.
- Multiple-comparison correction intentionally omitted: correction only
  increases T, so the closure direction (infeasible) is conservative; any
  reopen card must redo the calculation with its own declared correction.

Usage:
  python power_annex.py <output_dir>
Writes: <output_dir>/power_annex.json, <output_dir>/power_annex.md
Prints: sha256 of power_annex.json (for the double-run identity check).
"""

import hashlib
import itertools
import json
import os
import sys

Z_ALPHA = 1.959964  # z_{0.975}
Z_POWER = 0.841621  # z_{0.80}
K = (Z_ALPHA + Z_POWER) ** 2  # ~7.84888

D_GRID = [10, 30, 100, 300]        # eligible decision points/day (assumed)
EPS_GRID = [0.05, 0.10, 0.20]      # randomized abstain rate (assumed tolerable)
EFFECT_GRID = [0.2, 0.3, 0.5]      # standardized effect size d
STRATA_GRID = [1, 5]               # 1 = pooled; 5 = context-dependent proxy
DRIFT_WINDOW_DAYS = 60.0           # declared stationarity budget (frozen assumption)

# Reopen contour reference cell: context-dependent claim, moderate effect.
REOPEN_K = 5
REOPEN_D = 0.3


def days_to_power(D, eps, d, k):
    return k * K / (d * d * eps * (1.0 - eps) * D)


def build():
    with open(__file__, "rb") as source_file:
        code_path_hash = hashlib.sha256(source_file.read()).hexdigest()
    rows = []
    for D, eps, d, k in itertools.product(D_GRID, EPS_GRID, EFFECT_GRID, STRATA_GRID):
        t = days_to_power(D, eps, d, k)
        rows.append({
            "decisions_per_day": D,
            "epsilon": eps,
            "effect_d": d,
            "strata_k": k,
            "days_to_power": round(t, 1),
            "feasible_within_drift_window": bool(t <= DRIFT_WINDOW_DAYS),
        })

    # Reopen contour: eps*(1-eps)*D >= REOPEN_K * K / (REOPEN_D^2 * W)
    contour = REOPEN_K * K / (REOPEN_D ** 2 * DRIFT_WINDOW_DAYS)
    spot_checks = {
        # hand-verified reference values (see closure card G2)
        "pooled_D30_eps0.10_d0.3_k1_days": round(days_to_power(30, 0.10, 0.3, 1), 1),
        "strat_D30_eps0.10_d0.3_k5_days": round(days_to_power(30, 0.10, 0.3, 5), 1),
        "pooled_D30_eps0.10_d0.5_k1_days": round(days_to_power(30, 0.10, 0.5, 1), 1),
        "reopen_contour_eps_1meps_D": round(contour, 2),
        "reopen_min_D_at_eps0.10": int(-(-contour // 0.09)),  # ceil(contour/0.09)
        "K": round(K, 5),
    }
    expected = {
        "pooled_D30_eps0.10_d0.3_k1_days": 32.3,
        "strat_D30_eps0.10_d0.3_k5_days": 161.5,
        "pooled_D30_eps0.10_d0.5_k1_days": 11.6,
        "reopen_contour_eps_1meps_D": 7.27,
        "reopen_min_D_at_eps0.10": 81,
        "K": 7.84888,
    }
    for key, want in expected.items():
        got = spot_checks[key]
        assert abs(float(got) - float(want)) < 0.06, (key, got, want)

    annex = {
        "task_id": "EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A",
        "artifact": "power_annex",
        "kind": "analytic_bound_over_declared_assumptions_not_measurement",
        "provenance": {
            "producer_function": "power_annex.build",
            "input_artifacts": [{
                "path": "artifacts/EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A/power_annex.py",
                "sha256": code_path_hash,
            }],
            "run_id": "ego-outcome-utility-adapter-closure-001a-power-v1",
            "seed_context_episode_ids": {
                "seed_ids": "NOT_APPLICABLE_ANALYTIC_NO_RNG",
                "context_ids": "NOT_APPLICABLE_ASSUMPTION_GRID",
                "episode_ids": "NOT_APPLICABLE_NO_EPISODES",
            },
            "aggregation_rule": (
                "one deterministic row per Cartesian product of D_GRID, EPS_GRID, "
                "EFFECT_GRID and STRATA_GRID; no empirical aggregation"
            ),
            "code_path_hash": code_path_hash,
        },
        "model": {
            "alpha_two_sided": 0.05,
            "power": 0.80,
            "K": round(K, 5),
            "formula_days_pooled": "K / (d^2 * eps*(1-eps) * D)",
            "formula_days_stratified": "k * K / (d^2 * eps*(1-eps) * D)",
            "sigma_assumption": "worst-case 0.5 on [0,1] scores; d=0.3 ~ raw gap 0.15",
            "multiple_comparison_correction": "omitted; only increases days_to_power (conservative for closure)",
        },
        "assumptions": {
            "drift_window_days": DRIFT_WINDOW_DAYS,
            "grids": {
                "decisions_per_day": D_GRID,
                "epsilon": EPS_GRID,
                "effect_d": EFFECT_GRID,
                "strata_k": STRATA_GRID,
            },
        },
        "rows": rows,
        "reopen_contour": {
            "criterion": (
                "context-stratified (k=%d) effect d=%.1f reachable within the "
                "frozen drift window (%.0f days)" % (REOPEN_K, REOPEN_D, DRIFT_WINDOW_DAYS)
            ),
            "condition": "eps*(1-eps)*D >= %.2f" % round(contour, 2),
            "example": "at eps=0.10 requires D >= %d eligible decisions/day" % int(-(-contour // 0.09)),
        },
        "key_reading": [
            "Pooled comparisons can reach power in ~1 month at D>=30, eps=0.10, d>=0.3, "
            "but the pooled average effect is exactly what a static per-action table encodes: "
            "the power-feasible regime funds the static rival, not the learner.",
            "Context-stratified effects can fund the current context/action count table and "
            "an equal-access count_table control alike; reaching the contour would not by "
            "itself distinguish the candidate from that control.",
        ],
        "spot_checks": spot_checks,
    }
    return annex


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    annex = build()

    json_path = os.path.join(out_dir, "power_annex.json")
    with open(json_path, "w", newline="\n") as f:
        json.dump(annex, f, indent=2, sort_keys=True)
        f.write("\n")

    md_lines = [
        "# Power annex — EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A",
        "",
        "Analytic bounds over declared assumptions (NOT measurements).",
        "",
        "| D/day | eps | d | k | days to power | within %.0f-day window |" % DRIFT_WINDOW_DAYS,
        "|---|---|---|---|---|---|",
    ]
    for r in annex["rows"]:
        md_lines.append(
            "| %d | %.2f | %.1f | %d | %.1f | %s |"
            % (
                r["decisions_per_day"], r["epsilon"], r["effect_d"], r["strata_k"],
                r["days_to_power"], "yes" if r["feasible_within_drift_window"] else "no",
            )
        )
    md_lines += [
        "",
        "Reopen contour: %s (%s)." % (
            annex["reopen_contour"]["condition"], annex["reopen_contour"]["example"]),
        "",
        "Key reading:",
    ]
    for item in annex["key_reading"]:
        md_lines.append("- " + item)
    md_lines.append("")
    with open(os.path.join(out_dir, "power_annex.md"), "w", newline="\n") as f:
        f.write("\n".join(md_lines))

    with open(json_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print("power_annex.json sha256 = " + digest)


if __name__ == "__main__":
    main()
