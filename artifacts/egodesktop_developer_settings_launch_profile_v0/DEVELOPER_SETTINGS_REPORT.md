# EgoDesktop Developer Settings / Launch Profile v0 Report

- status: `pass`
- claim_ceiling: `local_desktop_developer_settings_only`
- runtime_authority: `none`
- settings file: `Electron userData/developer-settings.json`
- merge order: `defaults < saved settings < CLI args`
- smoke ignores persisted settings: `true`

## Implemented Behavior

EgoDesktop now has a `设置` button that opens a local settings window. The window can save a bounded developer profile and hide advanced fields until developer mode is enabled.

Saved settings can provide defaults for model path, PSPC preview flags, PSPC proposal hint file, TTS options, chat timeout, and debug overlay default visibility. Explicit CLI args still override saved values.

## Live vs Restart

Live-safe fields:

- `developer_mode_enabled`
- `debug_overlay_default_visible`
- `tts_enabled`

Restart-required fields:

- `model_path`
- `pspc_proposal_hint_file`
- `pspc_reply_preview_mode`
- `pspc_recording_mode`
- `tts_max_chars`
- `tts_base_voice`
- `tts_model_name`
- `tts_timeout_ms`
- `chat_timeout_ms`

## Side Effects

- no EgoOperator runtime modification
- no memory write
- no gate invocation
- no approval invocation
- no transport call
- no proactive trigger
- no runtime registration
- no PSPC mainline connection

## Failure Meaning

If a saved option does not appear to take effect, first check whether an explicit CLI arg is overriding it. If a restart-required option changes while EgoDesktop is already running, the correct result is a restart-required notice, not a hot restart.

## Rollback

Delete `EgoDesktop/src/developerSettings.js`, the settings window assets, IPC/preload/toolbar changes, targeted tests, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

This proves local EgoDesktop developer launch/profile ergonomics only.

## What This Does Not Prove

It does not prove PSPC mainline integration, true learning, durable memory, runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
