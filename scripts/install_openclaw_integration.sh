#!/bin/bash
# OpenEmotion → OpenClaw Integration Installer
# Usage: ./scripts/install_openclaw_integration.sh [--workspace] [--managed]

set -e

OPENEMOTION_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INTEGRATION_DIR="$OPENEMOTION_ROOT/integrations/openclaw"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR:-$HOME/.openclaw/workspace}"
MANAGED_DIR="$HOME/.openclaw/hooks"

MODE="${1:-workspace}"

echo "=== OpenEmotion → OpenClaw Integration Installer ==="
echo "OpenEmotion root: $OPENEMOTION_ROOT"
echo "Integration dir:  $INTEGRATION_DIR"

# Generate token if not exists
TOKEN_FILE="$OPENEMOTION_ROOT/.emotiond_token"
if [ ! -f "$TOKEN_FILE" ]; then
  echo ""
  echo "Generating EMOTIOND_OPENCLAW_TOKEN..."
  TOKEN=$(openssl rand -hex 32)
  echo "$TOKEN" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
  echo "Token saved to: $TOKEN_FILE"
else
  TOKEN=$(cat "$TOKEN_FILE")
  echo "Using existing token from: $TOKEN_FILE"
fi

# Install hook
echo ""
echo "Installing hook..."

if [ "$MODE" = "--managed" ]; then
  TARGET_DIR="$MANAGED_DIR/emotiond-bridge"
  echo "Mode: managed hooks ($TARGET_DIR)"
  mkdir -p "$MANAGED_DIR"
  cp -r "$INTEGRATION_DIR/hooks/emotiond-bridge" "$TARGET_DIR"
else
  TARGET_DIR="$WORKSPACE_DIR/hooks/emotiond-bridge"
  echo "Mode: workspace hooks ($TARGET_DIR)"
  mkdir -p "$WORKSPACE_DIR/hooks"
  ln -sf "$INTEGRATION_DIR/hooks/emotiond-bridge" "$TARGET_DIR"
fi

echo "Hook installed to: $TARGET_DIR"

# Create emotiond context directory
mkdir -p "$WORKSPACE_DIR/emotiond"
echo "Context directory: $WORKSPACE_DIR/emotiond/"

# Print configuration snippet
echo ""
echo "=== Configuration ==="
echo "Add to ~/.openclaw/openclaw.json:"
echo ""
cat << CONFIG_EOF
{
  "env": {
    "EMOTIOND_BASE_URL": "http://127.0.0.1:18080",
    "EMOTIOND_OPENCLAW_TOKEN": "$TOKEN"
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
CONFIG_EOF

echo ""
echo "=== Next Steps ==="
echo "1. Add the config above to ~/.openclaw/openclaw.json"
echo "2. Set EMOTIOND_OPENCLAW_TOKEN in emotiond environment:"
echo "   export EMOTIOND_OPENCLAW_TOKEN=\"$TOKEN\""
echo "3. Enable the hook:"
echo "   openclaw hooks enable emotiond-bridge"
echo "4. Restart gateway:"
echo "   openclaw gateway restart"
echo "5. Start emotiond:"
echo "   cd $OPENEMOTION_ROOT && source .venv/bin/activate && python -m emotiond.api"
echo ""
echo "Done!"
