"""
Engram Parser

Reads individual markdown entry files from entries/ directory.
Each file has YAML frontmatter (between --- delimiters) and markdown body.

Returns structured Entry objects with all metadata extracted.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Valid entry types and their ID prefixes
VALID_TYPES = {
    "decision": "DEC",
    "learning": "LRN",
    "mistake": "MST",
    "observation": "OBS",
    "goal": "GOL",
}

VALID_STATUSES = {"active", "superseded", "archived", "stale"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCES = {"manual", "scroll"}

# Frontmatter parsing patterns
FRONTMATTER_RE = re.compile(r"^---\s*\n(.+?)\n---\s*\n", re.DOTALL)
YAML_KV_RE = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)
YAML_LIST_RE = re.compile(r"^\s*-\s*(.+)$", re.MULTILINE)


@dataclass
class Entry:
    """A single knowledge entry."""
    id: str
    type: str
    date: str
    tags: list[str] = field(default_factory=list)
    status: str = "active"
    links: list[str] = field(default_factory=list)
    supersedes: Optional[str] = None
    project: Optional[str] = None
    confidence: Optional[str] = None
    source: str = "manual"
    title: str = ""
    body: str = ""
    file_path: Optional[str] = None

    @property
    def prefix(self) -> str:
        return self.id.split("-")[0] if "-" in self.id else ""

    @property
    def number(self) -> int:
        try:
            return int(self.id.split("-")[1])
        except (IndexError, ValueError):
            return 0


@dataclass
class ParseError:
    """An error encountered during parsing."""
    file_path: str
    message: str


def parse_yaml_list(raw: str) -> list[str]:
    """Parse a YAML-style list: [a, b, c] or multiline - items."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    # Multiline list
    items = YAML_LIST_RE.findall(raw)
    return [item.strip() for item in items]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file.

    Returns (metadata_dict, body_text).
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw_yaml = match.group(1)
    body = text[match.end():]

    metadata = {}
    for kv_match in YAML_KV_RE.finditer(raw_yaml):
        key = kv_match.group(1).strip()
        value = kv_match.group(2).strip()

        # Detect lists
        if value.startswith("["):
            metadata[key] = parse_yaml_list(value)
        else:
            metadata[key] = value.strip("'\"")

    return metadata, body.strip()


def extract_title(body: str) -> str:
    """Extract the first H1 heading as the title."""
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return ""


def parse_entry(file_path: Path) -> tuple[Optional[Entry], list[ParseError]]:
    """Parse a single entry file.

    Returns (entry_or_none, list_of_errors).
    """
    errors = []
    path_str = str(file_path)

    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, [ParseError(path_str, f"Cannot read file: {e}")]

    if not text.strip():
        return None, [ParseError(path_str, "Empty file")]

    metadata, body = parse_frontmatter(text)

    if not metadata:
        return None, [ParseError(path_str, "No YAML frontmatter found")]

    # Required fields
    entry_id = metadata.get("id")
    if not entry_id:
        errors.append(ParseError(path_str, "Missing required field: id"))

    entry_type = metadata.get("type")
    if not entry_type:
        errors.append(ParseError(path_str, "Missing required field: type"))
    elif entry_type not in VALID_TYPES:
        errors.append(ParseError(path_str, f"Invalid type '{entry_type}'. Valid: {list(VALID_TYPES.keys())}"))

    entry_date = metadata.get("date")
    if not entry_date:
        errors.append(ParseError(path_str, "Missing required field: date"))

    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if not tags:
        errors.append(ParseError(path_str, "Missing required field: tags"))

    status = metadata.get("status", "active")
    if status not in VALID_STATUSES:
        errors.append(ParseError(path_str, f"Invalid status '{status}'. Valid: {VALID_STATUSES}"))

    # If we have blocking errors on required fields, bail
    if not entry_id or not entry_type or not entry_date:
        return None, errors

    # Validate ID matches type prefix
    expected_prefix = VALID_TYPES.get(entry_type, "")
    if expected_prefix and not entry_id.startswith(expected_prefix + "-"):
        errors.append(ParseError(path_str, f"ID '{entry_id}' doesn't match type '{entry_type}' (expected prefix: {expected_prefix}-)"))

    # Optional fields
    links = metadata.get("links", [])
    if isinstance(links, str):
        links = [links]

    supersedes = metadata.get("supersedes")
    project = metadata.get("project")
    confidence = metadata.get("confidence")
    source = metadata.get("source", "manual")

    if confidence and confidence not in VALID_CONFIDENCE:
        errors.append(ParseError(path_str, f"Invalid confidence '{confidence}'. Valid: {VALID_CONFIDENCE}"))

    if source not in VALID_SOURCES:
        errors.append(ParseError(path_str, f"Unknown source '{source}'. Known: {VALID_SOURCES}"))

    title = extract_title(body)

    entry = Entry(
        id=entry_id,
        type=entry_type,
        date=entry_date,
        tags=tags,
        status=status,
        links=links,
        supersedes=supersedes,
        project=project,
        confidence=confidence,
        source=source,
        title=title,
        body=body,
        file_path=path_str,
    )

    return entry, errors


def load_entries(entries_dir: Path) -> tuple[list[Entry], list[ParseError]]:
    """Load all entries from a directory.

    Returns (entries, all_errors).
    """
    entries = []
    all_errors = []

    if not entries_dir.exists():
        return entries, [ParseError(str(entries_dir), "Entries directory not found")]

    for md_file in sorted(entries_dir.glob("*.md")):
        entry, errors = parse_entry(md_file)
        all_errors.extend(errors)
        if entry:
            entries.append(entry)

    return entries, all_errors


def load_knowledge_base(root: Path = None) -> tuple[list[Entry], list[ParseError]]:
    """Load the full knowledge base from the project root.

    Returns (entries, errors).
    """
    if root is None:
        root = Path(__file__).resolve().parent.parent

    entries_dir = root / "entries"
    return load_entries(entries_dir)
