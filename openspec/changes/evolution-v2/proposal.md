# Proposal: Evolution V2 (Gentle AI Absorption & Plandex Virtualization)

## Intent
Transform the project into a fully autonomous, Plandex-inspired system by eliminating external dependencies on Gentle AI (Yentl AI) and implementing virtualized context extension up to 2M tokens.

## Scope

### In Scope
- **Skill Absorption**: Replicate and improve all Gentle AI skills into a local `1mcp-agent` skill loader.
- **Native Memory Core**: Replace `engram-facade` with a multi-layered semantic engine.
- **Hierarchical Repo Map**: Implement a Plandex-style recursive index of the entire codebase for context navigation.
- **Sandbox Planning**: Integrate `sequential-thinking` with a virtual `diff` buffer for plan-first execution.
- **Token Pruning**: Add intelligent content reduction for efficient context window usage.

### Out of Scope
- Installing Plandex or using its CLI.
- Porting non-MCP functionality from Gentle AI.

## Capabilities

### New Capabilities
- **hierarchical-context**: Recursive repository navigation and dependency mapping.
- **virtual-sandbox**: Plan-first execution with staging buffers.
- **local-skill-registry**: Autonomous management of agent capabilities.

### Modified Capabilities
- **memory-router**: Upgrade `vk-cache` with hierarchical ranking and token pruning.
- **sequential-thinking**: Integrate with virtual context and sandbox planning.

## Approach
Implement a "Virtual Context" layer in `vk-cache` that uses recursive dependency lookups and a repo-wide index. Move all skill definitions into the local `MCP-servers/skills/` directory and update `1mcp-agent` to prioritize local skills.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `MCP-servers/vk-cache/` | Modified | New hierarchical router and token pruner. |
| `MCP-servers/skills/` | New | Localized agent skill definitions. |
| `1mcp-agent/` | Modified | Skill loader and Plandex-style context management. |
| `shared/retrieval/` | Modified | Recursive lookup logic and profile discovery. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Context Overload | High | Aggressive token pruning and hierarchical summaries. |
| Skill Drift | Med | Scrupulous auditing of original Gentle AI instructions. |
| Engine Perf | Med | Optimize llama.cpp Self-Extend parameters. |

## Rollback Plan
Revert to the `engram-facade` (V1 bridge) and re-enable external Gentle AI repositories.

## Success Criteria
- [ ] Zero external calls to Gentle AI / Yentl AI repositories.
- [ ] Agent can navigate and reason across 100+ files via virtual context.
- [ ] Plans are validated in sandbox before applying to disk.
- [ ] Full SDD compliance for all implementation steps.
