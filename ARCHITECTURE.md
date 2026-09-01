# ARCHITECTURE.md — Research Image Finder V0.1

Status: **provisional architecture for empirical spikes; no production implementation approved**
Last updated: 2026-08-31

The previous document described a full Research Preflight pipeline. That broader architecture is
paused. V0.1 implements only the folder-scoped source-image retrieval contract in [MVP.md](MVP.md).
Historical ADRs remain records of their decisions; they do not silently expand current scope.

## 1. Pipeline

```text
query file ──► QueryLoader ──► normalized query
                                   │
authorized roots ─► ScopeResolver ├──► FileDiscovery ─► Decoder ─► source records
                                   │                              │
                                   └──────── PolicyGate ◄─────────┘
                                                                  │
                             optional local IndexStore ◄──────────┤
                                                                  ▼
CandidateGenerator ─► candidate pairs ─► GeometricVerifier ─► ResultRanker
                                                                  │
                                                                  ▼
                                         evidence assets + coverage + provenance
                                                                  │
                                                                  ▼
                                                   local ResultsView / open file
```

There is no manuscript parser, panel segmenter, numeric/reference detector, paper crawler,
reasoning model, report-triage database, or remote service in the V0.1 path.

## 2. Module boundaries

| Module | Owns | Must not own |
| --- | --- | --- |
| `policy` | Authorized read roots, output/index root, zero-socket mode, path decisions | Image similarity or ranking |
| `query` | Query bytes, digest, decode and normalization metadata | Search-scope discovery |
| `discovery` | Bounded traversal, symlink handling, file inventory, coverage | Match inference |
| `decode` | Supported image decoding and normalized pixels | Silent file exclusion |
| `index` | Rebuildable source records and deterministic staleness | Evidence or scientific conclusions |
| `candidates` | High-recall pair proposal | Evidence-producing final match decision |
| `verify` | Correspondence, constrained transform, matched regions, failure reasons | Scientific legitimacy |
| `rank` | Stable ordering and grouping of verified candidates | Person/document rating |
| `evidence` | Thumbnails, context views, overlays, provenance | Reviewer adjudication |
| `ui` | Scope confirmation, progress, results, reveal/open action | Crawling or automatic reporting |

Dependencies flow downward through typed records. `ui` does not bypass `policy`; `rank` cannot
invent measurements; `candidates` cannot emit a final result without `verify`.

## 3. Deterministic evidence ownership

V0.1 has one evidence-producing path: deterministic geometric verification.

Candidate generators may include perceptual hashes, coarse image statistics, metadata hints, or
other cheap deterministic signals. They are allowed to order or prune only when their recall is
measured against a declared oracle. A pHash threshold is not a proof of correspondence and must
not own a returned match.

The initial verifier hypothesis is:

1. detect ORB or SIFT keypoints/descriptors;
2. match with ratio and mutual-consistency checks;
3. estimate similarity/affine transforms before considering more flexible models;
4. require minimum inliers, inlier ratio, bidirectional consistency, and spatial coverage;
5. record the transformed region and diagnostics;
6. route insufficient-feature cases to an explicit low-texture result, not a fabricated match.

NCC/phase correlation is an empirical fallback candidate, not a settled design. Low-texture
blots, repetitive microscopy, plots dominated by axes/text, screenshots, compression artifacts,
insets, and composited images are expected breakpoints and must be represented in S2.

## 4. No automatic legitimate-reuse inference

Per [ADR-0010](docs/adr/0010-no-benign-inference-from-observed-patterns.md):

- technical non-comparability may exclude a region, with a recorded reason;
- recurrence, containment, same-work identity, adjacency, serial imaging, and likely controls may
  annotate, group, or demote a candidate;
- those heuristics must not erase a technically reviewable observation;
- the software does not decide whether reuse is scientifically legitimate.

In Image Finder, this boundary is simpler than in the deferred preflight: results answer “which
files are visually plausible sources?” The user answers “what is their provenance and is this the
right original?”

## 5. PolicyGate and filesystem capability

`PolicyGate` is the single application authority for path and network capability decisions. It is
constructed before query or directory access and passed explicitly to modules that perform I/O.

Conceptual policy:

```text
mode                 = STRICT_LOCAL
reasoning_backend    = NULL
socket_capability    = DENY_ALL
query_path           = one explicit file
read_roots           = canonical user-selected directories
write_root           = one canonical user-selected index/output directory
follow_external_link = false
```

Required behavior:

- canonicalize and record roots before traversal;
- reject or skip symlink targets outside roots;
- resist path traversal, case-folding surprises, and time-of-check/time-of-use changes where the
  supported platform permits;
- never interpret embedded image metadata as a path or URL to fetch;
- give decoders byte streams from policy-approved files rather than unrestricted filenames when
  practical;
- use restrictive permissions for derived content;
- keep temporary files inside the selected output root or an explicitly audited private temp root.

Application checks are defense in depth. AC-2 is established by syscall-level testing of the full
process tree, not by assuming every dependency honors `PolicyGate`.

## 6. Zero-socket Strict Local

The default and only V0.1 configuration uses `NullBackend`, loads no model, and opens zero sockets
of every family. Network clients and model integrations are not V0.1 dependencies.

AC-1 runs the complete process tree under OS-enforced denial and tracing. Python monkeypatches and
import checks may provide fast feedback but are not the privacy guarantee.

[ADR-0009](docs/adr/0009-strict-local-capability-and-trust-boundary.md) also defines a possible
future **Local Model IPC** capability. If enabled in a later version, it is explicit, never a
fallback, visibly exits the zero-socket claim, and treats the model process as a separate trust
boundary. Image Finder V0.1 has no use for or path to that capability.

## 7. Source records and optional index

The source image itself remains the authority. Any index is disposable and rebuildable.

A source record minimally needs:

- canonical path relative to an authorized root plus a root identifier;
- content digest and stable filesystem identity where available;
- size and modification metadata used only for staleness detection;
- decoder and normalization version;
- dimensions/channels and coverage status;
- deterministic retrieval descriptors needed by the selected candidate path.

SQLite plus ordinary descriptor files is an acceptable baseline, but the physical layout is not
locked before S1/S2. The earlier ADR-0006 paper-corpus sizing does not establish that a reusable
index is necessary for this different folder-retrieval workload.

An index, if retained, must support atomic publication, interrupted-build recovery, corruption
detection, deterministic rebuild, file add/change/move/delete handling, and explicit version
incompatibility. It must not copy original image bytes by default merely for convenience.

## 8. Candidate and result identity

Identity rules are pre-implementation work. At minimum, result identity must derive from:

- query content digest;
- source content digest, not only path;
- verifier family/version and canonical effective parameters;
- canonicalized matched-region/transform representation.

Path is mutable metadata and must not be the only identity. A longer digest than the deferred
schema's short display identifier is required for interchange; a separate shortened display ID may
be used in the UI.

V0.1 does not reuse the broader `Finding` schema by pretending a retrieval candidate is an
integrity finding. A small candidate-result contract must be resolved before implementation, but
schema files are deliberately not changed in this design pass.

## 9. Result semantics and rendering

A result contains measured retrieval evidence, not a scientific conclusion. Required rendering:

- full query and source context;
- marked query/source matched regions;
- exact local source path and reveal/open action;
- deterministic measurements and transform summary;
- decoder/coverage limitations;
- a statement that visual correspondence does not establish acquisition provenance or scientific
  legitimacy.

All file names, paths, metadata, and image-derived text are untrusted rendering input. The minimal
viewer should prefer no JavaScript; if active content is later used, it requires strict escaping,
CSP, no external resources, and browser-level tests.

## 10. Deferred architecture

The following repository concepts are explicitly paused and must not be implemented under the
Image Finder V0.1 milestone:

- PDF ingest, figure extraction, panel segmentation, and within-manuscript checking;
- prior-paper corpus comparison and paper metadata lookup;
- numeric/reference detectors;
- optional narration or candidate-extraction models;
- persistent triage and institutional report workflow;
- network-enabled privacy modes;
- future model training.

If user evidence supports expansion, the design proceeds in the order in [PRODUCT.md §10](PRODUCT.md):
single-image retrieval → multi-panel provenance → manuscript self-check → broader preflight.
