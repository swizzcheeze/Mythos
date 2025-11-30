#!/usr/bin/env node

// Configuration for the Mythos Backend running in Docker
const BASE_URL = 'http://localhost:8001'; 
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
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional tags (e.g., ["magic", "location", "history"]).' }
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
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional tags to filter entries (e.g., ["magic", "ritual"]).' }
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
        id: { type: 'integer', description: 'Existing lore entry ID.' },
        topic: { type: 'string', description: 'Optional updated topic/title.' },
        content: { type: 'string', description: 'Optional updated content.' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Optional updated tags array.' }
      }
    }
  },
  {
    name: 'mythos_wipe_lore_db',
    description: 'IRREVERSIBLE: Wipe the current world database after confirmation.',
    inputSchema: {
      type: 'object',
      required: ['confirm'],
      properties: {
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
    description: 'Update fields for an active creation session; supports partial nested updates.',
    inputSchema: {
      type: 'object',
      required: ['session_id', 'updates'],
      properties: {
        session_id: { type: 'string', description: 'Session identifier from start.' },
        updates: { type: 'object', description: 'Nested object: { section: { field: value } } where value may be a string or an array of strings.' }
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
        'Content-Length': Buffer.byteLength(data)
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
      // Critical error: The bridge cannot connect to the Docker container.
      reject({ error: `[CRITICAL] Could not connect to Mythos Backend on port 8001. Is 'docker compose up' running?`, details: e.message });
    });

    req.write(data);
    req.end();
  });
}

// === MCP Stdio Protocol Implementation ===
// Allow overriding the MCP protocol via env; default to a widely supported version.
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
          // The result must be wrapped to conform to the MCP result structure
          process.stdout.write(JSON.stringify({
            jsonrpc: '2.0',
            id: request.id,
            result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
          }) + '\n');
        } catch (err) {
          // Return an error tied to the request id rather than throwing a parse error
          process.stdout.write(JSON.stringify({
            jsonrpc: '2.0',
            id: request.id,
            error: { code: -32000, message: err?.error || 'Tool call failed', data: err?.details || String(err) }
          }) + '\n');
        }
      } else if (request.method === 'initialize') {
        // Negotiate protocol with LM Studio: use env override or fallback default.
        // LM Studio log shows unsupported: 2024-11-01, so avoid that newer version.
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
        // Handle unknown methods
        process.stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: request.id,
          error: { code: -32601, message: `Method not found: ${request.method}` }
        }) + '\n');
      }
    } catch (e) {
      // General error handling for bad JSON or unexpected issues
      process.stdout.write(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: { code: -32700, message: 'Parse error or internal bridge failure.', details: e.message }
      }) + '\n');
    }
  }
});