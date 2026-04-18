# MCP Memory Server v3 — System Specification

> **Version**: 3.0.0
> **Last updated**: 2026-04-15
> **Status**: Operational — 63 tools, 9 servers, running on :3050

---

## 1. What This System Is

A self-contained, agent-independent memory stack for LLM-based agents. No Docker, no Homebrew, no external LLM required for core operation. All binaries bundled, all services launchd-managed.

The system provides **persistent, semantic, hierarchical memory** to any agent that connects via MCP protocol.

---

## 2. Architecture

### Topology

```
Agent (Cursor/Claude/VS Code)
         │
         ▼
┌──────────────────────┐
│  1MCP Gateway (:3050) │  ← Node.js, aggregates 9 servers → 63 tools
└──────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  9 MCP Servers (FastMCP, Python 3.12+)   │
│                                           │
│  automem           L0/L1 real-time ingest │
│  autodream         L2-L4 consolidation    │
│  vk-cache          L5 context assembly     │
│  sequential-thinking  Reasoning + sandbox  │
│  conversation-store   Thread recording     │
│  mem0-bridge          Semantic facts       │
│  engram-bridge        Decisions/entities   │
│  engram-facade        Gentle-AI compat     │
│  context7-proxy       Remote docs proxy    │
│                                           │
│  shared/                                  │
│  ├── embedding.py    llama.cpp wrapper     │
│  ├── retrieval/      Smart context router  │
│  ├── models/         Pydantic data models  │
│  ├── llm/            LLM backends          │
│  ├── compliance/     Code rule checker     │
│  ├── vault_manager/  Obsidian vault        │
│  └── observe.py      Instrumentation       │
│                                           │
│  skills/                                  │
│  ├── memory-core/    Universal protocol    │
│  ├── code/           Code analysis         │
│  ├── filesystem/     File operations       │
│  └── research/       Web search            │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Qdrant (:6333)       │  ← Native binary, launchd
│  Collections:         │
│  - automem            │
│  - conversations      │
│  - mem0_memories      │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│  llama.cpp (bundled)  │  ← 384d embeddings, all-MiniLM-L6-v2
└──────────────────────┘
```

### 6-Layer Memory Stack

| Layer | Name | Purpose | Storage | Trigger |
|-------|------|---------|---------|---------|
| L0 | RAW | Append-only JSONL audit trail | `~/.memory/raw_events.jsonl` | Every event |
| L1 | WORKING | Hot facts, recent steps | Qdrant + llama.cpp | Real-time |
| L2 | EPISODIC | Conversations, incidents, repo symbols | Qdrant | Every 10 turns |
| L3 | SEMANTIC | Decisions, entities, patterns | Engram filesystem + Qdrant | Every 1 hour |
| L4 | CONSOLIDATED | Summaries, narratives | Qdrant | Every 24 hours |
| L5 | CONTEXT | Ephemeral packs (assembled on demand) | In-memory | On request |

### Bidirectional Protocol

**PULL** (LLM requests context):
```
LLM → vk-cache.request_context(query, intent, token_budget)
Memory → LLM: ContextPack (ranked, deduplicated, pruned)
```

**PUSH** (Memory proactively reminds):
```
System → vk-cache.push_reminder(query, reason, agent_id)
LLM → vk-cache.check_reminders(agent_id) → receives pending reminders
LLM → vk-cache.dismiss_reminder(reminder_id)
```

---

## 3. Server Inventory

| Server | Tools | Lines | Purpose |
|--------|-------|-------|---------|
| automem | 4 | 327 | Real-time L0/L1 ingestion |
| autodream | 5 | 458 | L2-L4 consolidation + dreams |
| vk-cache | 7 | 545 | L5 context assembly + reminders |
| sequential-thinking | 10 | 465 | Reasoning, planning, sandbox |
| conversation-store | 5 | 200 | Thread recording + semantic search |
| mem0-bridge | 5 | 220 | Semantic fact storage |
| engram-bridge | 11 | 334 | Decision/entity Markdown files |
| engram-facade | 13 | 889 | Gentle-AI compatible interface |
| context7-proxy | 3 | 205 | Remote documentation proxy |
| **Total** | **63** | **3,623** | |

---

## 4. Shared Modules

| Module | Lines | Key Exports |
|--------|-------|-------------|
| embedding.py | 463 | `get_embedding`, `bm25_tokenize`, 3 backends |
| models/__init__.py | 277 | 9 Pydantic models, 4 enums |
| models/repo.py | 28 | `RepoNode`, `RepoMap` |
| llm/* | 922 | `get_llm`, `classify_intent`, `QueryIntent`, 3 backends |
| retrieval/__init__.py | 915 | `retrieve()`, 9 profiles, RRF fusion, repo proximity |
| retrieval/repo_map.py | 182 | `build_repo_map`, `get_repo_map` |
| retrieval/pruner.py | 247 | `prune_content` (AST for Python, heuristic fallback) |
| retrieval/index_repo.py | 152 | `build_repo_index_points`, `upsert_repository_index` |
| compliance/__init__.py | 293 | `verify_compliance`, 6 default rules |
| vault_manager/__init__.py | 758 | `vault` singleton, atomic writes, integrity check |
| observe.py | 443 | `observe` decorator, metrics, live dashboard |
| env_loader.py | 88 | `load_env` |
| **Total** | **4,816** | |

---

## 5. Data Storage

| Path | Purpose |
|------|---------|
| `~/.memory/raw_events.jsonl` | L0 append-only audit trail |
| `~/.memory/heartbeats/` | Agent heartbeat state |
| `~/.memory/staging_buffer/` | Virtual sandbox staging |
| `~/.memory/reminders/` | Pending context reminders |
| `~/.memory/thoughts/` | Sequential thinking sessions + plans |
| `~/.memory/dream/` | AutoDream state |
| `~/.memory/engram/` | L3 Markdown files (YAML frontmatter) |
| Qdrant `automem` | L1 working + L2 episodic + repo symbols |
| Qdrant `conversations` | Conversation threads |
| Qdrant `mem0_memories` | Semantic facts/preferences |

---

## 6. Infrastructure

| Service | Port | Management | Purpose |
|---------|------|------------|---------|
| 1MCP Gateway | 3050 | launchd | MCP tool aggregation |
| Qdrant | 6333 | launchd | Vector + sparse storage |
| llama.cpp | — | bundled subprocess | Local embeddings (384d) |

### Embedding Backends

| Backend | Config | Description |
|---------|--------|-------------|
| `llama_cpp` | default | Bundled llama-embedding binary + all-MiniLM-L6-v2 GGUF |
| `http` | `EMBEDDING_ENDPOINT` | Remote embedding API |
| `noop` | testing | Zero vectors, no computation |

### LLM Backends

| Backend | Purpose |
|---------|---------|
| `ollama` | Local Ollama for summarization during consolidation |
| `lmstudio` | LM Studio OpenAI-compatible |
| `llama_cpp` | Managed llama-server subprocess |

---

## 7. Key Design Decisions

1. **Self-contained**: No Docker, no Homebrew. All binaries bundled with corrected rpaths.
2. **Agent-independent**: Memory daemons run regardless of LLM connection state.
3. **Bidirectional**: LLM can PULL context, system can PUSH reminders.
4. **6-layer hierarchy**: RAW → WORKING → EPISODIC → SEMANTIC → CONSOLIDATED → CONTEXT.
5. **Scoped memory**: Each agent has isolated memory space (session/agent/domain/personal/global-core).
6. **Virtual context**: Context assembled via retrieval, not infinite KV cache.
7. **Virtual sandbox**: Plans stage to buffer before filesystem mutation.
8. **Local skills**: 1mcp-agent loads skills from `MCP-servers/skills/*/SKILL.md` at bootstrap.
9. **Repo-aware retrieval**: L2 repo symbol index enables structural code navigation.
10. **Compliance built-in**: Code verification against 6 default rules (Pydantic V2, no secrets, UTC datetime, etc.).
