"""
Query Tests — Functional Validation

Does search actually find what you're looking for?
Does filtering actually exclude what it should?
"""

import pytest
from tools.parser import Entry
from tools.query import (
    by_id, by_type, by_tag, by_project, by_status, by_source,
    search, linking_to, linked_from, render_entry_list,
)


def make_entry(id, type="decision", tags=None, project=None,
               status="active", links=None, title="", body="",
               source="manual"):
    return Entry(
        id=id, type=type, date="2026-03-16",
        tags=tags or ["test"], status=status,
        links=links or [], project=project,
        source=source, title=title, body=body,
    )


@pytest.fixture
def entries():
    return [
        make_entry("DEC-001", tags=["architecture", "python"],
                    project="engram", title="File-per-entry design",
                    body="Each entry lives in its own file."),
        make_entry("LRN-001", type="learning", tags=["testing"],
                    project="engram", title="Functional tests matter",
                    body="Test behavior not code paths.", links=["DEC-001"]),
        make_entry("MST-001", type="mistake", tags=["process"],
                    project="svx", title="Forgot to validate input",
                    body="The parser accepted malformed data."),
        make_entry("GOL-001", type="goal", tags=["engram"],
                    project="engram", title="Build knowledge system"),
        make_entry("OBS-001", type="observation", tags=["architecture"],
                    status="archived", title="Graph density is low"),
    ]


class TestById:
    def test_finds_existing(self, entries):
        assert by_id(entries, "DEC-001").title == "File-per-entry design"

    def test_returns_none_for_missing(self, entries):
        assert by_id(entries, "GHOST-999") is None


class TestByType:
    def test_filters_decisions(self, entries):
        results = by_type(entries, "decision")
        assert len(results) == 1
        assert results[0].id == "DEC-001"

    def test_no_matches(self, entries):
        assert by_type(entries, "nonexistent") == []


class TestByTag:
    def test_finds_by_tag(self, entries):
        results = by_tag(entries, "architecture")
        assert len(results) == 2  # DEC-001 and OBS-001

    def test_no_match(self, entries):
        assert by_tag(entries, "nonexistent") == []


class TestByProject:
    def test_filters_project(self, entries):
        results = by_project(entries, "engram")
        assert len(results) == 3

    def test_different_project(self, entries):
        results = by_project(entries, "svx")
        assert len(results) == 1
        assert results[0].id == "MST-001"


class TestByStatus:
    def test_active(self, entries):
        results = by_status(entries, "active")
        assert len(results) == 4

    def test_archived(self, entries):
        results = by_status(entries, "archived")
        assert len(results) == 1
        assert results[0].id == "OBS-001"


class TestSearch:
    def test_finds_in_title(self, entries):
        results = search(entries, "file-per-entry")
        assert len(results) == 1
        assert results[0].id == "DEC-001"

    def test_finds_in_body(self, entries):
        results = search(entries, "malformed data")
        assert len(results) == 1
        assert results[0].id == "MST-001"

    def test_case_insensitive(self, entries):
        results = search(entries, "FUNCTIONAL")
        assert len(results) == 1
        assert results[0].id == "LRN-001"

    def test_finds_by_id(self, entries):
        results = search(entries, "MST-001")
        assert len(results) == 1

    def test_no_match(self, entries):
        assert search(entries, "quantum entanglement") == []

    def test_broad_match(self, entries):
        """'entry' appears in DEC-001's title."""
        results = search(entries, "entry")
        assert any(r.id == "DEC-001" for r in results)


class TestLinkQueries:
    def test_linking_to(self, entries):
        """LRN-001 links to DEC-001."""
        results = linking_to(entries, "DEC-001")
        assert len(results) == 1
        assert results[0].id == "LRN-001"

    def test_linked_from(self, entries):
        """DEC-001 is linked from LRN-001."""
        results = linked_from(entries, "LRN-001")
        assert len(results) == 1
        assert results[0].id == "DEC-001"

    def test_no_backlinks(self, entries):
        results = linking_to(entries, "GOL-001")
        assert len(results) == 0

    def test_linked_from_nonexistent(self, entries):
        assert linked_from(entries, "GHOST") == []


class TestBySource:
    def test_filters_manual(self):
        entries = [
            make_entry("DEC-001", source="manual"),
            make_entry("DEC-002", source="scroll"),
            make_entry("LRN-001", type="learning", source="manual"),
        ]
        results = by_source(entries, "manual")
        assert len(results) == 2
        assert all(e.source == "manual" for e in results)

    def test_filters_scroll(self):
        entries = [
            make_entry("DEC-001", source="manual"),
            make_entry("DEC-002", source="scroll"),
            make_entry("LRN-001", type="learning", source="scroll"),
        ]
        results = by_source(entries, "scroll")
        assert len(results) == 2
        assert all(e.source == "scroll" for e in results)

    def test_no_match(self):
        entries = [make_entry("DEC-001", source="manual")]
        assert by_source(entries, "scroll") == []

    def test_default_source_is_manual(self):
        entries = [make_entry("DEC-001")]  # no source specified
        results = by_source(entries, "manual")
        assert len(results) == 1


class TestRender:
    def test_renders_entries(self, entries):
        output = render_entry_list(entries[:2])
        assert "DEC-001" in output
        assert "LRN-001" in output

    def test_empty_list(self):
        assert "No entries" in render_entry_list([])

    def test_shows_source_for_non_manual(self):
        entries = [make_entry("DEC-001", title="Scroll entry", source="scroll")]
        output = render_entry_list(entries)
        assert "source=scroll" in output

    def test_hides_source_for_manual(self):
        entries = [make_entry("DEC-001", title="Manual entry", source="manual")]
        output = render_entry_list(entries)
        assert "source=" not in output
