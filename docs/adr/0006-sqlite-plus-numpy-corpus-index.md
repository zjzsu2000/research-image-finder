# ADR-0006 — SQLite + NumPy memmap for the local corpus; no vector database

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [ARCHITECTURE.md §9](../../ARCHITECTURE.md), [EVALUATION.md § S4](../../EVALUATION.md), AC-13

## Context

The private lab corpus is the product's strategic differentiator
([PRODUCT.md §6](../../PRODUCT.md)). It needs an index over panels extracted from a lab's prior
papers, supporting nearest-neighbour retrieval from a subject manuscript.

"Nearest-neighbour search over embeddings" reliably summons a vector database — Qdrant, Milvus,
Chroma, pgvector, FAISS. That instinct is correct at scale and wrong here.

Actual sizing:

| Corpus | Panels | pHash scan | Embedding scan (768-d fp16) |
| --- | --- | --- | --- |
| 50 papers | ~1,500 | microseconds | ~2 MB, one BLAS call |
| 500 papers | ~15,000 | < 1 ms | ~23 MB, one BLAS call |
| 5,000 papers | ~150,000 | ~10 ms | ~230 MB, still trivially scannable |

Even at 100× a realistic lab corpus, brute force in NumPy is faster than the network round trip to
a vector database would be. A service would also introduce a daemon, a port, a connection string,
and a background process — every one of which is a liability in a tool whose central promise is
"nothing leaves this machine, and you can verify it" (ADR-0001).

## Decision

The corpus is a **portable directory**:

```
corpus/
  corpus.db                    # SQLite: documents, figures, panels, hashes, index_meta
  panels/<sha256>.png
  descriptors/<panel_id>.npz   # ORB/SIFT keypoints + descriptors
  embeddings.f16.npy           # memmapped [n_panels, dim], row-aligned to panels.row_id
  index_meta.json              # index_version, detector versions, embedding model + digest
```

Search cascade: pHash Hamming prefilter (brute force) → optional embedding cosine top-k → **ORB +
RANSAC geometric verification** (the only step that can produce a finding, per ADR-0005) →
suppression (content type, size, inset, recurring control, same-work).

No vector database, no server, no daemon, no background indexing process.

Row alignment between `panels.row_id` and the embedding matrix row index is the one invariant that
must hold; `index_meta.json` versions it, and any change to an extraction stage or the embedding
model marks affected rows stale for `preflight corpus reindex`.

**Revisit trigger:** above ~10⁵ panels *and* a measured latency problem. The first step then is
FAISS-Flat in-process — still no service.

## Rationale

- **There is no scale problem to solve.** Building infrastructure for one is the most likely way
  this project loses a month ([ARCHITECTURE.md §9](../../ARCHITECTURE.md)).
- **Portability is a user-visible feature.** The corpus is a folder the user owns: copy it,
  back it up, delete it, move it to another machine. A database service is none of those things.
- **It reduces the privacy attack surface to zero.** No listening port, no process to audit, no
  configuration that could point somewhere unexpected.
- **SQLite is the right tool for the relational part** — documents, figures, panels, provenance,
  staleness — and is in the standard library.
- **Memmap keeps memory flat.** A 150k-panel embedding matrix streams from disk without loading.
- **Debuggability.** A corrupt index is inspectable with `sqlite3` and a NumPy REPL, not a service
  dashboard.

## Consequences

**Positive.** Zero operational burden. Trivial backup, sharing, and deletion. No daemon in a
privacy-critical tool. Fast for every realistic corpus size. Simple to test — the whole index is
files. Air-gap friendly.

**Negative.** Brute-force scanning is O(n) per query, so a genuinely large index (institution-wide,
the future commercial layer) will need a different design — expected, and correctly deferred. No
concurrent multi-writer access, so two simultaneous `corpus build` runs are unsupported (guarded
by a lock file). Row alignment between SQLite and the `.npy` matrix is an invariant we maintain by
hand, and a compaction bug there would silently mismatch panels to embeddings — a specific risk
that deserves a dedicated test.

## Alternatives considered

- **FAISS.** Deferred, not rejected. It is the right *next* step above ~10⁵ panels, and it is
  in-process, so it would not violate the no-service principle. It is simply unnecessary now, and
  it adds a heavy dependency to an offline-install target (AC-14).
- **Qdrant / Milvus / Chroma as a service.** Rejected: a daemon and a port in a tool whose entire
  premise is verifiable locality.
- **pgvector / a Postgres dependency.** Rejected: enormous operational weight for a single-user
  desktop tool.
- **SQLite with a vector extension (sqlite-vec).** Attractive and worth revisiting; rejected for
  V0.1 only because it adds a compiled extension to the offline-install path for no measurable
  gain at current sizes.
- **A pure in-memory index rebuilt per run.** Rejected: corpus building is the expensive step
  (AC-13 allows 15 minutes) and must be amortized across runs.
