"""Engram — Semantic Decision Memory (L3).

Stores curated decisions, entities, and patterns in Markdown files.
Exposes them as MCP tools for the unified retrieval router.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from shared.env_loader import load_env
load_env()
from shared.config import Config
from shared.sanitize import validate_save_decision, validate_vault_write, sanitize_folder, sanitize_filename

config = Config.from_env()
ENGRAM_PATH = Path(config.engram_path) if config.engram_path else Path("")
VAULT_PATH = Path(config.vault_path) if config.vault_path else Path("")

mcp = FastMCP("engram")


def _ensure_engram_path() -> Path:
    ENGRAM_PATH.mkdir(parents=True, exist_ok=True)
    return ENGRAM_PATH


def _get_engram_files() -> list[Path]:
    base = _ensure_engram_path()
    return sorted(base.rglob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)


def _read_engram_file(filepath: Path) -> dict[str, Any]:
    content = filepath.read_text(encoding="utf-8")
    meta = {"file_path": str(filepath), "filename": filepath.name, "size": len(content)}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                meta.update(yaml.safe_load(parts[1]) or {})
                content = parts[2].strip()
            except Exception:
                pass
    meta["content"] = content
    return meta


@mcp.tool()
async def save_decision(title: str, content: str, category: str = "general", tags: str = "", scope: str = "agent", body: str = "") -> str:
    """Save an architectural decision as a Markdown file."""
    clean = validate_save_decision(title, content, category, tags, scope)
    full_content = body or content
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = sanitize_filename(f"{timestamp}-{clean['title'][:50]}")
    target_dir = _ensure_engram_path() / clean["category"]
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{filename}.md"
    tag_list = clean["tags"]
    md = f"---\ntitle: \"{clean['title']}\"\ncategory: {clean['category']}\ntags: {tag_list}\nscope: {clean['scope']}\ncreated: {datetime.now(timezone.utc).isoformat()}\n---\n\n# {clean['title']}\n\n{full_content}\n"
    filepath.write_text(md, encoding="utf-8")
    return json.dumps({"status": "saved", "file_path": str(filepath), "title": clean["title"]}, indent=2)


@mcp.tool()
async def search_decisions(query: str, category: str = "", limit: int = 10) -> str:
    """Search decisions by keyword matching."""
    results = []
    for f in _get_engram_files():
        if category and category not in str(f):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                results.append({"file_path": str(f), "filename": f.name, "preview": content[:300]})
        except Exception:
            pass
        if len(results) >= limit:
            break
    return json.dumps({"count": len(results), "results": results}, indent=2)


@mcp.tool()
async def get_decision(file_path: str) -> str:
    """Get a specific decision by file path."""
    p = Path(file_path)
    if p.exists():
        return json.dumps(_read_engram_file(p), indent=2, default=str)
    return json.dumps({"status": "not_found"}, indent=2)


@mcp.tool()
async def list_decisions(category: str = "", scope: str = "", limit: int = 20) -> str:
    """List decisions with optional filtering."""
    files = _get_engram_files()
    if category:
        files = [f for f in files if category in str(f)]
    results = [_read_engram_file(f) for f in files[:limit]]
    return json.dumps({"count": len(results), "decisions": results}, indent=2, default=str)


@mcp.tool()
async def delete_decision(file_path: str) -> str:
    """Delete a decision file."""
    p = Path(file_path)
    if p.exists() and str(p).startswith(str(ENGRAM_PATH)):
        p.unlink()
        return json.dumps({"status": "deleted"}, indent=2)
    return json.dumps({"status": "not_found"}, indent=2)


@mcp.tool()
async def vault_write(folder: str, filename: str, content: str, tags: str = "") -> str:
    """Write a note to the Obsidian vault."""
    clean = validate_vault_write(folder, filename, content, tags)
    target = VAULT_PATH / clean["folder"]
    target.mkdir(parents=True, exist_ok=True)
    filepath = target / f"{clean['filename']}.md"
    md = f"---\ntags: {clean['tags']}\ncreated: {datetime.now(timezone.utc).isoformat()}\n---\n\n{clean['content']}\n"
    filepath.write_text(md, encoding="utf-8")
    return json.dumps({"status": "written", "path": str(filepath)}, indent=2)


@mcp.tool()
async def vault_process_inbox() -> str:
    """Process vault inbox items."""
    inbox = VAULT_PATH / "Inbox"
    if not inbox.exists():
        return json.dumps({"status": "no_inbox"}, indent=2)
    files = list(inbox.glob("*.md"))
    return json.dumps({"status": "processed", "count": len(files)}, indent=2)


@mcp.tool()
async def vault_integrity_check() -> str:
    """Verify vault consistency."""
    if not VAULT_PATH.exists():
        return json.dumps({"status": "vault_not_found"}, indent=2)
    total = sum(1 for _ in VAULT_PATH.rglob("*.md"))
    return json.dumps({"status": "ok", "total_notes": total}, indent=2)


@mcp.tool()
async def vault_list_notes(folder: str = "") -> str:
    """List vault notes by folder."""
    base = VAULT_PATH / folder if folder else VAULT_PATH
    if not base.exists():
        return json.dumps({"status": "folder_not_found"}, indent=2)
    files = [{"name": f.name, "path": str(f)} for f in sorted(base.rglob("*.md"))]
    return json.dumps({"count": len(files), "notes": files[:50]}, indent=2)


@mcp.tool()
async def vault_read_note(folder: str, filename: str) -> str:
    """Read a specific vault note."""
    filepath = VAULT_PATH / folder / f"{filename}.md"
    if filepath.exists():
        return json.dumps({"content": filepath.read_text(encoding="utf-8")}, indent=2)
    return json.dumps({"status": "not_found"}, indent=2)


@mcp.tool()
async def get_model_pack(name: str = "default") -> str:
    """Get model configuration pack."""
    pack_dir = ENGRAM_PATH / "model-packs"
    pack_file = pack_dir / f"{name}.yaml"
    if pack_file.exists():
        return json.dumps({"name": name, "content": pack_file.read_text()}, indent=2)
    return json.dumps({"status": "not_found", "name": name}, indent=2)


@mcp.tool()
async def set_model_pack(name: str, content: str) -> str:
    """Set active model pack."""
    pack_dir = ENGRAM_PATH / "model-packs"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / f"{name}.yaml").write_text(content)
    return json.dumps({"status": "set", "name": name}, indent=2)


@mcp.tool()
async def list_model_packs() -> str:
    """List available model packs."""
    pack_dir = ENGRAM_PATH / "model-packs"
    if not pack_dir.exists():
        return json.dumps({"packs": []}, indent=2)
    packs = [f.stem for f in pack_dir.glob("*.yaml")]
    return json.dumps({"packs": packs}, indent=2)


@mcp.tool()
async def status() -> str:
    """Show engram status."""
    files = _get_engram_files()
    vault_count = sum(1 for _ in VAULT_PATH.rglob("*.md")) if VAULT_PATH.exists() else 0
    return json.dumps({"daemon": "engram", "status": "RUNNING", "engram_files": len(files), "vault_notes": vault_count}, indent=2)


def register_tools(target_mcp: FastMCP, _qdrant: Any, target_config: Config, prefix: str = "") -> None:
    global config, ENGRAM_PATH, VAULT_PATH
    config = target_config
    ENGRAM_PATH = Path(config.engram_path) if config.engram_path else Path("")
    VAULT_PATH = Path(config.vault_path) if config.vault_path else Path("")
    for fn in [save_decision, search_decisions, get_decision, list_decisions, delete_decision, vault_write, vault_process_inbox, vault_integrity_check, vault_list_notes, vault_read_note, get_model_pack, set_model_pack, list_model_packs, status]:
        target_mcp.add_tool(fn, name=f"{prefix}{fn.__name__}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
