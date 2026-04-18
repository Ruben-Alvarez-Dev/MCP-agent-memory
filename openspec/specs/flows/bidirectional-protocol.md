# Flows: Bidirectional Context Protocol

## Purpose

Defines how the LLM agent interacts with the memory system via PULL (request context) and PUSH (receive reminders).

## Requirements

### REQ-FP-01: PULL Flow (LLM requests context)

The system SHALL assemble context on demand when the LLM calls request_context.

#### Scenario: Full PULL cycle

- GIVEN LLM needs context for "fix auth bug in user.py"
- WHEN request_context(query="fix auth bug in user.py", intent="answer", token_budget=4000) called
- THEN system classifies intent as code_lookup
- AND selects "dev" retrieval profile
- AND queries Qdrant dense+sparse, Engram filesystem, mem0 in parallel
- AND fuses with Reciprocal Rank Fusion
- AND applies repo proximity ranking
- AND deduplicates at 0.85 similarity threshold
- AND prunes to fit token_budget using AST pruning for Python
- AND returns ContextPack with injection_text ready for LLM prompt

### REQ-FP-02: PUSH Flow (System proactively reminds)

The system SHALL push context reminders when the system detects relevant information.

#### Scenario: Reminder lifecycle

- GIVEN system detects relevant past decision about auth
- WHEN push_reminder(query="auth decision", reason="relevant_to_current_task", agent_id="gentleman") called
- THEN reminder saved to ~/.memory/reminders/{id}.json
- AND agent calls check_reminders(agent_id="gentleman") on next turn
- AND receives pending reminder
- AND calls dismiss_reminder(reminder_id) when processed

### REQ-FP-03: Context Shift Detection

The system SHALL detect when conversation domain changes via embedding cosine similarity.

#### Scenario: Domain change

- GIVEN previous query about "frontend React" and current query about "database migrations"
- WHEN detect_context_shift called
- AND computes cosine similarity < threshold
- AND returns shift_detected=True with domain analysis
