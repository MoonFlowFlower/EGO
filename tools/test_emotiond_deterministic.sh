#!/bin/bash
# Deterministic test script for emotiond API
# Usage: ./test_emotiond_deterministic.sh <agent_id> <counterparty_id> <subtype> [seconds]
# Example: ./test_emotiond_deterministic.sh testbot moonlight care

set -e

# Parameters with defaults
AGENT_ID=${1:-testbot}
COUNTERPARTY_ID=${2:-moonlight}
SUBTYPE=${3:-care}
SECONDS=${4:-60}

EMOTIOND_URL="http://127.0.0.1:18080"
TOKEN_FILE="$(dirname "$0")/../.emotiond_token"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load token if available
if [[ -f "$TOKEN_FILE" ]]; then
    TOKEN=$(cat "$TOKEN_FILE")
    AUTH_HEADER="X-Emotiond-Token: $TOKEN"
else
    AUTH_HEADER=""
    echo -e "${YELLOW}Warning: No token file found at $TOKEN_FILE${NC}"
fi

# Valid subtypes
VALID_SUBTYPES="care apology betrayal rejection ignored neutral uncertain repair_success time_passed"

# Validate subtype
if ! echo "$VALID_SUBTYPES" | grep -qw "$SUBTYPE"; then
    echo -e "${RED}Error: Invalid subtype '$SUBTYPE'${NC}"
    echo "Valid subtypes: $VALID_SUBTYPES"
    exit 1
fi

echo "=========================================="
echo "Emotiond Deterministic Test"
echo "=========================================="
echo "Agent ID:        $AGENT_ID"
echo "Counterparty ID: $COUNTERPARTY_ID"
echo "Subtype:         $SUBTYPE"
echo "Duration:        ${SECONDS}s"
echo "URL:             $EMOTIOND_URL"
echo "=========================================="

# Check if emotiond is running
echo -e "\n${YELLOW}Checking emotiond health...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$EMOTIOND_URL/health" 2>/dev/null || echo -e "\n000")
HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [[ "$HEALTH_HTTP_CODE" != "200" ]]; then
    echo -e "${RED}Error: emotiond not responding (HTTP $HEALTH_HTTP_CODE)${NC}"
    echo "Response: $HEALTH_BODY"
    exit 1
fi
echo -e "${GREEN}emotiond is healthy${NC}"
echo "$HEALTH_BODY" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_BODY"

# Step 1: Send world_event
echo -e "\n${YELLOW}Step 1: Sending world_event (subtype=$SUBTYPE)...${NC}"

EVENT_JSON=$(cat <<EOF
{
    "type": "world_event",
    "actor": "$COUNTERPARTY_ID",
    "target": "$AGENT_ID",
    "text": "Test event: $SUBTYPE from $COUNTERPARTY_ID",
    "meta": {
        "subtype": "$SUBTYPE",
        "severity": 0.5,
        "test": true
    },
    "agent_id": "$AGENT_ID",
    "counterparty_id": "$COUNTERPARTY_ID"
}
EOF
)

echo "Request JSON:"
echo "$EVENT_JSON" | python3 -m json.tool 2>/dev/null || echo "$EVENT_JSON"

EVENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$EMOTIOND_URL/event" \
    -H "Content-Type: application/json" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -d "$EVENT_JSON" 2>/dev/null || echo -e "\n000")

EVENT_HTTP_CODE=$(echo "$EVENT_RESPONSE" | tail -n1)
EVENT_BODY=$(echo "$EVENT_RESPONSE" | head -n -1)

if [[ "$EVENT_HTTP_CODE" != "200" ]]; then
    echo -e "${RED}Error: Event endpoint returned HTTP $EVENT_HTTP_CODE${NC}"
    echo "Response: $EVENT_BODY"
    exit 1
fi

echo -e "${GREEN}Event response (HTTP $EVENT_HTTP_CODE):${NC}"
echo "$EVENT_BODY" | python3 -m json.tool 2>/dev/null || echo "$EVENT_BODY"

# Step 2: Get decision with test_mode=true
echo -e "\n${YELLOW}Step 2: Getting decision (test_mode=true)...${NC}"

DECISION_JSON=$(cat <<EOF
{
    "user_id": "$AGENT_ID",
    "user_text": "Test decision for $SUBTYPE",
    "focus_target": "$COUNTERPARTY_ID"
}
EOF
)

echo "Request JSON:"
echo "$DECISION_JSON" | python3 -m json.tool 2>/dev/null || echo "$DECISION_JSON"

DECISION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$EMOTIOND_URL/decision?test_mode=true" \
    -H "Content-Type: application/json" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -d "$DECISION_JSON" 2>/dev/null || echo -e "\n000")

DECISION_HTTP_CODE=$(echo "$DECISION_RESPONSE" | tail -n1)
DECISION_BODY=$(echo "$DECISION_RESPONSE" | head -n -1)

if [[ "$DECISION_HTTP_CODE" != "200" ]]; then
    echo -e "${RED}Error: Decision endpoint returned HTTP $DECISION_HTTP_CODE${NC}"
    echo "Response: $DECISION_BODY"
    exit 1
fi

echo -e "${GREEN}Decision response (HTTP $DECISION_HTTP_CODE):${NC}"
echo "$DECISION_BODY" | python3 -m json.tool 2>/dev/null || echo "$DECISION_BODY"

# Step 3: Verify deterministic behavior - run twice with same input
echo -e "\n${YELLOW}Step 3: Verifying deterministic behavior...${NC}"

# Send same event again
EVENT_RESPONSE_2=$(curl -s -w "\n%{http_code}" \
    -X POST "$EMOTIOND_URL/event" \
    -H "Content-Type: application/json" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -d "$EVENT_JSON" 2>/dev/null || echo -e "\n000")

EVENT_BODY_2=$(echo "$EVENT_RESPONSE_2" | head -n -1)

# Get decision again
DECISION_RESPONSE_2=$(curl -s -w "\n%{http_code}" \
    -X POST "$EMOTIOND_URL/decision?test_mode=true" \
    -H "Content-Type: application/json" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -d "$DECISION_JSON" 2>/dev/null || echo -e "\n000")

DECISION_BODY_2=$(echo "$DECISION_RESPONSE_2" | head -n -1)

# Extract action from both decisions
ACTION_1=$(echo "$DECISION_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('action',''))" 2>/dev/null || echo "")
ACTION_2=$(echo "$DECISION_BODY_2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('action',''))" 2>/dev/null || echo "")

echo "First decision action:  $ACTION_1"
echo "Second decision action: $ACTION_2"

if [[ "$ACTION_1" == "$ACTION_2" && -n "$ACTION_1" ]]; then
    echo -e "${GREEN}✓ Deterministic behavior verified: same action returned${NC}"
else
    echo -e "${RED}✗ Non-deterministic behavior detected: actions differ${NC}"
fi

# Summary
echo -e "\n=========================================="
echo "Test Summary"
echo "=========================================="
echo "Event Status:    $(echo "$EVENT_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "parse_error")"
echo "Decision Status: $(echo "$DECISION_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "parse_error")"
echo "Action:          $ACTION_1"
echo "Deterministic:   $([[ "$ACTION_1" == "$ACTION_2" ]] && echo "YES" || echo "NO")"
echo "=========================================="

# Output raw JSON for scripting
echo -e "\n${YELLOW}Raw JSON Output:${NC}"
echo "EVENT_RESPONSE=$EVENT_BODY"
echo "DECISION_RESPONSE=$DECISION_BODY"
