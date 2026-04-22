"""mem0 — Semantic Memory (Mem0-compatible interface)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.qdrant_client import QdrantClient
from shared.embedding import async_embed, bm25_tokenize
from shared.sanitize import validate_add_memory

config = Config.from_env()
qdrant = QdrantClient(config.qdrant_url, "mem0_memories", config.embedding_dim)
DEFAULT_USER = "default"

mcp = FastMCP("mem0")


async def _embed(text: str) -> list[float]:
    try:
        return await async_embed(text)
    except Exception:
        return []


@mcp.tool()
async def add_memory(content: str, user_id: str = DEFAULT_USER, metadata: str = "") -> str:
    """Add a semantic memory for a user."""
    clean = validate_add_memory(content, user_id)
    vector = await _embed(clean["content"])
    sparse = bm25_tokenize(clean["content"])
    memory_id = f"mem0_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    meta = json.loads(metadata) if metadata.strip().startswith("{") else {}
    await qdrant.ensure_collection(sparse=True)
    await qdrant.upsert(memory_id, vector, {
        "memory_id": memory_id, "user_id": clean["user_id"],
        "content": clean["content"], "metadata": meta,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, sparse=sparse)
    return json.dumps({"status": "added", "memory_id": memory_id}, indent=2)


@mcp.tool()
async def search_memory(query: str, user_id: str = DEFAULT_USER, limit: int = 5) -> str:
    """Search semantic memories for a user."""
    vector = await _embed(query)
    results = await qdrant.search(vector, limit=limit)
    filtered = [r.get("payload", {}) for r in results if r.get("payload", {}).get("user_id") == user_id]
    return json.dumps({"count": len(filtered), "results": filtered}, indent=2, default=str)


@mcp.tool()
async def get_all_memories(user_id: str = DEFAULT_USER, limit: int = 50) -> str:
    """Get all memories for a user."""
    results = await qdrant.scroll({"must": [{"key": "user_id", "match": {"value": user_id}}]}, limit=limit)
    return json.dumps({"count": len(results), "memories": results}, indent=2, default=str)


@mcp.tool()
async def delete_memory(memory_id: str, user_id: str = DEFAULT_USER) -> str:
    """Delete a memory by ID."""
    point = await qdrant.get(memory_id)
    if point and point.get("payload", {}).get("user_id") == user_id:
        await qdrant.upsert(memory_id, [], {"deleted": True, "deleted_at": datetime.now(timezone.utc).isoformat()})
        return json.dumps({"status": "deleted", "memory_id": memory_id}, indent=2)
    return json.dumps({"status": "not_found"}, indent=2)


@mcp.tool()
async def status() -> str:
    """Show mem0 status."""
    ok = await qdrant.health()
    count = await qdrant.count() if ok else 0
    return json.dumps({"daemon": "mem0", "status": "RUNNING", "memories": count}, indent=2)


def register_tools(target_mcp: FastMCP, target_qdrant: QdrantClient, target_config: Config, prefix: str = "") -> None:
    global qdrant, config
    qdrant = QdrantClient(target_config.qdrant_url, "mem0_memories", target_config.embedding_dim)
    config = target_config
    for fn in [add_memory, search_memory, get_all_memories, delete_memory, status]:
        target_mcp.add_tool(fn, name=f"{prefix}{fn.__name__}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
