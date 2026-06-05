# EgoDesktop Developer Settings / Launch Profile v0 Acceptance

## Required Behavior

- Developer settings load defaults when no local file exists.
- Settings save to Electron `userData/developer-settings.json` and reload.
- Explicit CLI args override saved settings.
- Smoke mode ignores persisted settings.
- Unknown, executable, authority, credential, and runtime fields are rejected.
- The main viewer has a `设置` button.
- The settings window has a developer mode toggle.
- Advanced options are hidden until developer mode is enabled.
- Restart-required fields are labeled `重启后生效`.
- Live-safe fields are limited to developer mode, debug overlay default visibility, and TTS enabled state.

## Exposed Settings

- `model_path`
- `pspc_proposal_hint_file`
- `pspc_reply_preview_mode`
- `pspc_recording_mode`
- `tts_enabled`
- `tts_max_chars`
- `tts_base_voice`
- `tts_model_name`
- `tts_timeout_ms`
- `chat_timeout_ms`
- `debug_overlay_default_visible`
- `developer_mode_enabled`

## Forbidden

- No `--smoke`, `--out`, smoke text, test artifact path, credentials, provider keys, memory/gate/runtime authority, transport, proactive, action, tool, or scheduler settings.
- No EgoOperator runtime/gate/memory/approval/transport/proactive modification.
- No PSPC adapter creation or mainline enablement.

## Done Criteria

- Targeted Developer Settings tests pass.
- EgoDesktop full `npm test` passes.
- Existing Python desktop bridge regression tests pass.
- Report exists under `artifacts/egodesktop_developer_settings_launch_profile_v0/`.
- Repo-wide claim ceiling remains unchanged.

## What This Proves

It proves local EgoDesktop launch/profile ergonomics only.

## What This Does Not Prove

It does not prove PSPC integration, durable memory, runtime integration safety, stable user benefit, live autonomy, consciousness, subjective experience, or real emotion.
