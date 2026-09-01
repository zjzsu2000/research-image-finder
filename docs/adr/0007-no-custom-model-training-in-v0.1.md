# ADR-0007 — No custom model training in V0.1

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [DATASET_POLICY.md §11–§12](../../DATASET_POLICY.md), [ARCHITECTURE.md §11](../../ARCHITECTURE.md), [PRODUCT.md §10](../../PRODUCT.md)

## Context

The product roadmap anticipates genuinely useful specialized models: a scientific image-pair
classifier, a transformation classifier, a panel-type classifier, and — most valuable — a
false-positive suppressor that learns which repeated panels are legitimate loading controls.

The pull to start training immediately is strong, and there is a superficially available data
source: retraction databases plus PubPeer, joined to publisher PDFs. That path is a trap
([DATASET_POLICY.md §1–§2](../../DATASET_POLICY.md)) — it produces a model that predicts
controversy, not duplication.

There is also a more basic problem: **we do not yet know what a well-tuned classical baseline
achieves.** Spike S3 has not run. Training before that measurement risks spending weeks to build
something worse than ORB + RANSAC with good thresholds, which is a common and expensive outcome.

## Decision

**Research Preflight V0.1 trains no custom models and fine-tunes nothing.**

V0.1 may use: deterministic image matching (perceptual hashing, ORB/SIFT + RANSAC, NCC/phase
correlation); classical CV (thresholding, projection, contour analysis); pretrained models used
as-is; pretrained embeddings for candidate retrieval; and optional local LLMs for narrative and
candidate extraction only.

Custom models are considered only when **all five** hold
([DATASET_POLICY.md §11](../../DATASET_POLICY.md)):

1. the detector pipeline is empirically validated on the evaluation corpus;
2. sufficient level-B/C (confirmed or expert-reviewed) labels exist;
3. dataset provenance and licensing are clear and recorded per item;
4. an evaluation benchmark with splits and leakage checks is defined **first**;
5. there is evidence a trained model beats the **tuned** classical baseline — not an untuned
   strawman.

Any training run additionally requires an approved proposal answering the twelve questions in
[DATASET_POLICY.md §12](../../DATASET_POLICY.md).

## Rationale

- **We have no measured baseline to beat.** Condition 5 is the whole argument: without S3's
  numbers, "the model improves things" is unfalsifiable.
- **We have no trustworthy labels.** Retraction is paper-level and often unrelated to images;
  PubPeer is allegation, not confirmation. Training on either yields a controversy predictor.
- **Determinism is a product requirement** (AC-3, AC-7). A learned similarity score is harder to
  reproduce, explain, and defend when a PI disputes a finding about a trainee's work — which is
  the situation the tool exists to support.
- **The most valuable model needs data we can only get by shipping.** A false-positive suppressor
  is trained on `legitimate_reuse` dispositions, which do not exist until real PIs triage real
  reports.
- **Privacy-by-default forecloses harvesting** ([PRODUCT.md §12](../../PRODUCT.md)), so training
  data must be deliberately and lawfully constructed. That is a project, not a side effect.
- **Classical methods produce evidence directly.** An inlier count and a homography are inspectable
  in a way a learned score is not, which matters for AC-10.

## Consequences

**Positive.** V0.1 ships faster with a smaller dependency footprint and no GPU requirement
(AC-12, AC-14). Every finding is explainable and reproducible. No legal exposure from training on
publisher content. No risk of encoding a "which papers look suspicious" bias into the product's
core. Deterministic thresholds are tunable per-user and per-corpus in a way learned models are not.

**Negative.** Lower recall on hard cases: heavy compression, re-photographed figures, aggressive
resampling, and image pairs that are the same specimen but not the same file. No learned
suppression of legitimate reuse, so the recurring-control heuristic must carry that load with
hand-tuned rules. Low-texture panels remain the known weak spot, handled by NCC rather than by a
model that could learn blot structure. Competitors willing to train may show better benchmark
numbers before we do.

**Ongoing obligation.** Design V0.1's triage vocabulary to match the future label schema
([DATASET_POLICY.md §6](../../DATASET_POLICY.md)) so that when opt-in labels do become available,
they are immediately usable — the cheapest possible investment in a future we are deliberately
deferring.

## Alternatives considered

- **Train a duplicate classifier on retraction-derived data now.** Rejected on
  [DATASET_POLICY.md §1](../../DATASET_POLICY.md): methodologically invalid, legally risky, and it
  would produce a controversy predictor.
- **Fine-tune a pretrained embedding model on synthetic transforms.** Deferred, and the most
  defensible future option — synthetic data gives exact labels. Still premature: it must beat the
  tuned classical baseline (condition 5), and S3 has not yet established what that is.
- **Train a panel content-type classifier immediately.** Deferred to V0.2. This is the *most*
  justifiable near-term model (labels are cheap and uncontroversial), but heuristics are sufficient
  for V0.1's gating use, and every model added now is a dependency, a reproducibility question, and
  a provenance record.
- **Use a commercial vision API for image comparison.** Rejected outright: violates ADR-0001.
