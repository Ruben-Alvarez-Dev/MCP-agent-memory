#!/bin/bash
# Start Qdrant vector store for MCP-agent-memory
ulimit -n 10240
export MALLOC_CONF="background_thread:false,narenas:1"
ROOT="/Users/ruben/MCP-servers/MCP-agent-memory"
cd "$ROOT"
mkdir -p storage snapshots
exec "$ROOT/bin/qdrant" --config-path "$ROOT/bin/config.yaml"
