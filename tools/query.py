"""
Engram Query

Search and filter entries:
- By ID, type, tag, project, status
- Full-text search across titles and bodies
- Find entries linking to/from a given entry
"""

from typing import Optional
from .parser import Entry


def by_id(entries: list[Entry], entry_id: str) -> Optional[Entry]:
    """Find an entry by exact ID."""
    for e in entries:
        if e.id == entry_id:
            return e
    return None


def by_type(entries: list[Entry], entry_type: str) -> list[Entry]:
    """Filter entries by type."""
    return [e for e in entries if e.type == entry_type]


def by_tag(entries: list[Entry], tag: str) -> list[Entry]:
    """Filter entries that have a specific tag."""
    return [e for e in entries if tag in e.tags]


def by_project(entries: list[Entry], project: str) -> list[Entry]:
    """Filter entries by project."""
    return [e for e in entries if e.project == project]


def by_status(entries: list[Entry], status: str) -> list[Entry]:
    """Filter entries by status."""
    return [e for e in entries if e.status == status]


def search(entries: list[Entry], query: str) -> list[Entry]:
    """Full-text search across titles and bodies (case-insensitive)."""
    q = query.lower()
    results = []
    for e in entries:
        if q in e.title.lower() or q in e.body.lower() or q in e.id.lower():
            results.append(e)
    return results


def linking_to(entries: list[Entry], target_id: str) -> list[Entry]:
    """Find entries that link TO the given entry (backlinks)."""
    return [e for e in entries if target_id in e.links]


def linked_from(entries: list[Entry], source_id: str) -> list[Entry]:
    """Find entries that the given entry links TO (forward links)."""
    source = by_id(entries, source_id)
    if not source:
        return []
    return [e for e in entries if e.id in source.links]


def render_entry_list(entries: list[Entry], show_body: bool = False) -> str:
    """Render a list of entries as text."""
    if not entries:
        return "No entries found."

    lines = []
    for e in entries:
        status_icon = {"active": "+", "superseded": "~", "archived": "-", "stale": "?"}.get(e.status, " ")
        tags_str = ", ".join(e.tags)
        lines.append(f"  [{status_icon}] {e.id}: {e.title}")
        lines.append(f"      type={e.type}  date={e.date}  tags=[{tags_str}]")
        if e.links:
            lines.append(f"      links: {', '.join(e.links)}")
        if show_body and e.body:
            # Show first 2 lines of body
            body_preview = "\n".join(e.body.split("\n")[:3])
            lines.append(f"      {body_preview}")
        lines.append("")

    return "\n".join(lines)
