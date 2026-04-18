# context7-proxy Specification

## Purpose

Transparent proxy to the remote Context7 MCP API for up-to-date documentation retrieval.
Forwards JSON-RPC tool calls to `https://mcp.context7.com/mcp`. No local storage.

## Requirements

### REQ-C7-01: Resolve Library ID

The system SHALL forward library name resolution requests to Context7 upstream.

#### Scenario: Resolve known library

- GIVEN query="how to use React hooks" and libraryName="react"
- WHEN resolve_library_id called
- AND forwards to upstream Context7 API
- AND returns library ID, name, description, snippet count

#### Scenario: Unknown library

- GIVEN libraryName that doesn't exist
- WHEN resolve_library_id called
- AND returns empty results from upstream

### REQ-C7-02: Query Documentation

The system SHALL fetch documentation from Context7 using a resolved library ID.

#### Scenario: Valid query

- GIVEN libraryId="/facebook/react" and query="useState hook"
- WHEN query_docs called
- AND forwards to upstream
- AND returns relevant documentation snippets

### REQ-C7-03: Status

The system SHALL report upstream Context7 API reachability.

#### Scenario: Upstream reachable

- GIVEN Context7 API responds to health check
- WHEN status called
- AND returns status "OK"

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| Upstream URL | https://mcp.context7.com/mcp | Remote Context7 MCP endpoint |

## Dependencies

- None from shared modules (pure HTTP proxy)
