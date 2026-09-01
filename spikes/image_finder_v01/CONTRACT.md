# Research Image Finder V0.1 — disposable spike contract

Status: frozen for Steps 1–7; this is not a production API.

## Scope

- One query image and one explicitly selected local directory.
- Initial formats: PNG, JPEG/JPG, and single-page 8-bit grayscale/RGB/RGBA TIFF.
- Exhaustive local comparison first; no prefilter, pHash, embeddings, index, PDF, LLM, or
  network path.
- ORB and SIFT are compared with separately preregistered reasonable parameters.
- A diagnostic result is evidence of visual correspondence only. It is not a Research Preflight
  Finding and contains no scientific or conduct interpretation.

## Registered parameters

### Shared

- Normalize decoded pixels to 8-bit grayscale for feature extraction.
- Resize only when the long edge exceeds 1600 pixels, preserving aspect ratio.
- Lowe ratio test: 0.75.
- Homography RANSAC reprojection threshold: 5 pixels.
- Minimum tentative matches: 6.
- Minimum inliers for a geometrically supported candidate: 6.
- Output ranking: descending inlier count, then inlier ratio, then deterministic source digest.

### ORB

- `nfeatures=2500`, `scaleFactor=1.2`, `nlevels=8`, `fastThreshold=12`.
- Hamming BFMatcher; ratio-filtered matches.

### SIFT

- `nfeatures=0`, `nOctaveLayers=3`, `contrastThreshold=0.04`, `edgeThreshold=10`, `sigma=1.6`.
- L2 BFMatcher; ratio-filtered matches.

These parameters are spike registrations, not final V0.1 thresholds.

## Coverage contract

The scanner must report every supported file, unsupported extension, unreadable file, and TIFF
variant that it encounters. It must not follow symlinks outside the selected root. A decoder
failure is an explicit error record, never a silent omission.

## Evaluation contract

Every benchmark records:

- actual query/source/control counts;
- source lineage and transformation slice;
- algorithm and registered parameters;
- top-1/top-5/top-10 recovery;
- no-known-source candidate burden;
- latency and peak process memory where available;
- failures by transform/content/format slice;
- paths and evidence assets only in the local spike output, never in committed fixtures.

Synthetic transform results are limited to their declared envelope. They are not field-performance
claims. Control results are no-known-source observations with residual uncertainty.
