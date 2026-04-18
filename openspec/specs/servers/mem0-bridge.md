# mem0-bridge Specification

## Purpose

Semantic fact and preference storage. Wraps mem0ai library when available,
falls back to direct Qdrant operations. Stores per-user memories in `mem0_memories` collection.

## Requirements

### REQ-MB-01: Add Memory

The system SHALL accept content with optional user_id and metadata,
store as semantic memory in Qdrant `mem0_memories` collection.

#### Scenario: Add with default user

- GIVEN content="prefers dark mode"
- WHEN add_memory called
- AND stores with user_id from MEM0_USER env (default "ruben")
- AND returns memory_id

### REQ-MB-02: Search Memory

The system SHALL perform semantic search over stored facts for a user.

#### Scenario: Find relevant facts

- GIVEN query="theme preference" and user_id="ruben"
- WHEN search_memory called
- AND returns ranked results by semantic similarity

### REQ-MB-03: Get All Memories

The system SHALL list all stored memories for a user.

#### Scenario: Paginated list

- GIVEN user_id="ruben" and limit=20
- WHEN get_all_memories called
- AND returns up to 20 memory items with metadata

### REQ-MB-04: Delete Memory

The system SHALL remove a specific memory by ID.

#### Scenario: Valid deletion

- GIVEN existing memory_id
- WHEN delete_memory called
- AND removes point from Qdrant collection
- AND returns confirmation

### REQ-MB-05: Status

The system SHALL report backend type (mem0 or qdrant_direct) and llama.cpp availability.

#### Scenario: Direct backend

- GIVEN mem0ai library not installed
- WHEN status called
- AND reports backend "qdrant_direct"

## Storage

| Target | Collection | Format |
|--------|-----------|--------|
| Qdrant | `mem0_memories` | Dense vectors, user-scoped |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| MEM0_USER | ruben | Default user ID |

## Dependencies

- `shared.embedding`: get_embedding, _ensure_binaries
- Optional: `mem0ai` Python library
