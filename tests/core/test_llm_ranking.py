import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.llm.config import rank_by_relevance

# --- Unit Tests (SPEC-4.1: LLM Ranking Robust to JSON) ---

def test_rank_by_relevance_returns_list():
    """rank_by_relevance accepts query + items and returns a list."""
    items = [
        {"content": "About dogs", "score": 0.8},
        {"content": "About cats", "score": 0.9},
        {"content": "A story about a cat chasing a dog", "score": 0.7},
    ]

    # When no LLM available, falls back to original order
    ranked = rank_by_relevance("Tell me about felines", items)

    assert isinstance(ranked, list)
    assert len(ranked) == 3
    # Each item should still be a dict with content
    assert all("content" in item for item in ranked)


def test_rank_by_relevance_empty_items():
    """Empty items list returns empty list."""
    ranked = rank_by_relevance("query", [])
    assert ranked == []


def test_rank_by_relevance_preserves_all_items():
    """All items are preserved, just reordered."""
    items = [
        {"content": "A"},
        {"content": "B"},
        {"content": "C"},
    ]
    ranked = rank_by_relevance("query", items)
    assert len(ranked) == 3
    contents = {item["content"] for item in ranked}
    assert contents == {"A", "B", "C"}


def test_rank_by_relevance_top_k():
    """top_k parameter limits the output."""
    items = [{"content": f"item{i}"} for i in range(20)]
    ranked = rank_by_relevance("query", items, top_k=5)
    assert len(ranked) <= 5
