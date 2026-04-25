# ROADMAP — MCP-agent-memory

> The direction from here. Each release has a clear problem → solution → deliverable.

---

## Where We Are: v1.2 — The Backpack

**Status**: ✅ Shipped

The core loop works: plugin auto-triggers capture events, heartbeat tracks turns, consolidation runs on thresholds, conversations survive compaction. The agent no longer needs to remember to use 8 of its 53 tools — they fire automatically.

**What's proven**:
- HTTP sidecar pattern (plugin → localhost:8890 → Python functions → Qdrant)
- Auto-capturing every user prompt, tool call, and file edit
- Conventional commits enforcement (blocking hook)
- Anti-rationalization table reduces LLM skipping of memory saves
- Compaction flow preserves conversations automatically

---

## Next: v1.3 — Smart Context Injection

**Problem**: The agent captures events but doesn't get reminded of relevant past work proactively. When you start working on auth, it doesn't know you already solved an auth problem 3 sessions ago.

**Solution**: Activate `vk_cache_request_context` automatically on every user prompt. The plugin calls it via HTTP, gets a ContextPack, and injects it into the messages.

**Deliverables**:
- [ ] New HTTP endpoint: `POST /api/request-context` → `vk_cache_request_context`
- [ ] Plugin `chat.message` hook: fetch context for the user's query
- [ ] Plugin `experimental.chat.messages.transform`: inject ContextPack as a system message
- [ ] Rate limiting: max 1 context request per 30 seconds per session
- [ ] Token budget: max 2000 tokens of injected context

**Why this matters**: This closes the loop. Capture → Store → Consolidate → **Retrieve → Inject**. The agent starts every conversation with awareness of relevant past work.

---

## Then: v1.4 — Advisory Warnings

**Problem**: OpenCode doesn't support `additionalContext` like Claude Code. GSD uses 10/11 hooks as advisory warnings — we can't do that. But we can use `tool.execute.before` to BLOCK patterns.

**Solution**: Expand the enforcement gate beyond just commit messages. Add blocking rules for common agent mistakes.

**Deliverables**:
- [ ] Block: edits to `.env` files (throw error with explanation)
- [ ] Block: `read` on files over 1000 lines without `offset`/`limit` (wastes context)
- [ ] Block: more than 5 consecutive tool calls without user interaction (context spiral)
- [ ] Block: `write` without a prior `read` of the same file (blind edits)
- [ ] Configurable: enable/disable individual rules via env vars

**Reference**: GSD's `gsd-read-guard.js`, `gsd-prompt-guard.js`, `gsd-workflow-guard.js`

---

## Future: v1.5 — Context Monitor

**Problem**: The agent doesn't know when it's running low on context. GSD has `gsd-context-monitor.js` that warns at 35% remaining and does emergency saves at 25%. We can't read context window size from OpenCode plugins (no API for it).

**Solution**: Workaround via session message count estimation. OpenCode's SDK exposes message counts.

**Deliverables**:
- [ ] Track message count per session via `message.updated` events
- [ ] Estimate context usage (heuristic: ~500 tokens per message + tool output)
- [ ] At estimated 35% remaining: auto-save conversation + auto-consolidate
- [ ] At estimated 25% remaining: inject "WRAP UP NOW" instruction via system.transform

---

## Future: v1.6 — Embedding Pipeline Upgrade

**Problem**: BGE-M3 may be falling back to `all-minilm-l6-v2` silently. The embedding pipeline is critical for vector search quality.

**Solution**: Embedding integrity verification + model swap option.

**Deliverables**:
- [ ] Startup verification: embed a known string, check dimensions match config
- [ ] Health check: compare embedding against known reference vector (cosine similarity > 0.99)
- [ ] Support for alternative embedding backends (OpenAI, local Grpcire)
- [ ] Fallback chain: llama_server → openai_api → noop (with explicit logging)

---

## Future: v2.0 — Agent Orchestration

**Problem**: The backpack is designed for a single agent. Multi-agent workflows (SDD orchestrator + subagents) need shared memory.

**Solution**: Scope-aware memory with agent identity.

**Deliverables**:
- [ ] Agent-scoped memories: each agent has its own L1 but shares L3/L4
- [ ] Cross-agent context injection: orchestrator can pull sub-agent memories
- [ ] Session trees: parent-child session relationships in conversation store
- [ ] Agent registry: track which agents exist, their roles, and capabilities

---

## Vision: "La Mochila"

```
CLI-agent-memory  ← active orchestration layer (the tractor head)
       │
       ├── MCP-agent-memory  ← passive memory services (53 tools)
       │     ├── automem (events + working memory)
       │     ├── autodream (consolidation + dreams)
       │     ├── vk-cache (smart retrieval)
       │     ├── conversation-store (threads)
       │     ├── mem0 (semantic CRUD)
       │     ├── engram (decisions + vault)
       │     └── sequential-thinking (reasoning)
       │
       ├── agent-search  ← codebase indexing + semantic search
       │
       └── backpack-orchestrator  ← auto-trigger enforcement layer
             ├── Auto-capture every event
             ├── Auto-heartbeat every turn
             ├── Auto-save on compaction
             ├── Auto-consolidate on thresholds
             ├── Block bad commits
             └── Inject context proactively (v1.3)
```

The backpack hyperpowers the agent. The agent does the real work (writing code). The backpack makes sure the agent never forgets, never repeats mistakes, and always has context.

---

## Not Doing (Explicitly Out of Scope)

| Idea | Why Not |
|------|---------|
| Multi-user support | This is a single-developer tool, not a SaaS |
| Web dashboard | The agent is the interface, not a browser |
| Cloud storage | All data stays local (privacy-first) |
| Fine-tuning models | Embedding + vector search is sufficient |
| Real-time collaboration | Single-agent architecture by design |

---

## References That Inform Our Direction

| System | What We Learned |
|--------|----------------|
| **GSD** (57K stars) | Hook-based enforcement, wave execution, context monitor |
| **agent-skills** (22.8K stars) | Anti-rationalization tables, verification checklists, red flags |
| **Gentle AI** (not-that-gente-ai) | SDD DAG, blocking rules, self-check protocol, judgment day |
| **Supermemory** (22K stars) | MCP server with built-in memory/recall/context tools |
| **Cognee** (17K stars) | Graph+vector hybrid, lifecycle hooks, 4 APIs |
| **Mem0** (54K stars) | Dominant memory system, mem0-cli for CLI agents |
