"""AutoDream — Consolidation & Dream Daemon.

Promotes memory between layers:
  Every N turns:    L1 → L2 (working → episodic)
  Every hour:       L2 → L3 (episodic → semantic)
  Nightly / idle:   L3 → L4 (semantic → consolidated)
  Weekly:           Dream cycle, pattern detection
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.qdrant_client import QdrantClient
from shared.models import MemoryItem, MemoryLayer, MemoryScope, MemoryType
from shared.llm import get_llm
from shared.embedding import async_embed

config = Config.from_env()
qdrant = QdrantClient(config.qdrant_url, config.qdrant_collection, config.embedding_dim)

DREAM_PATH = Path(config.dream_path) if config.dream_path else Path("")
_state_path = DREAM_PATH / "state.json"
_state_path.parent.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("autodream")


def _load_state() -> dict:
    if _state_path.exists():
        return json.loads(_state_path.read_text())
    return {"last_promote_l1_l2": 0, "last_promote_l2_l3": 0, "last_promote_l3_l4": 0, "last_dream": 0, "turn_count": 0, "total_consolidated": 0, "total_dreams": 0}

def _save_state(state: dict) -> None:
    _state_path.write_text(json.dumps(state, indent=2))


async def _embed(text: str) -> list[float]:
    try:
        return await async_embed(text)
    except Exception:
        return []


async def _summarize(texts: list[str], prompt: str = "") -> str:
    content = "\n---\n".join(texts[:20])
    if not prompt:
        prompt = "Synthesize the following memories into a concise summary. Preserve key decisions, patterns, and facts.\n\n"
    try:
        llm = get_llm()
        if llm.is_available():
            resp = llm.ask(prompt + content, max_tokens=512, temperature=0.3)
            if resp.strip():
                return resp.strip()
    except Exception:
        pass
    return "\n".join(f"[{i+1}] {t[:200]}" for i, t in enumerate(texts[:10]))


async def _promote_l1_l2(state: dict) -> str | None:
    if state["turn_count"] - state.get("last_promote_l1_l2", 0) < config.dream_promote_l1:
        return None
    working = await qdrant.scroll({"must": [{"key": "layer", "match": {"value": 1}}]}, limit=100)
    if not working:
        return None
    groups: dict[str, list] = {}
    for m in working:
        key = f"{m.get('scope_type', '')}/{m.get('scope_id', '')}"
        groups.setdefault(key, []).append(m)
    episodes = []
    for scope_key, items in groups.items():
        if len(items) < 2:
            continue
        combined = "\n".join(f"- {m['content']}" for m in items[:10])
        avg_imp = sum(m.get("importance", 0) for m in items) / len(items)
        ep = MemoryItem(layer=MemoryLayer.EPISODIC, scope_type=items[0].get("scope_type", MemoryScope.AGENT), scope_id=items[0].get("scope_id", "system"), type=MemoryType.EPISODE, content=f"Episode ({len(items)} events):\n{combined}", importance=avg_imp, confidence=0.7)
        vector = await _embed(ep.content) or [0.0] * config.embedding_dim
        await qdrant.upsert(ep.memory_id, vector, ep.model_dump(mode="json"))
        for m in items:
            existing = await qdrant.get(m["memory_id"])
            if existing:
                payload = existing.get("payload", {})
                payload["promoted_to"] = ep.memory_id
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
                await qdrant.upsert(m["memory_id"], existing.get("vector", []), payload)
        episodes.append(ep.memory_id)
    state["last_promote_l1_l2"] = state.get("turn_count", 0)
    return f"Created {len(episodes)} episodes" if episodes else None


async def _promote_l2_l3(state: dict, now: float) -> str | None:
    if now - state.get("last_promote_l2_l3", 0) < config.dream_promote_l2:
        return None
    episodes = await qdrant.scroll({"must": [{"key": "layer", "match": {"value": 2}}]}, limit=50)
    if not episodes:
        return None
    summary = await _summarize([e.get("content", "") for e in episodes], "Extract key decisions, entities, and reusable patterns from these episodes.\n\n")
    sem = MemoryItem(layer=MemoryLayer.SEMANTIC, scope_type=MemoryScope.AGENT, scope_id="consolidated", type=MemoryType.DECISION, content=f"Consolidated from {len(episodes)} episodes:\n\n{summary}", importance=0.8, confidence=0.75)
    vector = await _embed(summary)
    await qdrant.upsert(sem.memory_id, vector, sem.model_dump(mode="json"))
    state["last_promote_l2_l3"] = now
    state["total_consolidated"] = state.get("total_consolidated", 0) + 1
    return f"Consolidated {len(episodes)} episodes into semantic memory"


async def _promote_l3_l4(state: dict, now: float) -> str | None:
    if now - state.get("last_promote_l3_l4", 0) < config.dream_promote_l3:
        return None
    semantic = await qdrant.scroll({"must": [{"key": "layer", "match": {"value": 3}}]}, limit=30)
    if not semantic:
        return None
    narrative = await _summarize([s.get("content", "") for s in semantic], "Write a coherent narrative from these memory fragments. What has been learned?\n\n")
    item = MemoryItem(layer=MemoryLayer.CONSOLIDATED, scope_type=MemoryScope.AGENT, scope_id="narrative", type=MemoryType.NARRATIVE, content=narrative, importance=0.9, confidence=0.6)
    vector = await _embed(narrative)
    await qdrant.upsert(item.memory_id, vector, item.model_dump(mode="json"))
    state["last_promote_l3_l4"] = now
    state["total_consolidated"] = state.get("total_consolidated", 0) + 1
    return "Created consolidated narrative"


@mcp.tool()
async def heartbeat(agent_id: str = "default", turn_count: int = 1) -> str:
    """Signal that the agent is alive. Triggers auto-consolidation if thresholds met."""
    state = _load_state()
    state["turn_count"] = state.get("turn_count", 0) + turn_count
    now = datetime.now(timezone.utc).timestamp()
    results = []
    for fn in [_promote_l1_l2, lambda s: _promote_l2_l3(s, now), lambda s: _promote_l3_l4(s, now)]:
        r = await fn(state)
        if r:
            results.append(r)
    if results:
        _save_state(state)
    return json.dumps({"status": "ok", "total_turns": state["turn_count"], "results": results or ["No consolidation due"]}, indent=2)


@mcp.tool()
async def consolidate(force: bool = False) -> str:
    """Run consolidation across all layers."""
    state = _load_state()
    state["turn_count"] = state.get("turn_count", 0) + 1
    now = datetime.now(timezone.utc).timestamp()
    results = []
    if force:
        state["last_promote_l1_l2"] = 0
        state["last_promote_l2_l3"] = 0
        state["last_promote_l3_l4"] = 0
    for fn in [_promote_l1_l2, lambda s: _promote_l2_l3(s, now), lambda s: _promote_l3_l4(s, now)]:
        r = await fn(state)
        if r:
            results.append(r)
    _save_state(state)
    return json.dumps({"status": "consolidation complete", "forced": force, "results": results}, indent=2)


@mcp.tool()
async def dream() -> str:
    """Trigger a deep dream cycle — pattern detection across all layers."""
    state = _load_state()
    now = datetime.now(timezone.utc).timestamp()
    if now - state.get("last_dream", 0) < config.dream_promote_l4:
        return json.dumps({"status": "Skipped — not due"}, indent=2)
    all_mem = []
    for layer in [MemoryLayer.WORKING, MemoryLayer.EPISODIC, MemoryLayer.SEMANTIC, MemoryLayer.CONSOLIDATED]:
        all_mem.extend(await qdrant.scroll({"must": [{"key": "layer", "match": {"value": layer.value}}]}, limit=30))
    if not all_mem:
        return json.dumps({"status": "No memories to dream about"}, indent=2)
    dream_text = await _summarize([m.get("content", "") for m in all_mem[:15]], "You are dreaming about everything you've learned. Find deep patterns and insights.\n\n")
    item = MemoryItem(layer=MemoryLayer.CONSOLIDATED, scope_type=MemoryScope.AGENT, scope_id="dream", type=MemoryType.DREAM, content=f"Dream:\n\n{dream_text}", importance=0.5, confidence=0.4)
    vector = await _embed(dream_text)
    await qdrant.upsert(item.memory_id, vector, item.model_dump(mode="json"))
    state["last_dream"] = now
    state["total_dreams"] = state.get("total_dreams", 0) + 1
    _save_state(state)
    return json.dumps({"status": "Dream cycle complete", "total_dreams": state["total_dreams"]}, indent=2)


@mcp.tool()
async def status() -> str:
    """Show AutoDream daemon status."""
    state = _load_state()
    return json.dumps({"daemon": "AutoDream", "status": "RUNNING", "state": state}, indent=2)


@mcp.tool()
async def get_consolidated(scope: str = "") -> str:
    """Get consolidated memories (L4)."""
    mems = await qdrant.scroll({"must": [{"key": "layer", "match": {"value": 4}}]}, limit=20)
    return json.dumps({"layer": "L4_CONSOLIDATED", "count": len(mems), "memories": mems}, indent=2, default=str)


@mcp.tool()
async def get_semantic(scope: str = "") -> str:
    """Get semantic memories (L3)."""
    mems = await qdrant.scroll({"must": [{"key": "layer", "match": {"value": 3}}]}, limit=20)
    return json.dumps({"layer": "L3_SEMANTIC", "count": len(mems), "memories": mems}, indent=2, default=str)


def register_tools(target_mcp: FastMCP, target_qdrant: QdrantClient, target_config: Config, prefix: str = "") -> None:
    global qdrant, config
    qdrant = target_qdrant
    config = target_config
    target_mcp.add_tool(heartbeat, name=f"{prefix}heartbeat")
    target_mcp.add_tool(consolidate, name=f"{prefix}consolidate")
    target_mcp.add_tool(dream, name=f"{prefix}dream")
    target_mcp.add_tool(status, name=f"{prefix}status")
    target_mcp.add_tool(get_consolidated, name=f"{prefix}get_consolidated")
    target_mcp.add_tool(get_semantic, name=f"{prefix}get_semantic")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
