# automem Specification

## Purpose

Real-time memory ingestion daemon. Always ON, runs independently of LLM agent.
Captures events, generates embeddings via llama.cpp, stores in Qdrant with dense+BM25 vectors,
and maintains an append-only JSONL audit trail.

## Requirements

### REQ-AM-01: Store Memory

The system SHALL accept content with optional metadata (type, scope, importance, tags),
generate dense embedding + BM25 sparse vector, store in Qdrant collection `automem`,
and append a raw L0 event to JSONL.

#### Scenario: Store with defaults

- GIVEN valid content string
- WHEN memorize(content="test fact") called
- THEN system creates MemoryItem layer=WORKING, scope=SESSION, type=FACT, importance=0.5
- AND stores point with dense vector + sparse BM25 in Qdrant
- AND appends RawEvent to ~/.memory/raw_events.jsonl
- AND returns JSON with status "stored", memory_id, layer "L1_WORKING"

#### Scenario: Store with custom scope and tags

- GIVEN content, scope="personal", tags="bug,auth", importance=0.9
- WHEN memorize called
- THEN MemoryItem has scope_type=PERSONAL, topic_ids=["bug","auth"]
- AND Qdrant point payload includes scope_type "personal"

### REQ-AM-02: Ingest Raw Event

The system SHALL accept fire-and-forget L0 events and automatically promote
non-trivial events (content > 20 chars) to L1 working memory.

#### Scenario: Short event — L0 only

- GIVEN event_type="terminal", content="ls" (under 20 chars)
- WHEN ingest_event called
- THEN appends RawEvent to JSONL only
- AND does NOT create working memory item
- AND returns status "ingested", layer "L0_RAW"

#### Scenario: Substantial event — L0 + L1

- GIVEN event_type="git", content with >20 chars
- WHEN ingest_event called
- THEN appends RawEvent to JSONL (L0)
- AND creates MemoryItem layer=WORKING in Qdrant (L1)
- AND returns layer "L0_RAW + L1_WORKING"

### REQ-AM-03: Agent Heartbeat

The system SHALL track agent liveness and signal when memory promotion is due.

#### Scenario: Regular heartbeat

- GIVEN agent_id="gentleman", turn_count=5
- WHEN heartbeat called
- THEN writes HeartbeatStatus JSON to ~/.memory/heartbeats/gentleman.json
- AND promotion_due=false (5 % 10 != 0)

#### Scenario: Promotion-triggering heartbeat

- GIVEN agent_id="gentleman", turn_count=10
- WHEN heartbeat called
- THEN promotion_due=true (10 % 10 == 0)

### REQ-AM-04: Daemon Status

The system SHALL report health of Qdrant, llama.cpp, JSONL count, stored memory count,
staging buffer contents, and active agents.

#### Scenario: All services running

- GIVEN Qdrant reachable, llama.cpp binary found, JSONL exists
- WHEN status called
- THEN returns JSON with qdrant="OK", llama_cpp="OK", raw_events_jsonl=N, stored_memories=M

#### Scenario: Qdrant unreachable

- GIVEN Qdrant at QDRANT_URL is down
- WHEN status called
- THEN returns qdrant="DOWN", does NOT crash

## Storage

| Target | Path/Collection | Format |
|--------|-----------------|--------|
| Qdrant | `automem` | Dense (1024d cosine) + BM25 sparse |
| JSONL | `~/.memory/raw_events.jsonl` | One RawEvent JSON per line |
| Heartbeats | `~/.memory/heartbeats/{agent_id}.json` | HeartbeatStatus JSON |
| Staging | `~/.memory/staging_buffer/` | Change set JSON files |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| QDRANT_URL | http://127.0.0.1:6333 | Qdrant endpoint |
| QDRANT_COLLECTION | automem | Target collection |
| EMBEDDING_DIM | 1024 | Dense vector dimension |
| AUTOMEM_JSONL | ~/.memory/raw_events.jsonl | L0 audit trail |
| AUTOMEM_PROMOTE_EVERY | 10 | Turns between L1→L2 promotion check |
| STAGING_BUFFER | ~/.memory/staging_buffer | Virtual sandbox path |

## Dependencies

- `shared.models`: MemoryItem, MemoryLayer, MemoryScope, MemoryType, RawEvent, RawEventType, HeartbeatStatus
- `shared.embedding`: get_embedding, bm25_tokenize, _ensure_binaries
- Qdrant (HTTP async client)
