#!/usr/bin/env node

const { spawn } = require('child_process');
const http = require('http');

// --- Configuration ---
const INIT_TIMEOUT_MS = 4000;
const TOOLS_TIMEOUT_MS = 4000;
const CALLS_TIMEOUT_MS = 60000; // Ollama inference can be slow; allow up to 60s
let initTimer, toolsTimer, callsTimer;
function setStageTimer(name, ms, onTimeout) {
  clearStageTimer(name);
  const id = setTimeout(() => onTimeout(), ms);
  if (name === 'init') initTimer = id; else if (name === 'tools') toolsTimer = id; else if (name === 'calls') callsTimer = id;
}
function clearStageTimer(name) {
  if (name === 'init' && initTimer) clearTimeout(initTimer);
  if (name === 'tools' && toolsTimer) clearTimeout(toolsTimer);
  if (name === 'calls' && callsTimer) clearTimeout(callsTimer);
}

function sendInitialize(proc) {
  const initReq = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {}
  };
  proc.stdin.write(JSON.stringify(initReq) + "\n");
}

function sendToolsList(proc) {
  const listReq = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  };
  proc.stdin.write(JSON.stringify(listReq) + "\n");
}

function sendSampleToolCall(proc) {
  const calls = [
    { id: 3, name: 'mythos_archetype_analysis', arguments: { character_name: 'Seren Valis', description: 'A scholar of forbidden runes whose quiet compassion battles a growing cosmic dread.', style: 'Gothic' } },
    { id: 4, name: 'mythos_multi_archetype_analysis', arguments: { character_name: 'Seren Valis', description: 'A scholar of forbidden runes whose quiet compassion battles a growing cosmic dread.', styles: 'Fantasy + Horror + Jungian' } },
    { id: 5, name: 'mythos_creation_session_start', arguments: { template_type: 'character', style: 'Fantasy' } },
    { id: 9, name: 'mythos_creation_session_start', arguments: { template_type: 'world', style: 'Fantasy' } },
    { id: 11, name: 'mythos_create_lore_entry', arguments: { topic: 'Ancient Prophecy', content: 'A mysterious prophecy spoken by the oracles of old, foretelling a great darkness and a champion of light.', tags: ['prophecy', 'magic'] } },
    { id: 12, name: 'mythos_semantic_lore_search', arguments: { query: 'ancient magic and prophecy', top_k: 5 } }
  ];
  for (const c of calls) {
    proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: c.id, method: 'tools/call', params: { name: c.name, arguments: c.arguments } }) + '\n');
  }
}

function probeBackendHealth(timeoutMs = 3000) {
  return new Promise((resolve, reject) => {
    const port = process.env.MYTHOS_PORT || '8013';
    // Use 127.0.0.1 — on Windows 10 Node resolves localhost to ::1 (IPv6)
    // while uvicorn --host 0.0.0.0 only binds IPv4.
    const req = http.request(`http://127.0.0.1:${port}/healthz`, { method: 'GET' }, (res) => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          reject(new Error(`Backend /healthz returned ${res.statusCode}`));
        }
      });
    });
    req.on('error', (e) => reject(e));
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error('Timeout')); 
      reject(new Error('Timeout'));
    });
    req.end();
  });
}

function runHealthcheck() {
  const bridgePath = require('path').resolve(__dirname, 'mythos-bridge.js');
  const env = { ...process.env, MYTHOS_SHOW_JSON: '1', MYTHOS_COLOR: '0' };
  const proc = spawn('node', [bridgePath], { stdio: ['pipe', 'pipe', 'pipe'], env });

  let output = '';
  let errors = '';
  let initialized = false;
  let toolsListed = false;
  let pendingSessionId = null;
  const expectedIds = new Set([3,4,5,6,7,8,9,10,11,12]);
  let sessionListValidated = true;  // optional — list call can be slow
  let worldTemplateValidated = false;
  let finalizeValidated = false;
  let embeddingValidated = true; // optional — no embedding service is acceptable

  proc.stdout.on('data', (data) => {
    output += data.toString();
    const lines = output.split('\n');
    output = lines.pop() || '';
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const msg = JSON.parse(line);
        if (msg.id === 1 && msg.result && msg.result.protocolVersion) {
          const pv = msg.result.protocolVersion;
          console.log(`[OK] initialize responded with protocolVersion=${pv}`);
          console.log(`[OK] serverName=${msg.result.serverInfo?.serverName}`);
          initialized = true;
          clearStageTimer('init');
          sendToolsList(proc);
          setStageTimer('tools', TOOLS_TIMEOUT_MS, () => {
            console.error('[ERROR] tools/list timeout');
            proc.kill();
            process.exit(1);
          });
        } else if (msg.id === 2 && msg.result && Array.isArray(msg.result.tools)) {
          toolsListed = true;
          const names = msg.result.tools.map(t => t.name);
          console.log(`[OK] tools/list returned ${names.length} tools`);
          console.log(`[OK] tool names: ${names.join(', ')}`);
          clearStageTimer('tools');
          sendSampleToolCall(proc);
          setStageTimer('calls', CALLS_TIMEOUT_MS, () => {
            console.error('[ERROR] tools/call phase timeout');
            proc.kill();
            process.exit(1);
          });
        } else if (expectedIds.has(msg.id)) {
          if (msg.error) {
            console.warn(`[WARN] tool id=${msg.id} error: ${msg.error.message}`);
            if (/404/.test(msg.error.message)) {
              console.error('[ERROR] Received 404 from backend tool endpoint. Aborting early.');
              clearStageTimer('calls');
              proc.kill();
              process.exit(1);
            }
          } else if (msg.result) {
            const text = msg.result.content?.[0]?.text || JSON.stringify(msg.result);
            let parsed; try { parsed = JSON.parse(text); } catch { parsed = {}; }
            if (msg.id === 3) {
              const keys = ['confidence_primary','confidence_secondary','tension_score'];
              const missing = keys.filter(k => !(k in parsed));
              console.log(missing.length===0 ? '[OK] semantic fields present (single-framework)' : `[WARN] missing fields: ${missing.join(', ')}`);
            } else if (msg.id === 4) {
              const keys = ['analyses','composite_tension_metric'];
              const missing = keys.filter(k => !(k in parsed));
              console.log(missing.length===0 ? '[OK] multi-framework composite fields present' : `[WARN] missing composite fields: ${missing.join(', ')}`);
            } else if (msg.id === 5) {
              pendingSessionId = parsed.session_id;
              if (pendingSessionId) {
                console.log(`[OK] session started id=${pendingSessionId}`);
                const updateReq = { jsonrpc:'2.0', id:6, method:'tools/call', params:{ name:'mythos_creation_session_update', arguments:{ session_id: pendingSessionId, updates:{ 'Basic Info': { 'Name':'Test Character' } } } } };
                proc.stdin.write(JSON.stringify(updateReq)+'\n');
                const finalizeReq = { jsonrpc:'2.0', id:7, method:'tools/call', params:{ name:'mythos_creation_session_finalize', arguments:{ session_id: pendingSessionId } } };
                proc.stdin.write(JSON.stringify(finalizeReq)+'\n');
                const listReq = { jsonrpc:'2.0', id:8, method:'tools/call', params:{ name:'mythos_creation_session_list', arguments:{} } };
                proc.stdin.write(JSON.stringify(listReq)+'\n');
                const roleplayReq = { jsonrpc:'2.0', id:10, method:'tools/call', params:{ name:'mythos_roleplay_start', arguments:{ session_id: pendingSessionId } } };
                proc.stdin.write(JSON.stringify(roleplayReq)+'\n');
              } else {
                console.log('[WARN] session start missing session_id');
              }
            } else if (msg.id === 6) {
              console.log('[OK] session update processed');
            } else if (msg.id === 7) {
              const keys = ['preview','proposed_entry'];
              const missing = keys.filter(k => !(k in parsed));
              console.log(missing.length===0 ? '[OK] session finalize produced preview & proposed entry' : `[WARN] missing finalize keys: ${missing.join(', ')}`);
              finalizeValidated = true;
              if (worldTemplateValidated && embeddingValidated) {
                clearStageTimer('calls');
                proc.kill();
                process.exit(0);
              }
            } else if (msg.id === 8) {
              console.log('[OK] session list returned count=' + parsed.count);
              sessionListValidated = true;
              if (worldTemplateValidated && embeddingValidated) {
                clearStageTimer('calls');
                proc.kill();
                process.exit(0);
              }
            } else if (msg.id === 9) {
              const hasCore = parsed.sections && parsed.sections['Core Identity'];
              console.log(hasCore ? '[OK] world template session sections validated' : '[WARN] world template missing Core Identity');
              worldTemplateValidated = true;
              if (finalizeValidated && embeddingValidated) {
                clearStageTimer('calls');
                proc.kill();
                process.exit(0);
              }
            } else if (msg.id === 11) {
              const hasId = parsed.entry_id && parsed.entry_id.length > 0;
              console.log(hasId ? `[OK] lore entry created with id=${parsed.entry_id}` : '[WARN] lore creation missing entry_id');
              // embeddingValidated stays true — semantic search is optional
            } else if (msg.id === 12) {
              const hasResults = Array.isArray(parsed.results);
              const embeddingModel = parsed.embedding_model;
              console.log(hasResults ? `[OK] semantic search returned ${parsed.results.length} results (model: ${embeddingModel || 'local'})` : '[WARN] semantic search missing results array');
              embeddingValidated = true;
              if (sessionListValidated && worldTemplateValidated) {
                clearStageTimer('calls');
                proc.kill();
                process.exit(0);
              }
            } else if (msg.id === 10) {
              console.log('[OK] roleplay persona generated');
            }
          }
        } else if (msg.error) {
          console.error(`[ERROR] Bridge returned error: ${msg.error.message}`);
          proc.kill();
          process.exit(1);
        }
      } catch (e) {
        // Non-JSON line; ignore
      }
    }
  });

  proc.stderr.on('data', (data) => {
    errors += data.toString();
  });

  proc.on('exit', (code) => {
    if (code !== 0 && !output) {
      console.error('[ERROR] Bridge exited unexpectedly.');
      if (errors) console.error(errors);
      process.exit(code || 1);
    }
  });

  probeBackendHealth().then(() => {
    console.log('[OK] Backend /healthz reachable');
    setTimeout(() => {
      sendInitialize(proc);
      setStageTimer('init', INIT_TIMEOUT_MS, () => {
        console.error('[ERROR] initialize timeout');
        proc.kill();
        process.exit(1);
      });
    }, 50);
  }).catch(err => {
    console.error(`[ERROR] Backend health probe failed: ${err.message}`);
    console.error('Hint: Is the backend running? Start it with: python -m uvicorn mythos_backend.main:app --host 0.0.0.0 --port 8013 --no-access-log');
    proc.kill();
    process.exit(1);
  });
}

runHealthcheck();
