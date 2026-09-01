# Verification Hardening Spike — measured result

Run: 2026-08-31, disposable synthetic benchmark, 1,000 positive source files and 120 hard-
negative source files. Parameters were frozen in `HARDENING_CONTRACT.md` before this run.

## Positive recovery

The target source was Top-1 for both algorithms on identity, crop, resize, rotation, and
brightness/contrast. SIFT was also Top-1 on flip. ORB did not recover flip within Top-10 (rank
219 affine, rank 244 homography). Homography produced extra geometrically supported candidates on
positives
(for example SIFT identity: 4 versus affine: 1) without improving target rank.

## Hard-negative geometric-support candidate count (120-source directory)

| Slice | ORB affine | SIFT affine | ORB homography | SIFT homography |
| --- | ---: | ---: | ---: | ---: |
| Repeated texture | 20 | 20 | 20 | 20 |
| Plot grids / axes | 20 | 0 | 20 | 0 |
| Text-heavy | 0 | 20 | 0 | 20 |
| Generic blot-like strips | 20 | 20 | 20 | 20 |
| Large blank background | 0 | 0 | 0 | 0 |
| Nearby microscopy-like | 0 | 2 | 0 | 2 |

These historical counts used the former `verified_match` status, now superseded by
`geometrically_supported_candidate`. They measure candidate burden for one no-known-source query
per slice. They are not detector false-positive labels and do not claim that the files are or are
not scientifically related. The hardening conjunction reduced the previous 1,000-source
absent-query candidate count substantially, but 20/120 on repeated textures, text-heavy images,
and generic blot strips would impose substantial human review burden if surfaced without ranking.

Concrete remaining geometrically supported hard-negative examples were recorded in the local
result JSON and overlays, for example:

- `hard_negative_sources/source_0000_repeated_texture.png` through the repeated-texture family;
- `hard_negative_sources/source_0001_plot_grid_axes.jpg` in the ORB plot-grid slice;
- `hard_negative_sources/source_0002_text_heavy.tif` in the SIFT text-heavy slice;
- `hard_negative_sources/source_0003_generic_blot_strip.png` in both algorithms.

The exact files are under `/private/tmp/image_finder_hardening/` and are not repository data.

## Timing

Timing is reported separately in `results.json` for discovery, file decode, descriptor extraction,
pair matching, geometric verification, and overlay rendering. Representative 1,000-source affine
runs:

| Query slice | ORB pair + geometry (ms) | SIFT pair + geometry (ms) |
| --- | ---: | ---: |
| Identity | 1,667 | 750 |
| Crop | 616 | 481 |
| Rotation | 2,901 | 786 |
| Flip | 1,575 | 575 |

Descriptor extraction dominated SIFT (approximately 6.8–8.2 seconds per 1,000-source run) while
ORB was approximately 1.2–1.5 seconds. Discovery and overlay rendering were small relative to
decode/descriptor work in this synthetic setup.

## Interpretation

- The conjunction prevents many low-count/random models, but it does not solve repeated
  structure. Spatial coverage and bidirectional residual checks can still pass on a repeated
  template.
- Full affine is preferable to unrestricted homography for this slice: it preserves flip recovery
  for SIFT and substantially reduces extra positive-side supported candidates, but it does not
  eliminate candidate burden on repetitive content.
- ORB flip recall is a concrete regression and must remain unsupported or separately handled until
  a future spike addresses it.
- NCC/phase correlation, pHash, index, embeddings, PDF, LLM, GUI, and packaging were not added.

This result blocked the original Steps 8–14. The subsequent product decision reframed the first
real-user slice as retrieval with human confirmation, not automatic verification. No thresholds
were changed after held-out inspection, and the user-trial slice does not resume threshold tuning.
