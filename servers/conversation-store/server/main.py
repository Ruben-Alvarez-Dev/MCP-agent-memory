"""Conversation Store — Thread persistence and search."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.qdrant_client import QdrantClient
from shared.embedding import async_embed, bm25_tokenize
from shared.sanitize import validate_save_conversation

config = Config.from_env()
qdrant = QdrantClient(config.qdrant_url, "conversations", config.embedding_dim)

mcp = FastMCP("conversation-store")


async def _embed(text: str) -> list[float]:
    try:
        return await async_embed(text)
    except Exception:
        return []


@mcp.tool()
async def save_conversation(thread_id: str, messages_json: str, summary: str = "") -> str:
    """Save a conversation thread with messages and optional summary."""
    clean = validate_save_conversation(thread_id, messages_json)
    text = summary or str(clean["messages"][:500])
    vector = await _embed(text)
    sparse = bm25_tokenize(text)
    await qdrant.ensure_collection(sparse=True)
    await qdrant.upsert(clean["thread_id"], vector, {
        "thread_id": clean["thread_id"], "messages": clean["messages"],
        "summary": summary, "created_at": datetime.now(timezone.utc).isoformat(),
    }, sparse=sparse)
    return json.dumps({"status": "saved", "thread_id": clean["thread_id"]}, indent=2)


@mcp.tool()
async def get_conversation(thread_id: str) -> str:
    """Retrieve a conversation thread by ID."""
    point = await qdrant.get(thread_id)
    if point:
        return json.dumps(point.get("payload", {}), indent=2, default=str)
    return json.dumps({"status": "not_found", "thread_id": thread_id}, indent=2)


@mcp.tool()
async def search_conversations(query: str, limit: int = 5) -> str:
    """Search conversations by semantic similarity."""
    vector = await _embed(query)
    results = await qdrant.search(vector, limit=limit)
    return json.dumps({"count": len(results), "results": [r.get("payload", {}) for r in results]}, indent=2, default=str)


@mcp.tool()
async def list_threads(limit: int = 20) -> str:
    """List recent conversation threads."""
    results = await qdrant.scroll(limit=limit)
    return json.dumps({"count": len(results), "threads": results}, indent=2, default=str)


@mcp.tool()
async def status() -> str:
    """Show conversation store status."""
    ok = await qdrant.health()
    count = await qdrant.count() if ok else 0
    return json.dumps({"daemon": "conversation-store", "status": "RUNNING", "threads": count}, indent=2)


def register_tools(target_mcp: FastMCP, target_qdrant: QdrantClient, target_config: Config, prefix: str = "") -> None:
    global qdrant, config
    qdrant = QdrantClient(target_config.qdrant_url, "conversations", target_config.embedding_dim)
    config = target_config
    for fn in [save_conversation, get_conversation, search_conversations, list_threads, status]:
        target_mcp.add_tool(fn, name=f"{prefix}{fn.__name__}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
