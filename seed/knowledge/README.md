# Curated Knowledge Markdown

This directory is the canonical source of truth for curated OpenPasture
ancestral knowledge. Each durable lesson belongs in its own Markdown file with
frontmatter that can be loaded into a `KnowledgeEntry`.

Generated databases, embedding indexes, queues, and batch files are retrieval or
workflow artifacts. Do not treat them as the durable corpus.

## Raw Transcripts

Raw YouTube transcripts live in the separate transcript repository. Knowledge
files in this directory should reference the transcript repo/path/range instead
of copying raw transcript text here.

For starter lessons that were not extracted from a transcript, set:

```yaml
source_kind: seed
transcript_repo: none
transcript_path: ""
transcript_ref: ""
```

## File Shape

Use `_template.md` for new lessons. Keep lesson bodies short, specific, and
useful in a movement or farm-planning decision.
