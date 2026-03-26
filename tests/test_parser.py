"""
Parser Tests — Functional Validation

These tests verify the parser DOES ITS JOB, not just that code runs:
1. Can it parse a well-formed entry correctly?
2. Does it catch missing required fields?
3. Does it catch invalid types, statuses, confidence levels?
4. Does it handle empty files, missing frontmatter, bad encoding?
5. Does it correctly extract titles, tags, links?
6. Does it validate ID-type prefix consistency?
"""

import pytest
from pathlib import Path
from tools.parser import (
    parse_entry,
    parse_frontmatter,
    extract_title,
    parse_yaml_list,
    load_entries,
    Entry,
    ParseError,
    VALID_TYPES,
    VALID_STATUSES,
    VALID_SOURCES,
)


@pytest.fixture
def tmp_entries(tmp_path):
    """Create a temporary entries directory."""
    entries_dir = tmp_path / "entries"
    entries_dir.mkdir()
    return entries_dir


def write_entry(directory: Path, filename: str, content: str) -> Path:
    """Helper to write an entry file."""
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


# --- parse_yaml_list ---

class TestParseYamlList:
    def test_bracket_list(self):
        assert parse_yaml_list("[a, b, c]") == ["a", "b", "c"]

    def test_bracket_list_with_quotes(self):
        assert parse_yaml_list("['a', \"b\"]") == ["a", "b"]

    def test_empty_bracket_list(self):
        assert parse_yaml_list("[]") == []

    def test_single_item(self):
        assert parse_yaml_list("[foo]") == ["foo"]


# --- parse_frontmatter ---

class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        text = "---\nid: DEC-001\ntype: decision\n---\n\n# Title"
        meta, body = parse_frontmatter(text)
        assert meta["id"] == "DEC-001"
        assert meta["type"] == "decision"
        assert body == "# Title"

    def test_no_frontmatter(self):
        text = "Just some markdown\n# No frontmatter here"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_list_in_frontmatter(self):
        text = "---\ntags: [python, testing]\n---\n\nbody"
        meta, body = parse_frontmatter(text)
        assert meta["tags"] == ["python", "testing"]

    def test_empty_body(self):
        text = "---\nid: X\n---\n"
        meta, body = parse_frontmatter(text)
        assert meta["id"] == "X"
        assert body == ""


# --- extract_title ---

class TestExtractTitle:
    def test_h1_title(self):
        assert extract_title("# My Title\n\nSome text") == "My Title"

    def test_no_title(self):
        assert extract_title("No heading here\nJust text") == ""

    def test_h2_not_title(self):
        assert extract_title("## Not a title\n# Real Title") == "Real Title"

    def test_title_with_spaces(self):
        assert extract_title("#   Spaced Title  ") == "Spaced Title"


# --- parse_entry: VALID entries ---

class TestParseEntryValid:
    def test_well_formed_decision(self, tmp_entries):
        content = """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [architecture, storage]
status: active
project: engram
confidence: high
links: [GOL-001]
---

# One file per entry

## Context

Testing the parser.

## Choice

Individual files.
"""
        path = write_entry(tmp_entries, "DEC-001.md", content)
        entry, errors = parse_entry(path)

        assert entry is not None
        assert entry.id == "DEC-001"
        assert entry.type == "decision"
        assert entry.date == "2026-03-16"
        assert entry.tags == ["architecture", "storage"]
        assert entry.status == "active"
        assert entry.project == "engram"
        assert entry.confidence == "high"
        assert entry.links == ["GOL-001"]
        assert entry.title == "One file per entry"
        assert entry.prefix == "DEC"
        assert entry.number == 1
        assert len(errors) == 0

    def test_minimal_valid_entry(self, tmp_entries):
        content = """---
id: OBS-001
type: observation
date: 2026-03-16
tags: [test]
status: active
---

# A minimal observation
"""
        path = write_entry(tmp_entries, "OBS-001.md", content)
        entry, errors = parse_entry(path)

        assert entry is not None
        assert entry.id == "OBS-001"
        assert entry.links == []
        assert entry.project is None
        assert entry.confidence is None
        assert len(errors) == 0

    def test_goal_entry(self, tmp_entries):
        content = """---
id: GOL-001
type: goal
date: 2026-03-16
tags: [engram, core]
status: active
---

# Build a knowledge system
"""
        path = write_entry(tmp_entries, "GOL-001.md", content)
        entry, errors = parse_entry(path)
        assert entry is not None
        assert entry.type == "goal"
        assert entry.prefix == "GOL"


# --- parse_entry: INVALID entries (does it catch problems?) ---

class TestParseEntryInvalid:
    def test_missing_id(self, tmp_entries):
        content = """---
type: decision
date: 2026-03-16
tags: [test]
---

# No ID
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("Missing required field: id" in e.message for e in errors)

    def test_missing_type(self, tmp_entries):
        content = """---
id: DEC-099
date: 2026-03-16
tags: [test]
---

# No type
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("Missing required field: type" in e.message for e in errors)

    def test_missing_date(self, tmp_entries):
        content = """---
id: DEC-099
type: decision
tags: [test]
---

# No date
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("Missing required field: date" in e.message for e in errors)

    def test_missing_tags(self, tmp_entries):
        content = """---
id: DEC-099
type: decision
date: 2026-03-16
---

# No tags
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        # Entry still created (tags not blocking) but error reported
        assert any("Missing required field: tags" in e.message for e in errors)

    def test_invalid_type(self, tmp_entries):
        content = """---
id: DEC-099
type: nonsense
date: 2026-03-16
tags: [test]
---

# Bad type
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert any("Invalid type" in e.message for e in errors)

    def test_invalid_status(self, tmp_entries):
        content = """---
id: DEC-099
type: decision
date: 2026-03-16
tags: [test]
status: banana
---

# Bad status
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert any("Invalid status" in e.message for e in errors)

    def test_invalid_confidence(self, tmp_entries):
        content = """---
id: DEC-099
type: decision
date: 2026-03-16
tags: [test]
confidence: maybe
---

# Bad confidence
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert any("Invalid confidence" in e.message for e in errors)

    def test_id_prefix_mismatch(self, tmp_entries):
        content = """---
id: LRN-001
type: decision
date: 2026-03-16
tags: [test]
---

# Wrong prefix for type
"""
        path = write_entry(tmp_entries, "bad.md", content)
        entry, errors = parse_entry(path)
        assert any("doesn't match type" in e.message for e in errors)

    def test_empty_file(self, tmp_entries):
        path = write_entry(tmp_entries, "empty.md", "")
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("Empty file" in e.message for e in errors)

    def test_no_frontmatter(self, tmp_entries):
        content = "Just text, no YAML frontmatter at all."
        path = write_entry(tmp_entries, "nofm.md", content)
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("No YAML frontmatter" in e.message for e in errors)

    def test_nonexistent_file(self, tmp_entries):
        path = tmp_entries / "ghost.md"
        entry, errors = parse_entry(path)
        assert entry is None
        assert any("Cannot read file" in e.message for e in errors)


# --- load_entries: batch loading ---

class TestLoadEntries:
    def test_loads_multiple_entries(self, tmp_entries):
        for i in range(1, 4):
            write_entry(tmp_entries, f"OBS-{i:03d}.md", f"""---
id: OBS-{i:03d}
type: observation
date: 2026-03-16
tags: [test]
status: active
---

# Observation {i}
""")
        entries, errors = load_entries(tmp_entries)
        assert len(entries) == 3
        assert len(errors) == 0

    def test_skips_bad_entries_loads_good(self, tmp_entries):
        # One good
        write_entry(tmp_entries, "DEC-001.md", """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [test]
---

# Good entry
""")
        # One bad (no frontmatter)
        write_entry(tmp_entries, "bad.md", "no frontmatter here")

        entries, errors = load_entries(tmp_entries)
        assert len(entries) == 1
        assert entries[0].id == "DEC-001"
        assert len(errors) > 0  # The bad file generated errors

    def test_nonexistent_directory(self, tmp_path):
        fake_dir = tmp_path / "nonexistent"
        entries, errors = load_entries(fake_dir)
        assert len(entries) == 0
        assert any("not found" in e.message for e in errors)

    def test_empty_directory(self, tmp_entries):
        entries, errors = load_entries(tmp_entries)
        assert len(entries) == 0
        assert len(errors) == 0


# --- source field ---

class TestSourceField:
    def test_source_parsed(self, tmp_entries):
        content = """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [test]
source: scroll
---

# Scroll-extracted decision
"""
        path = write_entry(tmp_entries, "DEC-001.md", content)
        entry, errors = parse_entry(path)
        assert entry is not None
        assert entry.source == "scroll"

    def test_source_defaults_to_manual(self, tmp_entries):
        content = """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [test]
---

# No source field
"""
        path = write_entry(tmp_entries, "DEC-001.md", content)
        entry, errors = parse_entry(path)
        assert entry is not None
        assert entry.source == "manual"

    def test_source_manual_explicit(self, tmp_entries):
        content = """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [test]
source: manual
---

# Explicit manual source
"""
        path = write_entry(tmp_entries, "DEC-001.md", content)
        entry, errors = parse_entry(path)
        assert entry is not None
        assert entry.source == "manual"
        assert len(errors) == 0

    def test_unknown_source_warns(self, tmp_entries):
        content = """---
id: DEC-001
type: decision
date: 2026-03-16
tags: [test]
source: alien
---

# Unknown source
"""
        path = write_entry(tmp_entries, "DEC-001.md", content)
        entry, errors = parse_entry(path)
        assert entry is not None  # still parses — forward compatible
        assert entry.source == "alien"
        assert any("Unknown source" in e.message for e in errors)

    def test_entry_dataclass_default(self):
        entry = Entry(id="DEC-001", type="decision", date="2026-03-16")
        assert entry.source == "manual"

    def test_valid_sources_constant(self):
        assert "manual" in VALID_SOURCES
        assert "scroll" in VALID_SOURCES
