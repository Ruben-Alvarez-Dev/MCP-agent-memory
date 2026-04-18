# shared/llm Specification

## Purpose

LLM abstraction layer with multiple backends. Used by autodream for summarization during consolidation, and by retrieval for intent classification.

## Requirements

### REQ-LL-01: Get LLM Backend

The system SHALL return the first available LLM backend from configured options.

#### Scenario: Ollama available

- GIVEN Ollama running at localhost:11434
- WHEN get_llm called
- AND returns OllamaBackend instance

### REQ-LL-02: Classify Intent

The system SHALL deterministically classify query intent without LLM calls (<0.1ms).

#### Scenario: Code query

- GIVEN query="fix bug in auth.py" and session_type="dev"
- WHEN classify_intent called
- AND returns QueryIntent with intent_type, entities, scope, needs_external, needs_ranking flags

### REQ-LL-03: QueryIntent Model

The system SHALL provide: intent_type, entities (list), scope, time_window, needs_external, needs_ranking, needs_consolidation.

## Backends

| Backend | Class | Endpoint |
|---------|-------|----------|
| ollama | OllamaBackend | localhost:11434/api/chat |
| lmstudio | LMStudioBackend | localhost:1234/v1/chat/completions |
| llama_cpp | LlamaCppBackend | Managed subprocess |
