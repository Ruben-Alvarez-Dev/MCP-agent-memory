# Tasks: Evolution V2 (Absorbing Gentle AI & Plandex Virtualization)

## Phase 1: Skill Absorption & Foundation

- [x] 1.1 Migrate all Gentle AI skill directories to `MCP-servers/skills/`.
- [x] 1.2 Create `1mcp-agent/src/core/skills/loader.ts` for local skill discovery.
- [x] 1.3 Register `loader.ts` in `1mcp-agent` main entry point.
- [x] 1.4 Create `MCP-servers/shared/models/repo.py` with `RepoNode` Pydantic models.

## Phase 2: Context Virtualization Engine

- [x] 2.1 Implement `MCP-servers/shared/retrieval/pruner.py` with AST-based body collapsing.
- [x] 2.2 Create repository indexing script to populate Qdrant L2 with symbol signatures.
- [x] 2.3 Add `get_repo_map` utility to `shared/retrieval/` to query L2 symbols.

## Phase 3: Recursive Intelligence (vk-cache)

- [x] 3.1 RED: Create test case for recursive dependency lookup in `vk-cache`.
- [x] 3.2 GREEN: Modify `vk-cache/server/main.py` to use `push_reminder` for detected dependencies.
- [x] 3.3 REFACTOR: Optimize `vk-cache` ranking to prioritize "Repo Proximity".

## Phase 4: Virtual Sandbox Execution

- [x] 4.1 Add `STAGING_BUFFER` (L1.5) support to `automem` daemon.
- [x] 4.2 Modify `sequential-thinking/server/main.py` to add `propose_change_set` tool.
- [x] 4.3 Implement `apply_sandbox` tool in `sequential-thinking` to flush staging to disk.

## Phase 5: Verification & Delivery

- [x] 5.1 Write E2E test verifying zero external calls during a complex coding task.
- [x] 5.2 Verify 2M token virtualization by running a "Project Audit" on 100+ files.
- [x] 5.3 Update `docs/SESSION-STATE.md` with V2 architecture and new capabilities.
