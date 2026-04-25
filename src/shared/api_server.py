"""
Backpack HTTP API — Lightweight sidecar for plugin-to-server communication.

Runs alongside the MCP stdio server in a background thread.
Plugin hooks call these endpoints via fetch() to trigger automatic memory
operations without involving the LLM.

Architecture:
    OpenCode hooks → fetch() → http://127.0.0.1:8890/api/* → Python functions → Qdrant

Uses stdlib http.server + threading — same pattern as observe.py dashboard.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable

logger = logging.getLogger("agent-memory.api")

# ── Module-level function references ─────────────────────────────────
# Set by start_api_server() before the HTTP server starts.
# These point to the SAME functions registered as MCP tools — zero duplication.

_ingest_event_fn: Callable | None = None
_automem_heartbeat_fn: Callable | None = None
_autodream_heartbeat_fn: Callable | None = None
_save_conversation_fn: Callable | None = None
_consolidate_fn: Callable | None = None
_request_context_fn: Callable | None = None

# Persistent event loop for the API thread.
# asyncio.run() closes the loop after each call — that breaks subsequent calls.
# Instead, we create one loop per thread and reuse it.
_event_loop: asyncio.AbstractEventLoop | None = None


def _run_async(coro: Any) -> Any:
    """Run an async coroutine on the thread's persistent event loop."""
    global _event_loop
    if _event_loop is None:
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop.run_until_complete(coro)


class _ApiHandler(BaseHTTPRequestHandler):
    """Thin HTTP handler that delegates to MCP tool functions."""

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json_response(200, {
                "status": "ok",
                "endpoints": [
                    "POST /api/ingest-event",
                    "POST /api/heartbeat",
                    "POST /api/heartbeat-dream",
                    "POST /api/save-conversation",
                    "POST /api/consolidate",
                    "POST /api/request-context",
                ],
            })
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self) -> None:
        body = self._read_body()
        if body is None:
            return

        try:
            if self.path == "/api/ingest-event" and _ingest_event_fn:
                result = _run_async(_ingest_event_fn(**body))
                self._json_response(200, self._serialize(result))

            elif self.path == "/api/heartbeat" and _automem_heartbeat_fn:
                result = _run_async(_automem_heartbeat_fn(**body))
                self._json_response(200, self._serialize(result))

            elif self.path == "/api/heartbeat-dream" and _autodream_heartbeat_fn:
                result = _run_async(_autodream_heartbeat_fn(**body))
                self._json_response(200, self._serialize(result))

            elif self.path == "/api/save-conversation" and _save_conversation_fn:
                result = _run_async(_save_conversation_fn(**body))
                self._json_response(200, self._serialize(result))

            elif self.path == "/api/consolidate" and _consolidate_fn:
                result = _run_async(_consolidate_fn(**body))
                self._json_response(200, self._serialize(result))

            elif self.path == "/api/request-context" and _request_context_fn:
                result = _run_async(_request_context_fn(**body))
                self._json_response(200, self._serialize(result))

            else:
                self._json_response(404, {"error": f"not found: {self.path}"})

        except Exception as e:
            logger.warning("API error on %s: %s", self.path, e)
            self._json_response(500, {"error": str(e)})

    def do_OPTIONS(self) -> None:
        """CORS preflight support."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── Helpers ──────────────────────────────────────────────────

    def _read_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw)
        except Exception as e:
            self._json_response(400, {"error": f"invalid body: {e}"})
            return None

    def _json_response(self, code: int, data: Any) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _serialize(self, result: Any) -> Any:
        """Handle Pydantic models, dicts, and plain values."""
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result
        return {"result": str(result)}

    def log_message(self, format: str, *args: Any) -> None:
        # Silence access logs — too noisy for every tool call
        pass


def start_api_server(
    ingest_event_fn: Callable,
    automem_heartbeat_fn: Callable,
    autodream_heartbeat_fn: Callable,
    save_conversation_fn: Callable,
    consolidate_fn: Callable,
    request_context_fn: Callable | None = None,
    port: int | None = None,
) -> HTTPServer:
    """Start the HTTP API server in a background thread.

    Call BEFORE mcp.run(transport="stdio") which blocks the main thread.

    Args:
        ingest_event_fn: automem.ingest_event function
        automem_heartbeat_fn: automem.heartbeat function
        autodream_heartbeat_fn: autodream.heartbeat function
        save_conversation_fn: conversation_store.save_conversation function
        consolidate_fn: autodream.consolidate function
        request_context_fn: vk_cache.request_context function (optional)
        port: Port to listen on (default: AUTOMEM_API_PORT env var or 8890)

    Returns:
        The HTTPServer instance (for testing / graceful shutdown).
    """
    global _ingest_event_fn, _automem_heartbeat_fn, _autodream_heartbeat_fn
    global _save_conversation_fn, _consolidate_fn, _request_context_fn

    _ingest_event_fn = ingest_event_fn
    _automem_heartbeat_fn = automem_heartbeat_fn
    _autodream_heartbeat_fn = autodream_heartbeat_fn
    _save_conversation_fn = save_conversation_fn
    _consolidate_fn = consolidate_fn
    _request_context_fn = request_context_fn

    if port is None:
        port = int(os.environ.get("AUTOMEM_API_PORT", "8890"))

    server = HTTPServer(("127.0.0.1", port), _ApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="backpack-api")
    thread.start()
    logger.info("Backpack API listening on http://127.0.0.1:%d", port)
    return server
