"""
Engram CLI

Unified command-line interface. 6 commands, not 80.

Usage:
    python3 -m tools health          # Is the system healthy?
    python3 -m tools validate        # What's broken?
    python3 -m tools list            # Show all entries
    python3 -m tools list decisions  # Filter by type
    python3 -m tools search <query>  # Full-text search
    python3 -m tools show <id>       # Show one entry in detail
    python3 -m tools graph           # Graph statistics
    python3 -m tools path <id> <id>  # Shortest path between entries
"""

import sys
from pathlib import Path

from .parser import load_knowledge_base
from .validator import validate, render_validation_report
from .health import render_health
from .query import (
    by_type, by_tag, by_project, by_status,
    search, by_id, linking_to, render_entry_list,
)
from .graph import compute_stats, pagerank, shortest_path
from .review import render_review_queue


ROOT = Path(__file__).resolve().parent.parent


def cmd_health():
    entries, errors = load_knowledge_base(ROOT)
    print(render_health(entries))


def cmd_validate():
    entries, errors = load_knowledge_base(ROOT)
    report = validate(entries, errors)
    print(render_validation_report(report))


def cmd_list(args):
    entries, _ = load_knowledge_base(ROOT)

    if args:
        filter_type = args[0].lower()
        # Try as type name
        type_map = {
            "decisions": "decision", "decision": "decision",
            "learnings": "learning", "learning": "learning",
            "mistakes": "mistake", "mistake": "mistake",
            "observations": "observation", "observation": "observation",
            "goals": "goal", "goal": "goal",
        }
        if filter_type in type_map:
            entries = by_type(entries, type_map[filter_type])
        elif filter_type.startswith("tag:"):
            entries = by_tag(entries, filter_type[4:])
        elif filter_type.startswith("project:"):
            entries = by_project(entries, filter_type[8:])
        elif filter_type.startswith("status:"):
            entries = by_status(entries, filter_type[7:])
        else:
            print(f"Unknown filter: {filter_type}")
            print("Usage: list [decisions|learnings|mistakes|observations|goals|tag:X|project:X|status:X]")
            return

    print(render_entry_list(entries))


def cmd_search(args):
    if not args:
        print("Usage: search <query>")
        return

    query = " ".join(args)
    entries, _ = load_knowledge_base(ROOT)
    results = search(entries, query)
    print(f"Search: '{query}' — {len(results)} result(s)\n")
    print(render_entry_list(results))


def cmd_show(args):
    if not args:
        print("Usage: show <entry-id>")
        return

    entry_id = args[0].upper()
    entries, _ = load_knowledge_base(ROOT)
    entry = by_id(entries, entry_id)

    if not entry:
        print(f"Entry '{entry_id}' not found.")
        return

    print(f"{'=' * 60}")
    print(f"  {entry.id}: {entry.title}")
    print(f"  Type: {entry.type}  Status: {entry.status}  Date: {entry.date}")
    print(f"  Tags: {', '.join(entry.tags)}")
    if entry.project:
        print(f"  Project: {entry.project}")
    if entry.confidence:
        print(f"  Confidence: {entry.confidence}")
    if entry.links:
        print(f"  Links: {', '.join(entry.links)}")
    if entry.supersedes:
        print(f"  Supersedes: {entry.supersedes}")
    print(f"{'=' * 60}")
    print()
    print(entry.body)

    # Show backlinks
    backlinks = linking_to(entries, entry_id)
    if backlinks:
        print(f"\n--- Linked by ---")
        for bl in backlinks:
            print(f"  {bl.id}: {bl.title}")


def cmd_graph():
    entries, _ = load_knowledge_base(ROOT)
    stats = compute_stats(entries)

    print(f"Graph: {stats.total_nodes} nodes, {stats.total_edges} edges")
    print(f"  Density: {stats.density:.2%}")
    print(f"  Clusters: {stats.clusters}")

    if stats.bridges:
        print(f"  Bridges: {', '.join(stats.bridges)}")
    else:
        print(f"  Bridges: none (good)")

    if stats.orphans:
        print(f"  Orphans: {', '.join(stats.orphans)}")
    else:
        print(f"  Orphans: none")

    # PageRank top entries
    if entries:
        scores = pagerank(entries)
        top = sorted(scores.items(), key=lambda x: -x[1])[:5]
        print(f"\n  Top entries (PageRank):")
        for eid, score in top:
            entry = by_id(entries, eid)
            title = entry.title[:40] if entry else "?"
            print(f"    {eid}: {title}  ({score:.4f})")


def cmd_review():
    entries, _ = load_knowledge_base(ROOT)
    print(render_review_queue(entries))


def cmd_path(args):
    if len(args) < 2:
        print("Usage: path <source-id> <target-id>")
        return

    source = args[0].upper()
    target = args[1].upper()
    entries, _ = load_knowledge_base(ROOT)
    path = shortest_path(entries, source, target)

    if path:
        print(f"Path: {' → '.join(path)}")
    else:
        print(f"No path between {source} and {target}")


def main():
    args = sys.argv[1:]
    if not args:
        print("engram — structured knowledge system")
        print()
        print("Commands:")
        print("  health           System health score")
        print("  validate         Check for problems")
        print("  list [filter]    List entries (filter: decisions, tag:X, project:X)")
        print("  search <query>   Full-text search")
        print("  show <id>        Show entry details")
        print("  graph            Graph statistics")
        print("  review           What needs attention today?")
        print("  path <id> <id>   Shortest path between entries")
        return

    cmd = args[0].lower()
    rest = args[1:]

    commands = {
        "health": lambda: cmd_health(),
        "validate": lambda: cmd_validate(),
        "list": lambda: cmd_list(rest),
        "search": lambda: cmd_search(rest),
        "show": lambda: cmd_show(rest),
        "graph": lambda: cmd_graph(),
        "review": lambda: cmd_review(),
        "path": lambda: cmd_path(rest),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Valid commands: {', '.join(commands.keys())}")
