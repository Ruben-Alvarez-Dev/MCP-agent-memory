# vk-cache Specification

## Purpose

Unified retrieval and context assembly (L5). Implements the bidirectional protocol:
PULL (LLM requests context → ContextPack) and PUSH (system sends reminders).
Does NOT store data — queries Qdrant, Engram, mem0, and conversations.

## Requirements

### REQ-VC-01: Request Context (PULL)

The system SHALL accept a query with intent and token budget, run smart retrieval
across all sources, pack results into a ContextPack, and return it.

#### Scenario: Code lookup query

- GIVEN query="inspect main.py", intent="answer", token_budget=4000
- WHEN request_context called
- AND runs smart_retrieve with intent classification
- AND includes repo_map section if query is code-related
- AND returns ContextPack with sections, total_tokens, metadata

#### Scenario: Zero results

- GIVEN query matches nothing in any source
- WHEN request_context called
- AND returns empty ContextPack with sources_used=[] and injection_text=""

### REQ-VC-02: Push Reminder (PUSH)

The system SHALL create and persist context reminders for agents.

#### Scenario: Push new reminder

- GIVEN query and reason
- WHEN push_reminder called
- AND creates ContextReminder with unique ID
- AND saves to ~/.memory/reminders/{id}.json
- AND returns status "reminder_pushed"

### REQ-VC-03: Check Reminders

The system SHALL return pending reminders for a given agent.

#### Scenario: Agent has pending reminders

- GIVEN agent_id with 2 saved reminder files
- WHEN check_reminders called
- AND returns list of 2 reminders sorted by creation time

### REQ-VC-04: Dismiss Reminder

The system SHALL delete a reminder file by ID.

#### Scenario: Valid reminder

- GIVEN existing reminder file
- WHEN dismiss_reminder called
- AND deletes the file and returns "dismissed"

### REQ-VC-05: Detect Context Shift

The system SHALL compare current and previous query embeddings to detect domain changes.

#### Scenario: Domain shift detected

- GIVEN current_query about "database" and previous_query about "frontend"
- WHEN detect_context_shift called
- AND computes cosine similarity between embeddings
- AND returns shift_detected=True if similarity < threshold

### REQ-VC-06: Verify Compliance

The system SHALL verify code against project compliance rules.

#### Scenario: Code with Pydantic V1 config

- GIVEN code containing `class Config:` inside a Pydantic model
- WHEN verify_compliance_tool called
- AND returns violation for PYDANTIC_V2_CONFIG rule

### REQ-VC-07: Daemon Status

The system SHALL report health of all backend services and active reminders.

#### Scenario: All backends healthy

- GIVEN Qdrant reachable, Engram path exists, llama.cpp available
- WHEN status called
- AND returns qdrant="OK", engram="OK", llama_cpp="OK", active_reminders=N

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| QDRANT_URL | http://127.0.0.1:6333 | Qdrant endpoint |
| QDRANT_COLLECTION | automem | Source collection |
| VK_MIN_SCORE | 0.3 | Minimum relevance score |
| VK_MAX_ITEMS | 8 | Max items per retrieval |

## Dependencies

- `shared.models`: ContextPack, ContextReminder, ContextRequest, ContextSource, MemoryLayer
- `shared.embedding`: get_embedding, _ensure_binaries
- `shared.retrieval`: retrieve, get_repo_map, prune_content
- `shared.compliance`: verify_compliance, add_rule, ProjectRule
