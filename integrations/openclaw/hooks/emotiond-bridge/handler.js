/**
 * Emotiond Bridge Hook v1.2
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

const EMOTIOND_BASE_URL = process.env.EMOTIOND_BASE_URL || 'http://127.0.0.1:18080';
const EMOTIOND_OPENCLAW_TOKEN = process.env.EMOTIOND_OPENCLAW_TOKEN || '';
const TIME_PASSED_MIN_DELTA = parseInt(process.env.EMOTIOND_TIME_PASSED_MIN_DELTA || '10', 10);
const TIME_PASSED_MAX_SECONDS = parseInt(process.env.EMOTIOND_TIME_PASSED_MAX_SECONDS || '300', 10);
const CONTEXT_FILE = 'emotiond/context.json';

// Hardcoded workspace path for this setup
const WORKSPACE_DIR = process.env.OPENCLAW_WORKSPACE_DIR || process.env.HOME + '/.openclaw/workspace';

const lastMessageTimestamps = new Map();

function clampSeconds(seconds) {
  return Math.max(1, Math.min(TIME_PASSED_MAX_SECONDS, Math.floor(seconds)));
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

const handler = async (event) => {
  if (event.type !== 'message' || event.action !== 'received') return;

  const ctx = event.context || {};
  const wsDir = ctx.workspaceDir || WORKSPACE_DIR;
  const convId = ctx.conversationId || ctx.channelId || 'default';
  const msgId = ctx.messageId || 'msg_' + Date.now();
  const ts = ctx.timestamp || Date.now() / 1000;
  const from = ctx.from || 'unknown';
  const chan = ctx.channelId || 'unknown';

  const lastTs = lastMessageTimestamps.get(convId) || ts;
  const delta = ts - lastTs;

  // Time passed
  if (delta >= TIME_PASSED_MIN_DELTA) {
    const secs = clampSeconds(delta);
    try {
      await sendTimePassed(convId, secs, msgId + ':tp');
      console.log('[emotiond-bridge] time_passed: ' + secs + 's -> ' + convId);
    } catch (e) {
      console.error('[emotiond-bridge] time_passed error: ' + e.message);
    }
  }
  lastMessageTimestamps.set(convId, ts);

  // Fetch decision
  let decision = null;
  let guidance = null;
  try {
    decision = await fetchDecision(convId);
    if (decision && decision.action) {
      guidance = getActionGuidance(decision.action);
      console.log('[emotiond-bridge] Decision: ' + decision.action + ' for ' + convId);
    }
  } catch (e) {
    console.error('[emotiond-bridge] Decision fetch error: ' + e.message);
  }

  // Write context
  const context = {
    target_id: convId,
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
  }

  console.log('[emotiond-bridge] Processed: ' + msgId + ' -> ' + (decision?.action || 'none'));
};

module.exports = handler;
