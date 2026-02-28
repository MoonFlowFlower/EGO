/**
 * Emotiond Bridge Hook
 *
 * Bridges OpenClaw message:received events to the emotiond daemon.
 * - Extracts conversationId as target_id for MVP-3.1 isolation
 * - Sends time_passed events when elapsed time > threshold
 * - Writes context file for skill consumption
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

// Configuration
const EMOTIOND_BASE_URL = process.env.EMOTIOND_BASE_URL || 'http://127.0.0.1:18080';
const EMOTIOND_OPENCLAW_TOKEN = process.env.EMOTIOND_OPENCLAW_TOKEN || '';
const TIME_PASSED_MIN_DELTA = parseInt(process.env.EMOTIOND_TIME_PASSED_MIN_DELTA || '10', 10);
const TIME_PASSED_MAX_SECONDS = parseInt(process.env.EMOTIOND_TIME_PASSED_MAX_SECONDS || '300', 10);

// Context file path (relative to workspace)
const CONTEXT_FILE = 'emotiond/context.json';

// In-memory state for time tracking (per target_id)
const lastMessageTimestamps = new Map();

/**
 * Send event to emotiond
 */
async function sendToEmotiond(event) {
  const url = new URL('/event', EMOTIOND_BASE_URL);

  const body = JSON.stringify(event);

  return new Promise((resolve, reject) => {
    const req = http.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${EMOTIOND_OPENCLAW_TOKEN}`,
        'X-Emotiond-Token': EMOTIOND_OPENCLAW_TOKEN,
      },
      timeout: 5000,
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode && res.statusCode < 400) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`emotiond returned ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('emotiond request timeout'));
    });

    req.write(body);
    req.end();
  });
}

/**
 * Write context file to workspace
 */
function writeContext(workspaceDir, context) {
  const contextPath = path.join(workspaceDir, CONTEXT_FILE);
  const contextDir = path.dirname(contextPath);

  // Ensure directory exists
  if (!fs.existsSync(contextDir)) {
    fs.mkdirSync(contextDir, { recursive: true });
  }

  fs.writeFileSync(contextPath, JSON.stringify(context, null, 2));
}

/**
 * Calculate clamped seconds for time_passed
 */
function clampSeconds(seconds) {
  return Math.max(1, Math.min(TIME_PASSED_MAX_SECONDS, Math.floor(seconds)));
}

/**
 * Main hook handler
 */
const handler = async (event) => {
  // Only handle message:received events
  if (event.type !== 'message' || event.action !== 'received') {
    return;
  }

  const ctx = event.context || {};
  const workspaceDir = ctx.workspaceDir || process.env.OPENCLAW_WORKSPACE_DIR || process.cwd();

  // Extract key fields
  const conversationId = ctx.conversationId || ctx.channelId || 'default';
  const messageId = ctx.messageId || `msg_${Date.now()}`;
  const timestamp = ctx.timestamp || Date.now() / 1000;
  const from = ctx.from || 'unknown';
  const channelId = ctx.channelId || 'unknown';

  // Build context object
  const contextData = {
    target_id: conversationId,
    channel_id: channelId,
    conversation_id: conversationId,
    message_id: messageId,
    from: from,
    timestamp: timestamp,
  };

  // Get last timestamp for this target
  const lastTimestamp = lastMessageTimestamps.get(conversationId) || timestamp;
  const timeDelta = timestamp - lastTimestamp;

  // Check if we should send time_passed
  if (timeDelta >= TIME_PASSED_MIN_DELTA) {
    const clampedSeconds = clampSeconds(timeDelta);

    contextData.last_time_passed = timestamp;

    // Send time_passed event
    const timePassedEvent = {
      type: 'world_event',
      actor: 'system',
      target: 'assistant',
      text: null,
      meta: {
        subtype: 'time_passed',
        seconds: clampedSeconds,
        source: 'openclaw',
        target_id: conversationId,
        request_id: `${messageId}:tp`,
      },
    };

    try {
      await sendToEmotiond(timePassedEvent);
      console.log(`[emotiond-bridge] Sent time_passed: ${clampedSeconds}s to target ${conversationId}`);
    } catch (err) {
      console.error(`[emotiond-bridge] Failed to send time_passed: ${err instanceof Error ? err.message : String(err)}`);
      // Continue - don't block message processing
    }
  }

  // Update last timestamp
  lastMessageTimestamps.set(conversationId, timestamp);

  // Write context file
  try {
    writeContext(workspaceDir, contextData);
  } catch (err) {
    console.error(`[emotiond-bridge] Failed to write context: ${err instanceof Error ? err.message : String(err)}`);
  }

  console.log(`[emotiond-bridge] Processed message: ${messageId} from ${conversationId}`);
};

module.exports = handler;
