"""
Integration Tests — End-to-End Validation

Tests the full pipeline: files on disk → parser → module → output.
One test per major feature. These catch wiring bugs that unit tests miss.
"""

import pytest
from pathlib import Path
from tools.parser import load_entries
from tools.validator import validate, render_validation_report
from tools.graph import compute_stats, find_bridges, pagerank, shortest_path
from tools.health import compute_health, render_health
from tools.query import search, by_type, linking_to
from tools.review import compute_review_queue

from datetime import date


ENTRY_TEMPLATE = """---
id: {id}
type: {type}
date: {date}
tags: [{tags}]
status: active
links: [{links}]
project: test
---

# {title}

{body}
"""


@pytest.fixture
def populated_kb(tmp_path):
    """Create a realistic knowledge base on disk."""
    entries_dir = tmp_path / "entries"
    entries_dir.mkdir()

    entries_data = [
        ("GOL-001", "goal", "engram", "", "Build the system", "The main goal."),
        ("DEC-001", "decision", "architecture", "GOL-001", "Use individual files", "Each entry is a file."),
        ("DEC-002", "decision", "testing", "GOL-001, DEC-001", "Test functionally", "Test behavior not syntax."),
        ("LRN-001", "learning", "testing", "DEC-002", "Functional tests work", "They catch real bugs."),
        ("MST-001", "mistake", "parser", "LRN-001, DEC-001", "Tags not validated", "Empty tags were accepted."),
        ("OBS-001", "observation", "architecture", "DEC-001", "Predecessor was bloated", "70 modules for 5K lines."),
    ]

    for id, type, tags, links, title, body in entries_data:
        content = ENTRY_TEMPLATE.format(
            id=id, type=type, date="2026-03-16", tags=tags,
            links=links, title=title, body=body,
        )
        (entries_dir / f"{id}.md").write_text(content)

    return entries_dir


class TestEndToEnd:
    def test_parse_validate_health_pipeline(self, populated_kb):
        """Full pipeline: disk → parse → validate → health score."""
        entries, errors = load_entries(populated_kb)
        assert len(entries) == 6
        assert len(errors) == 0

        report = validate(entries, errors)
        assert report.is_healthy

        health = compute_health(entries)
        assert health.score >= 70
        assert health.grade in ("A", "B", "C")

        # Render should not crash
        rendered = render_health(entries)
        assert "Health:" in rendered
        assert "/100" in rendered

    def test_parse_graph_pipeline(self, populated_kb):
        """Full pipeline: disk → parse → graph analysis."""
        entries, _ = load_entries(populated_kb)

        stats = compute_stats(entries)
        assert stats.total_nodes == 6
        assert stats.total_edges > 0
        assert stats.clusters == 1

        # PageRank should work and produce sensible results
        scores = pagerank(entries)
        assert len(scores) == 6
        # GOL-001 should have high PageRank (most linked to)
        assert scores["GOL-001"] > scores["OBS-001"]

    def test_parse_search_pipeline(self, populated_kb):
        """Full pipeline: disk → parse → search."""
        entries, _ = load_entries(populated_kb)

        # Search by text
        results = search(entries, "functional")
        assert any(r.id == "DEC-002" for r in results)

        # Search by type
        decisions = by_type(entries, "decision")
        assert len(decisions) == 2

        # Backlinks
        backlinks = linking_to(entries, "DEC-001")
        assert len(backlinks) >= 2  # DEC-002 and MST-001 link to it

    def test_parse_validate_catches_broken_link(self, populated_kb):
        """Pipeline catches broken links from real files."""
        # Add an entry with a broken link
        bad_content = ENTRY_TEMPLATE.format(
            id="DEC-099", type="decision", date="2026-03-16",
            tags="test", links="GHOST-999", title="Bad", body="Broken link.",
        )
        (populated_kb / "DEC-099.md").write_text(bad_content)

        entries, errors = load_entries(populated_kb)
        report = validate(entries, errors)
        assert not report.is_healthy
        assert any("GHOST-999" in e.message for e in report.errors)

    def test_health_degrades_with_problems(self, populated_kb):
        """Health score drops when problems are introduced."""
        entries, errors = load_entries(populated_kb)
        clean_health = compute_health(entries).score

        # Add broken entry
        bad_content = ENTRY_TEMPLATE.format(
            id="DEC-099", type="decision", date="2026-03-16",
            tags="test", links="GHOST-999", title="Bad", body="Broken.",
        )
        (populated_kb / "DEC-099.md").write_text(bad_content)

        entries2, errors2 = load_entries(populated_kb)
        broken_health = compute_health(entries2).score

        assert broken_health < clean_health

    def test_shortest_path_through_real_graph(self, populated_kb):
        """Find path between entries in a real knowledge base."""
        entries, _ = load_entries(populated_kb)

        # OBS-001 → DEC-001 → GOL-001 (through links)
        path = shortest_path(entries, "OBS-001", "GOL-001")
        assert path is not None
        assert path[0] == "OBS-001"
        assert path[-1] == "GOL-001"

    def test_review_queue_with_old_entries(self, populated_kb):
        """Review queue surfaces old entries correctly."""
        entries, _ = load_entries(populated_kb)

        # All entries are dated 2026-03-16. If "today" is 2026-03-30,
        # decisions (7d cadence) should be overdue (14d old)
        future = date(2026, 3, 30)
        items = compute_review_queue(entries, today=future)
        assert len(items) > 0
        # At least the decisions should be overdue
        overdue_ids = [i.entry.id for i in items if i.urgency == "overdue"]
        assert "DEC-001" in overdue_ids or "DEC-002" in overdue_ids

    def test_render_validation_report_format(self, populated_kb):
        """Validation report renders properly from real data."""
        entries, errors = load_entries(populated_kb)
        report = validate(entries, errors)
        rendered = render_validation_report(report)
        assert "entries checked" in rendered
        assert "HEALTHY" in rendered
