# EVALUATION.md — Research Image Finder V0.1

Status: **evaluation plan; spikes have not started**
Last updated: 2026-08-31

This document defines how the narrow folder-scoped Image Finder is evaluated. The former
manuscript-extraction, panel-segmentation, within-paper matching, paper-corpus, numeric/reference,
and LLM spikes are paused. Their earlier targets are not V0.1 results or gates.

Nothing may be described as detection or retrieval performance until measured by a frozen
procedure defined here.

## 1. Data classes are never interchangeable

| Data class | Purpose | May tune against? | May train on? | Location |
| --- | --- | --- | --- | --- |
| Product fixtures | Deterministic code-path and pathological-file tests | Yes | No | Small, openly licensed files in repo |
| Synthetic transform benchmark | Measure the declared transform envelope with exact lineage/geometry | Validation split only | No custom training in V0.1 | Versioned manifest + generator |
| Real query/source benchmark | Measure source retrieval on realistic pairs | Tuning split sparingly | No | Licensed/authorized evaluation store |
| Non-match/control benchmark | Measure technically reviewable false candidates | No after threshold freeze | No | Licensed/authorized evaluation store |
| Design-partner trial data | Assess real workflow and time-to-source | No unless separately donated | Never by default | Partner machine; results shared only explicitly |
| User production data | Run the product | Never | Never | User-selected local roots only |
| Future training data | Possible future model work | N/A | Only under future policy | Outside V0.1 |

Evaluation data is not assumed representative merely because it is real. Every report names the
dataset version, acquisition/authorization basis, actual size, and slices.

## 2. Evaluation units and annotations

### 2.1 Source record

A source record is one supported image file in an authorized root. Annotation includes:

- content digest and lineage group;
- file format, dimensions, channels, bit depth, compression, and decoder result;
- content type where known: blot, microscopy, plot, flow, photograph, schematic, or other;
- whether the file is an acquisition original, processed derivative, export, screenshot, or
  unknown—recorded only when authoritative provenance exists;
- duplicate-byte and derived-image family identifiers;
- directory scale and storage/filesystem characteristics relevant to discovery.

“Acquisition original” is not inferred from resolution, filename, metadata, or similarity.

### 2.2 Query/source pair

A positive pair states that a query was generated from or authoritatively linked to a particular
source file/region. It records:

- exact source lineage;
- query creation path;
- transformation parameters when known;
- source/query matched regions;
- label support and domain realism as separate fields per [DATASET_POLICY.md](DATASET_POLICY.md).

A non-match/control query has no known source in the selected directory. It is called no-known-
source, not proven absent: an unlabeled relationship may still exist.

### 2.3 Frozen definitions

Before threshold work, freeze:

- supported file and decoder matrix;
- discovery unit and symlink policy;
- query/source lineage and split grouping;
- applicable pair;
- candidate retrieval hit;
- verified match;
- clustered/actionable candidate;
- technically non-comparable exclusion;
- top-k recovery and candidate-inspection count;
- abandonment and time-to-confirm measurement;
- supported transformation/content envelope.

All denominators are explicit. Silent exclusions are evaluation failures.

## 3. Benchmark composition

### 3.1 Synthetic transform envelope

Generate query crops from openly licensed or specifically authorized source images with exact
geometry. The battery should cover individually and in combinations:

- crop and partial overlap;
- resize and aspect-preserving resampling;
- JPEG/compression and screenshot degradation;
- brightness/contrast/gamma changes;
- grayscale/color/channel conversion;
- horizontal/vertical flip;
- small and moderate rotation;
- annotation, label, scale-bar, or border additions;
- embedding in a larger canvas or figure-like layout.

The supported envelope is frozen before held-out evaluation. Results apply only within that
envelope and are never presented as field recall.

### 3.2 Real query/source pairs

Use every lawful, localized pair available from:

- openly licensed published/source assets with clear lineage;
- design-partner files processed on the partner's machine;
- specifically donated, authorized, already-published examples with provenance.

Report results separately by query origin, source format, content type, transformation, directory
size, and provenance certainty. Small samples produce wide intervals and narrow claims.

### 3.3 Hard negatives and no-known-source controls

Include:

- visually similar but independently acquired microscopy;
- adjacent/serial fields and multichannel views;
- generic blot layouts, blank backgrounds, and repeated label strips;
- plots sharing axes, fonts, legends, grids, or templates;
- screenshots/icons/schematics with common UI or design elements;
- unrelated images from the same experiment folder;
- a query whose true source is intentionally absent from the selected root;
- corrupt, unsupported, tiny, huge, multipage, and unusual-channel files.

ADR-0010 prevents defining recurrence, inset containment, or same-work identity away as “benign.”
Those observations remain reviewable; grouping and annotation control burden without erasing them.

### 3.4 Splits and leakage

Pre-register tuning, validation, and frozen held-out partitions. Group by source-image lineage and,
where relevant, experiment/session/export family so derivatives cannot cross splits. A screenshot
and its source export belong to the same group. Keep design-partner trials outside threshold
tuning unless a separate, explicit evaluation agreement says otherwise.

## 4. V0.1 spikes

Spikes are empirical design tests, not production code. They do not start until the current design
pass is approved.

### S1 — Folder discovery and decoder reality

**Question.** Can a bounded local scanner find and decode the image types and directory structures
that real researchers actually use without silent omissions or scope escape?

**Inputs.** Versioned directory fixtures plus read-only inventories from explicitly authorized
design-partner roots. Include nested directories, external drives, symlinks, unreadable entries,
duplicate paths, sidecars, large files, multipage TIFF, unusual channels, and corrupt files.

**Metrics.** Discovery recall for supported files, duplicate enumeration, decode success by slice,
bytes/time, peak memory, skipped/error coverage, path/symlink-policy correctness, and one-off scan
versus index cost.

**Decision.** Freeze the supported format/scope matrix. If proprietary/raw formats dominate the
real need, decide explicitly whether to integrate a trusted local decoder, narrow the supported
promise, or stop. If one-off scanning is adequate, remove the persistent index from V0.1.

### S2 — Candidate retrieval and geometric verification

**Question.** Which deterministic pipeline recovers realistic query/source relationships while
keeping the candidate list reviewable across content types?

**Comparisons.** Exhaustive ORB and/or SIFT baselines; constrained similarity/affine verification;
optional pHash/global signals as candidate generators; low-texture NCC/phase correlation only on
its own positive and hard-negative benchmark.

**Metrics.** Candidate-generator recall against the exhaustive oracle; verifier recall within the
synthetic envelope; top-1/top-5/top-10 recovery; real-pair results separately; clustered actionable
candidates on controls; transform accuracy; keypoint/inlier/spatial-coverage distributions;
runtime and memory by directory scale/content slice.

**Required reporting.** Confidence intervals, actual sample sizes, per-slice results, thresholds,
library versions, hardware, and all negative results. Synthetic and real-pair numbers are never
merged.

**Decision.** Drop any prefilter below 99% candidate recall. Drop embeddings from V0.1 unless a
future explicit decision accepts model weights. Constrain or drop homography if it overfits.
Treat low-texture content as unsupported if no fallback clears its predeclared negative benchmark.

### S3 — End-to-end provenance retrieval with researchers

**Question.** Does the tool reduce real source-recovery work, and is the evidence understandable?

**Procedure.** On the participant's machine, use a query whose source is known and a directory the
participant is authorized to search. Include at least one realistic alteration and one hard
negative/absent-source case. Do not collect raw content or paths unless separately authorized.

**Metrics.** Whether the known source is recovered; candidate position; candidates inspected;
time to confirmation; false confirmation; abandonment; coverage comprehension; trust in the
matched-region evidence; and whether opening/revealing the original file completes the task.

**Decision.** Proceed to production only if the user can complete the narrow job and the observed
failure modes have honest coverage states. If the user actually needs raw proprietary formats,
folder metadata, or batch panels first, revisit the scope before coding a broader preflight.

### Deferred spikes

The former figure extraction/panel segmentation, manuscript duplicate detection, prior-paper
corpus, numeric/reference, and LLM spikes are not V0.1 work. They require a new scope decision
after Image Finder evidence exists.

## 5. AC-5 and AC-6 statistical policy

The policy is: **adopt statistical discipline, but scope V0.1 honestly.**

V0.1 must:

- retain confidence intervals;
- retain per-slice reporting;
- separate synthetic transform-envelope performance from field-performance claims;
- retain clustered/actionable candidate counting;
- report the actual control-query and directory counts;
- state residual uncertainty;
- avoid claiming that no-known-source controls are proven negatives.

V0.1 must **not** require at least 50 expert-reviewed no-known-issue manuscripts as a ship gate.
That requirement belongs neither to the Image Finder workflow nor to an honest early sample. A
50-manuscript control set may be recorded as a later Research Preflight pilot/maturity target.

No alternative hard false-alarm threshold is invented merely to replace the rejected sample-size
gate. S2/S3 report the observed trade-off and the V0.1 review makes a scoped product decision. A
small sample may support a prototype decision while supporting only a weak field claim.

## 6. Acceptance-criteria mapping

| Criteria | Evidence |
| --- | --- |
| AC-1 zero sockets | OS-denied/traced complete process-tree run |
| AC-2 filesystem scope | Syscall audit with symlink/traversal and isolated environment fixtures |
| AC-3 determinism | Repeated canonical-result and evidence-asset comparison |
| AC-4 discovery/decode | S1 held-out directory fixtures and per-format slices |
| AC-5 retrieval/verification | S2 synthetic envelope, real pairs, and controls reported separately |
| AC-6 human burden | S2 candidate counts plus S3 time/candidates-to-confirm |
| AC-7 no model path | Dependency/build inspection and runtime model/process audit |
| AC-8 product boundary | CLI/UI/doc surface tests; absence of person/publication/crawler inputs |
| AC-9 safe output | Structured-output and rendered-copy tests |
| AC-10 evidence | S3 evidence-comprehension and open-original task |
| AC-11 provenance | Run-contract validation once the V0.1 result schema is resolved |
| AC-12 runtime | S1/S2 stage timings on named hardware/directory sizes |
| AC-13 index integrity | Only if indexing survives S1; mutation/interruption/corruption tests |
| AC-14 offline install | Clean supported-platform install and sample run with networking denied |

## 7. Reporting standards

Every result includes:

- dataset and manifest version/hash;
- actual query, source, directory, and control counts;
- split and lineage rules;
- point estimate and confidence interval where applicable;
- per-slice results and slices too small to interpret;
- supported transform/content envelope;
- threshold-selection set versus frozen held-out set;
- candidate-generator and verifier results separately;
- synthetic, real, and control results separately;
- hardware, software/library versions, seeds, and cold/warm state;
- excluded/unsupported cases and all known silent-miss risks.

A performance table without these fields is exploratory output, not acceptance evidence.

## 8. Guarding against tuning

- Thresholds are selected on tuning/validation data only.
- Frozen held-out data is examined only at a declared review point.
- New failure examples discovered after inspection enter a future corpus version; old and new
  results are both retained.
- No transform is added to the “supported envelope” after seeing held-out results without a new
  version and new holdout.
- Design-partner anecdotes inform workflow scope but are not silently counted as benchmark items.
- Negative results are recorded with the same prominence as successful configurations.
