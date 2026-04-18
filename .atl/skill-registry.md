# PROJECT-MCP-memory-server — Skill Registry

## Active Capabilities
- **Memory Stack**: 6-layer memory pipeline (L0-L5)
- **Agent Orchestration**: Unified 1MCP gateway
- **Local AI**: Bundled llama.cpp engine (GGUF)
- **Persistence**: Hybrid (Engram + Qdrant)

## Project Standards (auto-resolved)

### Python Development
- Use `pydantic` v2 for all data models.
- Prefer `aiohttp` for async HTTP requests.
- Follow `textual` patterns for TUI development.
- Testing: Use `pytest`. Structure tests in `tests/` matching source tree.

### Node.js / TypeScript Development
- Use `@modelcontextprotocol/sdk` for MCP interactions.
- Framework: `express` v5.
- Type Safety: Strict TypeScript. No `any`.
- Testing: Use `vitest`.
- Style: Follow `prettier` and `eslint` configurations in `1mcp-agent/`.

### SDD Workflow
- **Strict TDD Mode**: ACTIVE.
- **Spec Format**: RFC 2119 keywords (MUST, SHALL, SHOULD, MAY).
- **Design Pattern**: Composition over inheritance. Clear layer separation (Bridge/Service/Model).

## User Skills (Auto-detected triggers)

| Skill | Trigger Context | Purpose |
|-------|-----------------|---------|
| sdd-explore | `/sdd-explore` | Investigation & Research |
| sdd-propose | `/sdd-new`, `/sdd-propose` | Change Proposals |
| sdd-spec | `sdd-spec` | Detailed Specifications |
| sdd-design | `sdd-design` | Technical Design |
| sdd-tasks | `sdd-tasks` | Task Breakdown |
| sdd-apply | `/sdd-apply` | Implementation (TDD) |
| sdd-verify | `/sdd-verify` | Validation |
| sdd-archive | `/sdd-archive` | Finalization |
| go-testing | `go test`, `teatest` | Go-specific testing (not used here) |
| skill-creator | `create skill` | Creating new AI capabilities |
