# Engram — Thesis

> What engram is. What it must become. Where the gap lives.

---

## The Problem

AI agents are amnesiac. Every session starts from zero. Git tells you *what* changed. Code tells you *how* it works. But neither tells you:

- Why did we choose this approach over that one?
- What went wrong last time we tried something similar?
- What pattern keeps appearing across different projects?
- What should I be careful about that isn't obvious from the code?

This knowledge lives in conversations that end, in decisions made at 2am that nobody wrote down, in lessons that were learned but never landed anywhere durable. When the session closes, it's gone.

## The Thesis

**An AI agent with access to engram should make better decisions than one without it.**

That's the only test that matters. Not how many entries exist. Not how clean the graph is. Not what the health score says. Does the agent decide better because engram exists?

Engram is the structured knowledge layer that holds what code and git cannot:
- **Decisions** with reasoning and rejected alternatives
- **Learnings** discovered through doing, not reading
- **Mistakes** with root causes and prevention strategies
- **Observations** of patterns that haven't become conclusions yet
- **Goals** that define what success looks like

Every entry must pass the "so what?" test (DEC-003): if removing it wouldn't cause someone to make a wrong decision, it doesn't belong.

## What Engram Is Today

**51 entries of genuine quality.** Every one is real reasoning from real work across 5 projects — not filler, not implementation details, not restated git commits. The "so what?" test is enforced through culture and it works. Content quality is the strongest thing about engram.

**A well-built personal filing cabinet.** Seven modules, ~1,300 LOC, 139 tests, zero external deps. The validator catches real problems. Health scoring responds to degradation. The MCP server makes it accessible to any Claude Code session. The architecture is clean — parser → validator/graph/query/health/review → CLI/MCP.

**But fundamentally passive.** It stores knowledge. It validates consistency. It scores health. It surfaces things for review. It does not *do* anything with the knowledge. An agent queries engram, gets text back, and decides for itself what to do with it. Engram has no opinion about whether the answer was useful, whether the agent used it correctly, or whether two entries contradict each other.

Honest shape: **a library with no librarian.**

## What's Missing — Three Layers

The gap isn't "add field X" or "build feature Y." The gap is between what engram stores and what engram enables.

### Layer 1: Identity — Engram doesn't know what it contains

There is no `source` field. Engram can't distinguish curated reasoning from auto-extracted git data. If scroll deposits 200 entries, they're indistinguishable from the 51 hand-written ones.

There is no domain taxonomy. Cross-project queries depend on agents guessing the right freeform tag. One agent writes "security," another writes "auth," another writes "access-control." Same knowledge, invisible to each other.

There is no provenance. Who wrote this? In what context? What evidence supports the confidence level?

**Consequence:** You can't query "what does engram know about security across all projects?" and get a reliable answer. That's the most basic thing a cross-project knowledge system should do.

### Layer 2: Boundaries — Engram can't protect its own signal

If any source can write any entry with no distinction, engram's value degrades as it grows. The DEC-008 incident proved it — an agent logged implementation details because nothing stopped it. The dilution concern with scroll proved it from the other direction — 200 git-extracted entries would drown 51 curated ones.

Without boundaries:
- Core knowledge (curated reasoning) mixes with supporting evidence (git extractions)
- No mechanism for tiers, weight, or source separation
- Quality depends entirely on the discipline of whoever writes entries
- Growth becomes the enemy of signal

**Consequence:** The more engram grows, the harder it is to find what matters. That's the opposite of what a knowledge system should do.

### Layer 3: Connection — Engram doesn't surface what matters when it matters

The review queue is pull-only. 10 items are overdue because nobody runs it. The graph has 6 disconnected clusters — knowledge from vigil literally cannot reach knowledge from engram through links. PageRank exists but runs only on demand.

What a real knowledge backbone would do:
- Surface relevant entries *before* you start a task
- Warn when two entries contradict each other
- Notice when the same mistake appears across different projects
- Flag when a decision's reasoning is invalidated by new evidence
- Know when knowledge was used and whether it helped

None of that exists. The graph infrastructure is there, but it's inert.

**Observed (2026-03-26):** Satish reported that other Claude sessions check engram but never update it. Root cause: the CLAUDE.md instructions positioned engram as before/after bookends around work, not as triggers during work. Agents skip the "after" because it never clearly arrives. Fixed by rewriting instructions to fire on events (choosing between alternatives, finding root cause, discovering something non-obvious). This is the cheapest intervention — zero code change — but the deeper problem (engram is passive, doesn't surface knowledge proactively) remains.

**Consequence:** Engram depends on the agent already knowing what to look for. If you don't search, you don't find. The knowledge is there but it doesn't reach you.

## The Gap in One Sentence

Engram stores knowledge well but doesn't behave like a knowledge system.

## What It Must Become

Three stages, in order. Each builds on the previous.

### Stage 1: Know Itself

Engram must know what it contains and how things connect. This means:
- **Source field** — distinguish curated from extracted from imported
- **Connectivity** — one graph, not six islands
- **Domain taxonomy** — structured vocabulary for cross-project queries

Without this, everything else is built on a fragmented foundation.

### Stage 2: Protect Its Signal

Engram must keep core knowledge clean as it grows. This means:
- **Quality guardrails** — reject entries that fail the "so what?" test programmatically
- **Source-aware queries** — show provenance, let users scope by source
- **Entry creation tools** — reduce friction so the right knowledge gets in easily

Without this, growth dilutes quality.

### Stage 3: Act On What It Knows

Engram must become proactive. This means:
- **Relevant entries surfaced at task start** — not waiting for search
- **Contradiction detection** — two entries that disagree should be flagged
- **Cross-project pattern recognition** — same mistake in vigil and kv-secrets should be visible
- **Review enforcement** — not pull-only, not ignorable

Without this, engram is a reference book nobody opens.

## How We'll Know It's Working

The thesis is testable. Not today — but the evidence will accumulate:

1. Sessions that check engram make fewer repeated mistakes
2. Cross-project patterns are caught before they cause damage
3. New agents on old projects ramp up faster because the reasoning is preserved
4. The knowledge base grows without losing signal-to-noise
5. Entries are used, not just stored

If these things don't happen, engram failed — regardless of how clean the code is.

---

> Referenced by: [TRACE.md](TRACE.md) — operational plan for building toward this thesis.
