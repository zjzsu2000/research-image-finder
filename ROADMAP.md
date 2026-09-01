# ROADMAP.md — Research Image Finder V0.1

Status: **pre-implementation roadmap; stop for design review before spikes**
Last updated: 2026-08-31

The full Research Preflight roadmap is paused. The next product is a narrow, local-only,
folder-scoped, no-LLM source-image finder. No production code begins until the documentation,
result contract, and spike fixtures are reviewed.

## Phase 0 — Resolve the implementation contract

Required before S1–S3 begin:

- approve the Image Finder product boundary in README/PRODUCT/MVP;
- preserve ADR-0009's zero-socket default and ADR-0010's no-benign-inference rule;
- define supported query/source formats provisionally for S1;
- define canonical root and symlink policy per supported platform;
- define the minimal candidate-result and run/coverage contracts without reusing “Finding” by
  implication;
- decide whether the first usability shell is CLI + local HTML or a minimal desktop shell;
- prepare openly licensed fixtures and authorization-safe design-partner procedures;
- freeze S1–S3 definitions, splits, denominators, and stop decisions;
- specify supported OS/hardware for privacy and filesystem enforcement;
- decide how mounted network filesystems are detected, denied, or disclosed.

> ### STOP/REVIEW GATE 0 — design ready for spikes
>
> Confirm that the repository describes one product: query image + explicit authorized local
> roots + candidate source files. Confirm no author/publication crawler, manuscript scanner,
> LLM, persistent triage, or production implementation has entered scope.

## S1 — Folder discovery and decoder reality

Build only disposable evaluation code needed to answer:

- Which file formats and directory structures occur in real authorized lab folders?
- Can traversal remain inside explicit roots across symlinks, aliases/junctions, external drives,
  permissions, and file changes?
- What percentage of intended source files can the selected decoders actually read by slice?
- Is one-off scanning usable, or does a persistent index provide material benefit?
- Which raw/proprietary formats are common enough to change the product promise?

Outputs: frozen supported-format matrix, discovery/decode coverage report, privacy findings,
one-off-versus-index timing, and a decision to retain or drop the reusable index.

> ### STOP/REVIEW GATE 1 — scope reality
>
> If the desired files are mostly unsupported raw formats, do not hide the gap with aggregate
> coverage. Narrow the promise, choose a trusted decoder integration for evaluation, or stop. If
> an index does not materially improve the real job, remove it from V0.1.

## S2 — Candidate retrieval and geometric verification

Build disposable comparisons for:

- exhaustive ORB/SIFT baselines;
- candidate generation by pHash or other cheap deterministic signals;
- constrained similarity/affine-first verification;
- separately gated low-texture NCC/phase-correlation fallback;
- grouping without automatic legitimate-reuse suppression;
- runtime across measured directory sizes.

Outputs: candidate recall against the exhaustive oracle, synthetic transform-envelope results,
real-pair results, control-query candidate burden, per-slice failures, confidence intervals, and
actual sample sizes.

Decisions:

- drop any pruning prefilter below 99% candidate recall;
- do not add pretrained embeddings or model weights in V0.1;
- constrain/drop homography if it overfits;
- mark a content type unsupported if no path clears its predeclared negative benchmark;
- freeze only the transformation envelope supported by evidence.

> ### STOP/REVIEW GATE 2 — evidence path
>
> Synthetic results remain transform-envelope results, never field recall. Real pairs and
> controls remain separate. Review the actual control size and residual uncertainty. There is no
> ≥50-manuscript V0.1 ship gate.

## S3 — Real end-to-end retrieval

Run the narrow workflow with researchers on their machines and authorized files:

1. select one realistic query;
2. select the folder/drive scope;
3. run with sockets denied;
4. inspect ranked evidence;
5. open and confirm the original file;
6. run at least one absent-source or hard-negative case.

Measure source recovery, candidate rank, candidates inspected, time to confirmation, false
confirmation, abandonment, coverage understanding, and usefulness of paths/metadata/evidence.

> ### STOP/REVIEW GATE 3 — product value
>
> Proceed only if the workflow helps users locate sources and its failures are visible. Let the
> next real request determine whether the next step is better format support, metadata, reusable
> indexing, or multiple explicitly selected panels. Do not infer that a successful image matcher
> validates the broader Research Preflight platform.

## Production implementation — not started

Only after Gates 0–3 may a separate reviewed plan authorize production modules. That plan must
include tests first for:

- zero-socket and filesystem boundaries;
- discovery/decoder coverage;
- deterministic candidate/verification identity;
- output-language and product-surface safety;
- result evidence and provenance;
- index recovery, only if retained;
- offline packaging.

This roadmap does not authorize implementation now.

## Deferred Research Preflight work

The following are deliberately not scheduled for V0.1:

- manuscript PDF figure extraction and panel segmentation;
- automatic multi-panel provenance checking;
- within-manuscript duplicate review;
- authorized prior-paper corpus comparison;
- numeric, statistical, citation, or reference checks;
- persistent finding triage and institutional reports;
- local or remote LLM capabilities;
- network-enabled modes;
- custom model development;
- author/publication discovery or third-party investigation workflows.

Possible evolution remains: Image Finder → multi-panel figure provenance → manuscript self-check →
broader Research Preflight. Each arrow requires observed user demand and a new safety/architecture
review.

## Open questions for the spikes

### DEFER_TO_SPIKE

- Exact supported image and raw-file formats.
- One-off scan versus reusable index.
- ORB versus SIFT and content-specific routing.
- Whether pHash has any safe pruning role.
- Whether NCC/phase correlation can handle low-texture sources without unacceptable controls.
- Similarity/affine constraints and whether any homography path is justified.
- Final transform/content envelope and thresholds.
- Directory size at which indexing or coarse retrieval becomes necessary.
- Which path/date/metadata context users need to confirm provenance.
- Whether the next workflow is multiple manually selected panels.

### Resolve before production implementation, not by spikes alone

- Candidate-result schema and durable identity.
- Canonical serialization and float quantization.
- Supported OS security mechanisms and mounted-network-filesystem policy.
- Static-result/desktop rendering security.
- Offline packaging matrix.
- Dependency and decoder threat review.
- Output deletion/retention behavior.
- Exact open/reveal integration and path-redaction behavior.

## Decisions already resolved

- **Strict Local:** zero sockets by default, `NullBackend`, no model; loopback model IPC is a
  separate future capability that exits the guarantee (ADR-0009).
- **Observed patterns:** technical exclusions are allowed; recurrence/inset/same-work heuristics may
  annotate, group, or demote but may not erase reviewable observations; final legitimate-reuse
  determination is human (ADR-0010).
- **Detection-quality framing:** confidence intervals, per-slice results, synthetic-versus-real
  separation, clustered/actionable counts, actual control size, and residual uncertainty are
  required. At least 50 expert-reviewed control manuscripts is not a V0.1 ship gate; it may be a
  later Research Preflight pilot/maturity target.
- **Product boundary:** self-audit first. V0.1 is a query-image search over explicit authorized
  local roots, not a publication crawler or investigation product.
