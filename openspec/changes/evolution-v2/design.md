# Design: Evolution V2 (Absorbing Gentle AI & Plandex Virtualization)

## Technical Approach
Implement a "Virtualized Context Engine" by enhancing `vk-cache` with hierarchical repository mapping and recursive dependency resolution. Replace external Gentle AI dependency with a local Skill Registry managed by `1mcp-agent`.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repository Map | Hierarchical Symbol Index (L2) | Enables 2M-token navigation without full file loads. Uses Qdrant for fast retrieval of signatures. |
| Sandbox Staging | L1.5 Virtual Buffer (JSONL) | Decouples plan generation from disk operations. Allows atomic commits or rollbacks of change sets. |
| Skill Management | Local Manifest Discovery | Eliminates external latency/dependency. Skills are loaded as local MCP servers from `MCP-servers/skills/`. |
| Token Management | AST-based Pruning | Maximizes information density by collapsing irrelevant function bodies during retrieval. |

## Data Flow

    [LLM Agent] <──(PULL Context)──> [vk-cache] <──→ [Repo Map (Qdrant L2)]
         │                              │
    (Plan Step) ──→ [Sequential Thinking] ──→ [Sandbox (L1.5)]
         │                              │
    (Final Apply) ──────────────────────┴──────→ [Local Filesystem]

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `MCP-servers/shared/models/repo.py` | Create | Pydantic models for Hierarchical Repo Map. |
| `MCP-servers/vk-cache/server/main.py` | Modify | Implement `push_reminder` for recursive dependencies. |
| `1mcp-agent/src/core/skills/loader.ts` | Create | Local skill discovery and registration logic. |
| `MCP-servers/shared/retrieval/pruner.py` | Create | Intelligent token pruning using regex/AST patterns. |
| `MCP-servers/sequential-thinking/server/main.py` | Modify | Add `propose_change_set` and `apply_sandbox` tools. |

## Interfaces / Contracts

```python
class RepoNode(BaseModel):
    path: str
    type: str # file | class | function
    signature: str
    dependencies: List[str] # links to other nodes
```

```typescript
interface LocalSkill {
    name: string;
    instructions: string;
    tools: MCPTool[];
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Token Pruner | Test with files > 8k tokens to verify correct body collapsing. |
| Integration | Recursive Lookup | Verify `vk-cache` returns dependencies when a file is requested. |
| E2E | Sandbox Flow | Run full cycle: Create Plan -> Propose to Sandbox -> Apply to Disk -> Verify state. |

## Migration / Rollout
1. **Phase 1**: Port all Gentle AI skill folders to `MCP-servers/skills/`.
2. **Phase 2**: Activate `local-skill-registry` in `1mcp-agent`.
3. **Phase 3**: Implement `hierarchical-context` indexing task.
4. **Phase 4**: Switch `vk-cache` to use the new virtualized engine.

## Open Questions
- [ ] Should we use `tree-sitter` for all languages or start with Python/TypeScript only?
- [ ] How to handle large `diff` buffers in memory without performance hits?
