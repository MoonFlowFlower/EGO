# OpenEmotion ↔ OpenClaw Integration

This directory contains integration components for connecting OpenEmotion's emotiond daemon with OpenClaw.

## Quick Start

### 1. Start emotiond

```bash
cd /path/to/OpenEmotion
source .venv/bin/activate
python -m emotiond.api
# Running on http://127.0.0.1:18080
```

### 2. Configure OpenClaw

Add to `~/.openclaw/openclaw.json`:

```json
{
  "env": {
    "EMOTIOND_BASE_URL": "http://127.0.0.1:18080",
    "EMOTIOND_OPENCLAW_TOKEN": "your-secure-token-here"
  },
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "emotiond-bridge": { "enabled": true }
      }
    }
  }
}
```

### 3. Install Hook

```bash
# Option A: Symlink to workspace (recommended for development)
mkdir -p ~/.openclaw/workspace/hooks
ln -s /path/to/OpenEmotion/integrations/openclaw/hooks/emotiond-bridge \
      ~/.openclaw/workspace/hooks/emotiond-bridge

# Option B: Copy to managed hooks
cp -r /path/to/OpenEmotion/integrations/openclaw/hooks/emotiond-bridge \
      ~/.openclaw/hooks/emotiond-bridge
```

### 4. Enable Hook

```bash
openclaw hooks enable emotiond-bridge
openclaw hooks list  # Verify it shows ✓
```

### 5. Restart Gateway

```bash
openclaw gateway restart
```

### 6. Test

Send a message via your connected channel (Telegram, WhatsApp, etc.). Check:

```bash
# Context file should exist
cat ~/.openclaw/workspace/emotiond/context.json

# Gateway logs should show hook execution
tail -f ~/.openclaw/gateway.log | grep emotiond
```

## Components

### Skill: openemotion-emotiond

Location: `skills/openemotion-emotiond/SKILL.md`

Guides the agent to:
1. Classify user messages into event subtypes (care, apology, rejection, etc.)
2. Call `POST /event` to send events to emotiond
3. Call `GET /decision` to get action recommendations
4. Generate responses based on decision explanations

### Hook: emotiond-bridge

Location: `hooks/emotiond-bridge/`

Automatically:
1. Listens for `message:received` events
2. Extracts `conversationId` as `target_id`
3. Writes context to `emotiond/context.json`
4. Sends `time_passed` events when time delta > 10s

## Architecture

```
┌─────────────────┐     message:received     ┌────────────────────┐
│   OpenClaw      │ ──────────────────────▶  │  emotiond-bridge   │
│   Gateway       │                          │  (hook)            │
└─────────────────┘                          └─────────┬──────────┘
                                                       │
                                                       │ POST /event
                                                       │ (time_passed)
                                                       ▼
┌─────────────────┐     GET /decision        ┌────────────────────┐
│   Agent         │ ◀──────────────────────  │  emotiond          │
│  (with skill)   │     POST /event          │  (daemon)          │
└─────────────────┘ ───────────────────────▶ │                    │
                      (world_event)           └────────────────────┘
```

## Event Flow

### Per-Message Flow

1. **User sends message** → OpenClaw receives
2. **Hook fires** → `emotiond-bridge` extracts context, sends `time_passed`
3. **Agent processes** → Skill guides agent to:
   - Classify message subtype
   - Call `POST /event` with world_event
   - Call `GET /decision` for guidance
   - Generate response based on decision

### Target Isolation (MVP-3.1)

- `target_id` = `conversationId` (from hook context)
- Each conversation has independent learning residuals
- Changing conversations starts fresh (no cross-contamination)

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMOTIOND_BASE_URL` | Yes | `http://127.0.0.1:18080` | emotiond API endpoint |
| `EMOTIOND_OPENCLAW_TOKEN` | Yes | - | Bearer token for authenticated requests |
| `EMOTIOND_TIME_PASSED_MIN_DELTA` | No | `10` | Minimum seconds before sending time_passed |
| `EMOTIOND_TIME_PASSED_MAX_SECONDS` | No | `300` | Maximum seconds to report (clamped) |

### emotiond Tokens

Generate tokens for your deployment:

```bash
# Example: generate random token
openssl rand -hex 32
```

Configure in emotiond's environment:

```bash
export EMOTIOND_OPENCLAW_TOKEN="your-token-here"
```

The same token must be set in OpenClaw config.

## Verification Checklist

### Basic Integration

- [ ] emotiond running on configured port
- [ ] Hook enabled (`openclaw hooks list` shows ✓)
- [ ] Context file created after first message
- [ ] No errors in gateway logs

### Event Flow

- [ ] world_event sent for each user message
- [ ] time_passed sent when delay > 10s
- [ ] decision returned with explanation

### Target Isolation

- [ ] Same conversationId accumulates learning
- [ ] Different conversationId has independent residuals
- [ ] residuals don't cross-contaminate

## Troubleshooting

### Hook Not Executing

1. Check hook is enabled: `openclaw hooks list`
2. Check internal hooks enabled in config
3. Restart gateway: `openclaw gateway restart`
4. Check logs: `tail -f ~/.openclaw/gateway.log`

### emotiond Connection Errors

1. Verify emotiond is running: `curl http://127.0.0.1:18080/health`
2. Check `EMOTIOND_BASE_URL` matches
3. Verify token matches between emotiond and OpenClaw

### Context File Not Created

1. Check workspace directory exists
2. Check write permissions
3. Look for errors in hook logs

## Security Notes

1. **Tokens are secrets**: Never commit to git
2. **Source validation**: emotiond validates `source` server-side
3. **Target isolation**: `target_id` comes from hook context, not user input
4. **Rate limiting**: emotiond enforces 10s windows

## Next Steps

After Integration-0 is verified:

1. **Integration-1**: Map decision actions to response style templates
2. **Integration-2**: Add multi-channel identity binding
3. **Integration-3**: Plugin HTTP routes (when security model is resolved)

## Files

```
integrations/openclaw/
├── README.md                    # This file
├── skills/
│   └── openemotion-emotiond/
│       └── SKILL.md             # Skill documentation
└── hooks/
    └── emotiond-bridge/
        ├── HOOK.md              # Hook documentation
        └── handler.js           # Hook implementation
```

---

## Token Security

### Secure Token Setup

Tokens are now managed securely with the following priority order:

1. **Environment variable** (`EMOTIOND_OPENCLAW_TOKEN`) - Recommended for production
2. **User config file** (`~/.config/openemotion/emotiond_token`)
3. **Auto-generation** - If no token exists, one is generated automatically

### Quick Token Setup

```bash
# Option 1: Environment variable (recommended)
export EMOTIOND_OPENCLAW_TOKEN=$(openssl rand -hex 32)

# Option 2: Let emotiond auto-generate
python -m emotiond.api
# Check logs for token location: tail -f /tmp/emotiond.log | grep token
```

### Never Commit Tokens

Token files are now excluded via `.gitignore`:
```
.emotiond_token
**/.emotiond_token
emotiond_token
```

### Token Rotation

To rotate a compromised or stale token:

```bash
# Generate new token
openssl rand -hex 32 > ~/.config/openemotion/emotiond_token
chmod 600 ~/.config/openemotion/emotiond_token

# Update OpenClaw config
# Edit ~/.openclaw/openclaw.json with the new EMOTIOND_OPENCLAW_TOKEN

# Restart services
openclaw gateway restart
```

### If Token Was Committed to Git

See `docs/SECURITY.md` for instructions on cleaning git history using `git filter-branch` or BFG Repo-Cleaner.

**Important**: Always rotate a token that was ever committed to version control.

For comprehensive security documentation, see [`docs/SECURITY.md`](../../docs/SECURITY.md).
