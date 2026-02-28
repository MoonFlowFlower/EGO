---
name: openemotion-emotiond
description: "OpenEmotion emotiond integration - emotional intelligence for OpenClaw responses"
metadata:
  clawdbot:
    emoji: "💭"
version: 1.2.0
---

# OpenEmotion Emotiond Skill

Use emotional intelligence in your responses. The **emotiond-bridge** hook automatically provides decision guidance.

## Quick Start

The hook writes to `<workspace>/emotiond/context.json`:

```json
{
  "target_id": "telegram:8420019401",
  "decision": {
    "action": "approach",
    "explanation": { ... }
  },
  "guidance": {
    "tone": "warm, open, friendly",
    "intent": "engage warmly",
    "phrases": ["glad to hear", "I appreciate"]
  }
}
```

## How to Use

Before responding, read the context:

```bash
cat ~/.openclaw/workspace/emotiond/context.json
```

Then match your response to the guidance:
- **tone**: Style of your response
- **intent**: What you're trying to achieve
- **phrases**: Suggested phrases to use naturally

## Action Reference

| Action | Tone | When |
|--------|------|------|
| `approach` | Warm, open | Bond/trust high, safe to engage |
| `withdraw` | Brief, neutral | Low energy, self-protect |
| `boundary` | Clear, firm | Limits being tested |
| `repair_offer` | Gentle, healing | Trust low, repair possible |
| `observe` | Curious, neutral | Uncertain, need more info |
| `attack` | Defensive, sharp | Active threat |

## Example Responses

**approach** guidance:
> "Glad to hear from you! I appreciate you sharing that..."

**withdraw** guidance:
> "I understand. Noted."

**repair_offer** guidance:
> "I value our connection. Let me try to make this right..."

## Workflow

```
User message → Hook fires → Decision fetched → Context written → Agent reads → Response matches action
```

## Files

- Hook: `~/.openclaw/hooks/emotiond-bridge/handler.js`
- Context: `~/.openclaw/workspace/emotiond/context.json`
- emotiond: `http://127.0.0.1:18080`

## Fallback

If context missing/stale:
- Default to `observe` action
- Use curious, neutral tone
- Do not block user interaction
