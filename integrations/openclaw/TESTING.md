# Emotiond Testing Guide

## Deterministic Testing

### test_mode=true
All test and bot "status reports" MUST use test_mode=true to ensure reproducible results.

### Bash Test Script
```bash
./tools/test_emotiond_deterministic.sh <agent_id> <counterparty_id> <subtype> [seconds]
```

**Examples:**
```bash
# Test care event for moonlight
./tools/test_emotiond_deterministic.sh agent moonlight care

# Test betrayal event for main
./tools/test_emotiond_deterministic.sh agent main betrayal

# Test time_passed event
./tools/test_emotiond_deterministic.sh agent moonlight time_passed 120
```

## Identity Separation (Moonlight vs main)

### Mapping Rules
| Source | counterparty_id | Description |
|--------|-----------------|-------------|
| Telegram direct message | moonlight | User's personal Telegram account |
| Session/agent spawn | main | Agent's internal sessions |
| External API call | (from meta.actor) | Determined by caller |

### Implementation
- `emotiond_world_event` must carry `counterparty_id` explicitly
- `emotiond_get_decision` must specify `counterparty_id`
- Both identities share same Telegram ID but have separate relationship tracks

### Verification
Run test with both identities and verify trust/grudge/bond don't cross-contaminate:
```bash
# Run identity separation verification
./tools/test_identity_separation.sh
```

## Audit Rules
1. Bot MUST NOT report status without actual API response
2. Every status report MUST include decision_id, selected action, and candidates
3. No hallucinated trust/energy/candidates allowed

## API Response Format

### World Event Response
```json
{
  "status": "success",
  "event_id": "evt_abc123",
  "emotional_state": {
    "trust": 0.75,
    "energy": 0.60,
    "grudge": 0.10
  }
}
```

### Decision Response
```json
{
  "status": "success",
  "decision_id": "dec_xyz789",
  "action": "approach",
  "candidates": ["approach", "observe", "withdraw"],
  "confidence": 0.85
}
```

## Test Commands Reference

### Test Individual Endpoints

**Health Check:**
```bash
curl -s http://127.0.0.1:18080/health | python3 -m json.tool
```

**Send World Event:**
```bash
curl -s -X POST http://127.0.0.1:18080/event \
  -H "Content-Type: application/json" \
  -d '{
    "type": "world_event",
    "actor": "moonlight",
    "target": "agent",
    "agent_id": "agent",
    "counterparty_id": "moonlight",
    "meta": {"subtype": "care"}
  }' | python3 -m json.tool
```

**Get Decision (Deterministic):**
```bash
curl -s -X POST "http://127.0.0.1:18080/decision?test_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "agent",
    "user_text": "test",
    "focus_target": "moonlight"
  }' | python3 -m json.tool
```

## Valid Subtypes
- `care` - Positive interaction
- `apology` - Repair attempt
- `betrayal` - Trust violation
- `rejection` - Social rejection
- `ignored` - Being ignored
- `neutral` - No emotional valence
- `uncertain` - Ambiguous event
- `repair_success` - Successful relationship repair
- `time_passed` - Time decay event

---

## Enforcement (v1.4)

### Overview
The emotiond-enforcer hook intercepts bot responses and ensures they comply with emotiond decisions. It runs as a pre-send middleware.

### Hook Location
```
~/.openclaw/hooks/emotiond-enforcer/hook.json
~/.openclaw/hooks/emotiond-bridge/handler.js  (exports enforceDecision)
```

### Enforcement Rules

| Action | Enforcement | Template |
|--------|-------------|----------|
| `withdraw` | Replace with brief, neutral template | "I understand. Noted." |
| `boundary` | Check for violations, warn if detected | (no replacement) |
| `attack` | Sanitize to safe response | "I need to step back." |
| `approach` | Allow (no enforcement) | - |
| `repair_offer` | Allow (no enforcement) | - |
| `observe` | Allow (no enforcement) | - |

### Boundary Violation Patterns

The enforcer checks for these patterns when action is `boundary`:
- `I (love|adore|worship) you`
- `you('re| are) (my|the) (everything|world|life)`
- `I can't live without you`
- `forever together`
- `I'll do anything for you`

### Usage

**Programmatic Usage:**
```javascript
const { enforceDecision } = require('/home/moonlight/.openclaw/hooks/emotiond-bridge/handler.js');

// Enforce a decision before sending
const result = await enforceDecision('moonlight', 'I would love to help you!');

if (result.enforced) {
  console.log('Response was modified:', result.finalResponse);
  console.log('Reason:', result.reason);
} else {
  console.log('Response allowed:', result.finalResponse);
}
```

**Result Object:**
```javascript
{
  enforced: boolean,        // true if response was modified
  action: string,           // emotiond action (withdraw, boundary, etc.)
  originalResponse: string, // original proposed response (null if not enforced)
  finalResponse: string,    // the response to use
  reason: string,           // enforcement reason
  auditId: string,          // audit record ID
  decision_id: string       // emotiond decision ID
}
```

### Audit Log

All enforcement decisions are logged to:
```
~/.openclaw/workspace/emotiond/enforcement_audit.jsonl
```

**Audit Record Format:**
```json
{
  "audit_id": "audit_1709123456789_abc123",
  "timestamp": "2026-03-02T22:47:00.000Z",
  "target_id": "moonlight",
  "proposed_response_hash": "a1b2c3d4",
  "decision": {
    "action": "withdraw",
    "decision_id": "dec_xyz",
    "confidence": 0.85
  },
  "enforcement": {
    "action_taken": "replaced",
    "original_response": "I would love to help you!",
    "final_response": "I understand. Noted.",
    "reason": "withdraw_action_enforced"
  }
}
```

### Testing Enforcement

**Test withdraw enforcement:**
```bash
# First, trigger a withdraw action
curl -s -X POST http://127.0.0.1:18080/event \
  -H "Content-Type: application/json" \
  -d '{
    "type": "world_event",
    "actor": "moonlight",
    "target": "agent",
    "meta": {"subtype": "betrayal"}
  }'

# Then test enforcement
node -e "
const { enforceDecision } = require('/home/moonlight/.openclaw/hooks/emotiond-bridge/handler.js');
enforceDecision('moonlight', 'I really want to help you with this!').then(console.log);
"
```

**Test boundary check:**
```javascript
const { checkBoundaryViolations } = require('/home/moonlight/.openclaw/hooks/emotiond-bridge/handler.js');

const result = checkBoundaryViolations("I love you so much!");
// { hasViolation: true, matchedPatterns: ["I (love|adore|worship) you"] }
```

### Integration with OpenClaw

To use the enforcer as a pre-send hook, add to your OpenClaw configuration:
```json
{
  "hooks": {
    "pre-send": ["emotiond-enforcer"]
  }
}
```

---

## Troubleshooting

### emotiond not responding
```bash
# Check if process is running
pgrep -f emotiond

# Check port availability
ss -tlnp | grep 18080
```

### Token Issues
```bash
# Verify token file exists
cat .emotiond_token
```

### Non-deterministic Results
Ensure `test_mode=true` is set in the decision query parameter.

### Enforcement Not Working
```bash
# Check enforcement audit log
tail -f ~/.openclaw/workspace/emotiond/enforcement_audit.jsonl

# Verify hook is loaded
ls -la ~/.openclaw/hooks/emotiond-enforcer/
```

---

## Audit Trail (MVP-7.5)

### Overview
All emotiond API responses now include machine-parseable audit fields for request tracing and replay compatibility.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | string | Trace ID for request correlation across hook → tool → emotiond → enforcer |
| `policy_version` | string | Policy version for replay compatibility (default: "7.5.0") |
| `schema_version` | string | Response schema version for log parsing (default: "1.0") |

### Correlation ID Format
```
corr_<timestamp>_<random_hex>
```
Example: `corr_1709123456789_a1b2c3d4`

### Flow

```
┌─────────────────┐
│  Hook Entry     │  → Generate correlation_id
│  (handler.js)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Tool Call      │  → Pass correlation_id to emotiond
│  (index.ts)     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  emotiond API   │  → Include in response + logs
│  (api.py)       │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Enforcer       │  → Include in audit log
│  (handler.js)   │
└─────────────────┘
```

### API Response Examples

**Decision Response with Audit Fields:**
```json
{
  "status": "ok",
  "decision_id": 123,
  "action": "approach",
  "explanation": {...},
  "target_id": "moonlight",
  "created_at": "2026-03-02T17:00:00Z",
  "correlation_id": "corr_1709123456789_a1b2c3d4",
  "policy_version": "7.5.0",
  "schema_version": "1.0"
}
```

**Event with Correlation ID:**
```json
{
  "type": "world_event",
  "actor": "user",
  "target": "agent",
  "correlation_id": "corr_1709123456789_a1b2c3d4",
  "meta": {
    "subtype": "care",
    "target_id": "moonlight"
  }
}
```

### Tool Parameters

**emotiond_world_event:**
```json
{
  "counterparty_id": "moonlight",
  "subtype": "care",
  "correlation_id": "corr_optional_custom_id"
}
```

**emotiond_get_decision:**
```json
{
  "counterparty_id": "moonlight",
  "test_mode": true,
  "correlation_id": "corr_optional_custom_id"
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EMOTIOND_POLICY_VERSION` | "7.5.0" | Override policy version |
| `EMOTIOND_SCHEMA_VERSION` | "1.0" | Override schema version |

### Testing Audit Trail

```bash
# Send event with correlation_id
curl -s -X POST http://127.0.0.1:18080/event \
  -H "Content-Type: application/json" \
  -d '{
    "type": "world_event",
    "actor": "moonlight",
    "target": "agent",
    "correlation_id": "corr_test_123",
    "meta": {"subtype": "care"}
  }' | python3 -m json.tool

# Get decision with correlation_id
curl -s "http://127.0.0.1:18080/decision/target/moonlight?test_mode=true&correlation_id=corr_test_456" | python3 -m json.tool
```

### Log Parsing

Use `jq` to extract audit fields from logs:

```bash
# Extract all correlation IDs from enforcement audit
jq '.correlation_id' ~/.openclaw/workspace/emotiond/enforcement_audit.jsonl

# Filter by policy version
jq 'select(.policy_version == "7.5.0")' /var/log/emotiond.log

# Group by correlation_id for trace reconstruction
jq -s 'group_by(.correlation_id)' traces/moonlight.jsonl
```
