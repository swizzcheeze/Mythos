#!/usr/bin/env node

// Configuration for the Mythos Backend
const BASE_URL = `http://localhost:${process.env.MYTHOS_PORT || '8013'}`;
const http = require('http');

// Tool definitions, mirroring the FastAPI backend's Pydantic models
const tools = [
  {
    name: 'mythos_archetype_analysis',
    description: 'Analyzes a character using 22 archetype frameworks (Jungian, Disney, James Cameron, Norse, Greek, Horror, Sci-Fi, Stephen King, Alfred Hitchcock, Japanese, Korean, and more).',
    inputSchema: {
      type: 'object',
      properties: {
        character_name: { type: 'string', description: 'The name of the character or entity to analyze.' },
        description: { type: 'string', description: 'A brief bio or description of the character.' },
        style: { type: 'string', description: 'Optional archetype style: "Jungian" (default), "Disney", "James Cameron", "General", "Fantasy", "Gothic", "Dark Gothic", "Romance", "Mystery", "Adventure", "Norse", "Mythological", "Greek", "Horror", "Sci-Fi", "Quantum Physics", "Medieval", "C.S. Lewis", "Stephen King", "Alfred Hitchcock", "Japanese", or "Korean".' }
      },
      required: ['character_name', 'description']
    }
  },
  {
    name: 'mythos_create_lore_entry',
    description: 'Saves a new, structured entry into the world lore database for later retrieval.',
    inputSchema: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'The topic or title of the lore entry (e.g., "The Obsidian War").' },
        content: { type: 'string', description: 'The detailed narrative content of the lore entry.' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional tags (e.g., ["magic", "location", "history"]).' },
        world: { type: 'string', description: 'Optional target world name (defaults to "default").' }
      },
      required: ['topic', 'content']
    }
  },
  {
    name: 'mythos_get_inspiration',
    description: 'Generates a random, creative constraint or prompt to inspire new ideas and break writer\'s block.',
    inputSchema: {
      type: 'object',
      properties: {
        style: { type: 'string', description: 'The desired creative style or theme (e.g., "cosmic horror", "medieval fantasy", "cyberpunk").' }
      }
    }
  },
  {
    name: 'mythos_list_tools',
    description: 'Displays a user-friendly menu of all available Mythos tools with descriptions and parameters.',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'mythos_list_archetype_styles',
    description: 'Shows all 22 archetype frameworks (Jungian, Norse, Greek, Horror, Sci-Fi, Stephen King, Japanese, Korean, etc.) with their character types.',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'mythos_list_lore_entries',
    description: 'Retrieves saved worldbuilding entries from the database with optional search and tag filtering.',
    inputSchema: {
      type: 'object',
      properties: {
        search_query: { type: 'string', description: 'Optional search term to filter by topic or content.' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional tags to filter entries (e.g., ["magic", "ritual"]).' },
        world: { type: 'string', description: 'Optional target world name (defaults to "default").' }
      }
    }
  },
  {
    name: 'mythos_creation_mode',
    description: 'Interactive template-based creation guide for worldbuilding. Returns structured sections, creative prompts, and guided questions for 10 entity types: character, location, faction, magic_system, creature, artifact, event, culture, conflict, ritual.',
    inputSchema: {
      type: 'object',
      required: ['template_type'],
      properties: {
        template_type: { 
          type: 'string', 
          description: 'Template type: character, location, faction, magic_system, creature, artifact, event, culture, conflict, or ritual.'
        },
        style: { 
          type: 'string', 
          description: 'Optional creative style/genre (e.g., "Fantasy", "Cyberpunk", "Horror"). Defaults to "Fantasy".'
        }
      }
    }
  },
  {
    name: 'mythos_update_lore_entry',
    description: 'Edit an existing lore entry by ID; partial updates allowed.',
    inputSchema: {
      type: 'object',
      required: ['id'],
      properties: {
        id: { type: 'string', description: 'Existing lore entry ID (UUID string).' },
        topic: { type: 'string', description: 'Optional updated topic/title.' },
        content: { type: 'string', description: 'Optional updated content.' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional updated tags array.' },
        world: { type: 'string', description: 'Optional target world name (defaults to "default").' }
      }
    }
  },
  {
    name: 'mythos_wipe_lore_db',
    description: 'IRREVERSIBLE: Wipe the specified world database after confirmation.',
    inputSchema: {
      type: 'object',
      required: ['confirm'],
      properties: {
        confirm: { type: 'string', description: "Must be 'CONFIRM' to proceed." },
        world: { type: 'string', description: 'Optional target world name (defaults to "default").' }
      }
    }
  },
  {
    name: 'mythos_delete_world',
    description: 'IRREVERSIBLE: Delete an entire world directory (not allowed for default). Requires confirm=\'CONFIRM\'.',
    inputSchema: {
      type: 'object',
      required: ['name', 'confirm'],
      properties: {
        name: { type: 'string', description: 'World name to delete (folder-safe).' },
        confirm: { type: 'string', description: "Must be 'CONFIRM' to proceed." }
      }
    }
  },
  {
    name: 'mythos_list_worlds',
    description: 'List available worlds and show the active one.',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'mythos_create_world',
    description: 'Create a new world workspace, optionally select it immediately.',
    inputSchema: {
      type: 'object',
      required: ['name'],
      properties: {
        name: { type: 'string', description: 'World name (folder-safe).' },
        select_after_create: { type: 'boolean', description: 'Whether to make it active right away (default true).' }
      }
    }
  },
  {
    name: 'mythos_select_world',
    description: 'Switch active world; optionally create if missing.',
    inputSchema: {
      type: 'object',
      required: ['name'],
      properties: {
        name: { type: 'string', description: 'World name to activate.' },
        create_if_missing: { type: 'boolean', description: 'Create a new empty world if not found (default false).' }
      }
    }
  },
  {
    name: 'mythos_creation_session_start',
    description: 'Start an interactive creation session for a template type (character, location, faction, magic_system, creature, artifact, event, culture, conflict, ritual, world) and optional style.',
    inputSchema: {
      type: 'object',
      required: ['template_type'],
      properties: {
        template_type: { type: 'string', description: 'Template type including new world template.' },
        style: { type: 'string', description: 'Optional creative style; defaults to Fantasy.' }
      }
    }
  },
   {
    name: 'mythos_creation_session_update',
    description: 'Update fields for an active creation session. IMPORTANT: Always nest updates as { "Section": { "Field": value } }. Do NOT pass { "Section": "value" }—every section must contain an object with field names as keys. Example: { "Basic Info": { "Age": "23", "Occupation": "Enchantress" }, "Abilities": { "Skills": ["magic", "seduction"] } }.',
    inputSchema: {
      type: 'object',
      required: ['session_id', 'updates'],
      properties: {
        session_id: { type: 'string', description: 'Session identifier from start.' },
        updates: { 
          type: 'object',
          additionalProperties: {
            type: 'object',
            additionalProperties: true
          },
          description: 'MANDATORY nested structure: { "Section Name": { "Field Name": value } }. Every section value MUST be an object with field-name keys. Field values can be strings, arrays, or objects.'
        }
      }
    }
  },
  {
    name: 'mythos_creation_session_get',
    description: 'Retrieve the current state of a creation session.',
    inputSchema: { type: 'object', required: ['session_id'], properties: { session_id: { type: 'string' } } }
  },
  {
    name: 'mythos_creation_session_finalize',
    description: 'Assemble a preview and a proposed lore entry payload without saving.',
    inputSchema: {
      type: 'object',
      required: ['session_id'],
      properties: {
        session_id: { type: 'string', description: 'Session identifier from start.' },
        topic: { type: 'string', description: 'Optional proposed topic/title.' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional proposed tags.' }
      }
    }
  },
  {
    name: 'mythos_roleplay_start',
    description: 'Start roleplay by generating a persona prompt from a character session or provided fields.',
    inputSchema: {
      type: 'object',
      properties: {
        session_id: { type: 'string', description: 'Optional: existing character creation session id.' },
        character_name: { type: 'string', description: 'Optional: character name when no session provided.' },
        bio: { type: 'string', description: 'Optional: short bio/personality summary.' },
        style: { type: 'string', description: "Optional roleplay style (e.g., 'Fantasy', 'Noir')." },
        safety_guidelines: { type: 'array', items: { type: 'string' }, description: 'Optional list of behavioral guidelines.' }
      },
      required: []
    }
  },
  {
    name: 'mythos_creation_session_list',
    description: 'List active creation sessions with simple progress metadata.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', description: 'Optional max number of sessions to return.' }
      }
    }
  },
  {
    name: 'mythos_multi_archetype_analysis',
    description: 'Blend multiple archetype frameworks (e.g. "Fantasy + Horror + Jungian") to create a composite character analysis.',
    inputSchema: {
      type: 'object',
      required: ['character_name', 'description', 'styles'],
      properties: {
        character_name: { type: 'string', description: 'Name of the character.' },
        description: { type: 'string', description: 'Brief character bio.' },
        styles: { type: 'string', description: 'Composite styles string (Fantasy + Horror + Jungian). Delimiters: comma, plus, slash, with, and.' },
        max_frameworks: { type: 'integer', description: 'Safety cap on number of frameworks to blend (default 5).' }
      }
    }
  },
  {
    name: 'mythos_semantic_lore_search',
    description: 'Semantically search lore entries using embeddings. Finds thematically similar entries ranked by semantic similarity.',
    inputSchema: {
      type: 'object',
      required: ['query'],
      properties: {
        query: { type: 'string', description: 'Semantic search query (e.g., "ancient magic rituals", "prophecies of doom").' },
        top_k: { type: 'integer', description: 'Number of results to return (1-50, default 5).' },
        world: { type: 'string', description: 'Optional target world name (defaults to "default").' }
      }
    }
  }
];

/**
 * Handles the actual HTTP call to the FastAPI backend
 * @param {string} toolName 
 * @param {object} args 
 */
async function handleToolCall(toolName, args) {
  const url = `${BASE_URL}/call/${toolName}`;
  const data = JSON.stringify(args);
  
  return new Promise((resolve, reject) => {
    const req = http.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
        ...(process.env.MYTHOS_ADMIN_TOKEN ? { 'X-Admin-Token': process.env.MYTHOS_ADMIN_TOKEN } : {})
      }
    }, (res) => {
      let responseBody = '';
      res.on('data', (chunk) => { responseBody += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(responseBody));
          } catch (e) {
            reject({ error: "Invalid JSON response from Mythos backend.", details: responseBody });
          }
        } else {
          reject({ error: `Mythos Backend HTTP Error: ${res.statusCode}`, details: responseBody });
        }
      });
    });

    req.on('error', (e) => {
      reject({ error: `[CRITICAL] Could not connect to Mythos Backend. Is the backend running on port ${process.env.MYTHOS_PORT || '8013'}?`, details: e.message });
    });

    req.write(data);
    req.end();
  });
}

// --- Friendly Formatting Layer for Iterative Creation Sessions ---
function formatSessionToolOutput(toolName, result, args) {
  const showRaw = process.env.MYTHOS_SHOW_JSON === '1';
  const enableColor = process.env.MYTHOS_COLOR !== '0';
  const colors = enableColor ? {
    green: '[32m',
    yellow: '[33m',
    red: '[31m',
    cyan: '[36m',
    magenta: '[35m',
    reset: '[0m'
  } : { green:'', yellow:'', red:'', cyan:'', magenta:'', reset:'' };
  function colorizePct(pct) {
    if (!enableColor) return pct + '%';
    if (pct >= 80) return colors.green + pct + '%' + colors.reset;
    if (pct >= 40) return colors.yellow + pct + '%' + colors.reset;
    return colors.red + pct + '%' + colors.reset;
  }
  function sectionStats(sections, filled) {
    const lines = [];
    for (const sec of Object.keys(sections||{})) {
      const total = sections[sec].length;
      let done = 0;
      for (const field of sections[sec]) {
        const val = filled?.[sec]?.[field];
        if ((Array.isArray(val) && val.some(v => String(v).trim())) || (typeof val === 'string' && val.trim())) done++;
      }
      const pct = total ? Math.round((done/total)*100) : 0;
      lines.push(` • ${sec}: ${done}/${total} (${colorizePct(pct)})`);
    }
    return lines;
  }
  function remainingGlobal(sections, filled) {
    let total = 0, done = 0;
    for (const sec of Object.keys(sections||{})) {
      total += sections[sec].length;
      for (const field of sections[sec]) {
        const val = filled?.[sec]?.[field];
        if ((Array.isArray(val) && val.some(v => String(v).trim())) || (typeof val === 'string' && val.trim())) done++;
      }
    }
    return { total, done, remaining: total - done, pct: total ? Math.round((done/total)*100) : 0 };
  }
  if (showRaw) {
    return JSON.stringify(result, null, 2);
  }
  try {
    if (toolName === 'mythos_creation_session_start') {
      const { session_id, template_type, style, sections, creative_prompts } = result;
      const sectionNames = Object.keys(sections);
      const lines = [];
      lines.push(`New ${template_type} creation session started (style: ${style}).`);
      lines.push(`Session ID: ${session_id}`);
      lines.push(`Sections (${sectionNames.length}): ${sectionNames.join(', ')}`);
      lines.push('Prompts:');
      for (const p of creative_prompts || []) lines.push(` • ${p}`);
      lines.push('\nSection Progress (initial):');
      lines.push(...sectionStats(sections, {}));
      lines.push('\nNext: populate fields with mythos_creation_session_update.' );
      return lines.join('\n');
    }
    if (toolName === 'mythos_roleplay_start') {
      const showRaw = process.env.MYTHOS_SHOW_JSON === '1';
      if (showRaw) return JSON.stringify(result, null, 2);
      const p = result.persona || {};
      const lines = [];
      lines.push(`Roleplay Persona: ${p.name || 'Unnamed Character'}`);
      lines.push(`Style: ${p.style || 'Fantasy'}`);
      if (Array.isArray(p.traits) && p.traits.length) {
        lines.push('Traits:');
        p.traits.slice(0, 8).forEach(t => lines.push(`- ${t}`));
      }
      if (Array.isArray(p.background) && p.background.length) {
        lines.push('Background:');
        p.background.slice(0, 8).forEach(b => lines.push(`- ${b}`));
      }
      lines.push('---');
      lines.push('System Instructions:');
      lines.push(result.instructions || '(no instructions)');
      return lines.join('\n');
    }
    if (toolName === 'mythos_creation_session_update') {
      const { session_id, progress, filled, message } = result;
      const { completed_fields, total_fields } = progress || { completed_fields: 0, total_fields: 0 };
      const updatedSections = Object.keys(args.updates || {});
      const lines = [];
      lines.push(`${message} (Session: ${session_id})`);
      const pct = total_fields ? Math.round(((completed_fields||0)/(total_fields))*100) : 0;
      lines.push(`Progress: ${completed_fields}/${total_fields} fields filled (${colorizePct(pct)})`);
      for (const sec of updatedSections) {
        lines.push(`\n${sec}:`);
        const fields = args.updates[sec];
        for (const field of Object.keys(fields || {})) {
          const val = filled?.[sec]?.[field];
          if (Array.isArray(val)) {
            lines.push(` - ${field}:`);
            for (const item of val) lines.push(`    • ${item}`);
          } else if (typeof val === 'string') {
            if (val.includes(';')) {
              const parts = val.split(';').map(p => p.trim()).filter(Boolean);
              if (parts.length > 1) {
                lines.push(` - ${field}:`);
                for (const part of parts) lines.push(`    • ${part}`);
              } else {
                lines.push(` - ${field}: ${val.trim()}`);
              }
            } else {
              lines.push(` - ${field}: ${val.trim()}`);
            }
          } else {
            lines.push(` - ${field}: (empty)`);
          }
        }
      }
      const stats = remainingGlobal(result.sections || {}, filled);
      lines.push(`\nRemaining fields: ${stats.remaining} of ${stats.total}`);
      lines.push('Per-section progress:');
      lines.push(...sectionStats(result.sections || {}, filled));
      lines.push('\nUse get to view full session or finalize when ready.');
      return lines.join('\n');
    }
    if (toolName === 'mythos_creation_session_get') {
      const { id, template_type, style, sections, filled, prompts } = result;
      const lines = [];
      lines.push(`Session ${id} | Type: ${template_type} | Style: ${style}`);
      let total = 0, done = 0;
      for (const sec of Object.keys(sections||{})) {
        total += sections[sec].length;
        for (const field of sections[sec]) {
          const val = filled?.[sec]?.[field];
          if ((Array.isArray(val) && val.some(v => String(v).trim())) || (typeof val === 'string' && val.trim())) done++;
        }
      }
      const pct = total ? Math.round((done/total)*100) : 0;
      lines.push(`Progress: ${done}/${total} (${colorizePct(pct)})`);
      lines.push('Per-section progress:');
      lines.push(...sectionStats(sections, filled));
      for (const sec of Object.keys(sections||{})) {
        lines.push(`\n${sec}:`);
        for (const field of sections[sec]) {
          const val = filled?.[sec]?.[field];
          if (Array.isArray(val)) {
            if (val.length) {
              lines.push(` - ${field}:`);
              for (const item of val) lines.push(`    • ${item}`);
            } else {
              lines.push(` - ${field}: [ ]`);
            }
          } else if (typeof val === 'string' && val.trim()) {
            if (val.includes(';')) {
              const parts = val.split(';').map(p => p.trim()).filter(Boolean);
              if (parts.length > 1) {
                lines.push(` - ${field}:`);
                for (const part of parts) lines.push(`    • ${part}`);
              } else {
                lines.push(` - ${field}: ${val.trim()}`);
              }
            } else {
              lines.push(` - ${field}: ${val.trim()}`);
            }
          } else {
            lines.push(` - ${field}: [ ]`);
          }
        }
      }
      if (prompts?.length) {
        lines.push('\nPrompts:');
        for (const p of prompts) lines.push(` • ${p}`);
      }
      const stats = remainingGlobal(sections, filled);
      lines.push(`\nRemaining fields: ${stats.remaining}`);
      lines.push('\nUse update to add more details or finalize for preview.');
      return lines.join('\n');
    }
    if (toolName === 'mythos_creation_session_finalize') {
      const { preview, proposed_entry } = result;
      const lines = [];
      lines.push('Finalize Preview (ready to save via create lore entry):');
      lines.push('');
      lines.push(preview.trim());
      if (proposed_entry) {
        lines.push('\nSuggested Topic: ' + proposed_entry.topic);
        lines.push('Suggested Tags: ' + (proposed_entry.tags || []).join(', '));
      }
      const emptyCount = preview.split('\n').filter(l => /\[ \]/.test(l)).length;
      lines.push(`\nEmpty slots remaining: ${emptyCount}`);
      lines.push('\nIf satisfied: call mythos_create_lore_entry with proposed_entry details.');
      return lines.join('\n');
    }
    return JSON.stringify(result, null, 2);
  } catch (e) {
    return JSON.stringify(result, null, 2);
  }
}

// === MCP Stdio Protocol Implementation ===
const MCP_PROTOCOL_VERSION = process.env.MYTHOS_MCP_PROTOCOL || '2024-10-07';
process.stdin.setEncoding('utf8');

let buffer = '';
process.stdin.on('data', async (chunk) => {
  buffer += chunk;
  
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (!line.trim()) continue;
    
    try {
      const request = JSON.parse(line);
      
      if (request.method === 'tools/list') {
        process.stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: request.id,
          result: { tools }
        }) + '\n');
      } else if (request.method === 'tools/call') {
        try {
          const result = await handleToolCall(request.params.name, request.params.arguments || {});
          const formatted = formatSessionToolOutput(request.params.name, result, request.params.arguments || {});
          process.stdout.write(JSON.stringify({
            jsonrpc: '2.0',
            id: request.id,
            result: { content: [{ type: 'text', text: formatted }] }
          }) + '\n');
        } catch (err) {
          process.stdout.write(JSON.stringify({
            jsonrpc: '2.0',
            id: request.id,
            error: { code: -32000, message: err?.error || 'Tool call failed', data: err?.details || String(err) }
          }) + '\n');
        }
      } else if (request.method === 'initialize') {
        process.stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: request.id,
          result: {
            protocolVersion: MCP_PROTOCOL_VERSION,
            serverInfo: {
              serverName: 'Mythos World Engine Bridge',
              serverVersion: '1.0.1',
              name: 'Mythos World Engine Bridge',
              version: '1.0.1',
            },
            capabilities: {
              supportsMarkdown: true
            }
          }
        }) + '\n');
      } else {
        process.stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: request.id,
          error: { code: -32601, message: `Method not found: ${request.method}` }
        }) + '\n');
      }
    } catch (e) {
      process.stdout.write(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: { code: -32700, message: 'Parse error or internal bridge failure.', details: e.message }
      }) + '\n');
    }
  }
});
