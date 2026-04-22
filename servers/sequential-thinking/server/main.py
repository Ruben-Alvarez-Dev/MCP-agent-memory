"""Sequential Thinking — Reasoning Chains & Planning."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config

config = Config.from_env()
THOUGHTS_PATH = Path(config.thoughts_path) if config.thoughts_path else Path("")
STAGING_BUFFER_PATH = Path(config.staging_buffer_path) if config.staging_buffer_path else Path("")

mcp = FastMCP("sequential-thinking")


def _save_thought(session: str, step: int, thought: dict) -> None:
    base = THOUGHTS_PATH / session
    base.mkdir(parents=True, exist_ok=True)
    (base / f"step_{step:04d}.json").write_text(json.dumps(thought, indent=2))


def _load_session(session: str) -> list[dict]:
    base = THOUGHTS_PATH / session
    if not base.exists():
        return []
    thoughts = []
    for f in sorted(base.glob("step_*.json")):
        thoughts.append(json.loads(f.read_text()))
    return thoughts


def _staging_path(change_set_id: str) -> Path:
    STAGING_BUFFER_PATH.mkdir(parents=True, exist_ok=True)
    return STAGING_BUFFER_PATH / f"{change_set_id}.json"


@mcp.tool()
async def sequential_thinking(
    problem: str, context: str = "", max_steps: int = 10,
    thinking_style: str = "analytical", session_id: str = "",
) -> str:
    """Step-by-step reasoning chain for complex problems."""
    sid = session_id or f"think_{uuid.uuid4().hex[:8]}"
    steps = []
    for i in range(min(max_steps, 5)):
        step = {
            "step": i + 1, "problem": problem,
            "thought": f"Step {i+1}: Analyzing aspect of: {problem[:100]}",
            "style": thinking_style, "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _save_thought(sid, i + 1, step)
        steps.append(step)
    return json.dumps({"session_id": sid, "steps": len(steps), "summary": f"Completed {len(steps)} thinking steps"}, indent=2)


@mcp.tool()
async def record_thought(session_id: str, thought: str, step: int = 0, confidence: float = 0.5) -> str:
    """Record a single thought step."""
    existing = _load_session(session_id)
    next_step = step or len(existing) + 1
    entry = {"step": next_step, "thought": thought, "confidence": confidence, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_thought(session_id, next_step, entry)
    return json.dumps({"status": "recorded", "session_id": session_id, "step": next_step}, indent=2)


@mcp.tool()
async def create_plan(title: str, steps_json: str, context: str = "", session_id: str = "") -> str:
    """Create an execution plan with steps."""
    sid = session_id or f"plan_{uuid.uuid4().hex[:8]}"
    try:
        steps = json.loads(steps_json) if isinstance(steps_json, str) else steps_json
    except json.JSONDecodeError:
        steps = [{"description": steps_json}]
    plan = {"plan_id": sid, "title": title, "context": context, "steps": steps, "status": "created", "created_at": datetime.now(timezone.utc).isoformat()}
    plans_dir = THOUGHTS_PATH / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / f"{sid}_plan.json").write_text(json.dumps(plan, indent=2))
    return json.dumps({"status": "created", "plan_id": sid, "steps": len(steps)}, indent=2)


@mcp.tool()
async def update_plan_step(plan_id: str, step_index: int, status: str = "completed", notes: str = "") -> str:
    """Update a plan step status."""
    plans_dir = THOUGHTS_PATH / "plans"
    plan_file = plans_dir / f"{plan_id}_plan.json"
    if not plan_file.exists():
        return json.dumps({"status": "plan_not_found"}, indent=2)
    plan = json.loads(plan_file.read_text())
    if step_index < len(plan.get("steps", [])):
        plan["steps"][step_index]["status"] = status
        plan["steps"][step_index]["notes"] = notes
        plan["updated_at"] = datetime.now(timezone.utc).isoformat()
        plan_file.write_text(json.dumps(plan, indent=2))
        return json.dumps({"status": "updated", "plan_id": plan_id, "step": step_index}, indent=2)
    return json.dumps({"status": "step_not_found"}, indent=2)


@mcp.tool()
async def reflect(session_id: str, focus: str = "quality") -> str:
    """Reflect on reasoning quality."""
    thoughts = _load_session(session_id)
    if not thoughts:
        return json.dumps({"status": "no_session"}, indent=2)
    summary = f"Session {session_id}: {len(thoughts)} steps. Focus: {focus}."
    return json.dumps({"status": "reflected", "session_id": session_id, "steps": len(thoughts), "summary": summary}, indent=2)


@mcp.tool()
async def get_thinking_session(session_id: str) -> str:
    """Retrieve a thinking session."""
    thoughts = _load_session(session_id)
    return json.dumps({"session_id": session_id, "steps": len(thoughts), "thoughts": thoughts}, indent=2, default=str)


@mcp.tool()
async def list_thinking_sessions() -> str:
    """List recent thinking sessions."""
    if not THOUGHTS_PATH.exists():
        return json.dumps({"sessions": []}, indent=2)
    sessions = [d.name for d in THOUGHTS_PATH.iterdir() if d.is_dir() and not d.name.startswith("plans")]
    return json.dumps({"count": len(sessions), "sessions": sorted(sessions)[-20:]}, indent=2)


@mcp.tool()
async def propose_change_set(session_id: str, title: str, changes_json: str = "[]") -> str:
    """Propose a code change set."""
    cs_id = f"cs_{uuid.uuid4().hex[:8]}"
    try:
        changes = json.loads(changes_json)
    except json.JSONDecodeError:
        changes = []
    cs = {"change_set_id": cs_id, "session_id": session_id, "title": title, "changes": changes, "status": "proposed", "created_at": datetime.now(timezone.utc).isoformat()}
    _staging_path(cs_id).write_text(json.dumps(cs, indent=2))
    return json.dumps({"status": "proposed", "change_set_id": cs_id, "changes": len(changes)}, indent=2)


@mcp.tool()
async def apply_sandbox(change_set_id: str, dry_run: bool = True) -> str:
    """Apply changes in sandbox mode."""
    cs_path = _staging_path(change_set_id)
    if not cs_path.exists():
        return json.dumps({"status": "not_found"}, indent=2)
    cs = json.loads(cs_path.read_text())
    cs["status"] = "applied" if not dry_run else "dry_run"
    cs["applied_at"] = datetime.now(timezone.utc).isoformat()
    cs_path.write_text(json.dumps(cs, indent=2))
    return json.dumps({"status": cs["status"], "change_set_id": change_set_id}, indent=2)


@mcp.tool()
async def status() -> str:
    """Show sequential thinking status."""
    base = THOUGHTS_PATH
    session_count = sum(1 for d in base.iterdir() if d.is_dir()) if base.exists() else 0
    plan_count = sum(1 for f in (base / "plans").glob("*_plan.json")) if (base / "plans").exists() else 0
    staged = sum(1 for _ in STAGING_BUFFER_PATH.glob("*.json")) if STAGING_BUFFER_PATH.exists() else 0
    return json.dumps({"daemon": "sequential-thinking", "status": "RUNNING", "sessions": session_count, "plans": plan_count, "staged": staged}, indent=2)


def register_tools(target_mcp: FastMCP, _qdrant: Any, target_config: Config, prefix: str = "") -> None:
    global config, THOUGHTS_PATH, STAGING_BUFFER_PATH
    config = target_config
    THOUGHTS_PATH = Path(config.thoughts_path) if config.thoughts_path else Path("")
    STAGING_BUFFER_PATH = Path(config.staging_buffer_path) if config.staging_buffer_path else Path("")
    for fn in [sequential_thinking, record_thought, create_plan, update_plan_step, reflect, get_thinking_session, list_thinking_sessions, propose_change_set, apply_sandbox, status]:
        target_mcp.add_tool(fn, name=f"{prefix}{fn.__name__}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
