# Verification Hardening Spike — preregistered contract

This slice is frozen before the held-out run. It remains disposable spike code.

## Geometric-support conjunction

Historical hardening runs used `status=verified_match`. That term is superseded for all current
machine output by `status=geometrically_supported_candidate`. The conjunction is unchanged and
does not establish provenance. The status is emitted only when every condition below is true:

1. mutual/symmetric ratio-test correspondence is present;
2. at least 8 retained tentative correspondences;
3. at least 10 geometric inliers;
4. inlier ratio is at least 0.45;
5. query-side inlier bounding-box coverage is at least 0.08;
6. source-side inlier bounding-box coverage is at least 0.02;
7. median forward reprojection error is at most 3 pixels;
8. median backward reprojection error is at most 3 pixels;
9. the estimated transform and projected polygon are finite;
10. projected query area ratio is between 0.02 and 25.0.

RANSAC producing a model is not sufficient. Failed conditions are retained in the diagnostic
record. Passing all conditions provides geometric support for retrieval ranking only. The cap of
80 ratio-passed matches bounds RANSAC input but does not prune source files.

## Registered algorithm settings

- ORB: `nfeatures=2500`, `scaleFactor=1.2`, `nlevels=8`, `fastThreshold=12`, Hamming distance.
- SIFT: `nfeatures=0`, `nOctaveLayers=3`, `contrastThreshold=0.04`, `edgeThreshold=10`,
  `sigma=1.6`, L2 distance.
- Ratio threshold: 0.75 for both directions.
- Geometric reprojection threshold: 3 pixels; max 2,000 iterations; confidence 0.995.
- Primary model: full affine (reflection permitted for flip); unrestricted homography is a
  comparison arm only.

## Split and reporting rules

Positive transform slices and hard-negative content slices are labeled tuning or held-out before
execution. Thresholds are not changed after held-out results are inspected. Results are reported
per slice, algorithm, and transform model, with actual counts and timing stages:

- discovery;
- file decode;
- descriptor extraction;
- pair matching;
- geometric verification;
- overlay/rendering.

Synthetic positives are transform-envelope evidence only. Absent-source and hard-negative queries
measure geometric-support candidate burden in a no-known-source set. They are not detector labels,
scientific false-positive judgments, or proof of clean directories.
