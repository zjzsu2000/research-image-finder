# ADR-0003 — Finding types name observations, not inferences

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [FINDING_SCHEMA.md](../../FINDING_SCHEMA.md), [PRODUCT.md §8](../../PRODUCT.md), AC-9

## Context

The original design draft proposed `finding_type: "possible_image_reuse"` with
`severity: "high"`. Both are natural, readable, and wrong for this product.

`possible_image_reuse` is a claim about *what happened in the world*: that an image was reused.
What the detector actually established is that a region of one panel aligns to a region of another
under a specific geometric transform, with a measured inlier ratio. Those are different
statements, and the gap between them is exactly where a PI's judgment belongs.

`severity` carries an unavoidable connotation — severity *of what?* — that reads as
severity-of-misconduct.

These strings are not UI copy. They are machine-readable fields that will be exported, pasted into
emails, quoted in institutional processes, and potentially produced in legal discovery, stripped
of every surrounding caveat.

## Decision

1. **`finding_type` is `family.observation`, dotted, naming what was measured.**
   `image.duplicate_region_pair`, `numeric.sample_size_disagreement`,
   `stats.pvalue_inconsistent_with_statistic`, `reference.cited_not_listed`.
   Never `possible_image_reuse`, `suspected_manipulation`, or `likely_fabrication`.
2. **`severity` is replaced by `review_priority`** (`info | low | medium | high`), and `severity`
   is *forbidden* by the schema.
3. **`review_priority_note` is a required constant** on every finding: *"Ordering hint for human
   review. NOT a probability, likelihood, or indication of misconduct."* — so the caveat survives
   partial extraction of the JSON.
4. **A vocabulary denylist is enforced by schema validation**: `fraud`, `misconduct`,
   `fabrication`, `falsification`, `plagiarism`, `cheating`, `guilty`, `intent`, `verdict`, and
   `severity` may not appear as keys or enum values in findings or run manifests.
5. **Inference lives in prose, hedged, alongside benign explanations.** `why_flagged` states the
   measurement; `possible_benign_explanations` (minimum one, required) states the alternatives.
6. The same discipline governs triage labels: the strongest permitted is `possible_manipulation`,
   and it describes the image, not the author
   ([DATASET_POLICY.md §6](../../DATASET_POLICY.md)).

## Rationale

- **Machine-readable strings must survive decontextualization.** `image.duplicate_region_pair`
  read aloud in a meeting is accurate. `possible_image_reuse` read aloud is an allegation.
- **It keeps the detector honest.** Naming the type after the measurement makes it obvious when a
  detector is claiming more than it computed — a design smell that would otherwise hide behind a
  friendly label.
- **It makes the schema a safe interchange format.** If this schema is ever adopted between labs,
  tools, and institutions ([PRODUCT.md §11](../../PRODUCT.md)), observation-named types are what
  make that adoption defensible.
- **A denylist is a test.** Tone guidance in a style guide erodes; a failing build does not.

## Consequences

**Positive.** Findings are quotable without becoming accusations. The schema is legally safer and
more durable. Detectors are pushed toward measuring precisely. Report prose has a clear division
of labour: the type says what was measured, the prose says what it might mean, and the benign
explanations say what it probably means.

**Negative.** Type names are less immediately intuitive to a first-time user; the report must
supply human-readable titles alongside them ("A region appears in two figures"). Contributors must
learn the convention, and the denylist will occasionally reject a well-intentioned name. Some
findings are genuinely harder to name this way — `image.panel_contains_panel` for an inset is
precise but clumsy. Precision wins.

## Alternatives considered

- **Keep `possible_image_reuse` and rely on report framing.** Rejected: framing does not travel
  with the JSON.
- **Keep `severity` because it is a familiar convention.** Rejected: familiarity is exactly the
  problem — readers import their prior meaning, which here is severity of wrongdoing.
- **Add an explicit `inference` field carrying the hedged interpretation.** Rejected as premature
  structure; hedged interpretation belongs in prose where hedging is natural, and a structured
  inference field would be trivially strip-able into an assertion.
- **Use opaque numeric type codes.** Rejected: unreadable, and it would push interpretation into
  undocumented lookup tables.
