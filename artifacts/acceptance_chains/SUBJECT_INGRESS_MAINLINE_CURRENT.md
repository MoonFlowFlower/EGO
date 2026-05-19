# Acceptance Chain 0 - Subject Ingress Mainline

- status: `conditional_pass`
- evidence_level: `live_telegram_audit + task_status`
- verification_level: `repo_current`

## Summary

当前 live Telegram 路径中，大量 turn 仍在宿主 pre-runtime / policy interception 层结束；可以证明一部分真实聊天已进入主体，但还不能证明 live 聊天已稳定表现出 downstream tendency change。

## What It Proves

- authorized turn ingress is auditable through current real Telegram artifacts
- host_only and host_degraded_fallback are explicitly separated in the current audit workflow
- current host-only breakdown = {'control_plane_expected': 211, 'policy_driven_host_interception': 228, 'unexpected_subject_miss': 77}

## What It Does Not Prove

- background/proactive closure is fully complete
- all live user-visible paths are already green unless the fresh audit explicitly says so
- other acceptance chains may claim full live experience without subject ingress admission

## Sources

- artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.json
- docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md

## Details

- `host_only_breakdown`: {'control_plane_expected': 211, 'policy_driven_host_interception': 228, 'unexpected_subject_miss': 77}
- `ordinary_chat_breakdown`: {'policy_driven_host_interception': 228, 'unexpected_subject_miss': 58, 'control_plane_expected': 1}
- `pending_background_proactive_closure`: True

## Next Step

If this chain is still conditional, close background/proactive subject ingress before raising live-experience claims.
