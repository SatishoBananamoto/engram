"""
Health Score Tests — Functional Validation

The key question: does the score actually DROP when the system is degraded?

Tests intentionally break the system in specific ways and verify:
1. Broken links → score drops
2. Orphan entries → score drops
3. Stale entries → score drops
4. Missing entry types → score drops
5. Fragmented graph → score drops
6. A clean system → high score
"""

import pytest
from tools.parser import Entry
from tools.health import (
    compute_health,
    score_integrity,
    score_connectivity,
    score_freshness,
    score_coverage,
)


def make_entry(id, type="decision", date="2026-03-16", tags=None,
               status="active", links=None):
    return Entry(
        id=id, type=type, date=date,
        tags=tags or ["test"], status=status,
        links=links or [],
    )


class TestHealthScoreRespondsToProblems:
    """The core test: does the score move in the right direction?"""

    def test_clean_system_scores_high(self):
        entries = [
            make_entry("GOL-001", type="goal"),
            make_entry("DEC-001", links=["GOL-001"]),
            make_entry("LRN-001", type="learning", links=["DEC-001"]),
            make_entry("MST-001", type="mistake", links=["LRN-001"]),
            make_entry("OBS-001", type="observation", links=["DEC-001"]),
        ]
        report = compute_health(entries)
        assert report.score >= 70, f"Clean system scored {report.score}, expected >= 70"
        assert report.grade in ("A", "B", "C")

    def test_broken_links_lower_score(self):
        clean = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002"),
        ]
        broken = [
            make_entry("DEC-001", links=["GHOST-999"]),  # Broken link
            make_entry("DEC-002"),
        ]
        clean_score = compute_health(clean).score
        broken_score = compute_health(broken).score
        assert broken_score < clean_score, \
            f"Broken links ({broken_score}) should score lower than clean ({clean_score})"

    def test_orphans_lower_score(self):
        connected = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002", links=["DEC-001"]),
        ]
        with_orphan = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002"),
            make_entry("DEC-003"),  # Orphan — no links at all
        ]
        connected_score = compute_health(connected).score
        orphan_score = compute_health(with_orphan).score
        assert orphan_score < connected_score, \
            f"Orphans ({orphan_score}) should score lower than connected ({connected_score})"

    def test_stale_entries_lower_score(self):
        fresh = [
            make_entry("DEC-001", date="2026-03-16"),
        ]
        stale = [
            make_entry("DEC-001", date="2025-01-01"),  # Very old
        ]
        fresh_score = compute_health(fresh).score
        stale_score = compute_health(stale).score
        assert stale_score < fresh_score, \
            f"Stale ({stale_score}) should score lower than fresh ({fresh_score})"

    def test_missing_types_lower_score(self):
        diverse = [
            make_entry("GOL-001", type="goal"),
            make_entry("DEC-001", links=["GOL-001"]),
            make_entry("LRN-001", type="learning", links=["DEC-001"]),
            make_entry("MST-001", type="mistake", links=["LRN-001"]),
            make_entry("OBS-001", type="observation", links=["DEC-001"]),
        ]
        homogeneous = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002", links=["DEC-003"]),
            make_entry("DEC-003", links=["DEC-001"]),
        ]
        diverse_score = compute_health(diverse).score
        homo_score = compute_health(homogeneous).score
        assert homo_score < diverse_score, \
            f"Homogeneous ({homo_score}) should score lower than diverse ({diverse_score})"

    def test_fragmented_graph_lower_score(self):
        connected = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002", links=["DEC-003"]),
            make_entry("DEC-003"),
        ]
        fragmented = [
            make_entry("DEC-001"),  # Island 1
            make_entry("DEC-002"),  # Island 2
            make_entry("DEC-003"),  # Island 3
        ]
        conn_score = compute_health(connected).score
        frag_score = compute_health(fragmented).score
        assert frag_score < conn_score, \
            f"Fragmented ({frag_score}) should score lower than connected ({conn_score})"


class TestIntegrity:
    def test_no_errors_is_100(self):
        entries = [make_entry("GOL-001", type="goal")]
        dim = score_integrity(entries)
        assert dim.score == 100

    def test_errors_reduce_score(self):
        entries = [
            make_entry("DEC-001", links=["GHOST"]),  # broken link = error
        ]
        dim = score_integrity(entries)
        assert dim.score < 100


class TestConnectivity:
    def test_empty_is_zero(self):
        dim = score_connectivity([])
        assert dim.score == 0

    def test_single_cluster_no_orphans(self):
        entries = [
            make_entry("DEC-001", links=["DEC-002"]),
            make_entry("DEC-002"),
        ]
        dim = score_connectivity(entries)
        assert dim.score >= 80


class TestFreshness:
    def test_all_fresh(self):
        entries = [make_entry("DEC-001", date="2026-03-16")]
        dim = score_freshness(entries)
        assert dim.score == 100

    def test_all_stale(self):
        entries = [make_entry("DEC-001", date="2020-01-01")]
        dim = score_freshness(entries)
        assert dim.score == 0

    def test_archived_not_counted(self):
        entries = [make_entry("DEC-001", date="2020-01-01", status="archived")]
        dim = score_freshness(entries)
        # Archived entries are not active, so freshness shouldn't penalize
        assert dim.score == 100


class TestCoverage:
    def test_all_types_present(self):
        entries = [
            make_entry("GOL-001", type="goal"),
            make_entry("DEC-001"),
            make_entry("LRN-001", type="learning"),
            make_entry("MST-001", type="mistake"),
            make_entry("OBS-001", type="observation"),
        ]
        dim = score_coverage(entries)
        assert dim.score == 100

    def test_one_type_only(self):
        entries = [make_entry("DEC-001")]
        dim = score_coverage(entries)
        assert dim.score == 20  # 1/5 types

    def test_empty_is_zero(self):
        dim = score_coverage([])
        assert dim.score == 0
