# ADR-0002 — No aggregate integrity, fraud, or risk score

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [PRODUCT.md §8](../../PRODUCT.md), [FINDING_SCHEMA.md §4](../../FINDING_SCHEMA.md), AC-9

## Context

Every review tool feels pressure to produce a single number. It makes dashboards possible, sorts
work queues, demos well, and is the first thing a prospective institutional buyer asks for.

For this product it is actively dangerous. The tool's outputs will be read by a PI about a
trainee's work, and may be forwarded, quoted, or subpoenaed. A document-level score would be
interpreted as a probability of misconduct no matter what caveats surround it — and would be
computed from measurements (visual overlap, numeric disagreement) that carry no information about
intent whatsoever.

A score also destroys the product's core mechanic. The value is a PI *looking at two pictures*.
A number invites acting without looking, which is exactly the failure the tool exists to prevent.

## Decision

**No aggregate score exists at any level of the system.** No integrity score, fraud score, risk
score, trust score, document rating, or overall grade — not in the schema, not in the report, not
in the API, not internally.

Specifically:

- The finding schema and run-manifest schema have `propertyNames` constraints that **fail
  validation** if any key matches an aggregate-score or misconduct-vocabulary pattern (AC-9).
- There is deliberately no document-level summary object. The run manifest carries counts by
  `review_priority` for rendering, annotated in-schema as counts and not a rating.
- `review_priority` is per-finding, is an ordering hint, and ships with a constant
  `review_priority_note` restating that it is not a probability of misconduct
  (ADR-0003).
- The report leads with evidence. There is no gauge, traffic light, or headline number.

## Rationale

- **The measurement does not support the inference.** An 86% inlier ratio is a statement about
  pixel geometry. Aggregating several such statements into "this manuscript scores 0.72" invents
  information that was never measured.
- **Scores get quoted; caveats do not.** "The tool gave it a 0.9" survives the trip into an email
  thread. The paragraph explaining what 0.9 means does not.
- **A score would make false positives more damaging, not less.** It launders a specific,
  inspectable, arguable observation into an unarguable global judgment.
- **Schema-level prohibition outlasts intentions.** A future contributor under demo pressure will
  add a score if it is merely discouraged. A failing test is what actually prevents it.

## Consequences

**Positive.** The tool cannot be used as an automated screening filter over many manuscripts —
which is a *feature*, since that use would multiply the harm of false positives. Users must engage
with evidence. Legal exposure is reduced: we make no aggregate assertion about any document or
person. The product's stated positioning and its data model agree.

**Negative.** Harder to demo to institutional buyers who want a dashboard. No trivial way to sort
or triage a large batch. Some users will ask for it; the answer is no, and PRODUCT.md §8 explains
why. Any future institutional layer must find a way to prioritize review work that does not rank
documents — likely by finding counts and priority distribution, explicitly framed as workload
rather than risk.

## Alternatives considered

- **A score shown only in the UI, absent from the JSON.** Rejected: the screenshot is what gets
  forwarded, and it would still drive the "act without looking" behaviour.
- **A "confidence" score per finding.** Rejected as a label; the underlying quantities
  (`inlier_ratio`, `ncc_peak`, `discrepancy`) are already exposed as evidence, named for what they
  actually measure. A field called "confidence" would be read as confidence *that something is
  wrong*.
- **A document-level count as a headline ("7 items to review").** Partly retained — counts appear
  in the run manifest and the report's coverage section for navigation — but never as a rating,
  never compared across documents, and never in a rank-ordered list of manuscripts.
- **An institution-configurable scoring policy.** Rejected: delegating the decision does not make
  the inference valid, and it would guarantee the tool is used for screening.
