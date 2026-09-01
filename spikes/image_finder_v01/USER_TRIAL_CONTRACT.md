# Research Image Finder V0.1 — disposable user-trial contract

Status: frozen for the first real-user retrieval trial; not a production interface.

## Product interpretation

Research Image Finder is a retrieval aid. Machine output is a ranked candidate with optional
geometric support, never a provenance conclusion. `confirmed source` is a human decision only.
A candidate that passes the preregistered geometric conjunction is called a
`geometrically_supported_candidate`; it is not called verified or confirmed. A run with no useful
candidate does not establish that a source is absent.

## Frozen trial baseline

- One query image and one explicitly selected local directory.
- SIFT descriptors, exhaustive pair matching, and affine geometric support.
- Top-10 by default, with Top-20 as the only alternative.
- No homography default, prefilter, index, NCC/phase correlation, embeddings, PDF, model, LLM,
  cloud path, or socket.
- The hardening thresholds in `HARDENING_CONTRACT.md` are reused unchanged. This slice does not
  tune thresholds.

## Output and handling

The command-line trial writes one self-contained local HTML report outside the repository. The
Windows UI keeps results in memory and writes the same report only after the user chooses to save
it. The report contains full local source paths and embedded thumbnails/overlays, so it is
sensitive local trial material. It has no external assets or submission path. Both runners refuse
report output inside the repository and do not persist an index or per-file result JSON.

The reviewer may explicitly download one aggregate trial record from the report. It contains only:

- directory image count;
- total runtime;
- correct source rank, if known;
- candidates inspected before confirmation;
- time to confirmation;
- human outcome: confirmed, not found, or unsure.

The downloaded record excludes image bytes, thumbnails, local paths, and per-candidate diagnostics.
It is not committed by this spike.

## Windows trial shell

The first Windows shell uses Python's built-in Tkinter. Search runs on a worker thread so the
window remains responsive; the same zero-socket retrieval operation and selected-root scanner are
used. Results and optional human outcome remain in memory unless the user explicitly saves a local
HTML report or aggregate, path-free JSON record. Opening a result uses Windows Explorer only after
rechecking that the candidate is within the selected root.

Synthetic brightfield-like and immunofluorescence-like fixtures provide a trial-oriented smoke
test. They do not validate field performance, low-texture recovery, or provenance correctness on
real microscopy data.
