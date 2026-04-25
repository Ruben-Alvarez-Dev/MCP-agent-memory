# Architecture — MCP-agent-memory v1.2

> Single source of truth for how the system is built today.

---

## System Overview

MCP-agent-memory is a **passive memory service** — it exposes tools but doesn't initiate action. The `backpack-orchestrator` plugin is the **active enforcement layer** that calls those tools automatically.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         OPENCODE (Host)                              │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ backpack-orchestrator│  │    engram.ts     │  │background-agents │ │
│  │ (auto-triggers)      │  │ (Go binary       │  │ (delegations)    │ │
│  │                      │  │  lifecycle)      │  │                  │ │
│  └──────────┬───────────┘  └────────┬─────────┘  └──────────────────┘ │
│             │ HTTP :8890            │ HTTP :7437                      │
│             │                      │                                  │
│  ───────────┼──────────────────────┼──────────────────────────────── │
│  MCP stdio  │                      │                                  │
│             ▼                      ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │              MCP-agent-memory (Python, single process)           ││
│  │                                                                  ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          ││
│  │  │ automem  │ │autodream │ │ vk-cache │ │conv-store│          ││
│  │  │ (4 tools)│ │ (8 tools)│ │ (6 tools)│ │ (5 tools)│          ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          ││
│  │  │  mem0    │ │ engram   │ │ seq-think│ │  health  │          ││
│  │  │ (5 tools)│ │ (14 tools)│ │(10 tools)│ │ (1 tool) │          ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────┐ ││
│  │  │  Shared Layer                                               │ ││
│  │  │  config │ embedding │ qdrant_client │ sanitize │ api_server │ ││
│  │  └─────────────────────────────────────────────────────────────┘ ││
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────┐ ││
│  │  │  Storage                                                    │ ││
│  │  │  Qdrant (vectors) │ SQLite (cache) │ Filesystem (vault)    │ ││
│  │  └─────────────────────────────────────────────────────────────┘ ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Two Interfaces

### Interface 1: MCP stdio (for the LLM)

The agent sees 53 tools via the MCP protocol. It decides when to call them based on `BACKPACK_RULES` injected into the system prompt.

- Transport: stdin/stdout (JSON-RPC)
- Started by: OpenCode's MCP client
- Entry point: `src/unified/server/main.py`
- Each module registers tools with a prefix (e.g., `automem_*`)

### Interface 2: HTTP API sidecar (for the plugin)

The plugin calls 6 endpoints via HTTP to trigger automatic operations without involving the LLM.

- Transport: HTTP on `127.0.0.1:8890`
- Started by: Same `main.py`, in a background thread
- Entry point: `src/shared/api_server.py`
- Uses the SAME Python functions as the MCP tools — zero duplication

---

## Module Details

### automem — Real-time Memory Ingestion

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/automem/server/main.py` | MCP tools + HTTP API targets |
| Models | `src/shared/models.py` | `MemoryItem`, `RawEvent`, `HeartbeatStatus` |
| Sanitization | `src/shared/sanitize.py` | OWASP-grade input validation |

**Flow**: `ingest_event()` → validate → append to JSONL (L0) → embed → store to Qdrant (L1)

### autodream — Memory Consolidation

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/autodream/server/main.py` | Consolidation + dream tools |
| State | `data/memory/dream/state.json` | Turn counts, last promotion timestamps |

**Consolidation chain**: L1 (working) → L2 (episodic) → L3 (semantic) → L4 (consolidated)

**Thresholds** (configurable via env):
- L1→L2: every 10 turns
- L2→L3: every 3600 seconds
- L3→L4: every 86400 seconds
- Dream: every 604800 seconds

### vk-cache — Smart Context Retrieval

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/vk-cache/server/main.py` | Context retrieval tools |
| Retriever | `src/shared/retrieval/` | Smart routing (dense + sparse) |

**Flow**: `request_context(query)` → embed query → search Qdrant → rank results → return ContextPack

### conversation-store — Thread Persistence

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/conversation-store/server/main.py` | Save/search/get conversations |
| Collection | Qdrant `conversations` | Vector-indexed thread storage |

### engram — Decision Memory + Vault

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/engram/server/main.py` | Decision CRUD + vault management |
| Decisions | `data/memory/engram/` | Markdown files with YAML frontmatter |
| Vault | `data/vault/` | Obsidian-compatible note structure |

**NOTE**: This is separate from the Engram Go binary (`engram serve` on port 7437) which provides `mem_save`/`mem_search` tools.

### sequential-thinking — Reasoning Chains

| Component | File | Responsibility |
|-----------|------|---------------|
| Server | `src/sequential-thinking/server/main.py` | Thinking + plans + sandbox |
| Sessions | `data/memory/thoughts/` | JSON step files |

---

## Shared Infrastructure

### `shared/config.py`
Centralized `Config` dataclass. Reads from env vars, validates URLs/backends/dimensions.

### `shared/embedding.py` (701 lines)
Multi-backend embedding engine with fallback chain:
```
llama_server (HTTP, ~15ms) → llama_cpp (subprocess, ~1087ms) → http (OpenAI) → noop
```

### `shared/qdrant_client.py`
Async Qdrant HTTP client. Dense + sparse (BM25) vectors. Upsert, search, scroll, health.

### `shared/sanitize.py` (652 lines)
OWASP-grade input sanitization pipeline:
1. Control characters removal
2. Invisible characters stripping
3. BiDi override removal
4. Unicode normalization (NFC)
5. Whitespace normalization
6. Length validation
7. Path traversal prevention

### `shared/api_server.py` (182 lines)
HTTP sidecar for plugin communication. Runs in background thread using `http.server` + `threading`. Uses a persistent `asyncio.AbstractEventLoop` per thread to avoid "event loop is closed" errors.

---

## External Dependencies

| Service | Port | Purpose | Binary |
|---------|------|---------|--------|
| Qdrant | 6333 | Vector database (dense + sparse) | `bin/qdrant` |
| llama-server (embedding) | 8081 | BGE-M3 embeddings (1024 dims) | llama.cpp |
| llama-server (LLM) | 8080 | Qwen2.5:7b for consolidation | llama.cpp |
| Engram Go | 7437 | `mem_save`, `mem_search`, `mem_context` | `/opt/homebrew/bin/engram` |
| Backpack API | 8890 | HTTP sidecar for plugin calls | (same Python process) |
