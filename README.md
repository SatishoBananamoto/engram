# engram

Structured knowledge system for AI coding agents. Tracks decisions, learnings, mistakes, observations, and goals across projects.

## What It Does

AI agents lose context between sessions. Engram preserves the reasoning that code and git cannot: why you chose A over B, what broke and how to prevent it, patterns that span projects.

```
engram_search(query="rate limiting")
→ DEC-007: PyPI-only for transitive deps (vigil)
→ LRN-023: Stale signals compress dead package scores (vigil)
→ DEC-008: Budget tracking approach (vigil)
```

## Entry Types

| Type | Code | Example |
|------|------|---------|
| Decision | DEC | "Used PyPI-only for transitive deps because GitHub API budget" |
| Learning | LRN | "Stale positive signals inflate health scores on dead packages" |
| Mistake | MST | "Parser silently accepted entries with missing tags" |
| Observation | OBS | "Cross-tool integration creates emergent value" |
| Goal | GOL | "Build a knowledge system that proves itself by being used" |

## MCP Server

Engram runs as an MCP server for Claude Code:

```json
{
  "mcpServers": {
    "engram": {
      "command": "python3",
      "args": ["/path/to/engram/server.py"]
    }
  }
}
```

Tools: `engram_search`, `engram_add`, `engram_list`, `engram_show`, `engram_health`, `engram_graph`, `engram_validate`, `engram_path`, `engram_review`.

## Knowledge Graph

Entries link to each other forming a knowledge graph. The graph reveals non-obvious connections between projects:

- 100+ entries across 7 projects
- Cross-project links (vigil learnings inform caliber design)
- Health scoring: integrity, connectivity, freshness, coverage

## Integration with scroll

[scroll](https://github.com/SatishoBananamoto/scroll) extracts knowledge from git history and deposits it into engram automatically:

```bash
scroll ingest -n 10 -p my-project
scroll deposit -p my-project
```

## License

MIT
