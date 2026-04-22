"""Unified MCP Memory Server — Single entry point for all memory services.

Consolidates automem, autodream, vk-cache, conversation-store, mem0, engram,
and sequential-thinking into ONE MCP server with prefixed tool names.

Uses public API only — no private _tool_manager access.
Each module's register_tools() function handles tool registration.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.qdrant_client import QdrantClient
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP-agent-memory")
config = Config.from_env()
qdrant = QdrantClient(config.qdrant_url, config.qdrant_collection, config.embedding_dim)

# ── Register all module tools via public API ────────────────────

_loaded = []
_failed = []

_MODULES = [
    ("automem",             "automem/"),
    ("autodream",           "autodream/"),
    ("vk_cache",            "vk-cache/"),
    ("conversation_store",  "conversation-store/"),
    ("mem0",                "mem0/"),
    ("engram",              "engram/"),
    ("sequential_thinking", "sequential-thinking/"),
]

for import_name, dir_name, prefix in [(n, d, f"{n}_") for n, d in _MODULES]:
    try:
        import importlib.util
        mod_path = BASE_DIR / dir_name / "server" / "main.py"
        if not mod_path.exists():
            _failed.append((import_name, f"not found: {mod_path}"))
            continue
        spec = importlib.util.spec_from_file_location(import_name, str(mod_path))
        if not spec or not spec.loader:
            _failed.append((import_name, "bad spec"))
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[import_name] = mod
        spec.loader.exec_module(mod)
        if not hasattr(mod, "register_tools"):
            _failed.append((import_name, "no register_tools()"))
            continue
        mod.register_tools(mcp, qdrant, config, prefix=prefix)
        count = len(mcp._tool_manager._tools) - sum(t for _, t in _loaded)
        _loaded.append((import_name, len(mcp._tool_manager._tools)))
    except Exception as e:
        _failed.append((import_name, str(e)))

_total = len(mcp._tool_manager._tools)
_status_lines = []
_prev = 0
for name, total in _loaded:
    _status_lines.append(f"  ✓ {name}: {total - _prev} tools")
    _prev = total
_status_lines += [f"  ✗ {n}: {e}" for n, e in _failed]
STATUS_REPORT = (
    f"Unified Memory Server\n"
    f"  Modules: {len(_loaded)}/{len(_MODULES)} loaded\n"
    f"  Tools:   {_total} registered\n"
    + "\n".join(_status_lines)
)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
