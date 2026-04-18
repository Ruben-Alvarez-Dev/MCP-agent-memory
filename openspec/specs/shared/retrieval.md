# shared/retrieval Specification

## Purpose

Smart retrieval router. Classifies intent, selects profile, runs parallel retrieval from
Qdrant + Engram + mem0, fuses results with Reciprocal Rank Fusion, applies repo proximity
ranking, deduplicates, prunes, and packs into a bounded ContextPack.

## Requirements

### REQ-RT-01: Retrieve

The system SHALL accept a query and return a ContextPack within token budget.

#### Scenario: Dev profile code query

- GIVEN query="fix auth bug in main.py", session_type="dev", token_budget=4000
- WHEN retrieve called
- AND classifies intent as code_lookup via classify_intent
- AND selects "dev" RetrievalProfile
- AND queries Qdrant (dense + sparse), Engram, mem0 in parallel
- AND fuses with RRF, ranks with repo proximity boost
- AND deduplicates and prunes to budget
- AND returns ContextPack with sections, total_tokens, metadata

#### Scenario: Empty result set

- GIVEN query matching nothing
- WHEN retrieve called
- AND returns ContextPack with empty sections and total_tokens=0

### REQ-RT-02: Retrieval Profiles

The system SHALL provide 9 built-in profiles with different level weights, top_k, and token budgets.

Profiles: dev, infra, ops, data, docs, security, research, meeting, default.

### REQ-RT-03: Repo Proximity Boost

The system SHALL boost items whose path or dependencies overlap with query entities.

#### Scenario: Close repo item ranks higher

- GIVEN item with metadata.path="pkg/main.py" and query entities=["pkg","main"]
- WHEN ranking runs
- AND item gets proximity boost score > 0

### REQ-RT-04: Get Repo Map

The system SHALL build hierarchical repository map with dependency resolution.

#### Scenario: Python file with imports

- GIVEN query and project_root with Python files using imports
- WHEN get_repo_map called
- AND returns RepoMap with target file node + immediate dependency nodes

### REQ-RT-05: Prune Content

The system SHALL reduce content to fit token budget while preserving structure.

#### Scenario: Python AST pruning

- GIVEN Python source with classes and functions, max_tokens=30
- WHEN prune_content(path="service.py") called
- AND uses AST parser to preserve module docstring, class/function signatures, docstrings
- AND collapses bodies to "..."
- AND for non-Python files uses heuristic fallback

### REQ-RT-06: Index Repository

The system SHALL scan repo files, extract symbols and dependencies, and upsert to Qdrant L2.

#### Scenario: Index Python project

- GIVEN project_root with Python files
- WHEN build_repo_index_points called
- AND creates Qdrant points with layer=2, type="repo_symbol", dense+sparse vectors
- AND includes file nodes, function nodes, and class nodes with signatures and dependencies

## Configuration

9 built-in RetrievalProfile objects with per-level weights and top_k values.
