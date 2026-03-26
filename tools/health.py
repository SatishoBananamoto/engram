"""
Engram Health Score

Single composite score (0-100) that answers: "Is this knowledge base healthy?"

Dimensions:
- Integrity (40%): validation errors, broken links, duplicates
- Connectivity (30%): graph structure, orphans, clusters, bridges
- Freshness (20%): are entries being reviewed? are they stale?
- Coverage (10%): are all entry types represented?

The score should DROP when the system is degraded.
The score should RISE when problems are fixed.
This is verified by tests that intentionally degrade the system.
"""

from dataclasses import dataclass, field
from .parser import Entry
from .validator import validate
from .graph import find_clusters, find_bridges, find_orphans


@dataclass
class HealthDimension:
    name: str
    score: float  # 0-100
    weight: float
    details: list[str] = field(default_factory=list)


@dataclass
class HealthReport:
    dimensions: list[HealthDimension] = field(default_factory=list)
    entries_count: int = 0

    @property
    def score(self) -> float:
        if not self.dimensions:
            return 0
        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0
        return sum(d.score * d.weight for d in self.dimensions) / total_weight

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 90: return "A"
        if s >= 80: return "B"
        if s >= 70: return "C"
        if s >= 60: return "D"
        return "F"


def score_integrity(entries: list[Entry]) -> HealthDimension:
    """Score based on validation results. Errors = bad."""
    report = validate(entries)
    error_count = len(report.errors)
    warning_count = len(report.warnings)

    details = []

    # Each error costs 20 points, each warning costs 5
    score = max(0, 100 - error_count * 20 - warning_count * 5)
    details.append(f"Errors: {error_count}, Warnings: {warning_count}")

    if error_count == 0 and warning_count == 0:
        details.append("Clean — no issues found")

    return HealthDimension("Integrity", score, 0.40, details)


def score_connectivity(entries: list[Entry]) -> HealthDimension:
    """Score based on graph structure.

    Uses coverage-based scoring: what % of entries are in the largest
    connected component? A 45-entry cluster + 4 orphans is very different
    from 6 equal-sized islands — the score should reflect that.
    """
    if not entries:
        return HealthDimension("Connectivity", 0, 0.30, ["No entries"])

    n = len(entries)
    details = []

    # Coverage: % of entries in the largest connected component
    clusters = find_clusters(entries)
    largest = max(len(c) for c in clusters)
    coverage = largest / n
    base = coverage * 100
    details.append(f"Clusters: {len(clusters)} (largest: {largest}/{n})")

    # Bridges: structural fragility within the connected portion
    bridges = find_bridges(entries)
    bridge_penalty = len(bridges) * 3
    details.append(f"Bridges: {len(bridges)}")

    # Orphans: completely disconnected entries (worse than small clusters)
    # Already penalized by reducing coverage, but extra drag because
    # zero connections is worse than being in a small group
    orphans = find_orphans(entries)
    goal_ids = {e.id for e in entries if e.type == "goal"}
    real_orphans = [o for o in orphans if o not in goal_ids]
    orphan_penalty = len(real_orphans) * 2
    details.append(f"Orphans: {len(real_orphans)}")

    score = max(0, base - orphan_penalty - bridge_penalty)

    return HealthDimension("Connectivity", score, 0.30, details)


def score_freshness(entries: list[Entry]) -> HealthDimension:
    """Score based on staleness. Old active entries = bad."""
    from datetime import date, timedelta

    if not entries:
        return HealthDimension("Freshness", 0, 0.20, ["No entries"])

    today = date.today()
    stale_count = 0
    active_count = 0

    for entry in entries:
        if entry.status != "active":
            continue
        active_count += 1
        try:
            entry_date = date.fromisoformat(entry.date)
            if (today - entry_date).days > 90:
                stale_count += 1
        except (ValueError, TypeError):
            stale_count += 1  # Bad date = stale

    if active_count == 0:
        return HealthDimension("Freshness", 100, 0.20, ["No active entries to check"])

    stale_pct = stale_count / active_count
    score = max(0, 100 - stale_pct * 100)

    details = [f"Active: {active_count}, Stale (>90d): {stale_count}"]

    return HealthDimension("Freshness", score, 0.20, details)


def score_coverage(entries: list[Entry]) -> HealthDimension:
    """Score based on type diversity. Using all 5 types = good."""
    if not entries:
        return HealthDimension("Coverage", 0, 0.10, ["No entries"])

    types_present = {e.type for e in entries}
    expected_types = {"decision", "learning", "mistake", "observation", "goal"}
    coverage = len(types_present & expected_types) / len(expected_types) * 100

    missing = expected_types - types_present
    details = [f"Types present: {len(types_present)}/5"]
    if missing:
        details.append(f"Missing: {', '.join(sorted(missing))}")

    return HealthDimension("Coverage", coverage, 0.10, details)


def compute_health(entries: list[Entry]) -> HealthReport:
    """Compute full health report."""
    report = HealthReport(entries_count=len(entries))
    report.dimensions.append(score_integrity(entries))
    report.dimensions.append(score_connectivity(entries))
    report.dimensions.append(score_freshness(entries))
    report.dimensions.append(score_coverage(entries))
    return report


def render_health(entries: list[Entry]) -> str:
    """Render health report as text."""
    report = compute_health(entries)
    s = report.score
    grade = report.grade

    bar_len = int(s / 2)
    bar = "█" * bar_len + "░" * (50 - bar_len)

    lines = [
        f"Health: {s:.1f}/100 ({grade})",
        f"  [{bar}]",
        f"  Entries: {report.entries_count}",
        "",
    ]

    for dim in report.dimensions:
        lines.append(f"  {dim.name} ({dim.weight:.0%}): {dim.score:.0f}/100")
        for detail in dim.details:
            lines.append(f"    {detail}")

    return "\n".join(lines)
