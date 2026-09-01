# MVP.md — Research Image Finder V0.1 Scope Contract

Status: **binding V0.1 scope; implementation has not started**
Last updated: 2026-08-31

This document is a contract. Anything not listed in §1 is out of scope for V0.1. When in doubt,
the answer is “not in V0.1.” It supersedes the repository's earlier Research Preflight V0.1 scope
without rewriting the historical ADRs or the deferred Finding schemas.

> Query image → authorized local roots → candidate retrieval → deterministic verification →
> evidence-ranked source files → human confirmation.

## 1. Exact V0.1 capabilities

### 1.1 Query ingest

- Accept one local raster query image or one user-created crop per search.
- Preserve the original query bytes and digest in run provenance; analysis works from a derived
  normalized representation.
- Report decode failures, dimensions, color/channel handling, and any normalization applied.
- Do not infer author, paper identity, scientific legitimacy, or experimental provenance from the
  query.

The exact supported file-format matrix remains a pre-spike decision. A format is not “supported”
until decode and evidence rendering are tested on representative files.

### 1.2 Explicit folder-scoped discovery

- Require the user to select one or more local directories or mounted-drive roots.
- Recursively inventory supported image files only within those roots.
- Do not silently scan the home directory, sibling directories, other mounted volumes, browser
  history, cloud accounts, paper databases, or network shares not explicitly selected.
- Do not follow a symlink outside an authorized root. Record symlinks, unreadable files, decode
  failures, unsupported types, and exclusions in coverage.
- Allow a one-off scan. Add a reusable local index only if S1/S2 show that it materially improves
  the real workflow without weakening correctness or privacy.

### 1.3 Candidate retrieval

- Produce candidate source files from deterministic image signals.
- Treat pHash/dHash, global descriptors, filename/date metadata, or other cheap signals as
  **candidate generators only**. They do not own match evidence.
- Measure every pruning candidate generator against an exhaustive or otherwise predeclared oracle.
  It may reduce comparisons only after satisfying AC-5 candidate recall.
- Do not require pretrained embeddings or downloaded weights in V0.1.

### 1.4 Deterministic geometric verification

- Verify candidate correspondence using a measured classical path such as ORB or SIFT features,
  ratio/mutual checks, and constrained similarity/affine-first RANSAC.
- Record keypoint counts, inlier counts and ratio, spatial coverage, estimated transform, matched
  regions, and failure/low-texture reasons.
- Test NCC or phase correlation only as a separately evaluated low-texture fallback; it cannot be
  assumed safe for blots, blank backgrounds, or repeated textures.
- Preserve technically reviewable matches. Recurrence, containment/inset, same-work metadata, or
  a likely repeated control may annotate, group, or demote a result but may not suppress it.
- Permit exclusions only for technical non-comparability, with a recorded reason, per ADR-0010.

ORB versus SIFT, thresholds, low-texture fallback, and whether any prefilter is justified remain
spike questions, not architecture commitments.

### 1.5 Local results

Return a bounded ranked list of candidate source files. Each displayed candidate includes:

- source thumbnail and exact local path;
- file digest and basic filesystem/image metadata;
- query and source matched-region overlays;
- the estimated transform and deterministic measurements;
- a calm explanation of why it was returned and what the evidence cannot establish;
- a user action to open or reveal the original file in the operating system, where supported.

Ranking is a search convenience, not a scientific or conduct rating. V0.1 does not persist a
review-adjudication workflow. A minimal run artifact may record retrieval evidence and coverage,
but the deferred broader Finding/triage schema is not the V0.1 result contract.

### 1.6 Strict Local only; no LLM

- Default and only mode: Strict Local.
- `NullBackend` is the only reasoning backend used by V0.1; no model is loaded.
- The complete process tree opens zero sockets of every address family.
- No telemetry, update checks, remote lookup, paper download, model download, or silent fallback.
- Content-bearing writes are limited to the user-selected index/output root.

A future loopback model server is a separately disclosed capability that exits the zero-socket
guarantee and introduces a separate processor trust boundary. It is not part of this MVP. See
ADR-0009.

### 1.7 Interface

The exact CLI or desktop shell is not locked before the usability spike. The product surface must,
however, make three decisions explicit before work begins:

1. which query image is being searched;
2. which local roots are in scope;
3. where derived index/results may be written.

No interface may accept an author name, DOI, PubMed/ORCID identifier, publication list, or remote
URL as a shortcut to constructing the search scope.

## 2. Exact non-goals for V0.1

- No manuscript PDF ingest, automatic figure extraction, or panel segmentation.
- No within-manuscript duplicate scan.
- No “lab history” paper corpus or automatic prior-publication indexing.
- No author, DOI, PubMed, ORCID, publisher, or web crawler.
- No remote image search or cross-internet comparison.
- No mass scan of a third party's publication history.
- No numeric, statistical, reference, citation, methods/results, or text checks.
- No LLM, local model server, pretrained model download, or custom model training.
- No persistent report triage, reviewer identity system, or institutional workflow.
- No automatic conclusion about source originality, disclosure, legitimate reuse, error, intent,
  or scientific validity.
- No author/lab/manuscript ranking, aggregate rating, accusation generation, or notification to a
  third party.
- No guarantee that raw proprietary microscopy/acquisition formats are supported.
- No claim that failure to return a source proves the source file is absent.

## 3. User journey

```text
select query image
        │
        ▼
select authorized folder(s) / mounted drive(s)
        │
        ▼
confirm scope and output/index location
        │
        ▼
inventory + decode coverage
        │
        ▼
candidate generation → geometric verification
        │
        ▼
top candidates with path, thumbnail, and matched region
        │
        ▼
open original file → researcher confirms or rejects provenance
```

An unsuccessful run still has to be useful: it states exactly what was searched, what could not be
read, what was excluded, and which transformations/content types are outside measured support.

## 4. Safety and scientific boundary

V0.1 retrieves files; it does not inspect people. Its abuse-resistance comes from omitted product
surface as much as from language:

- explicit local roots rather than person/publication discovery;
- candidate files rather than “issues”;
- match evidence rather than conduct labels;
- no bulk third-party workflow;
- no auto-generated claim text;
- no outward communication.

The human reviewer has experimental context the matcher cannot access. A technically strong visual
match can still be a legitimate derivative, a disclosed inset, a repeated control, an intermediate
export, or the wrong provenance candidate. The final determination is always human.

## 5. Coverage requirements

Every run reports:

- canonical authorized roots and whether each was available;
- files discovered, decoded, indexed/compared, unsupported, unreadable, excluded, or errored;
- symlinks encountered and whether any resolved outside scope;
- supported format/size/channel limits;
- candidate-generation and verification stages actually run;
- low-texture or insufficient-feature cases;
- interrupted/incomplete status;
- index version and stale-file count, if an index is used.

“Nothing returned” must never look like “everything was searched successfully.”

## 6. Acceptance criteria

All numeric results are measurements on named, versioned datasets—not claims about field
performance beyond those datasets.

### Privacy, determinism, and product safety

**AC-1 — Zero sockets in default Strict Local.** The end-to-end V0.1 path runs under OS-enforced
denial and tracing for IP/network sockets and DNS, covering dependencies, native code, and
subprocesses, with zero socket attempts. `NullBackend` is active and no model is loaded.

**AC-2 — Filesystem scope.** A syscall-level audit in isolated environment directories confirms
that reads stay within the query, executable/dependency files, and explicitly selected roots, and
that content-bearing writes stay within the selected index/output root. Symlink and path-traversal
tests cannot escape those roots. Installation writes are tested separately.

**AC-3 — Deterministic result projection.** With identical input bytes, authorized-root snapshot,
effective configuration, component versions, and platform, the canonical candidate IDs, ordering,
evidence measurements, coverage, and assets are byte-identical after excluding explicitly listed
run metadata. Canonical pair ordering, serialization, float quantization, and seeds are specified
before implementation.

**AC-4 — Discovery and decode coverage.** On the frozen held-out directory fixtures, every
supported file is discovered once; unsupported, unreadable, duplicate-path, and out-of-root
symlink cases are reported with no silent omission. Results are reported by format, size, channel,
source type, and filesystem case rather than only as an aggregate.

### Retrieval quality

**AC-5 — Candidate-source retrieval and verification.** After the supported transform/content
envelope and thresholds are frozen, exhaustive verification reaches the predeclared recall target
on lineage-disjoint synthetic query/source pairs within that envelope, and any pruning candidate
generator achieves at least 99% recall relative to the exhaustive oracle. Real authorized or
openly licensed query/source pairs are reported separately and are never merged into a synthetic
“field recall” claim. Non-match/control queries report clustered actionable candidates with
confidence intervals, per-slice results, the actual query and directory counts, reviewer
dispositions, and residual uncertainty.

There is **no V0.1 requirement for at least 50 expert-reviewed no-known-issue manuscripts**. That
number belongs, at most, to a later Research Preflight pilot/maturity target. V0.1 adopts
statistical discipline without pretending that an achievable early control set can establish
field performance. The exact synthetic recall target is frozen before S2 after the transform
envelope and failure costs are defined; it is not back-filled after results are seen.

**AC-6 — Human retrieval burden.** On every real-pair evaluation, report top-1/top-5/top-10 source
recovery, the number of candidates inspected before the correct source, time to confirmation, and
abandonment/failure. On non-match controls, report the number of technically reviewable candidates
shown after grouping. The actual sample size and uncertainty accompany every summary. A fixed top-
10 UI cap is not itself evidence of acceptable false-positive burden.

**AC-7 — No model-dependent path.** The distributable V0.1 core and default execution path do not
load model weights, start or call a model process, or require an LLM/embedding extra. No model
failure can alter retrieval results because no such path exists.

**AC-8 — Product-boundary surface.** Automated interface tests and documentation review confirm
there is no input or command for author/DOI/PubMed/ORCID discovery, remote crawling, third-party
publication-history construction, person/lab ranking, allegation text, or external reporting.

**AC-9 — Observation-safe output.** Candidate records and rendered results describe measured
correspondence and verification steps only. They contain no document/person rating or automated
scientific-legitimacy conclusion. Priority/rank is explicitly defined as retrieval ordering.

**AC-10 — Evidence sufficient for source review.** Every returned candidate can be reviewed from
the query/source thumbnails, full-context views, matched-region overlays, path, transform summary,
and limitations. A user can open the original file without rerunning the matcher.

**AC-11 — Provenance.** Every run records tool, decoder, preprocessing, candidate-generator,
verifier, and result-format versions; effective parameter hash; query/source digests; authorized
roots; index snapshot/version if used; mode; policy results; and coverage. `models_used` and
`external_services_used` are empty in V0.1.

### Operational

**AC-12 — Runtime characterization.** On specified hardware and named directory sizes, report cold
and warm discovery, indexing, candidate, verification, and rendering times plus peak memory. A
runtime target becomes a hard gate only after S1 measures real design-partner directories; speed
cannot be improved by silently skipping supported files or applicable comparisons.

**AC-13 — Index correctness and recovery.** If a reusable index is retained, source additions,
changes, moves, deletions, interrupted builds, corruption, and version changes produce explicit,
deterministic stale/rebuild behavior. Search correctness matches the declared non-indexed oracle.
If S1/S2 show no material workflow benefit, the reusable index is removed from V0.1.

**AC-14 — Offline installation.** In a clean environment for each supported platform, installation
from a hash-pinned local artifact set with networking denied succeeds, then the sample search and
AC-1/AC-2 checks pass. No runtime data or model download is attempted.

## 7. Evaluation discipline for AC-5 and AC-6

- Freeze tuning, validation, and held-out lineage groups before threshold selection.
- Report confidence intervals even when they are wide.
- Report per-slice results for transform, content type, source format, compression, query quality,
  and directory scale.
- Keep controlled synthetic transform-envelope performance separate from results on real
  query/source pairs.
- Count grouped, technically reviewable candidates rather than raw pairwise correspondences.
- Report the actual control-set size and residual uncertainty.
- Do not call an achievable early evaluation corpus representative of field performance.
- Record ≥50 expert-reviewed control manuscripts only as a possible later pilot/maturity target
  for the deferred manuscript-preflight product.

## 8. Credible V0.1 demo

A credible demo uses a real, authorized local directory and a query derived from a known source
file but altered in a realistic way. With networking denied, the user:

1. selects the query and search root;
2. sees complete discovery/decoder coverage;
3. finds the known source among the returned candidates;
4. understands the matched-region evidence;
5. opens the original file;
6. sees a hard negative or low-texture case presented honestly rather than forced into a match.

The demo does not scan a named researcher, download papers, generate a conduct report, or rely on
an LLM. The strongest success is a researcher saying, “That is the original file I was looking
for,” and then explaining whether the evidence was sufficient to trust the result.
