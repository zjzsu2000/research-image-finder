# ADR-0008 — Private user data is not training data

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [DATASET_POLICY.md §3](../../DATASET_POLICY.md), [PRIVACY.md](../../PRIVACY.md), [PRODUCT.md §12](../../PRODUCT.md)

## Context

The standard AI product playbook is ship → instrument → harvest → train → compound. Applied here,
it would be extraordinarily effective: real unpublished manuscripts with real figure-assembly
errors, and real PI dispositions on real findings, are precisely the training data that would make
a false-positive suppressor work. No public corpus substitutes for it.

It is also the one thing that would destroy this product. The users who most need a local-first
integrity preflight are the users for whom a single instance of unpublished data leaving the lab
is a career, contractual, or regulatory event. And the concern is not hypothetical: institutional
review, sponsor agreements, IRB protocols, and pharma legal all ask the question directly.

The temptation will not arrive as a decision to harvest data. It will arrive as "anonymous
aggregate metrics," "opt-out crash reporting," or "we only send embeddings, not images." Each
looks small. Each ends the guarantee.

## Decision

**Manuscripts, figures, panels, corpora, intermediate artifacts, findings, and triage decisions
from Strict Local runs are not training data. By default and by construction.**

Specifically:

- No silent collection, no telemetry-based harvesting, no background upload, no "help improve the
  model" default.
- **Derived artifacts are user data too.** Embeddings, perceptual hashes, descriptors, and crops
  are derived from the manuscript and inherit its treatment. "We only send embeddings" is not an
  exception.
- Findings and triage dispositions — valuable as they are — are user data and are not collected.
- User material may enter a future dataset only through **explicit, informed, revocable opt-in**
  that names the specific items, the purpose, the retention, and whether redistribution is
  permitted, with the consent record stored alongside the data
  ([DATASET_POLICY.md §7](../../DATASET_POLICY.md)).
- **There is no collection endpoint and no collection code.** In Strict Local there is no network
  call at all (ADR-0001), so this is a property of the system rather than a policy about data we
  receive.
- Preference order for future data: openly licensed public corpora → synthetic ground truth →
  donated already-published figures → donated structured findings without image bytes → donated
  unpublished material under a written design-partner agreement, only if nothing above suffices.
- Changing this requires a new ADR, a major-version bump, and explicit user opt-in. It cannot
  happen through a settings default or a dependency update.

## Rationale

- **The guarantee is the product.** Without it, the target user cannot run the tool at all, and no
  amount of model quality compensates.
- **"We don't train on your data" is only credible when there is no collection path.** A disabled
  toggle invites the question of who can enable it; absent code does not.
- **Compliance review is a real gate.** Any collection mechanism must be re-defended in every
  procurement conversation, forever.
- **Consent obtained by default-on settings is not informed consent**, particularly where the data
  may include patient-identifiable imagery or a third party's unpublished work — the trainee's
  manuscript is not the PI's alone to donate.
- **Alternatives exist and are sufficient to start.** Synthetic ground truth gives exact labels at
  scale with zero privacy exposure ([DATASET_POLICY.md §5](../../DATASET_POLICY.md)).

## Consequences

**Positive.** The privacy promise is unconditional and testable. Air-gapped and regulated
deployment is possible. No data-breach surface. No consent-management or data-subject-request
machinery to build. The product's stated values and its implementation agree, which is what makes
adoption conversations short.

**Negative — stated plainly.** We forgo the most valuable training data available to us. We will
not know our field false-positive rate unless users choose to tell us. Improvement is slower and
requires deliberate, funded dataset construction. A competitor willing to harvest may improve
faster on paper. **We accept all of this.**

**Mitigation, not evasion.** Design-partner relationships under written agreement, where a small
number of labs consciously participate in evaluation, give us honest signal without a collection
mechanism — and the users are the ones deciding, item by item, what they share.

## Alternatives considered

- **Opt-in telemetry, default off.** Rejected for V0.1: the code's existence is the liability, and
  a default-off toggle is one careless release away from being default-on.
- **Federated or on-device learning.** Rejected as premature: substantial complexity, real
  privacy-leakage subtleties in model updates, and it presupposes a training program we have
  deliberately deferred (ADR-0007).
- **Collect only anonymized structured findings, no content.** Deferred, not rejected — it is the
  most defensible future option (preference level 4) — but it still requires a collection endpoint,
  so it belongs to a future Hybrid Privacy mode with explicit per-payload consent, never to Strict
  Local.
- **Collect only from users who explicitly donate published papers.** Accepted as future
  preference level 3, gated on the consent and provenance machinery in
  [DATASET_POLICY.md §7](../../DATASET_POLICY.md).
