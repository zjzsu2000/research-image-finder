# Research Preflight — Phase 1 Review Resolution

**Resolution date:** 2026-08-31
**Source review:** [Independent Phase 1 Design Review](2026-08-30-codex-phase1-design-review.md)
**Status:** Partial resolution; stop for maintainer review

> This document records disposition of an independent review. It is not itself a substitute for
> canonical product documents or accepted ADRs. A recommendation is binding only to the extent
> that the corresponding decision is explicitly reflected in those documents.

## 1. Scope and provenance

- The review was performed against the then-current Phase 1 Research Preflight documentation.
- No production implementation existed or was reviewed.
- The repository had no commits at review time and still has no committed implementation baseline.
- This resolution incorporates maintainer decisions made after the review, including the decision
  to pause the broad Research Preflight V0.1 and validate the narrower Research Image Finder first.
- This pass changes design documentation only. It does not modify schemas, implement persistence,
  start spikes, add ADR-0011 through ADR-0014, or authorize production code.

The disposition vocabulary is:

- **ACCEPT:** the recommendation or concern is accepted and reflected in current canonical design.
- **PARTIALLY_ACCEPT:** the concern is accepted, but the proposed mechanism, scope, or timing is
  only partly adopted or remains pre-implementation work.
- **REJECT:** the recommendation is deliberately not adopted in the stated form.
- **DEFER_TO_SPIKE:** the design must remain open until named empirical evidence exists.

## 2. Explicit maintainer decisions

### 2.1 Strict Local: zero sockets by default — ACCEPT

The default Strict Local configuration:

- opens zero IP/network sockets and, more strongly, zero sockets of any address family;
- uses `NullBackend` and loads no model;
- does not auto-detect, fall back to, or silently contact a local model;
- treats future loopback Local Model IPC as a separately named, explicitly enabled capability;
- visibly exits the zero-socket guarantee when that capability is enabled;
- treats the local model process as a separate trust boundary that may log, persist, or egress
  received content.

This is accepted in [ADR-0009](../adr/0009-strict-local-capability-and-trust-boundary.md) and
reflected in README, PRODUCT, MVP, ARCHITECTURE, PRIVACY, and ROADMAP. Research Image Finder V0.1
does not include Local Model IPC at all.

### 2.2 Detection-quality gates: statistical discipline, honestly scoped — PARTIALLY_ACCEPT

The review's statistical framing is accepted:

- confidence intervals are retained;
- per-slice reporting is retained;
- synthetic transform-envelope performance is kept separate from real/field-performance claims;
- pairwise matches are clustered into actionable review candidates before burden is counted;
- actual control-set/query-set and directory sizes are reported;
- residual uncertainty is stated;
- no-known-issue/no-known-source controls are not described as proven negatives.

The recommendation to require **at least 50 expert-reviewed no-known-issue manuscripts as a V0.1
ship gate is REJECTED**. It overstates what the first MVP can assemble and contradicts the decision
to scope V0.1 honestly. A 50-manuscript control set may be tracked as a later Research Preflight
pilot/maturity target. It is not an Image Finder V0.1 requirement and is not replaced by another
arbitrary small-sample false-alarm threshold.

### 2.3 Product boundary: Research Image Finder first — ACCEPT

The broad Research Preflight V0.1 is paused. The first open-source MVP is:

> one user-supplied query image + one or more explicitly selected authorized local roots →
> evidence-ranked candidate source files → human provenance confirmation.

The product is self-audit-first, local-only, folder-scoped, deterministic, and has no LLM. It does
not provide author/DOI/PubMed discovery, publisher crawling, automatic third-party paper corpora,
publication-history mass scanning, researcher ranking, allegation prose, or external reporting.

This decision accepts that open-source image-matching primitives can be repurposed. The safety
obligation is not an unenforceable promise that misuse is impossible; it is refusal to productize
the dangerous investigation workflow and its last-mile outputs.

## 3. ADR verification

### ADR-0009 — verified, no change required

[ADR-0009](../adr/0009-strict-local-capability-and-trust-boundary.md) accurately encodes all five
resolved points:

1. Strict Local default is zero sockets.
2. Default Strict Local uses `NullBackend` and no model.
3. Loopback Local Model IPC is separate, disclosed, and exits the zero-socket claim.
4. There is no silent default, auto-detection, or fallback.
5. The local model process is a separate trusted processor outside the application's guarantee.

The ADR also correctly moves enforcement from language-level monkeypatches to OS-level tests of
the process tree.

### ADR-0010 — verified, no change required

[ADR-0010](../adr/0010-no-benign-inference-from-observed-patterns.md) accurately encodes:

1. no automatic scientific-benignity inference from recurrence, containment/inset, serial or
   adjacent imaging, likely repeated controls, or same-work identity;
2. technical non-comparability exclusions are allowed and reported;
3. annotation, grouping, and review-priority demotion are allowed;
4. technically reviewable observations remain visible even when a heuristic suggests legitimate
   reuse;
5. the system describes observed patterns while the human makes the final legitimate-reuse and
   provenance determination.

The disclosed-metadata exception remains narrow: deterministic explicit disclosure may justify a
recorded rule, but annotation is preferred and the software still does not infer legitimacy from
pixels or recurrence.

## 4. Material review-finding dispositions

| Review finding / recommendation | Disposition | Resolution |
| --- | --- | --- |
| Narrow the release spine so secondary checks cannot block the image value proposition | **ACCEPT** | Scope narrowed further to Image Finder; PDF extraction, manuscript matching, paper corpus, numeric/reference checks, LLM, and persistent triage are out of V0.1. |
| Make Strict Local a coherent, OS-testable capability | **ACCEPT** | ADR-0009; zero sockets, `NullBackend`, no model, process-tree enforcement. |
| Stop automatic “benign” suppression | **ACCEPT** | ADR-0010; technical exclusions only, otherwise preserve/annotate/group/demote. |
| Repair AC-4–AC-6 definitions, splits, confidence reporting, and synthetic/real separation | **PARTIALLY_ACCEPT** | Statistical and leakage discipline accepted; criteria recast for source retrieval. Numeric field-performance guarantees wait for evidence. |
| Require ≥50 expert-reviewed control manuscripts for AC-5 | **REJECT** | Later pilot/maturity target only; not a V0.1 ship gate. |
| Separate candidate retrieval from geometric verification and use an exhaustive oracle | **ACCEPT** | Candidate generators cannot own evidence; any pruning path needs ≥99% recall against the declared oracle. |
| Decide whether pHash, ORB/SIFT, NCC, embeddings, and transform models survive measurement | **DEFER_TO_SPIKE** | S2 compares model-free alternatives. Embeddings/model weights are excluded from current V0.1. |
| Treat panel/comparable-region recovery as a gating risk | **PARTIALLY_ACCEPT** | Concern accepted, but removed from Image Finder V0.1 because the user supplies the query crop. Revisit only for multi-panel/manuscript expansion. |
| Repair Finding identity, recursive safety, coordinate/provenance, and JSONL/triage contracts | **PARTIALLY_ACCEPT** | Defects accepted. The existing Finding schemas are deferred and not reused as the Image Finder result contract. A minimal result/run contract remains required before production. No schemas changed in this pass. |
| Specify a safe report/triage persistence workflow | **PARTIALLY_ACCEPT** | Safety concern accepted; persistent triage is removed from V0.1. Minimal result rendering still needs CSP/escaping/path-handling decisions before production. |
| Make the V0.1 reasoning backend narration-only and isolate experimental candidates | **REJECT** | V0.1 removes LLM/model capability entirely instead of retaining narration. Any future model path requires a new scope decision. |
| Keep numeric/statistical detectors narrow and independently gated | **PARTIALLY_ACCEPT** | Scientific-validity concern accepted; all such detectors are out of Image Finder V0.1 and remain future work. |
| Independently gate reference checks | **PARTIALLY_ACCEPT** | Concern accepted; reference checking is out of Image Finder V0.1. |
| Keep SQLite/files appropriate to scale and avoid premature vector infrastructure | **PARTIALLY_ACCEPT** | No vector database/model embeddings. Whether even a reusable folder index is needed is deferred to S1/S2. ADR-0006's paper-corpus layout does not govern this workload. |
| Separate label support from domain realism | **ACCEPT** | DATASET_POLICY retains the two-axis hierarchy; EVALUATION applies it to real and synthetic source pairs. |
| Prevent private user material from becoming training data | **ACCEPT** | Queries, source files, paths, descriptors, indexes, results, and confirmations are explicitly user data and never training data by default. |
| Strengthen authority-to-donate and withdrawal semantics | **ACCEPT** | DATASET_POLICY already records operator authority as insufficient by itself and defines withdrawal limits. No donation workflow is in V0.1. |
| Expand narrative provenance | **REJECT** | There is no generated narrative or model in Image Finder V0.1. Reconsider only if narrative returns in a future scope. |
| Define real offline installation rather than developer editable install | **ACCEPT** | AC-14 requires a clean, hash-pinned, no-network install and sample run on named supported platforms. |
| Close source-file location and safe-sharing workflows | **PARTIALLY_ACCEPT** | Locating/opening the source file is now the core workflow. Cross-version triage merge and sharing/export remain outside V0.1. |
| Harden local rendering against manuscript/reviewer input | **PARTIALLY_ACCEPT** | Input-safety requirement retained for filenames, paths, metadata, and images; exact viewer architecture remains pre-implementation. |
| Add ADR-0011 through ADR-0014 immediately | **REJECT** | No new ADRs are added in this pass. Their topics are re-evaluated under the narrower product before any numbering or decision is locked. |

## 5. Cross-document consistency after this pass

- **README / PRODUCT / MVP:** define Image Finder as the current V0.1 and the broad Preflight as
  paused future work.
- **ARCHITECTURE:** contains only the folder-scoped deterministic retrieval path; historical ADRs
  do not silently expand it.
- **PRIVACY:** implements ADR-0009's zero-socket/default-no-model decision and adds explicit local
  root/write-root constraints.
- **EVALUATION:** replaces manuscript-control gates with query/source, directory, and control-query
  evaluation while preserving uncertainty discipline.
- **ROADMAP:** defines S1 discovery/decoding, S2 retrieval/verification, and S3 real user workflow;
  none has started.
- **DATASET_POLICY:** user source images and all derivatives remain private production data; no
  pretrained or custom model is loaded in V0.1.
- **FINDING_SCHEMA and `schemas/`:** unchanged and explicitly deferred; they are not asserted to be
  the current Image Finder result contract.
- **ADR-0009 / ADR-0010:** verified and unchanged.

## 6. Remaining DEFER_TO_SPIKE items

### S1

- actual lab folder/file-format distribution;
- supported decoder matrix and raw/proprietary-format gap;
- traversal and coverage behavior across real directory/filesystem cases;
- one-off scan versus reusable index;
- real directory size, runtime, and memory profile.

### S2

- ORB versus SIFT and any content-specific routing;
- whether pHash or another cheap signal has a safe pruning role;
- low-texture fallback viability for blots and repetitive imagery;
- similarity/affine constraints and whether homography is ever justified;
- supported transformation/content envelope and thresholds;
- real and control-query candidate burden with intervals and per-slice results.

### S3

- whether researchers can find a known source faster than manual browsing;
- acceptable candidates-inspected and time-to-confirm burden;
- required path/date/metadata context;
- false-confirmation and absent-source behavior;
- whether the next real need is multiple explicitly selected panels.

## 7. Remaining pre-implementation items

These are accepted design debts, not spike outcomes:

- define the minimal candidate-result, run, coverage, and evidence-asset schemas;
- define durable content-based identity, canonical serialization, float quantization, and pair
  ordering;
- choose CLI/local-HTML versus minimal desktop shell after the usability spike;
- define supported-platform OS enforcement and mounted-network-filesystem policy;
- complete decoder/dependency threat review and temporary-file policy;
- define output permissions, retention, purge, and path-redaction behavior;
- define safe local rendering, escaping, CSP/active-content rules, and reveal/open integration;
- define offline packaging platforms and hash-pinned artifact process;
- update or supersede historical ADRs only when an accepted current decision actually conflicts;
- decide whether a new product-boundary ADR is needed after maintainer review;
- review the deferred Finding schemas before any broader Research Preflight work resumes.

## 8. Files intentionally not changed in this pass

- `schemas/finding.schema.json`
- `schemas/run_manifest.schema.json`
- `schemas/examples/*`
- existing ADR-0001 through ADR-0010
- production source code (none added)

No ADR-0011 through ADR-0014 was added. No spike or production implementation was started. No
commit or push was performed.
