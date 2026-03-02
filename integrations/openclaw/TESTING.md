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
