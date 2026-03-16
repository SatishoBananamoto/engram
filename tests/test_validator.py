"""
Validator Tests — Functional Validation

Does the validator actually catch problems?
Each test creates a specific broken scenario and verifies detection.
"""

import pytest
from tools.parser import Entry, ParseError
from tools.validator import (
    check_broken_links,
    check_duplicate_ids,
    check_orphans,
    check_staleness,
    check_supersession,
    check_id_sequence_gaps,
    validate,
    ValidationReport,
)


def make_entry(id, type="decision", date="2026-03-16", tags=None,
               status="active", links=None, supersedes=None, **kwargs):
    """Helper to quickly create test entries."""
    return Entry(
        id=id,
        type=type,
        date=date,
        tags=tags or ["test"],
        status=status,
        links=links or [],
        supersedes=supersedes,
        **kwargs,
    )


# --- Broken Links ---

class TestBrokenLinks:
    def test_catches_broken_link(self):
        entries = [
            make_entry("DEC-001", links=["DEC-999"]),  # DEC-999 doesn't exist
        ]
        issues = check_broken_links(entries)
        assert len(issues) == 1
        assert "DEC-999" in issues[0].message
        assert issues[0].severity == "error"

    def test_valid_links_pass(self):
        entries = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002", links=["DEC-001"]),
        ]
        issues = check_broken_links(entries)
        assert len(issues) == 0

    def test_no_links_is_fine(self):
        entries = [make_entry("DEC-001")]
        issues = check_broken_links(entries)
        assert len(issues) == 0

    def test_multiple_broken_links(self):
        entries = [
            make_entry("DEC-001", links=["GHOST-001", "GHOST-002"]),
        ]
        issues = check_broken_links(entries)
        assert len(issues) == 2


# --- Duplicate IDs ---

class TestDuplicateIds:
    def test_catches_duplicate(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-001"),
        ]
        issues = check_duplicate_ids(entries)
        assert len(issues) == 1
        assert "Duplicate" in issues[0].message

    def test_unique_ids_pass(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-002"),
        ]
        issues = check_duplicate_ids(entries)
        assert len(issues) == 0


# --- Orphans ---

class TestOrphans:
    def test_catches_orphan(self):
        entries = [
            make_entry("DEC-001"),  # No links in or out
            make_entry("DEC-002", links=["DEC-003"]),
            make_entry("DEC-003", links=["DEC-002"]),
        ]
        issues = check_orphans(entries)
        assert len(issues) == 1
        assert issues[0].entry_id == "DEC-001"

    def test_goals_allowed_orphan(self):
        """Goals are root entries — they're allowed to have no links."""
        entries = [
            make_entry("GOL-001", type="goal"),  # No links, but that's OK
        ]
        issues = check_orphans(entries)
        assert len(issues) == 0

    def test_incoming_link_not_orphan(self):
        """If another entry links TO you, you're not an orphan."""
        entries = [
            make_entry("DEC-001"),  # No outgoing links
            make_entry("DEC-002", links=["DEC-001"]),  # But DEC-002 links to DEC-001
        ]
        issues = check_orphans(entries)
        assert len(issues) == 0

    def test_outgoing_link_not_orphan(self):
        entries = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002"),
        ]
        issues = check_orphans(entries)
        assert len(issues) == 0


# --- Staleness ---

class TestStaleness:
    def test_catches_stale_entry(self):
        entries = [
            make_entry("DEC-001", date="2025-01-01"),  # Very old
        ]
        issues = check_staleness(entries, stale_days=90)
        assert len(issues) == 1
        assert "Stale" in issues[0].message

    def test_fresh_entry_passes(self):
        entries = [
            make_entry("DEC-001", date="2026-03-16"),  # Today
        ]
        issues = check_staleness(entries, stale_days=90)
        assert len(issues) == 0

    def test_archived_not_flagged(self):
        """Archived entries shouldn't be flagged as stale."""
        entries = [
            make_entry("DEC-001", date="2020-01-01", status="archived"),
        ]
        issues = check_staleness(entries, stale_days=90)
        assert len(issues) == 0

    def test_superseded_not_flagged(self):
        entries = [
            make_entry("DEC-001", date="2020-01-01", status="superseded"),
        ]
        issues = check_staleness(entries, stale_days=90)
        assert len(issues) == 0

    def test_invalid_date_caught(self):
        entries = [
            make_entry("DEC-001", date="not-a-date"),
        ]
        issues = check_staleness(entries)
        assert len(issues) == 1
        assert "Invalid date" in issues[0].message

    def test_custom_stale_days(self):
        entries = [
            make_entry("DEC-001", date="2026-03-01"),  # 15 days ago
        ]
        # 30 days threshold — should pass
        assert len(check_staleness(entries, stale_days=30)) == 0
        # 10 days threshold — should flag
        assert len(check_staleness(entries, stale_days=10)) == 1


# --- Supersession ---

class TestSupersession:
    def test_catches_superseding_nonexistent(self):
        entries = [
            make_entry("DEC-002", supersedes="DEC-001"),  # DEC-001 doesn't exist
        ]
        issues = check_supersession(entries)
        assert len(issues) == 1
        assert "doesn't exist" in issues[0].message
        assert issues[0].severity == "error"

    def test_catches_unsuperseded_old_entry(self):
        """If you supersede DEC-001, DEC-001 should be marked superseded."""
        entries = [
            make_entry("DEC-001", status="active"),  # Still active!
            make_entry("DEC-002", supersedes="DEC-001"),
        ]
        issues = check_supersession(entries)
        assert len(issues) == 1
        assert "still 'active'" in issues[0].message

    def test_valid_supersession(self):
        entries = [
            make_entry("DEC-001", status="superseded"),
            make_entry("DEC-002", supersedes="DEC-001"),
        ]
        issues = check_supersession(entries)
        assert len(issues) == 0

    def test_orphaned_superseded_entry(self):
        """Superseded entry with no replacement should warn."""
        entries = [
            make_entry("DEC-001", status="superseded"),  # No entry supersedes this
        ]
        issues = check_supersession(entries)
        assert len(issues) == 1
        assert "orphaned" in issues[0].message.lower()

    def test_archived_also_valid(self):
        entries = [
            make_entry("DEC-001", status="archived"),
            make_entry("DEC-002", supersedes="DEC-001"),
        ]
        issues = check_supersession(entries)
        assert len(issues) == 0


# --- ID Sequence Gaps ---

class TestIdSequenceGaps:
    def test_catches_gap(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-003"),  # DEC-002 missing
        ]
        issues = check_id_sequence_gaps(entries)
        assert len(issues) == 1
        assert "DEC-002" in issues[0].message

    def test_no_gap(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-002"),
            make_entry("DEC-003"),
        ]
        issues = check_id_sequence_gaps(entries)
        assert len(issues) == 0

    def test_multiple_prefix_gaps(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-003"),
            make_entry("LRN-001", type="learning"),
            make_entry("LRN-005", type="learning"),
        ]
        issues = check_id_sequence_gaps(entries)
        assert len(issues) == 2  # One gap per prefix

    def test_large_gap_reported(self):
        entries = [
            make_entry("DEC-001"),
            make_entry("DEC-010"),
        ]
        issues = check_id_sequence_gaps(entries)
        assert len(issues) == 1
        assert "through" in issues[0].message  # Should report range


# --- Full Validate ---

class TestValidateFull:
    def test_clean_system(self):
        entries = [
            make_entry("GOL-001", type="goal"),
            make_entry("DEC-001", links=["GOL-001"]),
            make_entry("DEC-002", links=["DEC-001"]),
        ]
        report = validate(entries)
        assert report.is_healthy
        assert report.entries_checked == 3

    def test_unhealthy_system(self):
        entries = [
            make_entry("DEC-001", links=["GHOST-001"]),  # broken link
            make_entry("DEC-001"),  # duplicate
        ]
        report = validate(entries)
        assert not report.is_healthy
        assert len(report.errors) >= 2

    def test_parse_errors_included(self):
        entries = [make_entry("DEC-001")]
        parse_errors = [ParseError("bad.md", "No frontmatter")]
        report = validate(entries, parse_errors=parse_errors)
        assert not report.is_healthy
        assert any("Parse error" in e.message for e in report.errors)
