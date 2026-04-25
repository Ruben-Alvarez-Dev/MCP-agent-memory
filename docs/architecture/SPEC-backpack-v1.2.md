# Spec: backpack-orchestrator — v1.2

> The enforcement layer that makes memory automatic.

---

## Problem

53 MCP tools existed. The agent never used them because everything required manual LLM decisions. The tools were passive — they only worked if the agent remembered to call them.

**Root cause**: Instructions were in the wrong place (system prompt essays) and wrong format (asking the LLM to remember).

## Solution

Separate what's automatic from what needs judgment. Automate the repetitive stuff via OpenCode hooks. Give the LLM an anti-rationalization table for the rest.

## Architecture

```
OpenCode event → backpack-orchestrator hook → fetch(:8890) → Python function → Qdrant
```

The plugin has NO direct access to MCP tools. It communicates via HTTP to the sidecar running in the same Python process as the MCP server.

## Hooks (6 total)

### Hook 1: `chat.message` — Turn Start

| Action | Endpoint | Purpose |
|--------|----------|---------|
| Ingest user prompt | `POST /api/ingest-event` | Capture every user message as raw event |
| Heartbeat tick | `POST /api/heartbeat` | Count turns for consolidation thresholds |
| Capture in Engram Go | `POST :7437/prompts` | Cross-system capture |

**Behavior**: Fire-and-forget (no await). Silent fail if server not running. Skips sub-agent sessions.

### Hook 2: `tool.execute.before` — Enforcement Gate

| Condition | Action |
|-----------|--------|
| `git commit` with non-conventional message | **THROW** → blocks the tool call |
| Everything else | Pass through silently |

**Regex**: `^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9._-]+\))?!?: .+`

**Tested**: 13 cases (7 valid, 6 invalid) — all correct.

### Hook 3: `tool.execute.after` — Event Capture

| Action | Endpoint | Purpose |
|--------|----------|---------|
| Ingest tool event | `POST /api/ingest-event` | Capture every tool call result |

**Filtered tools** (skipped to avoid loops):
- All `automem_*`, `autodream_*`, `engram_*`, `vk_cache_*`, `conversation_store_*`, `mem0_*`, `sequential_thinking_*`
- All Engram Go tools: `mem_save`, `mem_search`, etc.

**Tested**: 37 cases (25 filtered + 12 pass through) — all correct.

### Hook 4: `experimental.chat.system.transform` — System Prompt

Injects `BACKPACK_RULES` (~40 lines) instead of old `MEMORY_INSTRUCTIONS` (~120 lines).

**Key differences from old approach**:
- Explicitly states what's automatic (agent doesn't need to worry about it)
- Only lists what NEEDS LLM judgment: decisions, bugfixes, discoveries, session summaries
- Includes anti-rationalization table from agent-skills/Osmani

### Hook 5: `experimental.session.compacting` — Lifecycle

| Step | Action | Critical? |
|------|--------|-----------|
| 1 | Save conversation via `POST /api/save-conversation` | ✅ Awaited |
| 2 | Consolidate via `POST /api/consolidate` | Fire-and-forget |
| 3 | Inject context from Engram Go | ✅ Awaited |
| 4 | Inject FIRST ACTION instruction | ✅ Inline |

### Hook 6: `event` — Session + File Events

| Event | Action |
|-------|--------|
| `session.idle` | Dream heartbeat tick (check consolidation) |
| `file.edited` | Ingest file change event |
| `session.created` | Register in Engram Go |
| `session.deleted` | Cleanup |

## Files

| File | Lines | Type |
|------|-------|------|
| `~/.config/opencode/plugins/backpack-orchestrator.ts` | 434 | OpenCode plugin |
| `src/shared/api_server.py` | 182 | HTTP sidecar |
| `src/unified/server/main.py` | +30 lines | Sidecar startup |
| `src/shared/sanitize.py` | +1 line | New event types |

## Relationship with engram.ts

Both plugins run simultaneously. The engram.ts was slimmed from 449 to 163 lines.

| Concern | Handled by |
|---------|-----------|
| System prompt injection | backpack-orchestrator (`BACKPACK_RULES`) |
| User prompt capture | backpack-orchestrator → MCP ingest + Engram Go |
| Tool event capture | backpack-orchestrator → MCP ingest |
| Compaction lifecycle | backpack-orchestrator (save + consolidate + context) |
| Engram Go server lifecycle | engram.ts (start, session register, manifest import) |
| Commit enforcement | backpack-orchestrator (`tool.execute.before`) |

## Audit Results (v1.2)

| Test Suite | Tests | Result |
|------------|-------|--------|
| T1: HTTP Sidecar endpoints | 6 | ✅ 6/6 |
| T2: Event ingestion edge cases | 6 | ✅ 6/6 |
| T3: Heartbeat turn counter | 3 | ✅ 3/3 |
| T4: Conventional Commits regex | 13 | ✅ 13/13 |
| T5: Memory tool filtering | 37 | ✅ 37/37 |
| T6: System prompt + cleanup | 8 | ✅ 8/8 |
| T7: Save conversation + consolidate | 2 | ✅ 2/2 |
| T8: Engram Go still works | 2 | ✅ 2/2 |
| T9: MCP tools + data flowing | 2 | ✅ 2/2 |
| **Total** | **79** | **✅ 79/79** |
