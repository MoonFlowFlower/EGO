# Status

- status: `in_progress`
- current_task: `EGODESKTOP-COMPANION-004`
- lane: `EgoDesktop local companion presentation`
- claim_ceiling: `local_desktop_companion_wording_and_route_repair_only`
- runtime_authority: `none`
- mainline_connected: `false for this local repair evidence`
- pspc_authority: `style/debug hint only`

## Task Sequence

1. `EGODESKTOP-COMPANION-001` companion wording and route repair package v0.
2. `EGODESKTOP-COMPANION-002` session-local recall wording repair v0.
3. `EGODESKTOP-COMPANION-003` timeout route misfire repair v0.
4. `EGODESKTOP-COMPANION-004` combined companion regression report v0.

## Current Notes

`EGODESKTOP-COMPANION-001` is accepted: the local task package and board lane exist.

`EGODESKTOP-COMPANION-002` is accepted: `scripts/ego_operator_desktop_turn.py` now applies a desktop-only visible reply rewrite when ordinary companion recall questions receive engineering memory-boundary text. The visible reply can cite same-window facts such as `椰果珍珠奶茶`, says the scope is `本次会话` / current window, and does not expose `candidate-local`, `operator memory`, `PROJECT_MEMORY`, `evidence ledger`, or `memory approval` unless the user explicitly asks an engineering memory question. Tests: `python -m pytest -q tests\test_ego_operator_desktop_session_context.py tests\test_ego_operator_desktop_companion_wording.py` passed.

`EGODESKTOP-COMPANION-003` is accepted: `EgoDesktop/src/desktopRecoveryContext.js` now uses route-neutral timeout fallback wording (`本地后端回复超时`) and classifies ordinary affectionate turns such as `喜欢你所以就摸摸你`, `像小猫一样`, and `摸摸头` as `general_chat`. Only explicit story/roleplay/adult-writing requests enter `creative` or `adult_creative`. Tests: `node --test EgoDesktop\tests\desktop_recovery_context.test.js` and `python -m pytest -q tests\test_ego_operator_desktop_recovery_context.py` passed.

Current task is `EGODESKTOP-COMPANION-004`: generate the combined regression report and go/no-go verdict for manual companion smoke.
