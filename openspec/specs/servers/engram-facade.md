# engram-facade Specification

## Purpose

Transparent bridge between the gentle-ai standalone Engram interface and the 6-layer memory pipeline.
Compatible with the gentle-ai tool naming convention (mem_save, mem_search, etc.).
Operates in dual mode: direct (uses shared modules) or gateway (HTTP to 1MCP gateway).

## Requirements

### REQ-EF-01: Save Observation (mem_save)

The system SHALL save an observation to L3 filesystem AND L0/L1 Qdrant pipeline simultaneously.

#### Scenario: Save with topic_key upsert

- GIVEN title="Auth model", content="...", topic_key="architecture/auth"
- WHEN mem_save called
- AND writes Markdown to engram filesystem (L3) — updates existing file if topic_key matches
- AND creates MemoryItem in Qdrant automem collection (L1) with dense+sparse vectors
- AND returns observation ID

#### Scenario: Save without topic_key

- GIVEN title and content, no topic_key
- WHEN mem_save called
- AND creates new file with generated slug from title

### REQ-EF-02: Search Observations (mem_search)

The system SHALL search across L3 filesystem AND L1-L4 Qdrant.

#### Scenario: With project filter

- GIVEN query="database" and project="my-app"
- WHEN mem_search called
- AND returns results from engram filesystem + Qdrant, filtered by project metadata

### REQ-EF-03: Get Observation (mem_get_observation)

The system SHALL return full untruncated observation content by ID (file path relative to engram root).

#### Scenario: Valid ID

- GIVEN id="agent/chose-sqlite.md"
- WHEN mem_get_observation called
- AND returns full content without truncation (search results truncate at 300 chars)

### REQ-EF-04: Update Observation (mem_update)

The system SHALL partially merge provided fields into an existing observation.

#### Scenario: Update content only

- GIVEN id and content="new content"
- WHEN mem_update called
- AND updates only content field, preserves title, type, project, scope

### REQ-EF-05: Get Recent Context (mem_context)

The system SHALL return recent observations and sessions for project/scope.

#### Scenario: Project context

- GIVEN limit=20, project="my-app"
- WHEN mem_context called
- AND returns last 20 observations for that project

### REQ-EF-06: Save Prompt (mem_save_prompt)

The system SHALL persist user prompt text for context tracking.

### REQ-EF-07: Session Start/End

The system SHALL register session start and close with optional summary.

#### Scenario: Start session

- GIVEN id="sess-abc", project="my-app", directory="/path/to/project"
- WHEN mem_session_start called
- AND records session metadata

### REQ-EF-08: Session Summary (mem_session_summary)

The system SHALL save a comprehensive end-of-session summary using Goal/Instructions/Discoveries/Accomplished format.

### REQ-EF-09: Suggest Topic Key (mem_suggest_topic_key)

The system SHALL generate a stable topic key from title or content for consistent upserts.

### REQ-EF-10: Capture Passive Learnings (mem_capture_passive)

The system SHALL extract `## Key Learnings:` or `## Aprendizajes Clave:` sections from text and save each item as a separate observation.

#### Scenario: Learnings extraction

- GIVEN content with "## Key Learnings:\n1. First\n2. Second"
- WHEN mem_capture_passive called
- AND creates 2 separate observations from numbered items

### REQ-EF-11: Status

The system SHALL report mode (direct/gateway), engram path, Qdrant status, and llama.cpp status.

## Dual Mode Operation

| Mode | Trigger | Behavior |
|------|---------|----------|
| direct | No MEMORY_SERVER_URL env | Uses shared modules directly (embedding, vault_manager, Qdrant HTTP) |
| gateway | MEMORY_SERVER_URL set | HTTP calls to 1MCP gateway at configured URL |

## Storage

| Target | Path/Collection | Format |
|--------|-----------------|--------|
| Engram L3 | ~/.memory/engram/ | Markdown + YAML frontmatter |
| Qdrant L0/L1 | automem collection | Dense + sparse vectors |

## Dependencies

- `shared.env_loader`: load_env
- `shared.models`: MemoryItem, MemoryLayer, MemoryScope, MemoryType
- `shared.embedding`: get_embedding, bm25_tokenize (direct mode)
- `shared.vault_manager`: vault (direct mode)
