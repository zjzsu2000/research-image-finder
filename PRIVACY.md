# PRIVACY.md — Research Image Finder V0.1

Status: **binding privacy boundary for V0.1; mechanisms remain to be implemented and tested**
Last updated: 2026-08-31

## 1. Privacy claim

Research Image Finder processes query and source images that may be unpublished, patient-related,
pre-patent, sponsor-restricted, or commercially sensitive. V0.1 therefore makes one narrow,
testable promise:

> The default Strict Local process uses no model and opens zero sockets. It reads image content
> only from the query and roots the user explicitly selects, and writes derived content only to a
> user-selected index/output root.

The promise applies only after the implementation passes AC-1 and AC-2. Until then it is a design
requirement, not a verified product fact.

## 2. Strict Local is the only V0.1 mode

| Property | V0.1 behavior |
| --- | --- |
| Network/socket capability | Denied for every address family; zero attempts required |
| Reasoning/model backend | `NullBackend`; no model loaded |
| Read scope | Query file, application/dependencies, and explicit authorized roots |
| Content-bearing write scope | Explicit index/output root only |
| Telemetry and crash upload | None |
| Update/model/data lookup | None |
| Remote URLs and paper lookup | Unsupported |

There is no “helpful” fallback to a network, model server, online decoder, or remote metadata
service. Missing functionality fails visibly or is reported as unsupported.

## 3. ADR-0009 interpretation

[ADR-0009](docs/adr/0009-strict-local-capability-and-trust-boundary.md) is controlling:

- default Strict Local means zero sockets, not merely zero non-loopback egress;
- `NullBackend` and no model are the default;
- a future loopback local-model connection is a separately named and explicitly enabled
  capability;
- enabling it visibly exits the zero-socket guarantee;
- it is never auto-detected and never a fallback;
- the local model process is a separate trust boundary that may log, persist, or egress data.

Research Image Finder V0.1 has no local-model feature, so the future exception is not reachable.

## 4. Read-scope rules

The user chooses the query file and each search root. Before traversal the application displays
and records canonical paths.

V0.1 must:

- reject an empty or implicit search scope;
- avoid defaulting to the home directory or all mounted volumes;
- avoid following symlinks, aliases, junctions, or mount indirections outside selected roots;
- avoid resolving image metadata, sidecars, or embedded strings as URLs;
- avoid reading sibling files unless the supported decoder explicitly requires a disclosed sidecar
  and policy permits it;
- report inaccessible directories, skipped files, decoder errors, and scope violations;
- treat mounted network filesystems as outside the zero-egress application guarantee even if they
  appear as local paths, and warn/deny according to the supported-platform policy decided before
  implementation.

The last point requires an explicit platform decision: a network filesystem can move content over
a socket opened by the OS rather than the application process. V0.1 must not market that case as
equivalent to a physically local disk without evidence.

## 5. Write-scope rules

All content-bearing derived data stays beneath one explicit index/output root:

- index database and descriptors, if indexing is retained;
- thumbnails, normalized images, and match overlays;
- run provenance and coverage;
- logs that contain paths or file metadata;
- temporary files and interrupted-build state.

Required controls:

- restrictive default permissions;
- atomic file publication where practical;
- no hidden global cache;
- no use of general OS temporary directories for image-bearing content unless an isolated,
  audited private temp root is explicitly configured beneath the output root;
- no shelling out to tools that write undeclared caches;
- safe handling of path traversal and symlink replacement;
- a complete delete operation for the selected derived-data root, documented separately from
  deletion of original source images.

The application never deletes or modifies original query/source files in normal operation.

## 6. Data inventory

| Data | Sensitivity | V0.1 handling |
| --- | --- | --- |
| Query image | Potentially unpublished or identifying | Read locally; digest and derived evidence may be written to output root |
| Source images | Potentially raw experimental data | Read locally; not copied wholesale into the index by default |
| Paths and filenames | May reveal subjects, projects, people, or experiments | Treated as sensitive derived data |
| Thumbnails/overlays | Content-bearing derivatives | Written only to output root |
| Hashes/descriptors | Linkable derivatives, not anonymous | Written only to output root; never transmitted |
| Filesystem timestamps/metadata | Potentially sensitive project history | Minimize and record purpose |
| Coverage and logs | Can expose directory structure | Written only to output root |

Private user content, derivatives, matches, and feedback are never training data by default. See
[DATASET_POLICY.md](DATASET_POLICY.md) and ADR-0008.

## 7. Testable enforcement

### AC-1: socket enforcement

Run the end-to-end process tree under supported-platform OS controls that deny and trace sockets,
including native libraries and subprocesses. The passing result is zero attempted sockets, not
merely zero successful connections. DNS, proxy, redirect, and generated-result behavior are
included.

Python socket monkeypatches and import checks are fast defense-in-depth tests only.

### AC-2: filesystem enforcement

Run in isolated `HOME`, `TMP`, and XDG-style directories while auditing syscalls across the full
process tree. Test:

- normal query and root traversal;
- unreadable paths;
- symlinks and path traversal;
- file changes during traversal;
- decoder/native-library caches;
- subprocess behavior, if any;
- interrupted index build;
- result rendering and reveal/open actions.

The audit distinguishes executable/dependency reads from content reads and installation writes
from runtime writes.

### Reported policy result

Every run records:

- mode and socket policy;
- canonical query/read/write roots;
- external services used (empty in V0.1);
- models used (empty in V0.1);
- attempted policy violations;
- incomplete audit status, where applicable.

The application must not claim a run was verified merely because it was configured as Strict
Local; configuration and observed enforcement are different facts.

## 8. Limits of the guarantee

The application cannot enforce or promise:

- encryption at rest;
- behavior of OS backup, search indexing, antivirus, endpoint monitoring, or cloud-sync software;
- security of the user's chosen output/search directory;
- behavior of mounted network storage outside the process;
- absence of vulnerabilities in image decoders or native libraries;
- authority to use files merely because the OS grants access;
- secure erasure from SSDs, backups, or snapshots;
- future behavior of a separately enabled local model process.

These are documented limits, not reasons to weaken the properties the application can enforce.

## 9. Threat model

### In scope

- accidental network use by application code or dependencies;
- telemetry, update, remote lookup, and model-download paths;
- filesystem writes outside declared roots;
- traversal or symlink escape;
- hidden decoder/subprocess caches;
- HTML or local-viewer injection through malicious filenames/metadata;
- unintended retention of thumbnails, paths, hashes, and descriptors;
- silent scan-scope widening.

### Explicitly out of scope for V0.1

- a compromised operating system or administrator;
- physical access to an unlocked machine;
- malicious decoder exploits beyond dependency hygiene and process isolation decisions;
- full sandboxing of image parsing, unless a pre-implementation review adds it;
- multi-user authorization and audit controls;
- protecting data placed by the user in a synced or backed-up directory;
- preventing a third party from modifying an open-source fork.

## 10. No collection

Research Image Finder V0.1 collects and transmits nothing. In particular, it does not collect:

- query/source pixels, thumbnails, or overlays;
- file paths, names, timestamps, or metadata;
- descriptors, hashes, or index statistics;
- candidate results, reviewer decisions, or usage events;
- crash reports or hardware/software fingerprints.

Any future donation or evaluation workflow must be a separately specified, explicit operation with
item-level authority, consent, provenance, and withdrawal semantics. It cannot be introduced as
telemetry or enabled by default.
