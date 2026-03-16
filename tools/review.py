"""
Engram Review Queue

Surfaces entries that need attention based on type-specific review cadences.

Not a validator (finds past problems) but a proactive tool (says "look at this today").

Review cadences:
- decision: 7 days  ("did this hold up?")
- mistake:  14 days ("was the prevention effective?")
- goal:     3 days  ("am I closer?")
- learning: 30 days ("still true? can I apply this?")
- observation: 30 days ("has this become a pattern?")
"""

from datetime import date, timedelta
from dataclasses import dataclass
from .parser import Entry


# Days after creation when an entry should be reviewed
REVIEW_CADENCE = {
    "decision": 7,
    "mistake": 14,
    "goal": 3,
    "learning": 30,
    "observation": 30,
}


@dataclass
class ReviewItem:
    entry: Entry
    days_since: int
    review_cadence: int
    urgency: str  # overdue, due, upcoming


def compute_review_queue(entries: list[Entry], today: date = None) -> list[ReviewItem]:
    """Compute which entries need review.

    Returns items sorted by urgency (overdue first, then due, then upcoming).
    """
    if today is None:
        today = date.today()

    items = []
    for entry in entries:
        if entry.status != "active":
            continue

        try:
            entry_date = date.fromisoformat(entry.date)
        except (ValueError, TypeError):
            continue

        days_since = (today - entry_date).days
        cadence = REVIEW_CADENCE.get(entry.type, 30)

        if days_since < 0:
            continue  # Future-dated entry

        # How many review cycles have passed?
        cycles_passed = days_since / cadence if cadence > 0 else 0

        if cycles_passed >= 2:
            urgency = "overdue"
        elif cycles_passed >= 1:
            urgency = "due"
        elif days_since >= cadence - 2:  # Within 2 days of due
            urgency = "upcoming"
        else:
            continue  # Not yet due

        items.append(ReviewItem(
            entry=entry,
            days_since=days_since,
            review_cadence=cadence,
            urgency=urgency,
        ))

    # Sort: overdue first, then due, then upcoming. Within each, oldest first.
    urgency_order = {"overdue": 0, "due": 1, "upcoming": 2}
    items.sort(key=lambda x: (urgency_order[x.urgency], -x.days_since))

    return items


def render_review_queue(entries: list[Entry], today: date = None) -> str:
    """Render the review queue as text."""
    items = compute_review_queue(entries, today)

    if not items:
        return "Review queue: empty — nothing needs attention right now."

    lines = [f"Review queue: {len(items)} item(s) need attention\n"]

    current_urgency = None
    for item in items:
        if item.urgency != current_urgency:
            current_urgency = item.urgency
            label = {"overdue": "OVERDUE", "due": "DUE NOW", "upcoming": "COMING UP"}[current_urgency]
            lines.append(f"  --- {label} ---")

        icon = {"overdue": "!!", "due": ">>", "upcoming": ".."}[item.urgency]
        lines.append(
            f"  [{icon}] {item.entry.id}: {item.entry.title}"
            f"  ({item.days_since}d old, review every {item.review_cadence}d)"
        )

    return "\n".join(lines)
