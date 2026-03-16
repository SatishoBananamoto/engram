"""
Engram MCP Server

Exposes the engram knowledge base as MCP tools that any Claude Code session can use.

Tools:
- engram_health: Get system health score
- engram_validate: Check for problems
- engram_search: Full-text search across entries
- engram_show: Show a specific entry with backlinks
- engram_list: List entries with optional filters
- engram_graph: Graph statistics and top entries
- engram_review: What needs attention today?
- engram_add: Add a new knowledge entry
- engram_path: Find connection path between entries
"""

import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Engram tools
from tools.parser import load_knowledge_base, VALID_TYPES, VALID_STATUSES
from tools.validator import validate, render_validation_report
from tools.health import render_health
from tools.query import (
    search, by_type, by_tag, by_project, by_status,
    by_id, linking_to, render_entry_list,
)
from tools.graph import compute_stats, pagerank, shortest_path
from tools.review import render_review_queue


ROOT = Path(__file__).resolve().parent
ENTRIES_DIR = ROOT / "entries"

mcp = FastMCP("engram", instructions="""
Engram is a structured knowledge system that tracks decisions, learnings, mistakes,
observations, and goals across projects. Use these tools to query, add to, and
maintain the knowledge base.

Entry types:
- decision (DEC): A choice with reasoning
- learning (LRN): Something discovered through doing
- mistake (MST): What broke, why, how to prevent
- observation (OBS): A pattern noticed
- goal (GOL): What we're trying to achieve
""")


def _load():
    """Load entries from disk."""
    return load_knowledge_base(ROOT)


@mcp.tool()
def engram_health() -> str:
    """Get the system health score (0-100). Shows integrity, connectivity, freshness, and coverage."""
    entries, _ = _load()
    return render_health(entries)


@mcp.tool()
def engram_validate() -> str:
    """Check the knowledge base for problems: broken links, duplicates, orphans, stale entries."""
    entries, errors = _load()
    report = validate(entries, errors)
    return render_validation_report(report)


@mcp.tool()
def engram_search(query: str) -> str:
    """Search entries by text. Searches titles, bodies, and IDs (case-insensitive)."""
    entries, _ = _load()
    results = search(entries, query)
    if not results:
        return f"No entries found for '{query}'."
    return f"Found {len(results)} result(s) for '{query}':\n\n{render_entry_list(results)}"


@mcp.tool()
def engram_show(entry_id: str) -> str:
    """Show a specific entry with full details and backlinks."""
    entries, _ = _load()
    entry_id = entry_id.upper()
    entry = by_id(entries, entry_id)

    if not entry:
        return f"Entry '{entry_id}' not found."

    lines = [
        f"{entry.id}: {entry.title}",
        f"Type: {entry.type}  Status: {entry.status}  Date: {entry.date}",
        f"Tags: {', '.join(entry.tags)}",
    ]
    if entry.project:
        lines.append(f"Project: {entry.project}")
    if entry.confidence:
        lines.append(f"Confidence: {entry.confidence}")
    if entry.links:
        lines.append(f"Links: {', '.join(entry.links)}")
    if entry.supersedes:
        lines.append(f"Supersedes: {entry.supersedes}")

    lines.append("")
    lines.append(entry.body)

    backlinks = linking_to(entries, entry_id)
    if backlinks:
        lines.append("\n--- Linked by ---")
        for bl in backlinks:
            lines.append(f"  {bl.id}: {bl.title}")

    return "\n".join(lines)


@mcp.tool()
def engram_list(filter_type: str = "") -> str:
    """List entries. Optional filter: 'decisions', 'learnings', 'mistakes', 'observations', 'goals', 'tag:X', 'project:X', 'status:X'."""
    entries, _ = _load()

    if filter_type:
        ft = filter_type.lower()
        type_map = {
            "decisions": "decision", "decision": "decision",
            "learnings": "learning", "learning": "learning",
            "mistakes": "mistake", "mistake": "mistake",
            "observations": "observation", "observation": "observation",
            "goals": "goal", "goal": "goal",
        }
        if ft in type_map:
            entries = by_type(entries, type_map[ft])
        elif ft.startswith("tag:"):
            entries = by_tag(entries, ft[4:])
        elif ft.startswith("project:"):
            entries = by_project(entries, ft[8:])
        elif ft.startswith("status:"):
            entries = by_status(entries, ft[7:])
        else:
            return f"Unknown filter: {filter_type}. Use: decisions, learnings, mistakes, observations, goals, tag:X, project:X, status:X"

    return render_entry_list(entries)


@mcp.tool()
def engram_graph() -> str:
    """Graph statistics: nodes, edges, density, clusters, bridges, and top entries by PageRank."""
    entries, _ = _load()
    stats = compute_stats(entries)

    lines = [
        f"Graph: {stats.total_nodes} nodes, {stats.total_edges} edges",
        f"  Density: {stats.density:.2%}",
        f"  Clusters: {stats.clusters}",
    ]

    if stats.bridges:
        lines.append(f"  Bridges: {', '.join(stats.bridges)}")
    else:
        lines.append(f"  Bridges: none")

    if stats.orphans:
        lines.append(f"  Orphans: {', '.join(stats.orphans)}")
    else:
        lines.append(f"  Orphans: none")

    if entries:
        scores = pagerank(entries)
        top = sorted(scores.items(), key=lambda x: -x[1])[:5]
        lines.append("\n  Top entries (PageRank):")
        for eid, score in top:
            entry = by_id(entries, eid)
            title = entry.title[:40] if entry else "?"
            lines.append(f"    {eid}: {title}  ({score:.4f})")

    return "\n".join(lines)


@mcp.tool()
def engram_review() -> str:
    """Show entries that need attention based on type-specific review cadences."""
    entries, _ = _load()
    return render_review_queue(entries)


@mcp.tool()
def engram_add(
    entry_type: str,
    title: str,
    tags: str,
    body: str,
    links: str = "",
    project: str = "",
    confidence: str = "",
    supersedes: str = "",
) -> str:
    """Add a new knowledge entry.

    Args:
        entry_type: decision, learning, mistake, observation, or goal
        title: Short title for the entry
        tags: Comma-separated tags (e.g. "architecture, python")
        body: The full markdown body content
        links: Comma-separated entry IDs to link to (e.g. "DEC-001, LRN-003")
        project: Project name (e.g. "svx", "persona-engine", "engram")
        confidence: high, medium, or low
        supersedes: ID of entry this replaces
    """
    entry_type = entry_type.lower().strip()
    if entry_type not in VALID_TYPES:
        return f"Invalid type '{entry_type}'. Valid: {list(VALID_TYPES.keys())}"

    prefix = VALID_TYPES[entry_type]

    # Find next available number
    entries, _ = _load()
    existing_numbers = [
        e.number for e in entries if e.prefix == prefix
    ]
    next_num = max(existing_numbers, default=0) + 1
    entry_id = f"{prefix}-{next_num:03d}"

    # Build tags list
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if not tag_list:
        return "Error: at least one tag is required."

    # Build links list
    link_list = [l.strip() for l in links.split(",") if l.strip()] if links else []

    # Build frontmatter
    from datetime import date
    today = date.today().isoformat()

    fm_lines = [
        "---",
        f"id: {entry_id}",
        f"type: {entry_type}",
        f"date: {today}",
        f"tags: [{', '.join(tag_list)}]",
        f"status: active",
    ]
    if link_list:
        fm_lines.append(f"links: [{', '.join(link_list)}]")
    if project:
        fm_lines.append(f"project: {project}")
    if confidence:
        fm_lines.append(f"confidence: {confidence}")
    if supersedes:
        fm_lines.append(f"supersedes: {supersedes}")
    fm_lines.append("---")

    # Build file content
    content = "\n".join(fm_lines) + f"\n\n# {title}\n\n{body}\n"

    # Write file
    file_path = ENTRIES_DIR / f"{entry_id}.md"
    file_path.write_text(content, encoding="utf-8")

    # Validate after adding
    entries2, errors2 = _load()
    report = validate(entries2, errors2)

    result = f"Created {entry_id}: {title}\n  File: {file_path.name}"
    if not report.is_healthy:
        issues = [f"  {i.message}" for i in report.errors[:3]]
        result += f"\n\n  WARNING — validation issues:\n" + "\n".join(issues)

    return result


@mcp.tool()
def engram_path(source_id: str, target_id: str) -> str:
    """Find the shortest connection path between two entries."""
    entries, _ = _load()
    source_id = source_id.upper()
    target_id = target_id.upper()

    path = shortest_path(entries, source_id, target_id)
    if path:
        return f"Path: {' → '.join(path)}"
    else:
        return f"No path between {source_id} and {target_id}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
