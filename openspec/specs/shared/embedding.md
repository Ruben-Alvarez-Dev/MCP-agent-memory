# shared/embedding Specification

## Purpose

Unified embedding generation with multiple backends. Generates dense vectors (for semantic search)
and BM25 sparse vectors (for keyword search) for Qdrant storage.

## Requirements

### REQ-EM-01: Get Embedding

The system SHALL generate a dense vector from text using the configured backend.

#### Scenario: llama_cpp backend (default)

- GIVEN text="hello world" and EMBEDDING_BACKEND="llama_cpp"
- WHEN get_embedding called
- AND executes bundled llama-embedding binary with all-MiniLM-L6-v2 model
- AND returns list of EMBEDDING_DIM floats (default 1024)

#### Scenario: http backend

- GIVEN EMBEDDING_BACKEND="http" and EMBEDDING_ENDPOINT set
- WHEN get_embedding called
- AND sends POST to endpoint, returns vector

#### Scenario: noop backend (testing)

- GIVEN EMBEDDING_BACKEND="noop"
- WHEN get_embedding called
- AND returns zero vector of EMBEDDING_DIM dimensions

### REQ-EM-02: BM25 Tokenize

The system SHALL convert text into Qdrant sparse vector format for BM25 keyword search.

#### Scenario: Tokenize text

- GIVEN text="hello world hello"
- WHEN bm25_tokenize called
- AND returns dict with token indices and frequencies suitable for Qdrant sparse_vectors

### REQ-EM-03: Backend Discovery

The system SHALL auto-detect available embedding backends at runtime.

#### Scenario: No llama.cpp binary

- GIVEN llama-embedding binary not found in PATH or engine/
- WHEN get_embedding called
- AND falls back to next available backend or raises error

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| EMBEDDING_BACKEND | llama_cpp | Backend: llama_cpp, http, noop |
| EMBEDDING_DIM | 1024 | Dense vector dimension |
| EMBEDDING_ENDPOINT | — | HTTP backend URL |
| EMBEDDING_MODEL | — | Model name for HTTP backend |
