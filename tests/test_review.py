"""
Review Queue Tests — Functional Validation

Does it surface the RIGHT entries at the RIGHT time?
- A 1-day-old decision should NOT be in the queue
- A 7-day-old decision SHOULD be in the queue
- A 14-day-old decision should be OVERDUE
- Archived entries should NEVER appear
- Goals should surface faster than learnings
"""

import pytest
from datetime import date
from tools.parser import Entry
from tools.review import compute_review_queue, REVIEW_CADENCE


def make_entry(id, type="decision", entry_date="2026-03-16", status="active"):
    return Entry(
        id=id, type=type, date=entry_date,
        tags=["test"], status=status,
        title=f"Test {id}",
    )


# Fixed "today" for predictable tests
TODAY = date(2026, 3, 30)


class TestReviewCadence:
    def test_fresh_decision_not_in_queue(self):
        """A 2-day-old decision shouldn't need review yet."""
        entries = [make_entry("DEC-001", entry_date="2026-03-28")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 0

    def test_7day_decision_is_due(self):
        """A 7-day-old decision should be due for review."""
        entries = [make_entry("DEC-001", entry_date="2026-03-23")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 1
        assert items[0].urgency == "due"
        assert items[0].entry.id == "DEC-001"

    def test_14day_decision_is_overdue(self):
        """A 14-day-old decision is 2x past cadence = overdue."""
        entries = [make_entry("DEC-001", entry_date="2026-03-16")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 1
        assert items[0].urgency == "overdue"

    def test_goal_surfaces_faster_than_learning(self):
        """Goals have 3-day cadence, learnings have 30-day."""
        entries = [
            make_entry("GOL-001", type="goal", entry_date="2026-03-26"),      # 4 days old
            make_entry("LRN-001", type="learning", entry_date="2026-03-26"),  # 4 days old
        ]
        items = compute_review_queue(entries, today=TODAY)
        # Goal should be in queue (4d > 3d cadence), learning should not (4d < 30d)
        assert len(items) == 1
        assert items[0].entry.id == "GOL-001"

    def test_mistake_14day_cadence(self):
        """A 14-day-old mistake should be due."""
        entries = [make_entry("MST-001", type="mistake", entry_date="2026-03-16")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 1
        assert items[0].urgency == "due"

    def test_upcoming_shows_near_due(self):
        """Entries within 2 days of due should show as upcoming."""
        # Decision cadence is 7d. Entry is 5d old = within 2d of being due
        entries = [make_entry("DEC-001", entry_date="2026-03-25")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 1
        assert items[0].urgency == "upcoming"


class TestReviewFiltering:
    def test_archived_excluded(self):
        """Archived entries should never appear in review queue."""
        entries = [make_entry("DEC-001", entry_date="2026-03-01", status="archived")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 0

    def test_superseded_excluded(self):
        entries = [make_entry("DEC-001", entry_date="2026-03-01", status="superseded")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 0

    def test_bad_date_excluded(self):
        entries = [make_entry("DEC-001", entry_date="not-a-date")]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 0


class TestReviewOrdering:
    def test_overdue_before_due(self):
        """Overdue items should come before due items."""
        entries = [
            make_entry("DEC-001", entry_date="2026-03-23"),  # 7d = due
            make_entry("DEC-002", entry_date="2026-03-16"),  # 14d = overdue
        ]
        items = compute_review_queue(entries, today=TODAY)
        assert len(items) == 2
        assert items[0].urgency == "overdue"  # DEC-002 first
        assert items[1].urgency == "due"       # DEC-001 second

    def test_multiple_types_sorted(self):
        entries = [
            make_entry("GOL-001", type="goal", entry_date="2026-03-20"),       # 10d, overdue (3d cadence)
            make_entry("DEC-001", entry_date="2026-03-23"),                     # 7d, due
            make_entry("GOL-002", type="goal", entry_date="2026-03-26"),       # 4d, due
        ]
        items = compute_review_queue(entries, today=TODAY)
        assert items[0].entry.id == "GOL-001"  # Overdue comes first
