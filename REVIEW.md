# Engram — Review

**Reviewer**: Claude (Opus 4.6, partner session)
**Date**: 2026-03-20
**Version Reviewed**: 32 entries, 7 modules, ~1,200 LOC, 139 tests, health 97/100
**Previous Review**: DESIGN.md (builder's self-assessment — accurate, honest, but not external)

---

## Summary

Engram is a structured knowledge system that tracks decisions, learnings, mistakes, observations, and goals across projects. It validates its own integrity, scores its health, builds a graph of relationships between entries, and surfaces entries for periodic review. It was built by using it — every entry is grounded in real work across engram, svx, scroll, persona-engine, and vigil. It is the most mature and self-proven project in the portfolio.

---

## Dimension Assessments

### Thesis & Positioning

The thesis is: structured knowledge from real work, validated through use, not generated through reading. This directly addresses the Collector's Fallacy (OBS-002) that kills PKM systems — saving feels like learning but isn't.

The predecessor (Claude-owns-this) proved the failure mode: 70 modules, 31K LOC of tools analyzing 269 bulk-generated entries. Engram inverted that: 7 modules, 1.2K LOC, 32 entries from actual engineering work. The tools-to-content ratio dropped from 6.7:1 to ~1.3:1.

This isn't a product for strangers. It's personal infrastructure and cross-project backbone. That's the right positioning — it doesn't need to compete in the PKM market. It needs to be useful to Satish and to the AI agents working with him.

### Architecture

7 modules, each with a clear single responsibility:

| Module | Role | Earns its place? |
|--------|------|------------------|
| parser.py | Read entry files → Entry objects | Yes — foundation |
| validator.py | Catch broken links, duplicates, staleness, supersession | Yes — primary value-add |
| graph.py | Directed graph, bridges, clusters, PageRank, paths | Yes — reveals structure |
| query.py | Search, filter by type/tag/project/status | Yes — basic retrieval |
| health.py | Composite score 0-100 across 4 dimensions | Yes — single-number health |
| review.py | Type-specific review cadences, urgency levels | Yes — proactive surfacing |
| cli.py | 8 commands | Yes — human interface |

Data flow is clean: entries on disk → parser → in-memory objects → validator/graph/query/health/review → CLI output. No circular dependencies, no hidden state.

The MCP server (exposed via engram tools in Claude Code) adds write capability (`engram_add`) that the CLI lacks. This asymmetry is a problem — see Weaknesses.

**Concern**: Lives in `tools/` with `python3 -m tools` as entry point. Not pip-installable, no pyproject.toml. If engram is meant to span projects (DEC-005), it needs proper packaging.

### Code Quality

| Metric | Value | Assessment |
|--------|-------|-----------|
| Tests | 139 | Strong |
| Pass rate | 100% | Clean |
| Runtime | 0.4s | Fast |
| External deps | 0 | Perfect |
| Test philosophy | Functional ("does it catch broken data?") | Right approach |

Test distribution: 30 parser + 28 validator + 24 graph + 22 query + 16 health + 11 review + 8 integration. Every module is tested. Integration tests cover end-to-end file-to-analysis pipeline.

Error handling is robust: parser returns `ParseError` lists instead of crashing. Validator categorizes issues into errors, warnings, and infos. Health score degrades proportionally to problems found.

Zero external dependencies. The graph algorithms (BFS, PageRank, bridge detection) are implemented in pure Python — correct choice for a <100 entry system.

### Completeness

**Complete:**
- Entry CRUD (via MCP, not CLI — gap noted below)
- Validation (6 independent checks: broken links, duplicate IDs, orphans, staleness, supersession chains, ID sequence gaps)
- Graph analysis (adjacency, clusters, bridges, PageRank, shortest path)
- Health scoring (integrity 40%, connectivity 30%, freshness 20%, coverage 10%)
- Review queue (type-specific cadences, urgency levels)
- CLI (8 commands covering all read operations)
- MCP server (9 tools including add, show, list, search, graph, health, validate, review, path)

**Missing:**
- CLI write commands (`engram add`, `engram edit`, `engram archive`)
- Push-based review notifications (review queue is pull-only)
- Cross-project health rollup
- Conflict/contradiction detection between entries
- Auto-suggest links on entry creation
- Schema versioning (schema.yaml has no version field)

### Usability

**For Satish in Claude Code**: Excellent. MCP tools are well-described, entry creation works via `engram_add`, querying is intuitive.

**For Satish in terminal**: Weak. No way to create entries from CLI. Every new entry requires hand-writing markdown with correct YAML frontmatter, correct ID sequencing, correct required sections per type. That's 2+ minutes of boilerplate per entry.

**For a stranger**: Not usable. No README, no installation instructions, no pyproject.toml. The DESIGN.md is thorough but it's a design document, not user documentation.

### Sustainability

Bus factor is 1 — but well-mitigated. Code is clean enough that a competent Python dev could maintain it. Tests are comprehensive. DESIGN.md explains every design decision and its rationale. The entry format is human-readable markdown — no proprietary format lock-in.

Maintenance burden is low: zero dependencies to update, schema is stable, test suite runs in 0.4s. The only ongoing work is writing entries and running reviews.

Growth ceiling: the current architecture handles <100 entries well. At 500+ entries, keyword search becomes insufficient (needs full-text indexing or embeddings), graph analysis gets slow (but still O(V+E) which is fine), and the flat file system needs directory organization.

### Portfolio Fit

Engram is the backbone of the portfolio. Scroll already produces engram-compatible entries. Vigil's signals could feed engram observations. SVX audit entries could become engram decisions. kv-secrets is independent.

It should not be promoted as a standalone product. Its value is as connective tissue — the shared knowledge layer that all other tools read from and write to.

---

## Strengths

1. **Self-proven through 6 closed loops.** The system caught its own bridge (LRN-001), its own missing feature (review queue), its own test gap (MST-003), its own validation flaw (MST-004), its own bad metric (MST-006), and its own research trap (DEC-004). No other project in the portfolio has this level of self-validation.

2. **Zero external dependencies.** Entire system is pure Python stdlib. Nothing to break, nothing to audit, nothing to update.

3. **Functional test philosophy.** 139 tests that answer "does the system catch problems?" not "does the code run?" — grounded in LRN-001's discovery that functional tests catch more real issues.

4. **Restraint.** The "What's Not Here" section in DESIGN.md shows genuine discipline. No PageRank visualization, no stress testing, no recommendation engine, no evolution simulator. Each omission is justified.

5. **Content quality.** 32 entries from real work across 5 projects. Not bulk-generated. Each passes the "so what?" test (DEC-003).

---

## Weaknesses

1. **No CLI write path.** Creating entries requires hand-writing markdown files with correct frontmatter. This friction will kill entry creation as the knowledge base grows. **Fix**: Add `engram add --type mistake --title "..."` that handles ID sequencing, section scaffolding, frontmatter generation, and opens the editor for body content.

2. **Graph is passive.** PageRank, bridges, paths exist but only run on demand. They don't proactively suggest links on entry creation or surface contradictions. **Fix**: When `engram_add` creates an entry (MCP or CLI), scan existing entries for tag/title keyword overlap and suggest links before saving.

3. **Review queue has no push mechanism.** If nobody runs `python3 -m tools review`, entries go stale silently. **Fix**: Add a daily summary to the MCP server ("3 entries due for review") or a git hook that warns when stale entries exist.

4. **Not pip-installable.** No pyproject.toml, no `engram` CLI entry point. Cross-project use (DEC-005) requires the source directory. **Fix**: Add pyproject.toml with `[project.scripts] engram = "tools.cli:main"`.

5. **DESIGN.md numbers are stale.** Shows 28 entries and 119 tests; actual count is 32 entries and 139 tests. **Fix**: Update the numbers, or better, make them computed (CLI command that outputs current stats).

---

## Recommendations (Priority Order)

1. **Add domain/subdomain taxonomy (DEC-009).** Seven fixed domains (security, architecture, performance, testing, ux, devops, strategy) with predefined subdomains. Enables cross-project discovery: an agent on kv-secrets queries `domain:security` and finds learnings from svx and vigil. Without this, agents dump freeform tags inconsistently and cross-project knowledge flow fails. Requires: schema.yaml update, parser/validator changes, MCP tool parameter, CLI support.

2. **Add `engram add` to CLI.** Interactive or flag-based entry creation with domain/subdomain selection. This is the highest-impact UX improvement.

3. **Add pyproject.toml and make it pip-installable.** If engram spans projects, `pip install -e ~/engram` should give you the `engram` command everywhere.

4. **Add entry quality guardrails to MCP tool.** The `engram_add` MCP tool currently accepts anything — including implementation details that belong in code comments, not engram. Add validation: reject entries where the body contains class names, method signatures, or code blocks longer than 5 lines. Prompt the agent to rewrite with reasoning instead of implementation details. This prevents the misuse pattern observed in the vigil session (DEC-008).

5. **Auto-suggest links on entry creation.** Scan existing entries for tag/domain overlap and keyword matches.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Agents misuse engram (log implementation, not reasoning) | **Confirmed** | High | Entry quality guardrails in MCP tool + CLAUDE.md rules |
| No structured taxonomy → cross-project queries fail | High | High | Domain/subdomain taxonomy (DEC-009) |
| Entry creation friction kills adoption | High | High | Build CLI `add` command |
| Review queue unused → entries go stale | Medium | Medium | Push notifications via MCP |
| Graph degrades as manual linking becomes burden | Medium | High | Auto-suggest links |
| Knowledge base outgrows flat-file architecture | Low (years away) | Medium | Monitor entry count, plan migration at ~500 |

---

## Observed Misuse (2026-03-21)

The vigil session logged DEC-008 — a 40-line entry containing class names, method signatures, depth weights, CLI flags, and implementation details. This is code documentation, not a knowledge entry. The code already contains this information. The entry fails engram's own "so what?" test (DEC-003).

**Root cause**: No guardrails on what `engram_add` accepts. An agent focused on implementation treats engram as a changelog rather than a knowledge system.

**Impact**: Noise entries dilute the knowledge base. Other agents searching engram find implementation details instead of reasoning. The graph becomes cluttered with entries that don't inform decisions.

**Fix**: Entry quality validation in the MCP tool (recommendation #4) + CLAUDE.md rules for proper engram usage (added 2026-03-21).

---

## Verdict

Engram is the most mature and self-consistent project in the portfolio. It proved its thesis through use, not through claims. The closed loops are real. The code is clean. The restraint is genuine. Two new findings from the portfolio review: (1) agents misuse engram without guardrails, logging implementation details instead of reasoning, and (2) cross-project knowledge discovery needs structured taxonomy, not freeform tags. Both are addressable — domain/subdomain taxonomy + entry quality validation.

**Grade: B+**
Strong fundamentals, proven thesis, self-validated through real use. Grade holds — the misuse pattern is a usage problem, not a code problem. Moves to A- when domain/subdomain taxonomy ships and entry quality guardrails prevent agents from dumping implementation details.
