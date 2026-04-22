"""vk-cache — Unified Retrieval & Context Assembly (L5).

Implements the BIDIRECTIONAL protocol:
  PULL: LLM requests context → returns ContextPack
  PUSH: System detects need → sends ContextReminder
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.qdrant_client import QdrantClient
from shared.models import ContextPack, ContextReminder, ContextSource, MemoryLayer
from shared.embedding import async_embed
from shared.retrieval import retrieve as smart_retrieve, get_repo_map, prune_content
from shared.sanitize import validate_request_context, validate_push_reminder, sanitize_text

config = Config.from_env()
qdrant = QdrantClient(config.qdrant_url, config.qdrant_collection, config.embedding_dim)

_reminders_path = Path(config.reminders_path) if config.reminders_path else Path("")
_reminders_path.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("vk-cache")


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _save_reminder(reminder: ContextReminder) -> None:
    (_reminders_path / f"{reminder.reminder_id}.json").write_text(reminder.model_dump_json(indent=2))


def _get_active_reminders(agent_id: str) -> list[ContextReminder]:
    reminders = []
    for f in _reminders_path.glob("*.json"):
        data = json.loads(f.read_text())
        reminders.append(ContextReminder(**data))
    return reminders


@mcp.tool()
async def request_context(query: str, agent_id: str = "default", intent: str = "answer", token_budget: int = 8000, scopes: str = "", mode: str = "standard") -> str:
    """LLM requests context. Returns a ContextPack with smart routing."""
    clean = validate_request_context(query, intent)
    session_map = {"answer": "dev", "plan": "dev", "review": "dev", "debug": "ops", "study": "docs"}
    pack = await smart_retrieve(query=clean["query"], session_type=session_map.get(clean["intent"], "dev"), token_budget=token_budget)
    sources = [ContextSource(scope=s.get("source", ""), layer=s.get("level", 0), mem_type="", score=s.get("confidence", 0), content_preview=s.get("content", "")[:500]) for s in pack.sections]
    parts = [f"[{s.get('source', '?')}] (conf={s.get('confidence', 0):.2f}): {s.get('content', '')[:200]}" for s in pack.sections]
    legacy = ContextPack(request_id="", query=clean["query"], sources=sources, summary="\n".join(parts) or "No context found", token_estimate=pack.total_tokens, reason=f"smart_retrieve:{pack.profile}")
    return json.dumps({"context_pack": legacy.model_dump(mode="json"), "injection_text": legacy.to_injection_text()}, indent=2)


@mcp.tool()
async def check_reminders(agent_id: str = "default") -> str:
    """Check pending context reminders."""
    reminders = _get_active_reminders(agent_id)
    result = [{"reminder_id": r.reminder_id, "reason": r.reason, "pack": r.pack.to_injection_text()} for r in reminders]
    return json.dumps({"agent_id": agent_id, "reminders": result, "count": len(result)}, indent=2)


@mcp.tool()
async def push_reminder(query: str, reason: str = "relevant_to_current_task", agent_id: str = "default") -> str:
    """System pushes a context reminder to the LLM."""
    clean = validate_push_reminder(query, agent_id)
    vector = await async_embed(clean["query"])
    results = await qdrant.search(vector, limit=5, score_threshold=config.vk_min_score)
    sources = [ContextSource(scope=f"{r.get('payload', {}).get('scope_type', '')}/{r.get('payload', {}).get('scope_id', '')}", layer=r.get("payload", {}).get("layer", 0), mem_type=r.get("payload", {}).get("type", ""), score=r.get("score", 0), content_preview=r.get("payload", {}).get("content", "")[:500]) for r in results]
    summary = "\n".join(f"[{s.layer}] [{s.score:.2f}] {s.content_preview}" for s in sources) or "No context found"
    pack = ContextPack(request_id="", query=clean["query"], sources=sources, summary=summary, token_estimate=_estimate_tokens(summary), reason=reason)
    reminder = ContextReminder(pack=pack, reason=reason)
    _save_reminder(reminder)
    return json.dumps({"status": "reminder_pushed", "reminder_id": reminder.reminder_id, "sources": len(sources)}, indent=2)


@mcp.tool()
async def dismiss_reminder(reminder_id: str) -> str:
    """Dismiss a reminder."""
    path = _reminders_path / f"{reminder_id}.json"
    if path.exists():
        path.unlink()
        return json.dumps({"status": "dismissed"}, indent=2)
    return json.dumps({"status": "not_found"}, indent=2)


@mcp.tool()
async def detect_context_shift(current_query: str, previous_query: str = "", agent_id: str = "default") -> str:
    """Detect if conversation context has shifted domains."""
    if not previous_query:
        return json.dumps({"shift_detected": False}, indent=2)
    try:
        v1, v2 = await async_embed(current_query), await async_embed(previous_query)
        dot = sum(a * b for a, b in zip(v1, v2))
        sim = dot / (math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(a*a for a in v2))) if v1 and v2 else 0
    except Exception:
        sim = 0.0
    shifted = sim < 0.7
    result = {"shift_detected": shifted, "similarity": round(sim, 4)}
    if shifted:
        vector = await async_embed(current_query)
        results = await qdrant.search(vector, limit=5)
        result["new_context"] = str(len(results)) + " sources found"
    return json.dumps(result, indent=2)


@mcp.tool()
async def status() -> str:
    """Show vk-cache router status."""
    q_ok = await qdrant.health()
    return json.dumps({"daemon": "vk-cache", "status": "RUNNING", "qdrant": "OK" if q_ok else "DOWN", "active_reminders": len(list(_reminders_path.glob("*.json")))}, indent=2)


def register_tools(target_mcp: FastMCP, target_qdrant: QdrantClient, target_config: Config, prefix: str = "") -> None:
    global qdrant, config
    qdrant = target_qdrant
    config = target_config
    for fn in [request_context, check_reminders, push_reminder, dismiss_reminder, detect_context_shift, status]:
        target_mcp.add_tool(fn, name=f"{prefix}{fn.__name__}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
