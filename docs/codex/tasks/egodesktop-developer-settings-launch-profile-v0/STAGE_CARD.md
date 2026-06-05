# EgoDesktop Developer Settings / Launch Profile v0 Stage Card

## Problem Reframe

EgoDesktop has accumulated local demo and preview flags that are painful to retype as command-line options. Moving every CLI option into the UI would create a second launcher and make smoke/test modes unsafe. This stage creates a bounded local developer settings profile instead.

## One Hypothesis

If EgoDesktop loads a small saved launch profile from Electron `userData`, while keeping explicit CLI arguments as the highest-priority override and ignoring persisted settings in smoke mode, local development becomes easier without changing EgoOperator runtime authority.

## Change Surface

- EgoDesktop local settings module, Electron main process IPC, preload bridge, settings window, and viewer toolbar button
- targeted EgoDesktop Node tests
- `docs/codex/tasks/egodesktop-developer-settings-launch-profile-v0/`
- `artifacts/egodesktop_developer_settings_launch_profile_v0/`
- scoped state/ledger/generated-view updates required for closeout

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Saved settings are local desktop launch/UI preferences only.
- Explicit CLI args override saved settings.
- Smoke mode ignores real saved settings.

## Boundaries

- claim ceiling: `local_desktop_developer_settings_only`
- runtime authority: `none`
- persistence: Electron `userData/developer-settings.json`
- mainline connected: `false`
- PSPC remains preview/shadow only

## Forbidden

- Do not modify EgoOperator runtime, gate, memory, approval, transport, proactive behavior, or human-trial harness.
- Do not expose credentials, provider keys, memory/gate/runtime authority, `--smoke`, `--out`, test output paths, or smoke text.
- Do not let saved settings override explicit CLI args.
- Do not let persisted user settings affect smoke runs.
- Do not hot-restart model, TTS worker, server, or runtime modules.

## Three-Level Verify

1. Settings module tests prove defaults, save/load, validation, CLI override, smoke isolation, and live-safe field handling.
2. UI/source tests prove settings button, developer mode, restart labels, and IPC wiring exist.
3. EgoDesktop regression tests prove existing PSPC, session context, recovery, TTS, and viewer behavior still pass.

## Rollback

Delete the settings module, settings window assets, IPC/preload/toolbar changes, tests, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

This proves EgoDesktop can persist a bounded local developer launch profile and expose a settings window without runtime authority.

## What This Does Not Prove

It does not prove PSPC mainline integration, true learning, durable memory, EgoOperator runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
