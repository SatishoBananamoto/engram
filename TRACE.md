# Engram — TRACE

> Single source of truth for engram evolution. Binding rules, honest gaps, phased plan.
> Once written here, follow it. No exceptions.
>
> **Why this exists:** [THESIS.md](THESIS.md) — what engram is, what it must become, where the gap lives.

**Current branch:** main
**Last session:** 2026-03-26
**Repo stats:** 52 entries, 7 modules, ~1,300 LOC, 151 tests, health 83/100

---

## NEXT SESSION — START HERE

**What just happened (2026-03-26):**
- Full codebase read: all 7 modules, server.py, schema.yaml, DESIGN.md, REVIEW.md
- Live diagnostics: health 62/100, connectivity 0/100 (6 clusters, 3 bridges, 4 orphans)
- Review queue: 10 items (2 overdue goals, 4 due decisions, 3 upcoming)
- Built `scroll deposit` module (in ~/scroll) — parked, waiting for `source` field
- Identified dilution risk: scroll entries shouldn't dilute engram's curated core
- Satish proposed "branches" (source field) to separate knowledge sources
- Created THESIS.md (engram identity), TRACE.md (operational plan)
- Updated memory with universal process rules
- Diagnosed agent adoption problem: agents check engram but never update it
  - **Seed:** engram instructions are time-based (before/after) not event-based (triggers)
  - **Fix:** Rewrote ~/CLAUDE.md engram section — trigger-based logging at moments of insight
  - See THESIS.md Layer 3 for the deeper problem (engram is passive)

**#1 Priority: Phase 1, Chunk 1 — Schema + Parser**
Why: The entire scroll integration and future multi-source knowledge flow depends on the `source` field. Schema + parser is the foundation. Everything else threads through it.

**What NOT to do:**
- Don't deposit scroll entries into engram until `source` field exists
- Don't fix connectivity (Phase 2) before source field (Phase 1)
- Don't add domain/subdomain taxonomy yet — that's Phase 4
- Don't refactor modules during schema work — one thing at a time

---

## Binding Rules

Non-negotiable. Every engram session.

### Process (from Satish — universal)

1. **Plan first.** No code until the plan exists and is aligned on.
2. **Chunk by chunk.** One chunk. Fix. Test. Update TRACE.md. Commit. Repeat.
3. **Find the seed.** Don't patch symptoms. Trace to root cause first.
4. **Use websearch when needed.** Don't guess.
5. **Proactively recommend next priority with reasoning.** Satish is always open to suggestions.
6. **Follow what's written.** If it's in TRACE.md, it's binding. Change it explicitly or follow it.

### Engineering (from working together)

7. **Verify before assert.** Check current code. Memory can be stale.
8. **Read the error.** Full text. Then fix the specific failure.
9. **Don't defend past work.** If wrong, say so.
10. **Update TRACE.md before committing.** If it's not here, the next session doesn't know.

---

## Current State

**Health: 62/100 (D)**
- Integrity: 80/100 (4 orphan warnings)
- Connectivity: 0/100 (6 clusters, 3 bridges, 4 orphans)
- Freshness: 100/100
- Coverage: 100/100

**What's broken:**

| ID | Problem | Severity |
|----|---------|----------|
| CON-1 | 6 clusters — graph is fragmented | High |
| CON-2 | 3 bridges (DEC-007, DEC-011, GOL-002) | Medium |
| CON-3 | 4 orphans (LRN-014, MST-008, MST-010, OBS-007) | Medium |
| REV-1 | 10 review items unactioned | Medium |

**What's missing** (see [THESIS.md](THESIS.md) for the deeper analysis):

| Gap | Blocks | Phase |
|-----|--------|-------|
| No `source` field | Scroll integration, multi-source knowledge | 1 |
| Fragmented graph | Cross-project knowledge flow | 2 |
| No domain taxonomy | Structured cross-project queries | 4 |
| No CLI write path | Easy entry creation | 5 |
| No quality guardrails | Agent misuse prevention | 5 |
| Not pip-installable | Cross-project CLI usage | 6 |

---

## The Work

### Phase 1: Source Field

**Goal:** Entries know where they came from. Queries can scope by source. Core stays clean.

**Design decisions (binding):**
- Valid values: `manual` (default), `scroll`. Future: `conversation`, `ci`, `import`.
- Existing entries without `source` default to `manual` in the parser. No breaking changes.
- Queries show all sources by default. `source:X` filter is opt-in.

#### Chunk 1: Schema + Parser ---- DONE (committed: 76e5f12)
- [x] Add `source` to schema.yaml (optional field, valid values, default)
- [x] Add `VALID_SOURCES` constant to parser.py
- [x] Add `source` field to Entry dataclass (default: "manual")
- [x] Parse `source` from frontmatter in `parse_entry()`
- [x] Default to "manual" when field is missing
- [x] Write parser tests: source parsed, source defaults, unknown source warns (6 tests)

#### Chunk 2: Validator + Query ---- DONE (committed: 76e5f12)
- [x] Source validation already in parser (warns on unknown — forward compatible). No validator change needed.
- [x] Add `by_source()` filter to query.py
- [x] Update `render_entry_list` — show `source=X` only when not "manual"
- [x] Write query tests: by_source filters (manual, scroll, no match, default), render shows/hides source (6 tests)

#### Chunk 3: CLI + MCP Server ---- DONE (committed: 76e5f12)
- [x] Add `source:` filter to cli.py `cmd_list`
- [x] Add `source:` filter to server.py `engram_list`
- [x] Add `source` parameter to server.py `engram_add` (default: "manual")
- [x] `source` written to frontmatter on every new entry
- [x] Verified live: `list source:manual` returns 52 entries, `list source:scroll` returns 0

#### Chunk 4: Backfill Existing Entries ---- DONE (committed: 76e5f12)
- [x] Script added `source: manual` to all 52 entries (after status: line)
- [x] All entries parse correctly (0 errors)
- [x] 151 tests passing, health unchanged

#### Chunk 5: Wire Scroll Deposit ---- DONE (committed: 3e95e5e in scroll)
- [x] Updated ~/scroll/scroll/deposit.py — `source: scroll` in rendered frontmatter
- [x] Updated ~/scroll/tests/test_deposit.py — verify source in rendering + engram parse roundtrip
- [x] Scroll tests: 25/25 passing. Engram tests: 151/151 passing.

---

### Phase 2: Connectivity Repair ---- DONE

**Goal:** Health above 90. Honest metric. Genuine links only.

**What actually happened:** Satish challenged "who connects the links and on what basis?" This led to auditing the clusters first, discovering the metric was lying (6 clusters penalized as 0/100 when 87% of entries were in one cluster), and fixing the metric before touching any links.

#### Chunk 1: Audit ---- DONE
- [x] Mapped all 6 clusters — largest has 45/52 entries spanning 8 project labels
- [x] Vigil cluster (3 entries) disconnected but internally linked
- [x] 4 orphans identified: MST-008, OBS-007, MST-010, LRN-014
- [x] Finding: fragmentation is mostly a metric problem, not a data problem

#### Chunk 2: Fix Metric ---- DONE (committed: 11e7982)
- [x] Replaced cluster-count penalty with coverage-based scoring (% in largest cluster)
- [x] Lighter penalties: orphans 2pts (was 15), bridges 3pts (was 10)
- [x] Details now show cluster size: "Clusters: 6 (largest: 45/52)"
- [x] All 16 health tests pass (directional checks all hold)
- [x] Health: 62 → 83 (D → B)

#### Chunk 3: Genuine Links ---- DONE (committed: e1a5b5c)
- [x] MST-008 → DEC-003 (bloated entries mistake validates "so what?" test)
- [x] OBS-007 → OBS-006 (both about Satish's process preferences)
- [x] MST-010 → LRN-013 (tracking docs must be live — mistake and protocol)
- [x] LRN-014 → DEC-007 (both vigil signal architecture)
- [x] Health: 83 → 92 (B → A). Clusters: 6 → 2. Orphans: 4 → 0. Warnings: 4 → 0.

#### Review Queue — DEFERRED
- [ ] Action overdue review items (separate session — not blocking anything)

---

### Phase 3: End-to-End Scroll Integration

**Goal:** Scroll extracts from a real repo → deposit into engram → entries visible with `source: scroll`.

#### Chunk 1: Real Extraction
- [ ] Pick a target repo (svx or vigil — both have meaningful git history)
- [ ] Run `scroll init` + `scroll ingest` on target repo
- [ ] Review extracted entries — verify quality before depositing
- [ ] Run `scroll deposit` → entries land in engram
- [ ] Verify `engram_list("source:scroll")` shows deposited entries
- [ ] Verify `engram_list("decisions")` shows both sources with provenance visible
- [ ] Run engram health — verify no degradation
- [ ] Update TRACE.md
- [ ] Commit

---

### Phase 4: Domain/Subdomain Taxonomy

**Goal:** `domain:security` finds all security entries across all projects.

Design already exists in DEC-009. Detailed task breakdown written when Phase 3 completes.

### Phase 5: CLI Write + Quality Guardrails

**Goal:** Terminal entry creation + programmatic "so what?" enforcement.

Detailed task breakdown written when Phase 4 completes.

### Phase 6: Packaging

**Goal:** `pip install -e ~/engram` — proper Python package.

Detailed task breakdown written when Phase 5 completes.

---

## Action Item Prefixes

| Prefix | Category |
|--------|----------|
| SRC-* | Source field |
| CON-* | Connectivity |
| INT-* | Scroll integration |
| DOM-* | Domain taxonomy |
| CLI-* | CLI improvements |
| QG-* | Quality guardrails |
| PKG-* | Packaging |
| BUG-* | Bug fixes |
| DOC-* | Documentation |

---

## Session Log

### 2026-03-26 — Assessment + Plan

**What happened:**
- Full codebase read: all 7 modules, server.py, schema.yaml, DESIGN.md, REVIEW.md
- Live diagnostics: health 62/100, 139 tests passing, 51 entries
- Built scroll deposit module (~/scroll — 25 tests, all passing)
- Identified dilution risk, Satish proposed source/branch concept
- Created THESIS.md, TRACE.md, updated universal process rules in memory

**Decisions:**
- D1: Source field before connectivity (quick + unblocks integration)
- D2: Existing entries default to `source: manual` (backward compatible)
- D3: TRACE.md as operational doc name
- D4: THESIS.md as identity doc — what engram is and must become
- D5: Show all sources by default, `source:` filter is opt-in (don't hide scroll entries)
- D6: Rewrote CLAUDE.md engram instructions from time-based to trigger-based

**Key finding:** Agents don't update engram because the instructions are bookends (before/after work), not triggers (at the moment of insight). GRAFT/TRACE work because they're gates in the commit cycle. Engram was a side-channel. Fixed by rewriting instructions to fire on events: "when you choose between alternatives → log a decision."

**Code changes:** ~/CLAUDE.md engram section rewritten. No engram code changes.

### 2026-03-26 (cont.) — Phase 1 + Phase 2

**What happened:**
- Phase 1 complete: source field threaded end-to-end (schema → parser → query → cli → server → 52 entries backfilled → scroll deposit wired). 151 tests (was 139).
- Phase 2: Satish challenged "on what basis" for manual linking. Audited clusters. Found metric was dishonest (penalized cluster count, not coverage). Fixed metric. Added 4 genuine links.
- Health: 62 → 92 (D → A). Zero warnings. Zero orphans.

**Commits:**
- engram `76e5f12`: source field + THESIS.md + TRACE.md + backfill (Phase 1)
- scroll `3e95e5e`: deposit module with source: scroll
- engram `11e7982`: fix connectivity metric — coverage-based
- engram `e1a5b5c`: 4 genuine links — orphans connected

**Decisions:**
- D7: Fix the metric, not the data (find the seed)
- D8: Coverage-based connectivity scoring (% in largest cluster, not cluster count)
- D9: Only link entries with genuine causal/thematic relationships — no score gaming

**Rule violation:** Committed metric fix and link changes without updating TRACE.md first. Broke rule #10. Caught by Satish.

**Pushed:** Both repos to GitHub.

**Next:** Phase 3 (real scroll integration) or Phase 4 (domain taxonomy) — to be decided next session.
