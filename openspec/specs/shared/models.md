# shared/models Specification

## Purpose

Pydantic V2 data models for the 6-layer memory stack. Defines enums, memory items,
context packs, reminders, scope policies, and agent backpacks.

## Requirements

### REQ-MD-01: Memory Layer Enum

The system SHALL define 6 memory layers: RAW(0), WORKING(1), EPISODIC(2), SEMANTIC(3), CONSOLIDATED(4), CONTEXT(5).

### REQ-MD-02: Memory Type Enum

The system SHALL define 17 memory types: FACT, STEP, PREFERENCE, DECISION, EPISODE, SUMMARY, NARRATIVE, DREAM, PATTERN, ENTITY, CONFIG, BUGFIX, LEARNING, MANUAL, ARCHITECTURE, DISCOVERY, OBSERVATION.

### REQ-MD-03: Memory Scope Enum

The system SHALL define 7 scopes: SESSION, AGENT, DOMAIN, PERSONAL, GLOBAL_CORE, FEDERATED, TEAM.

### REQ-MD-04: MemoryItem Model

The system SHALL provide a Pydantic model with: memory_id (auto UUID7), layer, scope_type, scope_id, type, content, importance (0-1), confidence (0-1), timestamps, topic_ids, entities, source_event_ids, metadata, embedding. Auto-generates `full_scope` property as "{scope_type}:{scope_id}".

### REQ-MD-05: ContextPack Model

The system SHALL provide a model for assembled context with: query, sections (list), total_tokens, injection_text, metadata (sources_used, profile, retrieval_time_ms).

### REQ-MD-06: ContextReminder Model

The system SHALL provide a model with: reminder_id, query, reason, agent_id, created_at, dismissed.

### REQ-MD-07: RawEvent Model

The system SHALL provide an L0 audit trail model with: event_id (auto UUID), type (RawEventType), source, actor_id, session_id, timestamp, attributes.

### REQ-MD-08: HeartbeatStatus Model

The system SHALL provide a model with: agent_id, session_id, turn_count, status, last_seen.

### REQ-MD-09: RepoNode/RepoMap Models

The system SHALL provide models for repository mapping: RepoNode (path, type, signature, dependencies, children) and RepoMap (root, nodes).
