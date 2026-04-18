# autodream Specification

## Purpose

Consolidation & dream daemon. Promotes memories across layers on configurable schedules.
Uses LLM for summarization when available, falls back to numbered concatenation.

## Requirements

### REQ-AD-01: Run Consolidation Pipeline

The system SHALL run L1→L2→L3→L4 promotion pipeline, respecting schedules unless forced.

#### Scenario: No promotion due

- GIVEN turn_count < PROMOTE_L1_TO_L2 threshold and no time thresholds met
- WHEN consolidate(force=False) called
- THEN increments turn_count in state
- AND returns results array with "Skipped — not due" entries

#### Scenario: Force consolidation

- GIVEN force=True
- WHEN consolidate called
- THEN runs ALL promotion stages regardless of schedule
- AND saves updated state to ~/.memory/dream/state.json

### REQ-AD-02: L1 to L2 Promotion (Working → Episodic)

The system SHALL group working memories by scope+topic into episodes when threshold met.

#### Scenario: Group related memories

- GIVEN 10+ working memories in same scope, turn_count % 10 == 0
- WHEN promote_l1_to_l2 runs
- THEN groups memories by scope_type/scope_id key
- AND creates MemoryItem layer=EPISODIC per group with combined content
- AND updates original items with promoted_to field

### REQ-AD-03: L2 to L3 Promotion (Episodic → Semantic)

The system SHALL extract decisions, entities, and patterns from episodes using LLM.

#### Scenario: LLM available

- GIVEN episodes exist and 1h threshold met and LLM is available
- WHEN promote_l2_to_l3 runs
- THEN calls LLM with extraction prompt
- AND creates MemoryItem layer=SEMANTIC with LLM summary
- AND stores dense embedding of summary in Qdrant

#### Scenario: LLM unavailable

- GIVEN episodes exist but no LLM backend available
- WHEN promote_l2_to_l3 runs
- THEN falls back to numbered concatenation of episode contents
- AND still creates SEMANTIC memory item with fallback summary

### REQ-AD-04: L3 to L4 Promotion (Semantic → Consolidated)

The system SHALL create coherent narratives from semantic memories.

#### Scenario: Narrative creation

- GIVEN semantic memories exist and 24h threshold met
- WHEN promote_l3_to_l4 runs
- THEN calls LLM with narrative prompt
- AND creates MemoryItem layer=CONSOLIDATED, type=NARRATIVE

### REQ-AD-05: Dream Cycle

The system SHALL run weekly pattern detection across ALL layers.

#### Scenario: Deep dream

- GIVEN 7d threshold met and memories exist across layers
- WHEN dream() called
- THEN queries WORKING + EPISODIC + SEMANTIC + CONSOLIDATED layers
- AND calls LLM with pattern detection prompt
- AND creates MemoryItem layer=CONSOLIDATED, type=DREAM

#### Scenario: Not due

- GIVEN last_dream timestamp < 7d ago
- WHEN dream() called
- AND returns "Skipped — not due for dream cycle"

### REQ-AD-06: Retrieve Layer Memories

The system SHALL return L3 and L4 memories on demand.

#### Scenario: Get consolidated with scope filter

- GIVEN consolidated memories exist
- WHEN get_consolidated(scope="frontend") called
- THEN returns only L4 memories matching scope_id="frontend"

### REQ-AD-07: Daemon Status

The system SHALL report schedule configuration and current state.

#### Scenario: Status check

- GIVEN daemon is running
- WHEN status() called
- AND returns schedule with all 4 promotion intervals in human-readable format
- AND returns current state (turns, timestamps, counts)

## Consolidation Schedule

| Transition | Default Trigger | Env Var |
|------------|----------------|---------|
| L1 → L2 | Every 10 turns | DREAM_PROMOTE_L1 |
| L2 → L3 | Every 3600s (1h) | DREAM_PROMOTE_L2 |
| L3 → L4 | Every 86400s (24h) | DREAM_PROMOTE_L3 |
| Dream | Every 604800s (7d) | DREAM_PROMOTE_L4 |

## Storage

| Target | Path | Format |
|--------|------|--------|
| Qdrant | `automem` collection | Same as automem server |
| State | `~/.memory/dream/state.json` | JSON with timestamps and counts |

## Dependencies

- `shared.models`: MemoryItem, MemoryLayer, MemoryScope, MemoryType
- `shared.llm`: get_llm (Ollama/LMStudio/llama.cpp backends)
- `shared.embedding`: get_embedding
- Qdrant (HTTP)
