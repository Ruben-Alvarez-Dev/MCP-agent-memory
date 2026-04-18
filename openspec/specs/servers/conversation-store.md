# conversation-store Specification

## Purpose

Store full conversation threads with semantic embeddings for later retrieval.
Each thread is embedded and stored in a dedicated Qdrant collection.

## Requirements

### REQ-CS-01: Save Conversation

The system SHALL accept a thread_id and messages JSON, embed the conversation,
and store in Qdrant `conversations` collection.

#### Scenario: New thread

- GIVEN thread_id="sess-123" and messages_json with 5 messages
- WHEN save_conversation called
- AND generates dense embedding of concatenated messages
- AND upserts point to Qdrant conversations collection
- AND returns status "saved"

### REQ-CS-02: Get Conversation

The system SHALL retrieve a conversation by thread_id from Qdrant.

#### Scenario: Existing thread

- GIVEN thread_id that exists in collection
- WHEN get_conversation called
- AND returns full message array and metadata

#### Scenario: Missing thread

- GIVEN thread_id not in collection
- WHEN get_conversation called
- AND returns empty result or error

### REQ-CS-03: Search Conversations

The system SHALL perform semantic search over stored conversations.

#### Scenario: Relevant results

- GIVEN query matching stored conversation content
- WHEN search_conversations(query="auth bug", limit=5) called
- AND returns ranked results by cosine similarity

### REQ-CS-04: List Threads

The system SHALL return recent conversation threads.

#### Scenario: List with limit

- GIVEN limit=10
- WHEN list_threads called
- AND returns up to 10 most recent thread metadata

### REQ-CS-05: Status

The system SHALL report collection health and document count.

## Storage

| Target | Path/Collection | Format |
|--------|-----------------|--------|
| Qdrant | `conversations` | Dense + BM25 sparse |

## Dependencies

- `shared.embedding`: get_embedding, _ensure_binaries
