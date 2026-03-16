# Engram — Design Document

## What This Is

Engram is a structured knowledge system that tracks decisions, learnings, mistakes, and observations. It validates its own integrity, scores its health, and surfaces problems.

It was built by using it — every entry in the knowledge base is a real decision, learning, or mistake from the build process itself.

## How It Differs from Claude-owns-this

| Dimension | Claude-owns-this (v1) | Engram (v2) |
|-----------|----------------------|-------------|
| **Purpose** | Self-referential showcase | Functional knowledge tool |
| **Modules** | 70+ Python files | 6 Python files |
| **LOC (tools)** | 31,135 | ~850 |
| **LOC (content)** | 4,641 | Grows organically |
| **Tools:Content ratio** | 6.7:1 | ~1:1 (and falling) |
| **Tests** | 731 (syntax-heavy) | 119 (functional) |
| **Entry storage** | Mega-files (memory.md with 120+ entries) | One file per entry |
| **Content source** | Bulk-generated in one 14-hour session | Written during actual work |
| **Entry types** | 4 (research, memory, learning, skill) | 5 (decision, learning, mistake, observation, goal) |
| **"Self-evolving"** | Claimed, not real — nothing auto-evolves | Not claimed — humans close the loop |
| **Dependencies** | Pure Python (same) | Pure Python (same) |
| **Test approach** | "Does the code run?" | "Does it catch broken data?" |

## Key Design Decisions

### 1. Individual files over mega-files (DEC-001)

Each entry is a markdown file with YAML frontmatter. Not one giant `memory.md`.

**Why**: Git blame per entry. Grep works naturally. No merge conflicts. Easy archiving. The predecessor proved mega-files don't scale past ~50 entries.

### 2. Five entry types that cover real work

| Type | Prefix | What it captures |
|------|--------|-----------------|
| `decision` | DEC | A choice with reasoning. Tracked to see if it holds up. |
| `learning` | LRN | Something discovered through doing, not reading. |
| `mistake` | MST | What broke, why, and how to prevent it. |
| `observation` | OBS | A pattern noticed. Data, not conclusion. |
| `goal` | GOL | What we're trying to achieve. Measurable. |

The predecessor had `research`, `memory`, `learning`, `skill` — these map to *how an AI thinks about itself*, not to *how work actually happens*. Engram's types map to the artifacts of real engineering work.

### 3. Six modules that earn their place

Every module exists because removing it would lose a capability:

| Module | What it does | Why it's needed |
|--------|-------------|----------------|
| `parser.py` | Reads entry files, extracts metadata | Can't do anything without parsing |
| `validator.py` | Catches broken links, duplicates, staleness | Main value-add: finds problems humans miss |
| `graph.py` | Builds connection graph, finds bridges/clusters | Reveals structural weaknesses |
| `query.py` | Search and filter entries | Basic retrieval |
| `health.py` | Single composite score (0-100) | "Is the system healthy?" in one number |
| `cli.py` | Command-line interface | Humans need to interact |

The predecessor had: wavelets, epidemic models, Fiedler vectors, spectral analysis, influence maximization, core-periphery detection, graph signal processing, random walks, heat kernels... None of which informed any decision about the knowledge base.

### 4. Functional testing over syntax testing

Every test answers: "Does this module do what it claims?"

- **Parser tests**: Give it broken data → does it report the right error?
- **Validator tests**: Create a specific problem → does the validator catch it?
- **Graph tests**: Build a known structure (chain, triangle, star) → does the algorithm produce the correct result?
- **Health tests**: Degrade the system → does the score actually drop?

The predecessor had 731 tests but most verified "does the function return without crashing?" Engram's 119 tests verify "does the system catch problems and respond correctly?"

### 5. The loop closes through use

```
Write entry → Validate → Check health → See problem → Fix it → Score improves
```

This loop was demonstrated during the build:
1. Built 3 entry types → health showed 60% coverage → added remaining types → coverage hit 100%
2. MST-001 only linked through LRN-001 → graph found a bridge → added direct links → bridge resolved → score hit 100/100
3. Parser didn't catch empty tags → wrote test proving the bug → fixed parser → test passes

The predecessor's tools could *describe* problems but nothing *closed the loop* — no tool led to a fix that improved the score.

### 6. Content from doing, not from reading

The predecessor's 269 entries were generated in one session by researching topics (Zettelkasten, ACT-R, CAS theory). The content was a survey, not experience.

Engram's entries come from building engram:
- DEC-001: Why individual files? Because the predecessor's mega-files didn't work.
- LRN-001: Functional tests catch more than syntax tests. Discovered while writing tests.
- MST-001: Parser accepted empty tags. Found while building, fixed, tested.
- OBS-001: Predecessor's tools:content ratio was 6.7:1. Observed during review.
- LRN-002: 6 modules is enough. Learned by building only what was needed.

Every entry is grounded in something that actually happened.

## What's Not Here (and Why)

- **No PageRank visualization** — PageRank is computed (5 LOC in graph.py) but not visualized with ASCII art. The number is enough.
- **No stress testing** — Bridges and clusters already tell you about fragility. A separate chaos engineering suite is overkill for a <100 entry system.
- **No recommendation engine** — The validator and health score surface problems. A human decides what to do. That's the right split.
- **No self-portrait / introspection report** — The system doesn't need to write about itself. `health` + `validate` + `graph` give you the picture.
- **No evolution simulator** — The system evolves when you use it, not when you simulate evolution.

## Architecture

```
entries/               # One markdown file per knowledge entry
├── GOL-001.md         #   YAML frontmatter + markdown body
├── DEC-001.md
├── LRN-001.md
├── MST-001.md
├── OBS-001.md
└── ...

tools/                 # 6 Python modules
├── parser.py          #   Read entries → Entry objects
├── validator.py       #   Check consistency → Issues
├── graph.py           #   Build graph → Stats, bridges, PageRank
├── query.py           #   Search/filter → Results
├── health.py          #   Score → 0-100
└── cli.py             #   Interface → Human

tests/                 # 119 functional tests
├── test_parser.py     #   "Does it catch bad data?"
├── test_validator.py  #   "Does it find real problems?"
├── test_graph.py      #   "Does it compute correctly on known structures?"
├── test_health.py     #   "Does the score respond to degradation?"
└── test_query.py      #   "Does search find the right things?"

schema.yaml            # Entry format definition
DESIGN.md              # This document
```

## Numbers

| Metric | Value |
|--------|-------|
| Python modules | 7 (parser, validator, graph, query, health, review, cli) |
| Tool LOC | ~1,200 |
| Tests | 139 (30 parser + 28 validator + 24 graph + 22 query + 16 health + 11 review + 8 integration) |
| Test pass rate | 100% |
| Test runtime | 0.4s |
| Entry types | 5 |
| Entries | 28 (6 decisions, 9 learnings, 6 mistakes, 6 observations, 2 goals) |
| Health score | 97/100 |
| Validation errors | 0 |
| External dependencies | 0 |
| Decisions superseded | 1 (DEC-002 → DEC-004) |
| Tool limitations found and fixed | 3 (review queue, integration tests, bidirectional supersession) |

## Closed Loops (things the system caught and fixed during its own build)

1. **Bridge detected → fixed**: Graph found LRN-001 was a structural chokepoint (97/100). Added direct links from MST-001 to core entries → 100/100.
2. **Missing review mechanism → built**: PKM research (LRN-003) revealed "notes never reviewed" is a top failure mode. System had no review queue → built one (review.py).
3. **No integration tests → added**: MST-003 identified that CLI had zero automated tests. Built 8 end-to-end tests covering full pipeline.
4. **One-directional supersession check → fixed**: MST-004 found validator only checked supersession forward, not reverse. Added bidirectional check.
5. **Wrong goal metric → corrected**: MST-006 identified that "30+ entries" was a quantity goal that incentivized filler. System's own "so what?" principle (DEC-003) contradicted its own goal (GOL-002).
6. **Research became its own trap → stopped**: DEC-004 superseded DEC-002 when PKM meta-research started becoming the Collector's Fallacy it was studying.

## How to Use

```bash
python3 -m tools health          # Am I healthy?
python3 -m tools validate        # What's broken?
python3 -m tools list            # Show all entries
python3 -m tools list decisions  # Filter by type
python3 -m tools search <query>  # Find entries
python3 -m tools show <id>       # Entry details + backlinks
python3 -m tools graph           # Connection stats
python3 -m tools review          # What needs attention today?
python3 -m tools path <id> <id>  # How are two entries connected?
```
