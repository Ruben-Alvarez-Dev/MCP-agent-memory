# Flows: Consolidation Pipeline

## Purpose

Defines how memories are promoted across layers by autodream on configurable schedules.

## Requirements

### REQ-FC-01: L1 to L2 (Working → Episodic)

The system SHALL group related working memories into episodes every 10 turns.

#### Scenario: Episode creation

- GIVEN 15 working memories in scope "session-abc" and turn_count reaches multiple of 10
- WHEN promote_l1_to_l2 runs
- THEN groups by scope_type/scope_id
- AND creates EPISODE items with combined content for groups with 2+ items
- AND marks originals with promoted_to field

### REQ-FC-02: L2 to L3 (Episodic → Semantic)

The system SHALL extract decisions and patterns from episodes every 1 hour using LLM.

#### Scenario: LLM summarization

- GIVEN 20 episodic memories and 1h elapsed
- WHEN promote_l2_to_l3 runs
- THEN calls LLM with extraction prompt
- AND creates SEMANTIC memory with extracted decisions/entities
- AND falls back to numbered concatenation if no LLM available

### REQ-FC-03: L3 to L4 (Semantic → Consolidated)

The system SHALL create coherent narratives from semantic memories every 24 hours.

#### Scenario: Narrative creation

- GIVEN 10 semantic memories and 24h elapsed
- WHEN promote_l3_to_l4 runs
- THEN calls LLM with narrative prompt
- AND creates CONSOLIDATED NARRATIVE memory

### REQ-FC-04: Dream Cycle

The system SHALL run weekly pattern detection across ALL layers.

#### Scenario: Deep dream

- GIVEN 7d elapsed since last dream
- WHEN dream_cycle runs
- THEN queries WORKING + EPISODIC + SEMANTIC + CONSOLIDATED
- AND calls LLM with pattern detection prompt
- AND creates CONSOLIDATED DREAM memory with confidence=0.4

### REQ-FC-05: State Persistence

The system SHALL persist promotion timestamps and counts to ~/.memory/dream/state.json after every consolidation run.
