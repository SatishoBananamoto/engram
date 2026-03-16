"""
Engram Validator

Checks the knowledge base for real problems:
- Broken links (entry references a non-existent ID)
- Duplicate IDs
- Orphan entries (no links in or out)
- Stale entries (old + active, need review)
- Schema violations caught by parser
- Supersession chains (is the superseded entry actually archived?)
- ID sequence gaps (DEC-001, DEC-003 — where's DEC-002?)

Every check answers: "Is this knowledge base consistent and maintained?"
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from .parser import Entry, ParseError, load_knowledge_base, VALID_TYPES


@dataclass
class Issue:
    """A validation issue."""
    severity: str  # error, warning, info
    entry_id: Optional[str]
    message: str


@dataclass
class ValidationReport:
    """Complete validation result."""
    issues: list[Issue] = field(default_factory=list)
    parse_errors: list[ParseError] = field(default_factory=list)
    entries_checked: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "info"]

    @property
    def is_healthy(self) -> bool:
        return len(self.errors) == 0


def check_broken_links(entries: list[Entry]) -> list[Issue]:
    """Find entries that link to non-existent IDs."""
    known_ids = {e.id for e in entries}
    issues = []
    for entry in entries:
        for link_id in entry.links:
            if link_id not in known_ids:
                issues.append(Issue(
                    severity="error",
                    entry_id=entry.id,
                    message=f"Broken link: references '{link_id}' which doesn't exist",
                ))
    return issues


def check_duplicate_ids(entries: list[Entry]) -> list[Issue]:
    """Find entries with the same ID."""
    id_counts = Counter(e.id for e in entries)
    issues = []
    for entry_id, count in id_counts.items():
        if count > 1:
            issues.append(Issue(
                severity="error",
                entry_id=entry_id,
                message=f"Duplicate ID: '{entry_id}' appears {count} times",
            ))
    return issues


def check_orphans(entries: list[Entry]) -> list[Issue]:
    """Find entries with no incoming or outgoing links."""
    known_ids = {e.id for e in entries}
    # Track which IDs are referenced
    referenced = set()
    has_links = set()
    for entry in entries:
        for link_id in entry.links:
            if link_id in known_ids:
                referenced.add(link_id)
                has_links.add(entry.id)

    issues = []
    for entry in entries:
        if entry.id not in referenced and entry.id not in has_links:
            # Goals are allowed to be orphans (they're roots)
            if entry.type != "goal":
                issues.append(Issue(
                    severity="warning",
                    entry_id=entry.id,
                    message="Orphan entry: no incoming or outgoing links",
                ))
    return issues


def check_staleness(entries: list[Entry], stale_days: int = 90) -> list[Issue]:
    """Find active entries older than stale_days that might need review."""
    issues = []
    today = date.today()
    cutoff = today - timedelta(days=stale_days)

    for entry in entries:
        if entry.status != "active":
            continue
        try:
            entry_date = date.fromisoformat(entry.date)
            if entry_date < cutoff:
                age_days = (today - entry_date).days
                issues.append(Issue(
                    severity="warning",
                    entry_id=entry.id,
                    message=f"Stale: active entry is {age_days} days old — review needed",
                ))
        except (ValueError, TypeError):
            issues.append(Issue(
                severity="warning",
                entry_id=entry.id,
                message=f"Invalid date format: '{entry.date}'",
            ))

    return issues


def check_supersession(entries: list[Entry]) -> list[Issue]:
    """Check that superseded entries are properly archived."""
    known_ids = {e.id for e in entries}
    entry_map = {e.id: e for e in entries}
    issues = []

    for entry in entries:
        if entry.supersedes:
            if entry.supersedes not in known_ids:
                issues.append(Issue(
                    severity="error",
                    entry_id=entry.id,
                    message=f"Supersedes '{entry.supersedes}' which doesn't exist",
                ))
            else:
                old_entry = entry_map[entry.supersedes]
                if old_entry.status not in ("superseded", "archived"):
                    issues.append(Issue(
                        severity="warning",
                        entry_id=entry.id,
                        message=f"Supersedes '{entry.supersedes}' but that entry is still '{old_entry.status}' (should be 'superseded' or 'archived')",
                    ))
    # Reverse check: superseded entries should have a replacement
    superseded_by = {e.supersedes for e in entries if e.supersedes}
    for entry in entries:
        if entry.status == "superseded" and entry.id not in superseded_by:
            issues.append(Issue(
                severity="warning",
                entry_id=entry.id,
                message=f"Marked as 'superseded' but no entry claims to supersede it — orphaned decision",
            ))

    return issues


def check_id_sequence_gaps(entries: list[Entry]) -> list[Issue]:
    """Check for gaps in ID sequences (DEC-001, DEC-003 but no DEC-002)."""
    by_prefix: dict[str, list[int]] = {}
    for entry in entries:
        prefix = entry.prefix
        num = entry.number
        if prefix and num > 0:
            by_prefix.setdefault(prefix, []).append(num)

    issues = []
    for prefix, numbers in by_prefix.items():
        numbers.sort()
        for i in range(len(numbers) - 1):
            if numbers[i + 1] - numbers[i] > 1:
                gap_start = numbers[i] + 1
                gap_end = numbers[i + 1] - 1
                missing = list(range(gap_start, gap_end + 1))
                issues.append(Issue(
                    severity="info",
                    entry_id=None,
                    message=f"ID gap: {prefix}-{missing[0]:03d}" +
                            (f" through {prefix}-{missing[-1]:03d}" if len(missing) > 1 else "") +
                            " missing",
                ))
    return issues


def validate(entries: list[Entry], parse_errors: list[ParseError] = None,
             stale_days: int = 90) -> ValidationReport:
    """Run all validation checks.

    Returns a complete ValidationReport.
    """
    report = ValidationReport(
        parse_errors=parse_errors or [],
        entries_checked=len(entries),
    )

    # Add parse errors as issues too
    for pe in report.parse_errors:
        report.issues.append(Issue(
            severity="error",
            entry_id=None,
            message=f"Parse error in {pe.file_path}: {pe.message}",
        ))

    # Run all checks
    report.issues.extend(check_broken_links(entries))
    report.issues.extend(check_duplicate_ids(entries))
    report.issues.extend(check_orphans(entries))
    report.issues.extend(check_staleness(entries, stale_days))
    report.issues.extend(check_supersession(entries))
    report.issues.extend(check_id_sequence_gaps(entries))

    return report


def render_validation_report(report: ValidationReport) -> str:
    """Render a human-readable validation report."""
    lines = [
        f"Validation: {report.entries_checked} entries checked",
        f"  Errors:   {len(report.errors)}",
        f"  Warnings: {len(report.warnings)}",
        f"  Info:     {len(report.infos)}",
    ]

    if report.errors:
        lines.append("\nERRORS:")
        for issue in report.errors:
            prefix = f"  [{issue.entry_id}]" if issue.entry_id else "  [—]"
            lines.append(f"{prefix} {issue.message}")

    if report.warnings:
        lines.append("\nWARNINGS:")
        for issue in report.warnings:
            prefix = f"  [{issue.entry_id}]" if issue.entry_id else "  [—]"
            lines.append(f"{prefix} {issue.message}")

    if report.infos:
        lines.append("\nINFO:")
        for issue in report.infos:
            prefix = f"  [{issue.entry_id}]" if issue.entry_id else "  [—]"
            lines.append(f"{prefix} {issue.message}")

    status = "HEALTHY" if report.is_healthy else "UNHEALTHY"
    lines.append(f"\nStatus: {status}")

    return "\n".join(lines)
