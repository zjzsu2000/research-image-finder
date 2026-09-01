# Disposable Image Finder V0.1 spike

This directory contains disposable spike and first-user-trial code. It is not production code and
is not the Research Preflight Findings pipeline. Research Image Finder is treated as a retrieval
aid: machine output is a ranked candidate with optional geometric support, and only a human may
confirm a source.

Run tests with:

```bash
../../.spike-venv/bin/python -m unittest discover -s spikes/image_finder_v01/tests
```

Run the deterministic synthetic benchmark (results go to `/private/tmp` by default):

```bash
.spike-venv/bin/python spikes/image_finder_v01/run_benchmark.py
```

The benchmark is intentionally exhaustive: no pHash, prefilter, index, NCC, phase correlation,
embedding, model, PDF, or network path is present. It generates only PNG/JPEG/single-page 8-bit
grayscale/RGB/RGBA TIFF files. Unsupported TIFF variants are explicit decode errors.

Run the frozen SIFT/affine user-trial prototype with:

```bash
.spike-venv/bin/python spikes/image_finder_v01/run_trial.py QUERY_IMAGE SELECTED_DIRECTORY
```

It produces Top-10 candidates in a self-contained report under `/private/tmp` by default. Use
`--top-n 20` for Top-20 or `--output /an/outside-repository/directory` to select another local
destination. The command refuses output inside the repository. It creates no index and no
per-file JSON. The report contains sensitive local paths and embedded thumbnails/overlays; it is
the user's local material and should be deleted after the trial if no longer needed.

The report's optional trial form creates a local aggregate JSON download only when the reviewer
presses the download button. It excludes paths and images. Neither the report nor that record may
be committed.

## Windows trial UI

On a prepared Windows machine, double-click `start_windows_gui.bat`. The window lets the user pick
one query image and one folder or drive, start a recursive search, inspect Top-10/Top-20 results,
open a candidate's containing folder in Explorer, and make an optional human confirmation entry.
No HTML or trial record is saved unless the user explicitly clicks a save button.

The prepared environment needs Python 3 with Tkinter plus the packages in
`requirements-windows.txt`. This slice is source-only and does not include an installer or `.exe`.
Dependency installation is setup work and is not performed by the Strict Local retrieval runtime.

The GitHub Actions workflow builds an unsigned `ResearchImageFinder.exe` with PyInstaller after
unit, documentation, Windows-path, non-interactive GUI-module, and frozen-bundle smoke checks pass.
The uploaded artifact is named `ResearchImageFinder-windows-x64`. CI validates the Windows build
path only; actual interactive Windows user validation remains outstanding.

Run the small generated microscopy-oriented slice with:

```bash
.spike-venv/bin/python spikes/image_finder_v01/run_microscopy_trial_slice.py
```

Its brightfield-like and immunofluorescence-like images are synthetic visual fixtures. Recovery on
that slice does not establish performance on a researcher's real microscopy or raw files.

`CONTRACT.md`, `HARDENING_CONTRACT.md`, and `USER_TRIAL_CONTRACT.md` freeze the applicable
parameters and interpretations. Benchmark JSON and overlays are local diagnostics; they must not
be committed when they contain local paths.
