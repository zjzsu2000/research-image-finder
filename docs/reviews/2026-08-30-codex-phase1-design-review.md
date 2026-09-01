# Research Preflight — Independent Phase 1 Design Review

**Date:** 2026-08-30
**Reviewer:** Codex
**Status:** GO WITH CHANGES

> This document is an independent design review artifact.
> It records reviewer findings and recommendations; it is not itself an
> accepted product or architecture decision. Recommendations become binding
> only when explicitly resolved into the canonical design documents or ADRs.

## Review provenance

- **Reviewed repository state:** the then-current Phase 1 design repository, including the
  canonical product, MVP, architecture, privacy, finding-schema, dataset-policy, evaluation,
  roadmap, ADR, and machine-readable schema documents present on 2026-08-30.
- **Implementation state:** no production implementation was present or reviewed. The repository
  contained design documentation, schemas, examples, and a documentation-validation script.
- **Version-control state:** the repository had no commits at review time. The reviewed files were
  staged as additions on an unborn `main` branch.
- **Review basis:** this review was performed against the then-current Phase 1 documentation and
  does not incorporate later decisions unless they are explicitly resolved into canonical
  documents or ADRs.
- **Validation observation:** `python3 tools/validate_docs.py` reported `OK — 219 checks passed`.
  That result confirms the checks implemented by the script; it does not establish the broader
  runtime, privacy, scientific-validity, or evaluation claims discussed below.

## 1. Executive verdict

**GO WITH CHANGES** — proceed with carefully specified S1–S3 empirical spikes, but do not begin
production implementation until the critical issues in this review are resolved.

The product boundary and safety philosophy are unusually thoughtful: evidence-first findings, no
aggregate score, strict locality, explicit coverage reporting, and separation of evaluation data
from future training data are sound foundations. The V0.1 scope is nevertheless wider than its
stated image-focused wedge because numeric checks, reference parsing, a private corpus, local LLM
integration, report triage, and packaging all remain release requirements. Strict Local is not
currently a coherent testable contract: the documents promise zero network/socket activity while
also permitting loopback model servers, and the proposed tests do not cover native libraries,
subprocesses, proxies, DNS, synced folders, or a local model server's own behavior.

The image pipeline correctly treats figure extraction as a primary risk, but panel and comparable-
region recovery are equally gating. The proposed pHash prefilter can discard exactly the transformed
pairs that geometric verification is intended to recover, while automatic suppression of repeated
controls, insets, and same-work matches makes scientific judgments not supported by the measured
evidence. The evaluation plan is suitable for early spikes but not yet sufficient for a ship gate:
it relies heavily on synthetic positives, too few no-known-issue controls, and several gameable or
impossible conditions. The finding schema has strong intent but does not yet encode the claimed
recursive vocabulary restrictions, reproducibility contract, stable triage identity, or output-
stream format. These defects can be corrected without a wholesale redesign; most are specification
and gate-definition problems that should be resolved before code hardens them.

## 2. Critical implementation blockers

### 2.1 The release scope contradicts the stated image-first wedge

**Issue.** Numeric, statistical, reference, corpus, LLM, and triage work are described as secondary
or optional, but all fourteen acceptance criteria must be green and the credible demo requires a
corpus hit.

**Why it matters.** This makes the image-first prioritization unenforceable. A weak reference parser
or low-coverage GRIM detector could delay the image product despite repeated statements that it
must not. It also prevents a clear go/no-go decision when the core visual workflow works but a
secondary capability does not.

**Affected documents and sections.** `MVP.md` introduction and §§1.4–1.7, 7, and 9;
`ROADMAP.md` Weeks 4–5; `PRODUCT.md` §9.

**Recommended change.** Define one mandatory V0.1 release spine: PDF ingest, figure/panel recovery,
within-manuscript matching, coverage, evidence report, and safe triage persistence. Make corpus
comparison a conditional V0.1 capability gated by S4. Treat numeric/reference detectors and local-
LLM narration as separately gated experimental capabilities that cannot block the image release.
Do not require an optional corpus capability in the credible-demo contract.

### 2.2 Strict Local cannot be enforced as currently worded

**Issue.** “No socket/request for any reason” conflicts with permitted loopback HTTP to Ollama or
llama.cpp. A Python `socket.socket` monkeypatch and import lint do not detect native-library
sockets, subprocesses such as `curl`, direct system calls through `ctypes`, proxy behavior,
network-capable third-party packages, browser fetches, or dependencies outside the project package.

`PolicyGate.allow_write` can mediate application-owned writes, but it cannot by itself mediate
writes performed by native dependencies or subprocesses. A user-designated output directory may
also be cloud-synced, backed up, indexed, or scanned by software outside Research Preflight.

**Why it matters.** This is the product's central promise. An overstated privacy guarantee is worse
than a narrower accurate one, particularly for unpublished, pre-patent, clinical, or sponsor-
restricted material.

**Affected documents and sections.** `README.md` Privacy promise; `PRIVACY.md` §§2–5 and 8–10;
`ARCHITECTURE.md` §§5–7; ADR-0001.

**Recommended change.** Define Strict Local as one of the following and use the definition
consistently:

1. zero IP sockets, which excludes HTTP model servers and permits only in-process, local-process,
   or Unix-domain IPC; or
2. zero non-loopback egress, with loopback explicitly disclosed and tested as a distinct
   capability.

Add OS-level network denial or tracing to CI. Prohibit redirects and proxy-environment use for
loopback backends, restrict endpoints to literal loopback addresses, and avoid DNS resolution.
Treat a local model server as a separately trusted processor that may log, persist, or egress data;
the application cannot guarantee the server's behavior. State that OS backups, antivirus,
indexing, and cloud-synced directories are outside the application guarantee. Runtime filesystem
tests must include dependencies, native code, subprocesses, symlink escape, and temporary-file
behavior.

### 2.3 “Benign-pattern suppression” makes unsupported scientific judgments

**Issue.** Recurrence, inset containment, or same-work status is used to suppress findings before
human review.

**Why it matters.** A repeated loading control can be legitimate, wrongly paired to an experiment,
or itself an assembly error. An inset can be valid yet require disclosure. A preprint/publication
match may contain a changed or replaced panel. Frequency and document identity do not establish
benignity. Suppressing these observations can create a silent false negative precisely where the
product promises evidence for human verification.

**Affected documents and sections.** `PRODUCT.md` §8; `MVP.md` §§1.3–1.4;
`ARCHITECTURE.md` §§3 and 9; ADR-0004 through ADR-0006.

**Recommended change.** Suppress only technically non-comparable material or an explicitly
disclosed relationship established from deterministic metadata. Otherwise group, annotate, and
possibly demote repeated controls, insets, serial images, and same-work matches. The software may
describe the observed pattern; it must not infer that the relationship is benign.

### 2.4 S1–S3 and AC-4–AC-6 are not yet valid ship gates

**Issue.** AC-4 requires “every miss detectable,” which is impossible when an unrecognized figure
also lacks a recognized caption. S2 has no release criterion despite being as gating as extraction.
S3 uses synthetic positives and near-zero-assumed real positives, while only ten no-known-issue
manuscripts support the false-alarm target. AC-6 can be met by thresholding away findings and mixes
coverage notes, benign groups, numeric findings, and actionable image findings.

**Why it matters.** These metrics can certify a detector that performs well on generated
transformations but poorly on real scientific figures. A ten-document control set is too small to
support a strong claim about a rare but high-harm false-positive event. “No known issue” is also not
negative ground truth.

**Affected documents and sections.** `EVALUATION.md` §§2–3; `MVP.md` AC-4–AC-6;
`ROADMAP.md` Week 0.

**Recommended change.** Before running spikes, define annotation rules, denominators, clustering,
actionable-finding semantics, confidence intervals, per-publisher/content-type minima, and
threshold-selection versus held-out splits. Measure caption-detectable misses rather than claiming
all misses are detectable. Add downstream match-recovery metrics to S2. Add real confirmed region
pairs and hard benign negatives to S3; report synthetic performance as transform-envelope
performance, not field recall.

### 2.5 The image cascade can lose the cases it claims to recover

**Issue.** pHash/dHash is a mandatory prefilter even though ADR-0005 correctly states that it is
weak for crop, flip, rotation, and partial reuse. S3 does not clearly separate candidate-retrieval
recall from geometric-verification recall.

**Why it matters.** ORB/SIFT cannot confirm a pair that the prefilter discarded. For a typical
within-manuscript workload of tens of panels, exhaustive local-feature comparison may be affordable
and safer than a recall-losing prefilter.

**Affected documents and sections.** `MVP.md` §1.3; `EVALUATION.md` S3; ADR-0005.

**Recommended change.** Benchmark four separable stages: candidate retrieval, correspondence,
transform verification, and suppression/grouping. Include exhaustive ORB/SIFT verification as the
within-document oracle. Test pHash, embeddings, and other cheap signals only as recall-measured
candidate generators. Require near-perfect candidate recall before any prefilter is permitted to
reduce comparisons.

### 2.6 The canonical schema does not yet provide its claimed safety or persistence

**Issue.** The JSON Schema applies `safeKey` only at the top level, while open nested objects such
as `params`, `parsed`, and `input_digests` can contain arbitrary keys. The documentation validator
recursively scans only committed examples, not arbitrary emitted runtime output. Image evidence
assets are not conditionally required by the schema. Coordinate space, preprocessing, identity
fields, pair ordering, and canonical float encoding are undefined.

Finding IDs include detector version and volatile locations. They may be stable for an identical
run with an identical detector, but they will not preserve triage across detector upgrades,
changed segmentation boxes, or modest manuscript edits. Sixteen hexadecimal characters provide a
64-bit identifier, which is also an unnecessarily small interchange identity space.

**Why it matters.** This undermines AC-3, AC-9, AC-10, and the claimed stable interchange format.
It also risks either losing triage silently or incorrectly attaching an old disposition to a new
observation.

**Affected documents and sections.** `FINDING_SCHEMA.md` §§1–5;
`schemas/finding.schema.json`; `tools/validate_docs.py`.

**Recommended change.** Define evidence-family-specific identity fields, canonical pair ordering
and serialization, coordinate systems, render DPI, preprocessing versions, and conditional asset
requirements. Use a longer identity digest. Separate a detector-occurrence ID from a durable
review-link key, and define explicit triage migration behavior when extraction or detector
versions change. Enforce vocabulary recursively on every emitted object through runtime validation;
do not claim JSON Schema alone provides that property.

### 2.7 The report/triage workflow is underspecified and creates avoidable harm

**Issue.** The primary journey says users record triage from the report, but a self-contained
static HTML file cannot update `triage.json`. The CLI triage interaction is not specified.
Generated findings and human-entered conclusions are also mixed in one canonical export, including
the structured reason `possible_manipulation`.

**Why it matters.** The main human workflow may be unusable, and forwarded HTML/JSON can turn
machine observations or unattributed reviewer notes into employment, institutional, or
reputational evidence. A single banner is not sufficient when findings are copied or extracted
individually.

**Affected documents and sections.** `PRODUCT.md` §3; `MVP.md` §§1.6 and 1.8;
`FINDING_SCHEMA.md` §3 `triage`.

**Recommended change.** Specify one persistence mechanism before report implementation—for
example, a static report that downloads a triage sidecar subsequently imported by the CLI, or a
dedicated terminal workflow. Keep system findings and reviewer annotations as separately
attributable records. Replace `possible_manipulation` with observation-oriented reviewer reasons,
or explicitly mark it as a human assertion with reviewer identity/class and timestamp. Require the
disclaimer adjacent to every finding, escape all manuscript and reviewer text, apply a restrictive
Content Security Policy, and define a share/export mode that omits sensitive paths, free text, and
optional triage.

### 2.8 The LLM boundary is internally safe only if candidate extraction has no V0.1 effect

**Issue.** AC-7 requires LLM-on and LLM-off to produce identical findings, while the
`ReasoningBackend` is also allowed to discover candidate claims that deterministic extraction did
not find. The current corollary excludes LLM-only findings from the default output.

**Why it matters.** As specified, candidate extraction is presented as a capability but cannot
change the V0.1 product result. Keeping the pathway in the core interface adds privacy, testing,
and conceptual complexity without product value. It also makes it easier for a later
implementation to accidentally weaken AC-7.

**Affected documents and sections.** `MVP.md` §1.7; `ARCHITECTURE.md` §§3–4 and 10; ADR-0004.

**Recommended change.** Make the V0.1 reasoning backend narration-only. If candidate extraction is
measured during S5, write its candidates and deterministic verification results to a separate
experimental diagnostic artifact that cannot enter, remove, reprioritize, or reorder default
findings. Revisit product inclusion only after an explicit V0.2 decision.

## 3. Important non-blocking issues

### 3.1 Numeric and statistical checks

Percentage/count arithmetic is tractable. P-value recomputation is tractable only when tail,
correction, test family, degrees of freedom, and rounding convention are explicit. Cross-section
sample-size reconciliation still requires semantic equivalence: identical group labels do not
prove that the denominators should match when attrition, per-outcome missingness, analysis subsets,
or exclusions exist. GRIM is particularly risky with missing data, composite scales, weighting,
or rounded means. These checks should remain off by default unless S5 validates each detector
independently.

### 3.2 Reference checks

The reference scope is broad for an unspiked secondary feature. `cited_not_listed` and exact
duplicate entries are plausible. `listed_not_cited` may be stylistically legitimate, while
`malformed_entry` depends on citation style and parser reliability. No quality acceptance
criterion currently covers reference detectors.

### 3.3 Panel segmentation should be evaluated by downstream utility

Exact panel count is not always scientifically meaningful for stacked blots, shared-axis plots,
nested insets, or composite microscopy. Measure whether comparable regions are recovered well
enough for matching, not only whether a human-preferred count was reproduced. Annotation
disagreement should itself be treated as evidence that the unit of comparison is ambiguous.

### 3.4 Expected image-pipeline breakpoints

- **Low-texture blots:** few stable keypoints; NCC can match blank backgrounds, label strips, or
  generic band layouts. Strip/lane-aware normalization may be required, but must be evaluated
  rather than assumed.
- **Microscopy:** repetitive texture, serial sections, adjacent fields, multichannel views, and
  scale bars can create geometrically consistent benign matches. Different images of similar
  tissue may look locally alike without sharing source pixels.
- **Plots:** shared axes, fonts, legends, grids, and plotting templates can dominate local
  features. Vector-to-raster rendering changes can also destabilize descriptors.
- **Insets:** containment is expected but may still need disclosure. Insets should be grouped and
  contextualized, not assumed benign or silently removed.
- **Repeated controls:** repetition count is not proof that reuse is scientifically appropriate.
  Whether a control may be shared depends on experimental provenance that is not present in the
  pixels.
- **Composited figures:** reused regions may cross inferred panel boundaries or be embedded in a
  larger montage. A panel-first comparison can hide them.
- **Flexible homography:** a projective model can overfit repetitive correspondences. S3 should
  compare similarity/affine-first verification, bidirectional consistency, spatial coverage, and
  homography plausibility constraints.
- **Phase correlation/NCC:** whole-image techniques do not automatically solve cropped, rotated,
  or partially composited reuse and need separate transform-specific evaluation.

### 3.5 Corpus architecture

SQLite plus ordinary files is suitable at the stated scale, and rejecting a vector database or
daemon is appropriate. The memmapped embedding matrix and per-panel descriptor-file layout should
remain provisional until S3/S4 demonstrate that embeddings add recall and descriptor loading is a
bottleneck. The corpus needs atomic rebuild, corruption and row-alignment detection, restrictive
permissions, source deletion/update semantics, and deterministic staleness handling.

“The lab's own prior papers” should mean material the operator is authorized to process, not any
third-party investigation corpus. This cannot be perfectly enforced, but the intended-use and
authorization boundary should be represented in configuration and report provenance.

### 3.6 Dataset and future-ML policy

The current label-confidence hierarchy conflates label certainty with deployment realism.
Synthetic labels have high transformation certainty but low field realism; expert-reviewed real
pairs can have lower certainty but higher deployment relevance. Record label support/provenance
and domain realism/source type as separate dimensions.

The highest-realism future model paths are:

1. a public-data panel-type classifier, if heuristic routing is empirically limiting;
2. synthetic-invariance training for candidate retrieval, if it beats the tuned classical
   baseline on lineage-held-out data;
3. a transformation or correspondence model trained on exact synthetic geometry and evaluated on
   real confirmed pairs; and
4. a false-positive ranking/grouping model trained only from explicitly donated, attributable
   expert dispositions with sufficient contextual features.

A general “same source versus legitimate reuse versus problematic reuse” classifier is less
realistic because legitimacy depends on experimental context, disclosure, and provenance, not
pixels alone. Domain-adapted language models are not justified until a measured language task is
the limiting factor.

Future donation consent is incomplete. A PI may not have authority to donate a trainee's,
coauthor's, patient's, sponsor's, or publisher's material. “Revocable” also cannot automatically
untrain a released model. Future policy needs authority-to-donate, IP/IRB basis, downstream
redistribution, withdrawal cutoff, and trained-model removal semantics.

### 3.7 Narrative provenance

`narrative_source` should identify the template or prompt version, model digest or explicit
inability to obtain it, decoding parameters, and which fields were generated. Human-edited
narrative is not currently representable. A single model attribution for several independently
generated prose fields may also be insufficient.

### 3.8 Offline installation

`pip install -e .` is a developer operation and does not prove that a user can install from a
wheelhouse. Supported OS/architecture combinations, Python versions, hashes, dependency artifacts,
and clean-environment behavior must be defined. Installation and runtime privacy are separate
claims and should be tested separately.

### 3.9 Missing or incomplete user workflows

The current design does not close the loop on locating original acquisition/source files after a
finding, distinguishing manuscript versions, handling supplementary material, merging triage after
manuscript edits, or safely sharing only selected findings. These may remain outside V0.1, but the
report should not imply that it closes those workflows. The PDF-only wedge is defensible for a
pre-submission tool, but design-partner interviews should verify that draft PDFs are actually
available at the point users want to run the review.

### 3.10 Report and parser security

All manuscript-derived strings and reviewer notes must be treated as untrusted input when
rendering HTML. Offline HTML can still execute injected script when later opened on a connected
machine. A static external-URL scan does not detect dynamically constructed URLs, injected markup,
forms, meta refresh, SVG references, or JavaScript behavior. Prefer no JavaScript; otherwise use
strict escaping, a restrictive CSP, no external navigation, and browser-level tests.

The documented decision not to sandbox PDF parsing is acceptable as a declared V0.1 gap for a
self-review tool, but it should remain visible. “Offline” reduces exfiltration impact; it does not
prevent a malicious PDF from exploiting a parser or damaging local data.

## 4. What the design gets right

- The distinction between measured observation and misconduct inference is explicit, repeated,
  and reflected in finding-type design.
- Refusing aggregate integrity, fraud, trust, or risk scores is the correct product-safety choice,
  especially for reports that may be forwarded or used in institutional processes.
- `NullBackend` as the default and deterministic evidence ownership are strong architectural
  boundaries.
- The three coverage states—ran and found nothing, ran but nothing applicable, and did not run—are
  excellent and prevent “not checked” from looking like “clean.”
- Figure extraction is correctly recognized as gating, with stop/review outcomes rather than
  schedule-driven optimism.
- The private corpus is a genuinely differentiated local-first use case, and avoiding a vector
  database/server at this scale is appropriate.
- Separating product fixtures, evaluation data, future training data, and production user data is
  exactly right.
- “Retracted paper does not equal positive label” is stated strongly and at the correct
  figure/panel/region/finding granularity.
- Public allegations are correctly limited to candidate discovery rather than direct supervision.
- Lineage-aware splitting and licensing provenance are unusually good early dataset decisions.
- The synthetic transform benchmark is an appropriate instrument for controlled invariance
  testing, provided it is not mistaken for field performance.
- No model downloads, telemetry, auto-update, or silent backend fallback are coherent defaults.
- The design correctly prioritizes precision over recall because false-positive harm is asymmetric.
- Evidence crops and overlays are treated as the user-facing product rather than a similarity
  score.
- The roadmap includes explicit failure outcomes for spikes instead of assuming the chosen
  architecture must survive measurement.
- The dataset policy treats embeddings, hashes, descriptors, findings, and triage as user-derived
  data rather than claiming they are anonymous by default.

## 5. Cross-document contradictions

1. **Zero network versus loopback sockets.** `README.md` and Privacy Mode A say no network request
   for any reason; ADR-0001 and `ARCHITECTURE.md` permit loopback HTTP for local models.
2. **AC-1 versus local-LLM coverage.** AC-1 says the full pipeline succeeds when `socket.socket`
   raises; the included local backend necessarily needs a socket unless it is excluded from “full
   pipeline.”
3. **LLM candidate extraction versus finding equality.** `MVP.md` and ADR-0004 call candidate
   extraction a V0.1 capability, but LLM-only candidates are excluded from the default result to
   preserve AC-7. It therefore cannot affect the V0.1 product output.
4. **Secondary checks must not delay versus all ACs mandatory.** `MVP.md` says numeric/reference
   work must not delay the image workflow, while AC-8 is mandatory for shipping.
5. **Optional corpus versus mandatory demo.** `MVP.md` §1.4 calls corpus comparison optional;
   `MVP.md` §9 says a credible demo must show a cross-paper corpus hit.
6. **Suppression versus emitted benign findings.** `MVP.md` says recurring controls and insets are
   suppressed before findings; the low-priority schema example intentionally emits a recurring-
   control finding, and the demo allows it to be surfaced.
7. **Sole geometric evidence path versus NCC evidence.** ADR-0005 calls geometric verification the
   sole evidence-producing path, then makes NCC/phase correlation an evidence-producing fallback.
8. **One Finding per JSONL line versus run header.** `ARCHITECTURE.md` describes `findings.jsonl`
   as one canonical Finding per line; `MVP.md` §6 says the same file has a run header containing
   coverage. No header schema exists.
9. **Schema-enforced recursive denylist versus actual schema.** `FINDING_SCHEMA.md` and ADR-0002
   say forbidden keys fail schema validation anywhere; `propertyNames` is only applied at the
   root, and nested open objects remain unrestricted.
10. **Observation-only structured vocabulary versus `possible_manipulation`.** ADR-0003 says
    machine-readable strings must survive decontextualization, while the canonical triage enum
    includes an inference-laden label.
11. **Fully reproducible evidence versus incomplete reconstruction data.** The schema claims
    findings can be re-derived without rerunning, but it records summaries and hashes rather than
    original bytes, exact preprocessing, coordinate spaces, and canonical identity rules.
12. **Content-type vocabulary drift.** `MVP.md`'s classifier list omits `flow_cytometry`, while
    the schema includes it.
13. **Strict Local data-at-rest scope.** Privacy Mode A says run and corpus directories only;
    `PRIVACY.md` §9 additionally permits an explicitly configured cache root.
14. **Canonical triage versus sidecar triage.** `Finding` requires an embedded `triage` object,
    while the run layout treats `triage.json` as a separate persistence source. The authoritative
    source and merge semantics are not defined.

## 6. Acceptance criteria review

### AC-1 — Modify

**Proposed wording:**

> The default Strict Local pipeline completes under OS-enforced denial of AF_INET/AF_INET6 and
> DNS, with zero attempted non-loopback connections recorded. Dependency, native-code,
> subprocess, proxy, redirect, and generated-report paths are included. If loopback model IPC is
> supported, it is separately enabled, disclosed, restricted to literal loopback with no proxies
> or redirects, and excluded from any zero-socket claim.

### AC-2 — Modify

**Proposed wording:**

> During runtime, all content-bearing writes resolve beneath the run, corpus, or explicitly
> configured cache roots. A syscall-level audit in isolated HOME/TMP/XDG directories covers
> dependencies and subprocesses and tests symlink/path traversal. Outputs use restrictive
> permissions. Installation writes are tested separately.

### AC-3 — Modify

**Proposed wording:**

> On a named supported platform, identical input bytes, effective configuration, component
> versions, and disabled optional models produce byte-identical canonical finding records and
> evidence assets after excluding explicitly listed run metadata. Canonical serialization, float
> quantization, pair ordering, and RNG seeds are specified.

The current tolerance-based comparison is not sufficient for identity fields: if floats may vary
within a tolerance, the design must specify which quantized values enter an ID and which are merely
diagnostic.

### AC-4 — Modify

**Proposed wording:**

> On a frozen held-out set with stated per-publisher minima, macro figure recall is at least 85%,
> no publisher slice is below the predeclared floor, and spurious extraction rate has a defined
> denominator. Caption-detectable misses are reported; the report must not claim unknown misses
> are detectable. IoU and confidence intervals are reported.

Twenty documents across five publishers are adequate for a spike, but too sparse for a strong
publisher-generalization claim. The V0.1 ship gate should either enlarge the held-out corpus or
state its uncertainty explicitly.

### AC-5 — Modify

**Proposed wording:**

> After thresholds and the supported transform/content envelope are frozen, candidate retrieval
> and verifier performance are measured separately. Held-out lineage-disjoint synthetic recall is
> at least 90%, with candidate recall at least 99%. Real confirmed pairs and hard benign pairs are
> reported separately. Across at least 50 expert-reviewed no-known-issue manuscripts, at least 95%
> have zero actionable image false positives and the one-sided 95% upper bound on mean false
> positives is below 0.25 per manuscript.

Synthetic recall is a statement about the declared transformation envelope, not estimated field
recall. Real confirmed-pair recall should be reported immediately and become a hard gate once a
predeclared adequate sample exists.

### AC-6 — Modify

**Proposed wording:**

> On the held-out control set, after match clustering and excluding coverage notes, the median
> actionable review groups are at most 5 and P95 is at most 10, reported separately by detector
> family and by expert disposition. Thresholds are frozen before this measurement. This is a
> usability budget, not a substitute for AC-5 precision.

Count clusters rather than pairwise matches so a control repeated five times does not create ten
independent queue items. Do not use an absolute maximum that a single unusual but legitimate paper
can fail; inspect and report the tail instead.

### AC-7 — Modify

**Proposed wording:**

> For narration-only backends, canonical finding IDs, types, priority, evidence, assets, and
> ordering are identical to NullBackend. LLM-generated candidate claims, if evaluated, are written
> to a separate experimental artifact and cannot enter the default finding stream.

The compared JSON projection must be specified exactly. Model-use provenance and narrative fields
may differ, but detectors must not receive model-dependent inputs in the default run.

### AC-8 — Modify and split

**Proposed wording:**

> Each numeric detector and each reference detector passes independently. Checks requiring
> unstated semantic or statistical assumptions remain experimental. For each enabled detector,
> report applicable-item count, recall on realistic seeded cases, and an expert-reviewed false-
> positive confidence bound. A failing detector is removed rather than averaged with stronger
> detectors.

Create separate subcriteria for proportion arithmetic, explicit-assumption p-value recomputation,
sample-size reconciliation, GRIM, and each reference check. “Zero false positives on 20 documents”
is an observation, not a sufficiently precise false-positive guarantee.

### AC-9 — Modify

**Proposed wording:**

> Every emitted artifact passes recursive runtime safety validation. System-generated structured
> fields contain no aggregate rating or accusatory inference; fixed disclaimers are present in
> HTML, Markdown, and run manifest and adjacent to each rendered finding. Human annotations are
> stored in a separately attributed namespace. Reports contain no headline document rating.

The schema denylist is defense in depth, not a complete safety mechanism. Report titles, CSS
classes, free text, generated prose, and export transformations must also be tested.

### AC-10 — Modify

**Proposed wording:**

> Every finding is inspectable without rerunning: image findings include full-context views,
> crops, matched-region overlays, coordinate systems, and limitations; numeric/reference findings
> include exact spans and assumptions. Exact recomputation is a separate property requiring source
> inputs and reproduction metadata.

“Sufficient for human review” and “sufficient to re-derive the detector result” are different
claims and should not be conflated.

### AC-11 — Modify

**Proposed wording:**

> Every finding references a manifest containing tool, parser, extraction, preprocessing,
> detector, and schema versions; effective parameter hash; input and asset digests; run mode;
> policy results; models; and template/prompt versions. A missing model digest is explicitly
> marked and prevents claiming exact narrative reproduction.

Prefer authoritative run-level provenance plus a manifest reference over duplicating large,
potentially divergent provenance objects into every finding.

### AC-12 — Modify

**Proposed wording:**

> On specified hardware, OS, and Python, at frozen accuracy thresholds, the 40-page benchmark
> completes in under 3 minutes at P95 over at least five cold-process runs. Stage timings and peak
> RSS are reported; timing cannot be improved by skipping applicable comparisons.

### AC-13 — Modify

**Proposed wording:**

> A 50-paper corpus builds in under 15 minutes and searches in under 60 seconds at frozen recall
> thresholds; correctness, candidate recall, index integrity, atomic rebuild, staleness, cold/warm
> timings, and disk size are also tested. A larger 500-paper characterization is reported before
> claiming the architecture covers the stated lab-size range.

The current latency targets are likely easy at 1,500 panels; correctness and false-positive
multiplication are the more important S4 risks.

### AC-14 — Modify

**Proposed wording:**

> In a clean VM for every supported OS/architecture/Python combination, installation from a hash-
> pinned local wheelhouse using `--no-index` succeeds, then the sample report and privacy checks
> complete with networking denied. No runtime model or data download is attempted.

## 7. Proposed ADR changes/additions

The repository states that accepted ADRs are superseded rather than silently rewritten. The
following ADRs should be added only after the relevant recommendations are explicitly accepted.
They are proposals from this review, not existing decisions.

### Proposed ADR-0009 — Exact Strict Local capability and trust boundary

- Decide zero socket versus zero non-loopback egress.
- Define loopback, local-process, and Unix-domain IPC semantics.
- Cover native dependencies, subprocesses, redirects, proxies, DNS, OS sync, and local model
  trust.
- Define which privacy properties are application-enforced, OS-enforced, tested, or out of scope.

### Proposed ADR-0010 — Comparable-region recovery and coverage uncertainty

- Separate figure extraction from panel/comparable-region recovery.
- Define what runtime coverage can and cannot know.
- Specify whole-figure fallback and downstream match-aware evaluation.
- Define the role of content-type classification without implying semantic correctness.

### Proposed ADR-0011 — Candidate retrieval, verification, grouping, and suppression

- Separate candidate-retrieval recall from evidence verification.
- Define constrained transform models and plausibility checks.
- Prohibit automatic benign inference from recurrence, inset, serial-image, or same-work status.
- Define grouping and review-priority behavior independently of detector evidence.

### Proposed ADR-0012 — Finding identity, triage linkage, and output-container format

- Separate stable detector occurrence IDs from durable review-link keys.
- Define canonicalization, collision budget, pair ordering, and migration.
- Decide whether JSONL contains findings only or typed run/finding records.
- Define the authoritative relationship between embedded triage and `triage.json`.

### Proposed ADR-0013 — Report safety and annotation provenance

- Define static HTML security and CSP requirements.
- Separate system narrative from reviewer annotations.
- Define safe sharing/export, redaction, and sensitive-output handling.
- Require adjacent non-adjudication framing for individually extracted findings.

### Proposed ADR-0014 — Evaluation governance

- Define threshold freezing and held-out access rules.
- Require confidence intervals and adequate slice sizes.
- Separate synthetic transform-envelope claims from field-performance claims.
- Define when real-positive evidence becomes a release gate.
- Define metric retirement or revision after a failed spike.

If these recommendations are accepted, the relevant portions of ADR-0001, ADR-0003, ADR-0004,
and ADR-0005 should be superseded. ADR-0006 should preserve the durable decision—SQLite and no
service—while treating the embedding/memmap layout as provisional. ADR-0002 and ADR-0007 should
remain unchanged. ADR-0008 should later be extended or superseded for authority-to-donate and
withdrawal-after-training semantics.

## 8. Pre-spike checklist

Before S1–S3 begin:

- [ ] Freeze annotation manuals for figure, panel, inset, label strip, stacked blot, composite,
      and comparable region.
- [ ] Measure inter-rater agreement on figure boxes, panel count, and comparable regions—not only
      disagreement resolution on a small overlap.
- [ ] Define every denominator: spurious figure, exact panel count, applicable pair, false alarm,
      actionable finding, and grouped finding.
- [ ] Version and hash corpus manifests; verify per-item license and source-image lineage.
- [ ] Prevent overlap by article, preprint/publication family, source image, and preferably
      lab/author cluster.
- [ ] Pre-register tuning, validation, and held-out partitions before threshold work.
- [ ] Give each publisher and content type a minimum held-out representation.
- [ ] Add hard benign negatives: adjacent microscopy, multichannel views, repeated legitimate
      controls, common plotting templates, insets, scale bars, and near-identical preprint
      versions.
- [ ] Add every available localized real confirmed pair; keep its results separate from synthetic
      performance.
- [ ] For S1, report caption-detectable misses separately from silent misses.
- [ ] For S2, measure downstream region-match recovery as well as panel-count accuracy.
- [ ] For S3, run exhaustive within-document local-feature comparison as the oracle and measure
      each candidate prefilter's recall independently.
- [ ] Compare similarity/affine-first verification against unrestricted homography; require
      bidirectional consistency and spatial coverage.
- [ ] Give NCC/phase correlation its own negative benchmark of blank backgrounds, generic blot
      strips, and repeated textures.
- [ ] Freeze the supported transformation envelope before acceptance evaluation.
- [ ] Predeclare what result causes dropping pHash, embeddings, NCC, or a content type from V0.1.
- [ ] Record library versions, feature settings, seeds, hardware, cold/warm state, and every
      threshold.
- [ ] Complete design-partner questions 6 and 7 before fixing the report's finding budget or
      rendering priority.
- [ ] Record spike failures and negative results with the same prominence as successes.

Questions that should deliberately remain unresolved until the spikes produce evidence:

- ORB versus SIFT, including content-type-specific routing.
- Whether pHash has any place in within-manuscript candidate generation.
- Whether pretrained embeddings add candidate recall sufficient to justify their dependency and
  corpus-storage cost.
- Whether NCC, phase correlation, or a more specialized low-texture method can meet the precision
  requirement.
- Whether whitespace/contour panel segmentation is adequate, needs a layout model, or should be
  deemphasized in favor of whole-figure region matching.
- The exact detection thresholds and supported transformation envelope.
- The final corpus descriptor/embedding physical layout.
- Any custom-model path; ADR-0007 correctly defers this.

## 9. Recommended documentation changes

### Required before S1–S3

- **`EVALUATION.md`** — repair S1–S3 datasets, denominators, split rules, real-positive slices,
  per-content metrics, confidence reporting, and prefilter-versus-verifier measurement.
- **`MVP.md`** — revise AC-4 through AC-6, add a panel/comparable-region gate, and distinguish
  image release requirements from secondary experimental capabilities.
- **`ROADMAP.md`** — update Week 0 inputs, stop gates, and the decisions that remain provisional
  until spike results exist.
- **`DATASET_POLICY.md`** — separate label certainty from domain realism and clarify evaluation
  grouping and control-set limitations.

### Required before production implementation

- **`README.md`** — state the exact, supportable Strict Local promise and the status of optional
  loopback models.
- **`PRODUCT.md`** — align the product wedge, report safety, and optional capabilities with the
  release contract.
- **`MVP.md`** — resolve the mandatory spine, corpus status, secondary detectors, LLM scope,
  triage workflow, and revised ACs.
- **`ARCHITECTURE.md`** — resolve privacy enforcement, candidate/verification boundaries,
  suppression semantics, identity, output format, and narration-only V0.1 scope.
- **`PRIVACY.md`** — narrow promises to mechanically enforceable behavior; cover local model trust,
  native/subprocess behavior, synced directories, report active content, and filesystem
  enforcement limits.
- **`FINDING_SCHEMA.md`** — define coordinate/preprocessing provenance, conditional evidence,
  stable review linkage, annotation attribution, narrative provenance, and recursive safety
  validation.
- **`DATASET_POLICY.md`** — add future authority-to-donate and withdrawal semantics while
  preserving the existing no-training decision for V0.1.
- **`EVALUATION.md`** — align all acceptance mappings with the revised criteria and add reference-
  detector evaluation if those detectors remain enabled.
- **`ROADMAP.md`** — sequence implementation from the revised release spine and ensure optional
  work cannot block it.
- **`schemas/finding.schema.json`** — encode the revised finding, evidence, identity, narrative,
  and annotation contracts.
- **`schemas/run_manifest.schema.json`** — encode the exact run/output contract and revised policy
  semantics.
- **`schemas/examples/*.json`** — update examples to exercise every revised evidence and
  attribution rule, including benign grouping without unsupported suppression.
- **`tools/validate_docs.py`** — validate the revised cross-document and emitted-artifact
  invariants without overstating what JSON Schema alone guarantees.
- **`docs/adr/README.md`** — list new ADRs only after the decisions are explicitly accepted.
- **New ADRs corresponding to the proposals in §7** — add only after decision owners resolve the
  recommendations.

ADR-0002 and ADR-0007 do not need substantive changes. Existing accepted ADRs should remain as
historical records and be superseded rather than rewritten to conceal the original decision.
