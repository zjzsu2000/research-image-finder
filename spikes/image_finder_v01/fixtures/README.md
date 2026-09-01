# Fixture policy

The benchmark generates synthetic PNG, JPEG, and single-page 8-bit TIFF fixtures at run time.
This keeps the repository small and makes lineage/transform ground truth deterministic. The
fixture manifest is `../manifests/fixture_manifest.json`.

`run_microscopy_trial_slice.py` also generates two small synthetic, microscopy-like slices at run
time: brightfield-like texture and immunofluorescence-like texture. They are deliberately labeled
synthetic visual fixtures, not biological data and not evidence of field performance. Their bytes
are created in a temporary directory and deleted after the run.

Real query/source pairs must remain on the authorized researcher's machine unless separately
licensed and donated. Do not commit paths, thumbnails, source images, or derived descriptors.
