"""
Engram Graph

Builds a directed graph from entry links and computes:
- Connections (in-degree, out-degree, total)
- Bridges (entries whose removal fragments the graph)
- Clusters (connected components)
- PageRank (importance scoring)
- Shortest path between entries

No external dependencies. Pure Python.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .parser import Entry


@dataclass
class GraphStats:
    """Summary statistics for the knowledge graph."""
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
    clusters: int = 0
    bridges: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)


def build_adjacency(entries: list[Entry]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build directed adjacency lists.

    Returns (outgoing, incoming) where:
    - outgoing[id] = set of IDs this entry links TO
    - incoming[id] = set of IDs that link TO this entry
    """
    known_ids = {e.id for e in entries}
    outgoing: dict[str, set[str]] = {e.id: set() for e in entries}
    incoming: dict[str, set[str]] = {e.id: set() for e in entries}

    for entry in entries:
        for link_id in entry.links:
            if link_id in known_ids:
                outgoing[entry.id].add(link_id)
                incoming[link_id].add(entry.id)

    return outgoing, incoming


def build_undirected(entries: list[Entry]) -> dict[str, set[str]]:
    """Build undirected adjacency list (for connectivity analysis)."""
    outgoing, incoming = build_adjacency(entries)
    undirected: dict[str, set[str]] = {eid: set() for eid in outgoing}
    for eid in outgoing:
        undirected[eid].update(outgoing[eid])
        undirected[eid].update(incoming[eid])
    return undirected


def find_clusters(entries: list[Entry]) -> list[set[str]]:
    """Find connected components (treating graph as undirected).

    Returns list of sets, each set containing the IDs in one cluster.
    """
    if not entries:
        return []

    adj = build_undirected(entries)
    visited = set()
    clusters = []

    for start_id in adj:
        if start_id in visited:
            continue
        # BFS from this node
        cluster = set()
        queue = deque([start_id])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            cluster.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        clusters.append(cluster)

    return clusters


def find_bridges(entries: list[Entry]) -> list[str]:
    """Find bridge entries — nodes whose removal increases the number of clusters.

    A bridge entry is a structural chokepoint. Removing it fragments the graph.
    """
    if len(entries) <= 2:
        return []

    baseline_clusters = len(find_clusters(entries))
    bridges = []

    for target in entries:
        # Remove this entry and check connectivity
        remaining = [e for e in entries if e.id != target.id]
        # Also remove links TO the removed entry
        patched = []
        for e in remaining:
            patched_entry = Entry(
                id=e.id, type=e.type, date=e.date, tags=e.tags,
                status=e.status,
                links=[l for l in e.links if l != target.id],
                title=e.title, body=e.body,
            )
            patched.append(patched_entry)

        new_clusters = len(find_clusters(patched))
        if new_clusters > baseline_clusters:
            bridges.append(target.id)

    return bridges


def find_orphans(entries: list[Entry]) -> list[str]:
    """Find entries with zero connections (no in or out links to known entries)."""
    outgoing, incoming = build_adjacency(entries)
    orphans = []
    for eid in outgoing:
        if not outgoing[eid] and not incoming[eid]:
            orphans.append(eid)
    return orphans


def pagerank(entries: list[Entry], damping: float = 0.85,
             iterations: int = 100, tolerance: float = 1e-6) -> dict[str, float]:
    """Compute PageRank scores for all entries.

    Higher score = more important (more entries link to it, and those entries
    are themselves important).
    """
    if not entries:
        return {}

    outgoing, incoming = build_adjacency(entries)
    n = len(entries)
    scores = {e.id: 1.0 / n for e in entries}

    for _ in range(iterations):
        new_scores = {}
        for eid in scores:
            # Sum of (score of linker / number of outgoing links from linker)
            rank_sum = 0.0
            for linker_id in incoming[eid]:
                out_count = len(outgoing[linker_id])
                if out_count > 0:
                    rank_sum += scores[linker_id] / out_count

            new_scores[eid] = (1 - damping) / n + damping * rank_sum

        # Check convergence
        diff = sum(abs(new_scores[eid] - scores[eid]) for eid in scores)
        scores = new_scores
        if diff < tolerance:
            break

    return scores


def shortest_path(entries: list[Entry], source_id: str, target_id: str) -> Optional[list[str]]:
    """Find shortest path between two entries (undirected).

    Returns list of IDs from source to target, or None if no path exists.
    """
    adj = build_undirected(entries)
    if source_id not in adj or target_id not in adj:
        return None
    if source_id == target_id:
        return [source_id]

    visited = {source_id}
    queue = deque([(source_id, [source_id])])

    while queue:
        node, path = queue.popleft()
        for neighbor in adj[node]:
            if neighbor == target_id:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None  # No path exists


def compute_stats(entries: list[Entry]) -> GraphStats:
    """Compute summary statistics for the knowledge graph."""
    if not entries:
        return GraphStats()

    outgoing, incoming = build_adjacency(entries)
    n = len(entries)
    total_edges = sum(len(targets) for targets in outgoing.values())
    max_edges = n * (n - 1) if n > 1 else 1
    density = total_edges / max_edges if max_edges > 0 else 0

    clusters = find_clusters(entries)
    bridges = find_bridges(entries)
    orphans = find_orphans(entries)

    return GraphStats(
        total_nodes=n,
        total_edges=total_edges,
        density=density,
        clusters=len(clusters),
        bridges=bridges,
        orphans=orphans,
    )
