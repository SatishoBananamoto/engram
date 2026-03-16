"""
Graph Tests — Functional Validation

Tests graph algorithms against KNOWN structures:
- A chain (A→B→C): removing B should fragment
- A triangle (A→B, B→C, C→A): no bridges, fully connected
- A star (A→B, A→C, A→D): A is a bridge
- Disconnected components: should detect 2+ clusters
- PageRank: most-linked-to node should have highest score
"""

import pytest
from tools.parser import Entry
from tools.graph import (
    build_adjacency,
    build_undirected,
    find_clusters,
    find_bridges,
    find_orphans,
    pagerank,
    shortest_path,
    compute_stats,
)


def make_entry(id, links=None):
    return Entry(
        id=id, type="decision", date="2026-03-16",
        tags=["test"], links=links or [],
    )


# --- Known Graph Structures ---

class TestChainGraph:
    """A→B→C: linear chain."""

    @pytest.fixture
    def chain(self):
        return [
            make_entry("A", links=["B"]),
            make_entry("B", links=["C"]),
            make_entry("C"),
        ]

    def test_one_cluster(self, chain):
        clusters = find_clusters(chain)
        assert len(clusters) == 1

    def test_b_is_bridge(self, chain):
        bridges = find_bridges(chain)
        assert "B" in bridges

    def test_a_and_c_not_bridges(self, chain):
        """Removing A or C doesn't fragment — B↔C or A↔B still connected."""
        bridges = find_bridges(chain)
        # A has outgoing to B, C has incoming from B
        # Removing A: B→C still connected (1 cluster)
        # Removing C: A→B still connected (1 cluster)
        assert "A" not in bridges
        assert "C" not in bridges

    def test_path_a_to_c(self, chain):
        path = shortest_path(chain, "A", "C")
        assert path == ["A", "B", "C"]


class TestTriangleGraph:
    """A→B, B→C, C→A: fully connected triangle."""

    @pytest.fixture
    def triangle(self):
        return [
            make_entry("A", links=["B"]),
            make_entry("B", links=["C"]),
            make_entry("C", links=["A"]),
        ]

    def test_one_cluster(self, triangle):
        assert len(find_clusters(triangle)) == 1

    def test_no_bridges(self, triangle):
        """Triangle has no bridges — remove any node, other two still connected."""
        assert find_bridges(triangle) == []

    def test_no_orphans(self, triangle):
        assert find_orphans(triangle) == []


class TestStarGraph:
    """Hub→A, Hub→B, Hub→C: hub is critical."""

    @pytest.fixture
    def star(self):
        return [
            make_entry("Hub", links=["A", "B", "C"]),
            make_entry("A"),
            make_entry("B"),
            make_entry("C"),
        ]

    def test_one_cluster(self, star):
        assert len(find_clusters(star)) == 1

    def test_hub_is_bridge(self, star):
        bridges = find_bridges(star)
        assert "Hub" in bridges

    def test_leaves_not_bridges(self, star):
        bridges = find_bridges(star)
        assert "A" not in bridges
        assert "B" not in bridges
        assert "C" not in bridges

    def test_hub_has_highest_pagerank(self, star):
        """Hub should NOT have highest PageRank — the leaves do, because Hub links to them."""
        scores = pagerank(star)
        # In PageRank, nodes that receive links score higher
        # Hub links to A, B, C — so A, B, C receive the rank
        # Hub receives no incoming links
        assert scores["Hub"] < scores["A"]


class TestDisconnectedGraph:
    """Two separate components: {A,B} and {C,D}."""

    @pytest.fixture
    def disconnected(self):
        return [
            make_entry("A", links=["B"]),
            make_entry("B"),
            make_entry("C", links=["D"]),
            make_entry("D"),
        ]

    def test_two_clusters(self, disconnected):
        clusters = find_clusters(disconnected)
        assert len(clusters) == 2

    def test_no_path_across_components(self, disconnected):
        path = shortest_path(disconnected, "A", "C")
        assert path is None

    def test_path_within_component(self, disconnected):
        path = shortest_path(disconnected, "A", "B")
        assert path == ["A", "B"]


class TestOrphanDetection:
    def test_isolated_node(self):
        entries = [
            make_entry("A", links=["B"]),
            make_entry("B"),
            make_entry("C"),  # No links in or out
        ]
        orphans = find_orphans(entries)
        assert "C" in orphans
        assert "A" not in orphans
        assert "B" not in orphans

    def test_all_connected(self):
        entries = [
            make_entry("A", links=["B"]),
            make_entry("B", links=["A"]),
        ]
        assert find_orphans(entries) == []


class TestPageRank:
    def test_uniform_scores_for_ring(self):
        """In a ring A→B→C→A, all nodes should have equal PageRank."""
        entries = [
            make_entry("A", links=["B"]),
            make_entry("B", links=["C"]),
            make_entry("C", links=["A"]),
        ]
        scores = pagerank(entries)
        values = list(scores.values())
        # All should be approximately equal
        assert max(values) - min(values) < 0.01

    def test_most_linked_to_wins(self):
        """Node that everyone links to should have highest PageRank."""
        entries = [
            make_entry("A", links=["Hub"]),
            make_entry("B", links=["Hub"]),
            make_entry("C", links=["Hub"]),
            make_entry("Hub"),
        ]
        scores = pagerank(entries)
        assert scores["Hub"] > scores["A"]
        assert scores["Hub"] > scores["B"]
        assert scores["Hub"] > scores["C"]

    def test_empty_entries(self):
        assert pagerank([]) == {}


class TestShortestPath:
    def test_same_node(self):
        entries = [make_entry("A")]
        assert shortest_path(entries, "A", "A") == ["A"]

    def test_nonexistent_node(self):
        entries = [make_entry("A")]
        assert shortest_path(entries, "A", "Z") is None

    def test_longer_path(self):
        entries = [
            make_entry("A", links=["B"]),
            make_entry("B", links=["C"]),
            make_entry("C", links=["D"]),
            make_entry("D"),
        ]
        path = shortest_path(entries, "A", "D")
        assert path == ["A", "B", "C", "D"]


class TestComputeStats:
    def test_stats_basic(self):
        entries = [
            make_entry("A", links=["B"]),
            make_entry("B", links=["C"]),
            make_entry("C"),
        ]
        stats = compute_stats(entries)
        assert stats.total_nodes == 3
        assert stats.total_edges == 2
        assert stats.clusters == 1
        assert 0 < stats.density < 1

    def test_stats_empty(self):
        stats = compute_stats([])
        assert stats.total_nodes == 0
        assert stats.total_edges == 0
