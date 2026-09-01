# ADR-0005 — Geometric verification is the primary evidence path; perceptual hashing is a prefilter

- **Status:** Accepted *(gated on spike S3 confirming the premise)*
- **Date:** 2026-08-30
- **Relates to:** [ARCHITECTURE.md §3, §9](../../ARCHITECTURE.md), [EVALUATION.md § S3](../../EVALUATION.md), AC-5

## Context

Perceptual hashing (pHash, dHash, aHash) is the obvious first tool for near-duplicate image
detection: fast, tiny, and trivially indexable as a Hamming distance over 64-bit codes. The
original design draft listed it alongside local features as a peer technique.

But the cases that matter in scientific figure integrity are precisely the ones pHash handles
worst:

- a **cropped** region reused elsewhere — pHash describes the whole image, and a crop changes it
  globally;
- a **flipped** or **rotated** panel — not a small perturbation in hash space;
- a **rescaled** panel composited at different sizes;
- a **partial region** of one panel appearing inside another;
- **contrast- or brightness-adjusted** reuse from figure preparation.

Additionally, a Hamming distance is poor evidence. "phash_hamming = 6" tells a PI nothing they can
look at or argue with. It does not say *which region* matched or *what transform* relates the two
panels — and the transform is often the most informative part of the finding.

## Decision

1. **Geometric verification is the sole evidence-producing image comparison path.** ORB (or SIFT)
   keypoints → Lowe ratio test → RANSAC homography. Only a match surviving geometric verification
   may become a finding.
2. **pHash/dHash are prefilters only.** They cheaply narrow the candidate set. Their distance is
   recorded in `evidence.phash_hamming` as a diagnostic, never as the basis for a finding.
3. **Low-texture fallback is required, not optional.** Western blots and uniform fluorescence
   panels often yield too few keypoints. For panels below a keypoint floor, normalized
   cross-correlation / phase correlation provides the match and `evidence.method` records which
   path produced it.
4. **The estimated transform is first-class evidence.** `estimated_transform` (flip, rotation,
   scale, type) and the homography are recorded, and the report renders the matched region
   outlined on both crops.
5. **Pretrained embeddings, if used at all, sit alongside pHash as a Layer-2 recall booster**
   whose candidates must still pass geometric verification (ADR-0004).

## Rationale

- **It survives the transforms that matter**, which is the entire detection problem.
- **It produces evidence a human can act on.** "142 geometrically consistent matches under a
  horizontal flip, covering 40% of each panel," plus an outlined overlay, is something a PI can
  evaluate in seconds. A Hamming distance is not.
- **The transform is diagnostic in itself.** A pure horizontal flip between two panels captioned as
  different conditions is far more informative than any similarity number.
- **RANSAC's inlier structure is a natural precision knob**, and precision is the governing metric
  ([MVP.md §5](../../MVP.md)).
- **The cost is affordable.** At tens of panels per manuscript and thousands per lab corpus, the
  pHash prefilter makes exhaustive geometric verification cheap enough
  (ADR-0006).

## Consequences

**Positive.** Crop, flip, rotation, scale, and partial reuse are detectable. Every image finding
ships with a picture and a transform. Thresholds (`min_inliers`, `inlier_ratio`) are
interpretable, tunable, and recorded in `reproduction.params`. No training data required.

**Negative.** Substantially more computation than hashing alone, requiring the prefilter cascade to
stay tractable. Low-texture panels need a second code path with its own thresholds and failure
modes. Repetitive textures (regular arrays, gratings, tiled structures) can produce spurious but
geometrically consistent matches — a known false-positive source that suppression must handle.
Insets legitimately produce strong geometric matches, so containment detection is mandatory rather
than optional.

**Status caveat.** This ADR is **gated on S3**. If measurement shows pHash-only meets AC-5 on the
transform battery, this decision is wrong and must be revised. The spike exists to test it, and
the result — either way — is recorded in EVALUATION.md.

## Alternatives considered

- **pHash/dHash only.** Rejected on the analysis above; S3 will produce the numbers that confirm
  or refute it.
- **Deep embedding similarity as the primary signal.** Rejected for V0.1: embeddings measure
  semantic similarity, so two distinct micrographs of the same tissue score highly — a
  false-positive generator. They also produce no transform and no region, failing AC-10.
- **A trained duplicate classifier.** Rejected: no trustworthy labels, no measured baseline to beat,
  and it would compromise reproducibility (ADR-0007).
- **Block-matching / copy-move forensics from the image-forensics literature.** Deferred. It is the
  right family for *within-image* cloning, which V0.1 does not cover, and it carries a higher
  false-positive rate on legitimate scientific imagery than we can afford at this stage.
