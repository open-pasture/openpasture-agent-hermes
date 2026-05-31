from __future__ import annotations

from datetime import datetime

import pytest

import openpasture.runtime as runtime
from openpasture.domain import KnowledgeEntry, SourceRecord
from openpasture.knowledge.seed_loader import load_markdown_knowledge_entries
from openpasture.runtime import get_knowledge_store, init_knowledge_store, initialize

pytestmark = pytest.mark.alpha


def test_initialize_autoloads_seed_on_first_run(monkeypatch):
    monkeypatch.delenv("OPENPASTURE_LOAD_SEED", raising=False)

    initialize()

    assert get_knowledge_store().count() > 0


def test_initialize_skips_autoload_when_store_already_has_entries(monkeypatch):
    monkeypatch.delenv("OPENPASTURE_LOAD_SEED", raising=False)

    store = init_knowledge_store()
    store.store_entries(
        [
            KnowledgeEntry(
                id="knowledge_existing",
                farm_id=None,
                entry_type="principle",
                content="Existing local knowledge should not trigger seed reload.",
                sources=[
                    SourceRecord(
                        source_url="https://example.com/existing",
                        source_title="Existing Entry",
                        source_author="Local Farmer",
                        source_kind="manual",
                    )
                ],
                created_at=datetime.utcnow(),
                tags=["local"],
                category="grazing-management",
            )
        ]
    )

    def fail_loader(*args, **kwargs):
        raise AssertionError("Seed loader should not run when knowledge.db already has entries.")

    monkeypatch.setattr(runtime, "load_seed_knowledge", fail_loader)

    initialize()

    assert get_knowledge_store().count() == 1


def test_openpasture_load_seed_zero_skips_first_run(monkeypatch):
    monkeypatch.setenv("OPENPASTURE_LOAD_SEED", "0")

    initialize()

    assert get_knowledge_store().count() == 0


def test_openpasture_load_seed_one_forces_reload(monkeypatch):
    monkeypatch.setenv("OPENPASTURE_LOAD_SEED", "1")

    store = init_knowledge_store()
    store.store_entries(
        [
            KnowledgeEntry(
                id="knowledge_existing",
                farm_id=None,
                entry_type="principle",
                content="Existing local knowledge should not block a forced reload.",
                sources=[
                    SourceRecord(
                        source_url="https://example.com/existing",
                        source_title="Existing Entry",
                        source_author="Local Farmer",
                        source_kind="manual",
                    )
                ],
                created_at=datetime.utcnow(),
                tags=["local"],
                category="grazing-management",
            )
        ]
    )

    calls = {"count": 0}

    def fake_loader(*args, **kwargs):
        calls["count"] += 1
        return []

    monkeypatch.setattr(runtime, "load_seed_knowledge", fake_loader)

    initialize()

    assert calls["count"] == 1


def test_markdown_seed_loader_preserves_transcript_reference(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "_template.md").write_text("ignored")
    (knowledge_dir / "lesson.md").write_text(
        """---
id: greg-judy-rumen-fill-001
title: Rumen fill shows allocation
author: Greg Judy
entry_type: signal
category: animal-behavior
tags:
  - animal-signals
  - allocation
source_kind: youtube
source_url: https://www.youtube.com/watch?v=abc123
source_title: Reading Cattle on Pasture
transcript_repo: openpasture-transcripts
transcript_path: greg-judy/reading-cattle-on-pasture.md
transcript_ref: openpasture-transcripts/greg-judy/reading-cattle-on-pasture.md#L120-L155
segment: 00:12:00-00:15:30
---

Rumen fill after a move helps show whether the last allocation was close.
"""
    )

    entries = load_markdown_knowledge_entries(knowledge_dir)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.id == "greg-judy-rumen-fill-001"
    assert entry.entry_type == "signal"
    assert entry.category == "animal-behavior"
    assert entry.tags == ["animal-signals", "allocation"]
    assert entry.content == "Rumen fill after a move helps show whether the last allocation was close."

    source = entry.primary_source
    assert source is not None
    assert source.source_url == "https://www.youtube.com/watch?v=abc123"
    assert source.source_title == "Reading Cattle on Pasture"
    assert source.source_author == "Greg Judy"
    assert source.source_kind == "youtube"
    assert source.segment == "00:12:00-00:15:30"
    assert source.transcript_repo == "openpasture-transcripts"
    assert source.transcript_path == "greg-judy/reading-cattle-on-pasture.md"
    assert (
        source.transcript_ref
        == "openpasture-transcripts/greg-judy/reading-cattle-on-pasture.md#L120-L155"
    )


def test_initialize_loads_markdown_seed_entries(monkeypatch):
    monkeypatch.delenv("OPENPASTURE_LOAD_SEED", raising=False)

    initialize()

    store = get_knowledge_store()
    entry = store.get_entry("greg-judy-rumen-fill")
    assert entry is not None
    assert entry.primary_author == "Greg Judy"
    assert entry.primary_source is not None
    assert entry.primary_source.transcript_repo == "none"
