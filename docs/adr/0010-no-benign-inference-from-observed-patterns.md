# ADR-0010 — No benign inference from observed patterns; suppress only non-comparable material

- **Status:** Accepted
- **Date:** 2026-08-30
- **Amends:** [ADR-0003](0003-observation-named-finding-types.md) (extends the observation-not-inference
  rule from naming to filtering), [ADR-0005](0005-geometric-verification-over-perceptual-hashing.md)
  and [ADR-0006](0006-sqlite-plus-numpy-corpus-index.md) (their suppression stages)
- **Relates to:** [PRODUCT.md §8](../../PRODUCT.md), [MVP.md §§1.3–1.4](../../MVP.md), AC-5, AC-6, AC-10
- **Origin:** [Codex Phase 1 design review](../reviews/2026-08-30-codex-phase1-design-review.md) §2.3

## Context

The Phase 1 design specified "benign-pattern suppression" before findings are emitted: panels
matching three or more others were treated as recurring controls, containment relationships as
insets, and corpus matches against a version of the same work as same-work artifacts. In each
case the match was to be removed from the output.

This is an inference of benignity, and the evidence does not support it:

- A repeated loading control can be legitimate, **wrongly paired to the wrong experiment**, or
  itself the assembly error. Repetition count is a fact about the document, not about whether the
  reuse is scientifically appropriate — that depends on experimental provenance which is not
  present in the pixels.
- An inset is expected, and may still require disclosure in the legend.
- A preprint-to-publication match may contain a **changed or replaced** panel, which is precisely
  the interesting case.

Suppressing on these grounds produces a silent false negative exactly where the product promises
evidence for human verification. It also contradicts ADR-0003: we committed to naming observations
rather than inferences, and then proposed to *delete* observations on the strength of an inference.

The design was already inconsistent with itself here. `schemas/examples/finding_image_low_benign.json`
emits a recurring-control finding at low priority, while the prose said suppression removes it.
**The example was right and the prose was wrong.**

## Decision

Two categories, with a hard line between them.

### 1. Exclusion — permitted, and only for technical non-comparability

Material may be excluded from comparison **before** matching when it is not a comparable image
region at all:

- scale bars, colorbars, axis strips, panel-label glyph strips;
- regions below the minimum usable pixel dimensions;
- non-image content (rendered text blocks, vector rule lines);
- panels that failed extraction or segmentation quality checks.

Exclusions are recorded on the panel with a reason, counted in `coverage.panel_exclusion_reasons`,
and reported. Excluding material is a statement about *our ability to compare it*, never about
whether a relationship would have been benign.

### 2. Annotation, grouping, and demotion — the only permitted response to an observed pattern

Recurrence, containment/inset relationships, serial or adjacent imaging, and same-work status
**must not suppress a finding.** They are recorded as evidence fields
(`recurring_control_candidate`, `recurring_control_match_count`, `inset_relationship`,
`same_work_candidate`), used to **group** related matches into a single review item, and may
**demote `review_priority`**.

The software may describe the observed pattern. It may not conclude the relationship is benign.

### 3. Priority demotion is permitted; suppression is not

Demotion survives this ADR's own argument because `review_priority` is defined as a review-queue
ordering hint that is explicitly not a claim about the world (ADR-0003), and ships with
`review_priority_note` saying so. Ordering a queue by where a human's attention is likely to be
well spent is legitimate. Removing the observation from the queue is not.

### 4. Disclosed relationships

A relationship may be suppressed only when disclosure is established from **deterministic
metadata** — for example, a figure legend that explicitly states the reuse, matched by an exact
deterministic rule. Even then, annotation is preferred over suppression, and any such rule must be
recorded in `reproduction.params` so the user can see what was applied.

### 5. Grouping becomes a required capability, not a nicety

Because nothing is suppressed, a control repeated five times produces ten pairwise matches. Those
must collapse into **one review item** with its member pairs attached. Consequently AC-6 counts
**actionable review groups**, not pairwise matches, and grouping must exist before AC-6 can be
measured at all.

## Rationale

- **It restores consistency with ADR-0003.** Observation-not-inference has to govern filtering as
  well as naming, or it is a naming convention rather than a principle.
- **The failure mode it prevents is invisible.** A false positive is arguable in front of the
  user; a suppressed true positive is not. We are structurally unable to detect that error, which
  is exactly why the rule must be categorical.
- **The wrong-control case is real and common.** "This control was reused" and "this control was
  reused *from the wrong experiment*" look identical to a frequency heuristic and are completely
  different findings.
- **The information is preserved either way.** Grouping and demotion deliver the same noise
  reduction as suppression, without discarding evidence — the user sees one calm, well-explained
  item rather than nothing.

## Consequences

**Positive.** No silent false negatives from benignity heuristics. The recurring-control case
becomes a presentation problem, which is tractable, rather than a detection decision, which is
not. Findings stay honest about what was measured. Users can audit what the tool decided not to
show them, because it did not decide that.

**Negative.** More findings reach the report, so the finding budget (AC-6) is harder to meet and
depends on grouping quality rather than on threshold aggressiveness. Grouping and clustering
become required V0.1 work that was previously implicit. The report design carries more weight:
a recurring control must read as calm and contextual, not alarming — poor presentation of a
correctly-surfaced benign pattern is now the dominant alarm-fatigue risk.

**Consequences for the spikes.** S3 must measure candidate retrieval, correspondence, transform
verification, and grouping as **separate stages**, since grouping quality now directly determines
AC-6. S3 must also include hard benign negatives — adjacent microscopy, multichannel views,
repeated legitimate controls, shared plotting templates, insets, scale bars, near-identical
preprint versions — because these can no longer be defined out of the measurement.

## Alternatives considered

- **Keep suppression, with a `--show-suppressed` flag.** Rejected: a default that hides
  observations is the default that ships, and almost nobody passes the flag. The harm is the
  default behaviour.
- **Suppress only same-work matches, since the corpus document is a version of the subject.**
  Rejected, and it is the most tempting exception: a preprint-to-publication comparison is exactly
  where a *replaced or altered* panel would show up. Demote and group instead.
- **A learned false-positive classifier deciding what to suppress.** Rejected for V0.1 by
  [ADR-0007](0007-no-custom-model-training-in-v0.1.md), and it would inherit this ADR's objection
  regardless: a model asserting benignity is still asserting benignity.
- **Emit everything with no demotion at all.** Rejected: it would meet the letter of
  observation-not-inference while making the report unusable, and `review_priority` is already
  defined in a way that makes ordering legitimate.
