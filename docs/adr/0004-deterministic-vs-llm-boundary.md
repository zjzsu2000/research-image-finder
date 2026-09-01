# ADR-0004 — The boundary between deterministic detectors, pretrained ML, and LLM reasoning

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [ARCHITECTURE.md §3–§4](../../ARCHITECTURE.md), [PRODUCT.md §7](../../PRODUCT.md), AC-3, AC-7

## Context

"LLM optional" is easy to state and hard to keep. The usual decay path is well worn: the LLM
starts as a narrator, then helps extract numbers, then adjudicates ambiguous extractions, then
suppresses findings that "look benign," and eventually the system cannot function without it — at
which point the tool is non-reproducible, non-auditable, and capable of manufacturing findings
that no measurement supports.

For a research-integrity tool this is disqualifying. A PI confronting a trainee needs to be able
to say *what was measured*. "A language model thought the numbers disagreed" is not that.

At the same time, language models are genuinely useful here: for readable explanations, for
finding candidate numeric claims in prose that regexes miss, and for grouping related findings.

## Decision

Three layers with hard, testable boundaries.

**Layer 1 — deterministic detectors. Owns 100% of findings and 100% of evidence.**
PDF parsing, figure extraction, panel segmentation, hashing, ORB/SIFT + RANSAC, NCC, transform
estimation, benign-pattern suppression, statistical recomputation, offline reference checks, and
**priority assignment** (a rule table, never a model).

**Layer 2 — pretrained ML. Recall boosters and false-positive suppressors only.**
Pretrained embeddings for corpus retrieval; content-type classification (heuristic in V0.1).
**A Layer-2 hit is never a finding.** Every candidate it surfaces must be confirmed by a Layer-1
geometric check before it becomes one. Layer 2 can be deleted entirely and the system still works,
with lower recall and unchanged precision.

**Layer 3 — LLM. Language, never measurement.**
*Allowed:* writing `why_flagged`, `possible_benign_explanations`, `recommended_verification`;
**extract-then-verify** (proposing candidate numeric claims that a Layer-1 checker then verifies);
presentational clustering.
*Forbidden:* asserting any mismatch not computed by Layer 1; judging image similarity or
estimating transforms; assigning or altering `review_priority`; emitting a finding with no
Layer-1 evidence.

**The invariant (AC-7):**

> A run with the LLM enabled and a run with the LLM disabled produce identical finding IDs,
> `finding_type`, `review_priority`, `evidence`, and `evidence_assets`. Only narrative prose and
> `narrative_source` may differ.

**Corollary for extract-then-verify.** An LLM-proposed candidate can only cause a deterministic
check to *run*. If a candidate would be the sole path to a finding, that finding carries
`detector.params.candidate_source = "llm"` and is **excluded from the default V0.1 finding set** —
making it a V0.2 scope question rather than an AC-7 violation.

Enforcement: `ReasoningBackend.narrate` receives a fully-formed finding and returns a `Narration`
whose type cannot express a change to evidence or priority; the AC-7 test compares full runs both
ways; `NullBackend` is the default and the reference implementation.

## Rationale

- **It makes "LLM optional" mechanical.** The invariant is a test, not an intention, and it is
  cheap to keep if written early and expensive to retrofit.
- **It bounds the blast radius of hallucination.** A compromised or confused model degrades prose
  quality. It cannot manufacture a finding about a person's work.
- **It preserves reproducibility (AC-3)**, which an integrity tool cannot do without.
- **It keeps the product provider-agnostic.** Since no finding depends on a model, no model is
  load-bearing, and swapping or removing backends is safe.
- **It matches where LLMs are actually reliable** — fluent explanation and candidate generation —
  and keeps them away from where they are not: precise measurement and calibrated judgment.

## Consequences

**Positive.** The system works fully with zero models installed. Findings are always defensible by
pointing at a computation. Backends are swappable. A user disputing a finding can be answered with
arithmetic. Testing is tractable, because Layer 1 is pure functions with fixed inputs and outputs.

**Negative.** Some genuinely useful LLM capabilities are foreclosed in V0.1 — notably free-form
cross-modal consistency reasoning ("the text says the effect was significant but the table shows
p = 0.21"), which would require an LLM to be the evidence source. Extract-then-verify is more work
than extract-and-assert. Prose quality from `NullBackend` templates is workmanlike. And the
`candidate_source = "llm"` exclusion means some real inconsistencies found only via LLM extraction
will not be reported in V0.1 — a deliberate, documented recall cost.

## Alternatives considered

- **LLM as a first-class detector with confidence scores.** Rejected: non-reproducible,
  non-auditable, and capable of asserting things about a person's work with no measurement behind
  them.
- **LLM as an adjudicator over deterministic findings (suppress the benign ones).** Rejected,
  though tempting: it would let a model silently *remove* a real finding, which is worse than
  adding a false one and is invisible in the output.
- **LLM as a final report editor with free rein over the text.** Rejected: it could restate a
  hedged observation as an assertion. Narration is per-finding and structurally constrained.
- **No LLM at all.** Considered seriously. Rejected because template prose is noticeably worse at
  articulating benign explanations, and benign explanations are a load-bearing safety feature
  ([PRODUCT.md §8](../../PRODUCT.md)) — but the system must remain fully functional without one,
  which is exactly what AC-7 guarantees.
