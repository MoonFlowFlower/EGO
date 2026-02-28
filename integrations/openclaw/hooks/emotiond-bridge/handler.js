/**
 * Emotiond Bridge Hook v1.3
 * 
 * Integration-2: Sends user_message world_event for behavior learning
 * 
 * v1.3 features:
 * - A1: Runtime Context 覆盖写入 TOOLS.md (marker-based)
 * - A3: 轨迹日志 (traces/<target_id>.jsonl)
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const crypto = require('crypto');

const EMOTIOND_BASE_URL = process.env.EMOTIOND_BASE_URL || 'http://127.0.0.1:18080';
const EMOTIOND_OPENCLAW_TOKEN = process.env.EMOTIOND_OPENCLAW_TOKEN || '';
const TIME_PASSED_MIN_DELTA = parseInt(process.env.EMOTIOND_TIME_PASSED_MIN_DELTA || '10', 10);
const TIME_PASSED_MAX_SECONDS = parseInt(process.env.EMOTIOND_TIME_PASSED_MAX_SECONDS || '300', 10);
const CONTEXT_FILE = 'emotiond/context.json';

// Hardcoded workspace path for this setup
const WORKSPACE_DIR = process.env.OPENCLAW_WORKSPACE_DIR || process.env.HOME + '/.openclaw/workspace';
const TOOLS_MD_PATH = process.env.HOME + '/.openclaw/workspace/TOOLS.md';

// Markers for runtime context block
const RUNTIME_BEGIN = '<!-- EMOTIOND_RUNTIME_BEGIN -->';
const RUNTIME_END = '<!-- EMOTIOND_RUNTIME_END -->';

// v1.3: Per-target_id timestamp tracking (was using convId, now explicit target_id)
const lastMessageTimestamps = new Map();

function clampSeconds(seconds) {
  return Math.max(1, Math.min(TIME_PASSED_MAX_SECONDS, Math.floor(seconds)));
}

/**
 * v1.3 A3: Hash text for trace logging (first 8 chars of sha256)
 */
function hashText(text) {
  if (!text) return null;
  return crypto.createHash('sha256').update(text).digest('hex').slice(0, 8);
}

function getActionGuidance(action) {
  const g = {
    approach: { tone: 'warm, open, friendly', intent: 'engage warmly', phrases: ['glad to hear', 'I appreciate'] },
    withdraw: { tone: 'brief, neutral', intent: 'conserve energy', phrases: ['I understand', 'noted'] },
    boundary: { tone: 'clear, firm', intent: 'establish limits', phrases: ['I need to be clear', 'not comfortable'] },
    repair_offer: { tone: 'gentle, conciliatory', intent: 'rebuild trust', phrases: ['I value our connection', 'let me make this right'] },
    observe: { tone: 'curious, neutral', intent: 'gather info', phrases: ['tell me more', 'help me understand'] },
    attack: { tone: 'defensive, sharp', intent: 'push back', phrases: ['I have to push back', 'not acceptable'] }
  };
  return g[action] || g.observe;
}

async function fetchDecision(targetId) {
  return new Promise((resolve, reject) => {
    const url = new URL('/decision/target/' + encodeURIComponent(targetId), EMOTIOND_BASE_URL);
    const req = http.request(url, {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + EMOTIOND_OPENCLAW_TOKEN },
      timeout: 3000
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        if (res.statusCode < 400) {
          try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
        } else { reject(new Error('HTTP ' + res.statusCode)); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.end();
  });
}

async function sendTimePassed(targetId, seconds, reqId) {
  return new Promise((resolve, reject) => {
    const url = new URL('/event', EMOTIOND_BASE_URL);
    const body = JSON.stringify({
      type: 'world_event',
      actor: 'system',
      target: 'assistant',
      text: null,
      meta: { subtype: 'time_passed', seconds, source: 'openclaw', target_id: targetId, request_id: reqId }
    });
    const req = http.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + EMOTIOND_OPENCLAW_TOKEN
      },
      timeout: 3000
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
    req.end();
  });
}

/**
 * Send user_message world_event to emotiond for behavior learning.
 * This allows emotiond to learn user patterns (message length, frequency, etc.)
 */
async function sendUserMessageEvent(conversationId, messageLength, fromUser) {
  return new Promise((resolve, reject) => {
    const url = new URL('/event', EMOTIOND_BASE_URL);
    const body = JSON.stringify({
      type: 'world_event',
      actor: fromUser || 'user',
      target: 'assistant',
      text: null,
      meta: {
        subtype: 'user_message',
        target_id: conversationId,
        message_length: messageLength,
        source: 'openclaw'
      }
    });
    const req = http.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + EMOTIOND_OPENCLAW_TOKEN
      },
      timeout: 3000
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        if (res.statusCode < 400) {
          resolve(data);
        } else {
          reject(new Error('HTTP ' + res.statusCode + ': ' + data));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
    req.end();
  });
}

/**
 * v1.3 A1: Write runtime context to TOOLS.md with markers
 * Overwrites the block between markers, or appends if markers not found
 */
function writeRuntimeContext(toolsMdPath, runtime, traceRecord) {
  try {
    let content = '';
    try {
      content = fs.readFileSync(toolsMdPath, 'utf8');
    } catch (e) {
      // File doesn't exist, will create
      content = '';
    }

    const runtimeBlock = RUNTIME_BEGIN + '\n```json\n' + JSON.stringify(runtime, null, 2) + '\n```\n' + RUNTIME_END;

    const beginIdx = content.indexOf(RUNTIME_BEGIN);
    const endIdx = content.indexOf(RUNTIME_END);

    let newContent;
    if (beginIdx !== -1 && endIdx !== -1 && endIdx > beginIdx) {
      // Markers exist, replace the block
      newContent = content.slice(0, beginIdx) + runtimeBlock + content.slice(endIdx + RUNTIME_END.length);
    } else {
      // Markers don't exist, append to end
      newContent = content.trimEnd() + '\n\n' + runtimeBlock + '\n';
    }

    fs.writeFileSync(toolsMdPath, newContent, 'utf8');
    console.log('[emotiond-bridge] Runtime context written to TOOLS.md');
    return true;
  } catch (e) {
    console.error('[emotiond-bridge] TOOLS.md write error: ' + e.message);
    traceRecord.errors.push({ operation: 'write_tools_md', error: e.message });
    return false;
  }
}

/**
 * v1.3 A3: Append trace record to traces/<target_id>.jsonl
 */
function appendTrace(tracesDir, targetId, traceRecord) {
  try {
    if (!fs.existsSync(tracesDir)) {
      fs.mkdirSync(tracesDir, { recursive: true });
    }
    const tracePath = path.join(tracesDir, targetId + '.jsonl');
    fs.appendFileSync(tracePath, JSON.stringify(traceRecord) + '\n', 'utf8');
    console.log('[emotiond-bridge] Trace appended to: ' + tracePath);
    return true;
  } catch (e) {
    console.error('[emotiond-bridge] Trace write error: ' + e.message);
    return false;
  }
}

const handler = async (event) => {
  if (event.type !== 'message' || event.action !== 'received') return;

  const ctx = event.context || {};
  const wsDir = ctx.workspaceDir || WORKSPACE_DIR;
  const convId = ctx.conversationId || ctx.channelId || 'default';
  const msgId = ctx.messageId || 'msg_' + Date.now();
  const ts = ctx.timestamp || Date.now() / 1000;
  const from = ctx.from || 'unknown';
  const chan = ctx.channelId || 'unknown';
  
  // Extract message content for user_message event
  const messageText = ctx.text || ctx.message || '';
  const messageLength = messageText.length;

  // v1.3: Use convId as target_id (consistent with emotiond)
  const targetId = convId;

  // v1.3 A3: Initialize trace record
  const traceRecord = {
    timestamp: new Date().toISOString(),
    inbound: {
      messageId: msgId,
      ts: ts,
      text_hash: hashText(messageText),
      dt_seconds: null // Will be set after time calculation
    },
    sent_events: [],
    errors: []
  };

  const lastTs = lastMessageTimestamps.get(targetId) || ts;
  const delta = ts - lastTs;

  // Update trace with dt_seconds
  traceRecord.inbound.dt_seconds = delta >= TIME_PASSED_MIN_DELTA ? clampSeconds(delta) : null;

  // Time passed
  if (delta >= TIME_PASSED_MIN_DELTA) {
    const secs = clampSeconds(delta);
    const reqId = chan + ':' + msgId + ':tp';
    try {
      await sendTimePassed(targetId, secs, reqId);
      console.log('[emotiond-bridge] time_passed: ' + secs + 's -> ' + targetId);
      traceRecord.sent_events.push({ type: 'time_passed', seconds: secs, request_id: reqId });
    } catch (e) {
      console.error('[emotiond-bridge] time_passed error: ' + e.message);
      traceRecord.errors.push({ operation: 'send_time_passed', error: e.message });
    }
  }
  lastMessageTimestamps.set(targetId, ts);

  // Fetch decision
  let decision = null;
  let guidance = null;
  try {
    decision = await fetchDecision(targetId);
    if (decision && decision.action) {
      guidance = getActionGuidance(decision.action);
      console.log('[emotiond-bridge] Decision: ' + decision.action + ' for ' + targetId);
    }
  } catch (e) {
    console.error('[emotiond-bridge] Decision fetch error: ' + e.message);
    traceRecord.errors.push({ operation: 'fetch_decision', error: e.message });
  }

  // v1.3 A1: Build runtime context for TOOLS.md
  const runtime = {
    target_id: targetId,
    channel: chan,
    from: from,
    conversation_id: convId,
    message_id: msgId,
    ts: ts,
    dt_seconds: delta >= TIME_PASSED_MIN_DELTA ? clampSeconds(delta) : null,
    request_id_base: chan + ':' + msgId,
    pre_decision: decision ? {
      action: decision.action,
      decision_id: decision.decision_id
    } : null,
    allowed_subtypes_infer: ["care","apology","ignored","rejection","betrayal","neutral","uncertain"]
  };

  // v1.3 A1: Write runtime context to TOOLS.md
  writeRuntimeContext(TOOLS_MD_PATH, runtime, traceRecord);

  // Write context (legacy, keeping for compatibility)
  const context = {
    target_id: targetId,
    channel_id: chan,
    conversation_id: convId,
    message_id: msgId,
    from: from,
    timestamp: ts,
    decision: decision ? { action: decision.action, decision_id: decision.decision_id, explanation: decision.explanation } : null,
    guidance: guidance,
    generated_at: new Date().toISOString()
  };

  const ctxPath = path.join(wsDir, CONTEXT_FILE);
  const ctxDir = path.dirname(ctxPath);
  try {
    if (!fs.existsSync(ctxDir)) fs.mkdirSync(ctxDir, { recursive: true });
    fs.writeFileSync(ctxPath, JSON.stringify(context, null, 2));
    console.log('[emotiond-bridge] Context written to: ' + ctxPath);
  } catch (e) {
    console.error('[emotiond-bridge] Context write error: ' + e.message);
    traceRecord.errors.push({ operation: 'write_context_json', error: e.message });
  }

  // Integration-2: Send user_message world_event for behavior learning
  if (messageLength > 0) {
    try {
      await sendUserMessageEvent(targetId, messageLength, from);
      console.log('[emotiond-bridge] user_message event sent: len=' + messageLength + ' -> ' + targetId);
      traceRecord.sent_events.push({ type: 'user_message', message_length: messageLength });
    } catch (e) {
      console.error('[emotiond-bridge] user_message event error: ' + e.message);
      traceRecord.errors.push({ operation: 'send_user_message', error: e.message });
    }
  }

  // v1.3 A3: Write trace record
  const tracesDir = path.join(wsDir, 'integrations/openclaw/traces');
  appendTrace(tracesDir, targetId, traceRecord);

  console.log('[emotiond-bridge] Processed: ' + msgId + ' -> ' + (decision?.action || 'none'));
};

module.exports = handler;
