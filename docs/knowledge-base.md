# Knowledge Base

The knowledge base is the agent's durable ancestral memory.

## Purpose

`openPasture` should not rely only on generic model priors. It should reason with curated lessons from trusted practitioners and connect those lessons to the daily condition of a specific farm.

## Canonical Storage

Curated ancestral knowledge is stored as Markdown files in this repository. Those
Markdown files are the source of truth an agent should edit, review, and commit.
Runtime databases, embeddings, and search indexes are generated artifacts built
from the Markdown corpus; they are useful for retrieval but are not the durable
knowledge base.

Raw transcripts should not be committed here. For YouTube ingestion, store the
raw transcript in the transcript repository and include a reference to that
transcript in the knowledge Markdown frontmatter.

## Source Types

The first ingestion focus is YouTube transcripts from trusted rotational and regenerative grazing practitioners.

Examples of source categories:

- rotational grazing instruction,
- daily movement practices,
- animal behavior signals,
- multi-species sequencing,
- pasture observation heuristics,
- technology-assisted pasture systems.

## Extraction Model

Every source should be distilled into one or more `KnowledgeEntry` objects.

The initial types are:

- `principle`: a durable rule of thumb,
- `technique`: a repeatable management move,
- `signal`: something observable that changes interpretation,
- `mistake`: a known anti-pattern or warning sign.

## Pipeline

```mermaid
flowchart LR
    Source[SourceURL] --> Transcript[TranscriptAcquisition]
    Transcript --> TranscriptRepo[TranscriptRepo]
    TranscriptRepo --> Markdown[KnowledgeMarkdown]
    Markdown --> Embedding[EmbeddingGeneration]
    Embedding --> Retrieval[RetrievalAtPlanTime]
```

## Retrieval During Planning

When the agent evaluates a movement decision, it should retrieve the most relevant knowledge entries for the current farm context rather than loading the entire corpus blindly.

The result should ground recommendations in explicit lessons and make the reasoning legible.

## Seed Knowledge

The repository includes starter knowledge based on cross-cutting principles and named practitioners. This seed exists to make the first local test useful before a farmer adds their own sources. Starter lessons should follow the same Markdown format as newly ingested knowledge.

## Batch Operations

Author-scale ingestion should use batch manifests and queue-driven processing rather than one-off scripts. The reusable runner now supports:

- creating an ingestion batch from discovered sources,
- claiming one source at a time for agent processing,
- recording source-level results,
- inspecting batch totals and failures.

## Productization

For the product path of the shared ancestral corpus, see `docs/knowledge-productization.md`.
