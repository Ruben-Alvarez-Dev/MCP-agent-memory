# MCP-agent-memory

> **Persistent multi-layer memory for AI coding agents.**
> 53 MCP tools + HTTP API + auto-trigger plugin. Zero-config memory that works without the LLM remembering to use it.

---

## What It Does

AI coding agents (OpenCode, Claude Code, etc.) are stateless — they forget everything when a session ends or context compacts. MCP-agent-memory gives them a **backpack** of persistent memory that survives across sessions, compactions, and restarts.

The backpack captures events **automatically** (no LLM decision needed) and provides 53 tools the agent can use when it needs to recall, decide, or reason.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                        THE BACKPACK SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐  │
│  │  backpack-orchestrator│    │      MCP-agent-memory            │  │
│  │  (OpenCode Plugin)    │    │      (Python MCP Server)         │  │
│  │                       │    │                                   │  │
│  │  AUTO-TRIGGERS:       │    │  53 MCP TOOLS:                   │  │
│  │  • Every user prompt  │──→│  • automem (ingest, memorize)     │  │
│  │  • Every tool call    │──→│  • autodream (consolidate, dream) │  │
│  │  • Every file edit    │──→│  • vk-cache (context retrieval)   │  │
│  │  • Session idle       │──→│  • conversation-store (threads)   │  │
│  │  • Context compact    │──→│  • mem0 (semantic CRUD)           │  │
│  │  • Commit validation  │    │  • engram (decisions, vault)      │  │
│  │                       │    │  • sequential-thinking (plans)    │  │
│  │  HTTP → localhost:8890│    │                                   │  │
│  └──────────────────────┘    │  HTTP API → localhost:8890       │  │
│                               │  MCP stdio → stdin/stdout        │  │
│                               └──────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐  │
│  │  engram.ts (Plugin)   │    │  Engram Go Binary               │  │
│  │  Go binary lifecycle  │──→│  mem_save, mem_search, etc.      │  │
│  │  Session registration │    │  SQLite + FTS5                   │  │
│  └──────────────────────┘    └──────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        STORAGE                               │   │
│  │  Qdrant (vectors) │ SQLite (embedding cache) │ Filesystem   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Memory Layers

```
L0 RAW          → Append-only event lake (JSONL)
L1 WORKING      → Steps, facts, hot dialogue (Qdrant)
L2 EPISODIC     → Grouped events, incidents (Qdrant)
L3 SEMANTIC     → Decisions, entities, patterns (Qdrant + Engram files)
L4 CONSOLIDATED → Narratives, deep summaries (Qdrant)
L5 CONTEXT      → Ephemeral context packs (vk-cache)
```

### What's Automatic vs What Needs Agent Judgment

| Category | Trigger | Examples |
|----------|---------|----------|
| **AUTO** (plugin handles it) | Every user prompt, tool call, file edit, compaction | `automem_ingest_event`, `automem_heartbeat`, `conversation_store_save_conversation`, `autodream_consolidate` |
| **LLM DECIDES** | Agent recognizes a decision, bugfix, or discovery | `automem_memorize`, `engram_save_decision`, `vk_cache_request_context` |
| **USER ASKS** | Explicit user request | `health_check`, `*_status`, `*_delete_*`, `engram_search_decisions` |

---

## Project Evolution

| Version | Milestone | What Changed |
|---------|-----------|--------------|
| **v0.1** | Proof of concept | Individual MCP servers (automem, autodream, etc.) running separately |
| **v0.2** | Unified server | 7 servers consolidated into one `main.py` with dynamic module loading |
| **v1.0** | MVP Release | 53 tools, 92% domain coverage, full sanitization, install script, benchmarks |
| **v1.1** | Security audit | OWASP-grade input sanitization (652 lines), path confinement, threat model |
| **v1.2** | **The Backpack** ⬅️ *current* | `backpack-orchestrator` plugin + HTTP API sidecar. Auto-triggers for ingest, heartbeat, consolidation, conversation save, commit enforcement |

### v1.2 — The Backpack (Current)

**The problem it solves**: 53 MCP tools existed but the agent never used them because everything required manual LLM decisions. The tools were passive — they only worked if the agent remembered to call them.

**The solution**: Separate what's automatic from what needs judgment. The `backpack-orchestrator.ts` plugin handles all automatic operations via OpenCode hooks. The LLM only needs to decide on **decisions, bugfixes, and discoveries** — guided by an anti-rationalization table.

**Files added/changed in v1.2**:
- `src/shared/api_server.py` — HTTP sidecar (localhost:8890) for plugin-to-server communication
- `src/unified/server/main.py` — Starts HTTP sidecar alongside MCP stdio
- `src/shared/sanitize.py` — Added `tool_call`, `user_prompt`, `file_edited` event types
- Plugin: `~/.config/opencode/plugins/backpack-orchestrator.ts` — 6 auto-trigger hooks

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/Ruben-Alvarez-Dev/MCP-agent-memory/main/install.sh | bash
```

The installer:
1. Creates Python venv (3.12+)
2. Installs dependencies (pydantic, httpx, mcp)
3. Starts Qdrant vector database
4. Downloads BGE-M3 embedding model + starts llama-server
5. Generates config (`.env` + directory structure)
6. Auto-detects and configures MCP client (OpenCode, Claude Desktop, Pi)
7. Runs verification (imports, connectivity, unit tests)

### Post-Install: Enable the Backpack Plugin

For OpenCode users, copy the plugin:

```bash
cp plugins/backpack-orchestrator.ts ~/.config/opencode/plugins/
```

Then restart OpenCode. The plugin auto-connects to the HTTP API on localhost:8890.

---

## Configuration

### Environment Variables (`config/.env`)

```env
QDRANT_URL=http://127.0.0.1:6333
EMBEDDING_BACKEND=llama_server
LLAMA_SERVER_URL=http://127.0.0.1:8081
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
LLM_BACKEND=llama_cpp
LLM_MODEL=qwen2.5:7b
AUTOMEM_API_PORT=8890              # HTTP sidecar port (default: 8890)
```

### MCP Client Configuration

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
{
  "mcpServers": {
    "MCP-agent-memory": {
      "type": "local",
      "command": ["/path/to/.venv/bin/python3", "-u", "/path/to/src/unified/server/main.py"],
      "env": {
        "PYTHONPATH": "/path/to/src",
        "MEMORY_SERVER_DIR": "/path/to/MCP-agent-memory",
        "QDRANT_URL": "http://127.0.0.1:6333",
        "EMBEDDING_BACKEND": "llama_server",
        "LLAMA_SERVER_URL": "http://127.0.0.1:8081",
        "EMBEDDING_MODEL": "bge-m3",
        "EMBEDDING_DIM": "1024"
      }
    }
  }
}
```

---

## Tools Reference — 53 Tools

### AutoMem — Real-time Memory Ingestion (`automem_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `automem_ingest_event` | ✅ | Ingest raw L0 event (terminal, git, file, tool_call, user_prompt, file_edited) |
| `automem_heartbeat` | ✅ | Signal agent alive, track turns, pre-compute embeddings |
| `automem_memorize` | 🧠 | Store a memory requiring judgment (decision, bugfix, discovery, fact) |
| `automem_status` | 👤 | Show AutoMem daemon status |

### AutoDream — Memory Consolidation (`autodream_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `autodream_heartbeat` | ✅ | Check consolidation thresholds (L1→L2→L3→L4) |
| `autodream_consolidate` | ✅ | Run consolidation across all layers |
| `autodream_dream` | ✅ | Trigger deep dream cycle (background pattern detection) |
| `autodream_get_consolidated` | 🧠 | Retrieve L4 consolidated memories |
| `autodream_get_semantic` | 🧠 | Retrieve L3 semantic memories |
| `autodream_force_promote` | 👤 | Force-promote memories between layers (debug) |
| `autodream_dream_status` | 👤 | Check background dream task status |
| `autodream_status` | 👤 | Show AutoDream daemon state |

### VK-Cache — Smart Context Retrieval (`vk_cache_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `vk_cache_request_context` | 🧠 | Smart context retrieval with intent classification |
| `vk_cache_check_reminders` | ✅ | Check pending context reminders |
| `vk_cache_push_reminder` | ✅ | Push a context reminder for later injection |
| `vk_cache_detect_context_shift` | ✅ | Detect domain shift between queries |
| `vk_cache_dismiss_reminder` | ⚙️ | Dismiss a reminder (internal) |
| `vk_cache_status` | 👤 | Show VK-Cache router status |

### Conversation Store (`conversation_store_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `conversation_store_save_conversation` | ✅ | Save a conversation thread (auto on compaction) |
| `conversation_store_search_conversations` | 🧠 | Search past conversations by similarity |
| `conversation_store_get_conversation` | 🧠 | Retrieve a conversation by thread ID |
| `conversation_store_list_threads` | 👤 | List recent conversation threads |
| `conversation_store_status` | 👤 | Show conversation store status |

### Mem0 — Semantic Memory (`mem0_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `mem0_add_memory` | 🧠 | Add a semantic memory for a user |
| `mem0_search_memory` | 🧠 | Search semantic memories |
| `mem0_get_all_memories` | 👤 | List all memories for a user |
| `mem0_delete_memory` | 👤 | Delete a memory by ID |
| `mem0_status` | 👤 | Show mem0 status |

### Engram — Decision Memory & Vault (`engram_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `engram_save_decision` | 🧠 | Save an architectural decision as Markdown |
| `engram_search_decisions` | 🧠 | Search decisions by keyword |
| `engram_get_decision` | 🧠 | Get a specific decision by file path |
| `engram_list_decisions` | 🧠 | List decisions with optional filtering |
| `engram_delete_decision` | 👤 | Delete a decision file |
| `engram_vault_write` | 🧠 | Write a note to the Obsidian vault |
| `engram_vault_read_note` | 🧠 | Read a vault note |
| `engram_vault_list_notes` | 🧠 | List notes in a vault folder |
| `engram_vault_process_inbox` | 👤 | Process vault inbox items |
| `engram_vault_integrity_check` | 👤 | Verify vault consistency |
| `engram_get_model_pack` | 🧠 | Read a model configuration pack |
| `engram_set_model_pack` | 👤 | Create or update a model pack |
| `engram_list_model_packs` | 👤 | List available model packs |
| `engram_status` | 👤 | Show engram status |

### Sequential Thinking (`sequential_thinking_*`)

| Tool | Auto? | Description |
|------|-------|-------------|
| `sequential_thinking_sequential_thinking` | 🧠 | Multi-step reasoning chain |
| `sequential_thinking_record_thought` | 🧠 | Record a single thinking step |
| `sequential_thinking_create_plan` | 🧠 | Create an execution plan |
| `sequential_thinking_update_plan_step` | 🧠 | Update a plan step status |
| `sequential_thinking_reflect` | 🧠 | Reflect on reasoning quality |
| `sequential_thinking_propose_change_set` | 🧠 | Propose a code change set |
| `sequential_thinking_apply_sandbox` | 🧠 | Apply changes in sandbox mode |
| `sequential_thinking_get_thinking_session` | 🧠 | Retrieve a thinking session |
| `sequential_thinking_list_thinking_sessions` | 👤 | List recent thinking sessions |
| `sequential_thinking_status` | 👤 | Show sequential thinking status |

### Health

| Tool | Description |
|------|-------------|
| `health_check` | Check health of all memory subsystems (Qdrant, embedding, collections, disk) |

**Legend**: ✅ = auto-triggered by plugin | 🧠 = LLM decides when | 👤 = user-triggered | ⚙️ = internal

---

## HTTP API — Plugin Sidecar

The MCP server exposes a lightweight HTTP API on port 8890 for plugin-to-server communication. This runs in a background thread alongside the MCP stdio server.

| Method | Endpoint | Maps to MCP Tool |
|--------|----------|-----------------|
| GET | `/api/health` | Health check |
| POST | `/api/ingest-event` | `automem_ingest_event` |
| POST | `/api/heartbeat` | `automem_heartbeat` |
| POST | `/api/heartbeat-dream` | `autodream_heartbeat` |
| POST | `/api/save-conversation` | `conversation_store_save_conversation` |
| POST | `/api/consolidate` | `autodream_consolidate` |

---

## Project Structure

```
MCP-agent-memory/
├── src/                          # Active source code
│   ├── unified/server/main.py    # Entry point (MCP stdio + HTTP sidecar)
│   ├── automem/                  # L0/L1 real-time memory
│   ├── autodream/                # L1→L4 consolidation
│   ├── vk-cache/                 # Smart context retrieval
│   ├── conversation-store/       # Thread persistence
│   ├── mem0/                     # Semantic memory CRUD
│   ├── engram/                   # Decision memory + vault
│   ├── sequential-thinking/      # Reasoning chains
│   └── shared/                   # Config, embedding, sanitize, API server
├── tests/                        # Test suite
├── docs/                         # Documentation (see below)
├── config/                       # .env template
├── scripts/                      # Lifecycle, watchdog, Qdrant management
├── bin/                          # Qdrant binary
├── models/                       # GGUF models (BGE-M3, Qwen2.5)
└── install.sh                    # 8-step installer
```

---

## Security

- **Input sanitization**: OWASP-grade — Unicode normalization, bidi stripping, invisible char removal, path traversal prevention (652 lines in `sanitize.py`)
- **Filename validation**: OS-safe filenames, Windows reserved name checking
- **Path confinement**: Engram decisions and vault restricted to project directories
- **Config validation**: URLs, backends, dimensions validated at startup
- **HTTP API**: localhost only (127.0.0.1), no network exposure

## Testing

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

## License

MIT
