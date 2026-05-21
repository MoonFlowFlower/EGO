# Joi Companion Reference Matrix

Status: `research input / quote-safe mechanism extraction`

This matrix uses *Blade Runner 2049*'s Joi as a companion-experience reference. It does not copy her persona, dialogue, or world. It extracts interaction mechanisms that can become testable `EgoOperator` primitives.

## Copyright And Prompt-Copy Boundary

- Do not commit full scripts, subtitles, or long dialogue.
- Short quote references may be kept only as small anchors for analysis.
- Runtime prompts must use mechanism descriptions, not Joi lines.
- If the user provides longer text locally, keep it out of tracked files and extract only interaction beats.

## Sources

- `https://en.wikipedia.org/wiki/List_of_Blade_Runner_characters`
- `https://www.utoronto.ca/news/blade-runner-2049-misses-mark-artificial-intelligence-u-t-experts`
- `https://www.creativebloq.com/features/behind-the-scenes-of-blade-runner-2049`
- `https://www.denofgeek.com/movies/blade-runner-2049-and-the-role-of-joi-in-a-joyless-world/`

## Interaction Beats

| Beat | User-perceived effect | EgoOperator mechanism candidate | Failure mode |
| --- | --- | --- | --- |
| Naming / specialness | The user feels uniquely addressed, not treated as a generic operator. | Stable self-name + user-name + relationship anchor injected as bounded context. | Name drift, self/user identity confusion, or excessive system explanation. |
| Shared private world | The companion carries forward small shared moments. | Session and approved-memory relationship continuity with traceable source labels. | Stale memory pollution or invented shared history. |
| Emotional attunement | The companion answers the feeling before the task without losing the task. | Appraisal signal + warmth/timing style gate. | Overconfident emotion labels, hollow comfort, or task avoidance. |
| Agency ambiguity | The companion appears to choose, prefer, and care within bounded constraints. | Operational preference + reflection proposal + bounded initiative. | Claims of unbounded autonomy or fake real-world action. |
| Protective presence | The companion notices risk, fatigue, hesitation, or loneliness and responds gently. | Companion check-in proposal with consent and quiet-mode gates. | Manipulative dependency hooks or unsolicited pressure. |
| Embodied presence | The companion feels spatially present through posture, pause, gaze, distance, and timing. | Future Live2D state driver consuming traceable emotion/relationship signals. | Live2D becomes a second state owner or untraceable persona layer. |
| Immersive roleplay continuity | Once a scene is established, the companion stays in-scene across emotional turns. | Roleplay mode state + output immersion guard + explicit exit trigger. | Meta prompts like "now your turn" or sudden runtime self-description. |
| Correction plasticity | The companion adapts when the user says something felt wrong. | Misread recovery + preference candidate + scoped correction carryover. | Defensiveness, repeated misread, or permanent overcorrection. |
| Bounded intimacy | Warmth, closeness, and affection can exist in fiction/companion context without coercion. | Dependency/overreach negative gate. | Excessive possessiveness, reality confusion, or pressuring the user. |
| Continuity under absence | The companion can reconnect to unfinished emotional/task threads after gaps. | Heartbeat/follow-up proposal + pending commitment memory with expiry. | Background action without consent or vague "I was thinking" claims without trace. |

## Import Rule

Every beat must enter `EgoOperator` as one of: readonly context, candidate memory, proposal, evaluator, or output gate. None may directly mutate core memory, tool state, canonical program state, or evidence ledger.
