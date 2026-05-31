"""Load foundational Markdown grazing knowledge into the local knowledge base."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

from openpasture.domain import KnowledgeEntry, SourceRecord
from openpasture.domain.knowledge import KnowledgeType
from openpasture.knowledge.embedder import KnowledgeEmbedder
from openpasture.store.knowledge_protocol import KnowledgeStore


VALID_ENTRY_TYPES = {"principle", "technique", "signal", "mistake"}


def _knowledge_root() -> Path:
    return Path(__file__).resolve().parents[3] / "seed" / "knowledge"


def _split_frontmatter(text: str, path: Path) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ValueError(f"Knowledge Markdown '{path}' must start with frontmatter.")
    try:
        _, raw_frontmatter, body = text.split("---\n", 2)
    except ValueError as error:
        raise ValueError(f"Knowledge Markdown '{path}' has invalid frontmatter.") from error
    return _parse_frontmatter(raw_frontmatter, path), body.strip()


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_frontmatter(raw_frontmatter: str, path: Path) -> dict[str, object]:
    payload: dict[str, object] = {}
    current_list_key: str | None = None

    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise ValueError(f"Knowledge Markdown '{path}' has a list item without a key.")
            payload.setdefault(current_list_key, [])
            list_value = payload[current_list_key]
            if not isinstance(list_value, list):
                raise ValueError(f"Knowledge Markdown '{path}' has mixed scalar/list frontmatter.")
            list_value.append(_parse_scalar(line.removeprefix("  - ")))
            continue

        current_list_key = None
        if ":" not in line:
            raise ValueError(f"Knowledge Markdown '{path}' has invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Knowledge Markdown '{path}' has an empty frontmatter key.")
        if value.strip():
            payload[key] = _parse_scalar(value)
            continue
        payload[key] = []
        current_list_key = key

    return payload


def _require_text(payload: dict[str, object], key: str, path: Path) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"Knowledge Markdown '{path}' is missing required field '{key}'.")
    return value


def _optional_text(payload: dict[str, object], key: str) -> str | None:
    value = str(payload.get(key, "")).strip()
    return value or None


def _list_value(payload: dict[str, object], key: str, path: Path) -> list[str]:
    raw_value = payload.get(key, [])
    if not isinstance(raw_value, list):
        raise ValueError(f"Knowledge Markdown '{path}' field '{key}' must be a list.")
    return [str(item).strip() for item in raw_value if str(item).strip()]


def _entry_from_markdown(path: Path) -> KnowledgeEntry:
    payload, body = _split_frontmatter(path.read_text(), path)
    if not body:
        raise ValueError(f"Knowledge Markdown '{path}' must include lesson body text.")

    entry_type = _require_text(payload, "entry_type", path)
    if entry_type not in VALID_ENTRY_TYPES:
        raise ValueError(
            f"Knowledge Markdown '{path}' field 'entry_type' must be one of {sorted(VALID_ENTRY_TYPES)}."
        )

    source_title = _optional_text(payload, "source_title") or _require_text(payload, "title", path)
    return KnowledgeEntry(
        id=_require_text(payload, "id", path),
        farm_id=None,
        entry_type=cast(KnowledgeType, entry_type),
        content=" ".join(body.split()),
        sources=[
            SourceRecord(
                source_url=_require_text(payload, "source_url", path),
                source_title=source_title,
                source_author=_require_text(payload, "author", path),
                source_kind=_require_text(payload, "source_kind", path),
                segment=_optional_text(payload, "segment"),
                transcript_repo=_optional_text(payload, "transcript_repo"),
                transcript_path=_optional_text(payload, "transcript_path"),
                transcript_ref=_optional_text(payload, "transcript_ref"),
            )
        ],
        created_at=datetime.utcnow(),
        tags=_list_value(payload, "tags", path),
        category=_optional_text(payload, "category"),
    )


def load_markdown_knowledge_entries(root: str | Path | None = None) -> list[KnowledgeEntry]:
    """Read checked-in Markdown knowledge files without writing generated artifacts."""
    knowledge_root = Path(root) if root is not None else _knowledge_root()
    if not knowledge_root.exists():
        return []

    entries: list[KnowledgeEntry] = []
    for path in sorted(knowledge_root.rglob("*.md")):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        entries.append(_entry_from_markdown(path))
    return entries


def load_seed_knowledge(store: KnowledgeStore, embedder: KnowledgeEmbedder) -> list[KnowledgeEntry]:
    entries = load_markdown_knowledge_entries()
    if not entries:
        return []

    embedding_ids = embedder.embed(entries)
    for entry, embedding_id in zip(entries, embedding_ids, strict=False):
        entry.embedding_id = embedding_id
    store.store_entries(entries)
    return entries
