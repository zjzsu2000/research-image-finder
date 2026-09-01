# Research Image Finder

The first open-source MVP in the Research Preflight project.

Research Image Finder is a **local-first tool for researchers to locate likely source images in
their own authorized research files**. Give it a query image or figure panel, select a local
folder or external drive, and review the most likely source files with thumbnails, paths, and
matched-region evidence.

> Self-audit first · Folder-scoped · Zero sockets by default · Human confirmation required

## Current status

**Design baseline plus disposable implementation spike.** No production implementation has been
reviewed or accepted. The current spike remains under `spikes/image_finder_v01/`; its Windows GUI
is a prototype awaiting a real-Windows smoke test, not a validated Windows release. The repository
also retains broader Research Preflight design artifacts and schemas as future design material;
they are **not** the current V0.1 contract unless [MVP.md](MVP.md) says otherwise.

## V0.1 workflow

```text
query image or cropped panel
        ↓
user selects authorized local folder / drive
        ↓
local discovery and candidate retrieval
        ↓
deterministic affine geometric support
        ↓
top candidate files + paths + matched regions
        ↓
researcher confirms the source
```

The job is deliberately narrow: reduce the time researchers spend manually browsing old drives,
folders, and image files when tracing figure provenance.

## Product boundary

Research Image Finder is designed for research self-audit and provenance recovery. It does not:

- accept an author name, DOI, PubMed query, or publication list as an input;
- crawl publisher sites or download third-party papers;
- build a third-party author's publication corpus;
- mass-scan a researcher's publication history;
- rank researchers, manuscripts, or labs;
- produce accusation text, document-level ratings, or conclusions about legitimate reuse;
- make misconduct determinations;
- decide whether a match is appropriate in its scientific context.

Open source cannot make misuse impossible. The product constraint is therefore to avoid
productizing the dangerous last mile: the project may expose a local image-matching primitive,
but it will not provide an investigator workflow around it.

## Privacy promise

The default and only V0.1 mode is **Strict Local**:

- the default process uses `NullBackend`, loads no model, and opens zero sockets;
- no telemetry, crash reporting, auto-update, remote lookup, or model download;
- reads are limited to the query and user-selected search roots;
- content-bearing writes are limited to a user-selected index/output root;
- skipped, unreadable, and out-of-scope files are reported rather than silently ignored.

A future loopback model server would be a separately disclosed capability that exits the
zero-socket guarantee and creates a separate trust boundary. It is not part of this MVP. See
[ADR-0009](docs/adr/0009-strict-local-capability-and-trust-boundary.md) and
[PRIVACY.md](PRIVACY.md).

## Evidence, not adjudication

A returned item is a **candidate source file**, not a claim that two scientific images were used
properly or improperly. Ranking is a retrieval aid. The user makes the final provenance and
legitimate-reuse determination from the original files and experimental context. If no candidate
is returned, that does not prove the source is absent.

Observed recurrence, inset containment, or same-work identity must not make a technically valid
match disappear. Technical non-comparability may exclude a region; otherwise the system may
annotate, group, or demote candidates while preserving the evidence. See
[ADR-0010](docs/adr/0010-no-benign-inference-from-observed-patterns.md).

## Documentation

| Document | Purpose |
| --- | --- |
| [PRODUCT.md](PRODUCT.md) | Current product boundary, users, workflow, and abuse constraints |
| [MVP.md](MVP.md) | Binding Research Image Finder V0.1 scope and AC-1…AC-14 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Local retrieval pipeline and enforcement boundaries |
| [PRIVACY.md](PRIVACY.md) | Testable zero-socket and filesystem guarantees |
| [EVALUATION.md](EVALUATION.md) | V0.1 datasets, spikes, metrics, and uncertainty rules |
| [ROADMAP.md](ROADMAP.md) | Pre-implementation sequence and stop/review gates |
| [DATASET_POLICY.md](DATASET_POLICY.md) | Separation of user, evaluation, fixture, and future training data |
| [FINDING_SCHEMA.md](FINDING_SCHEMA.md) | Deferred broader Preflight finding contract; not the Image Finder V0.1 result contract |
| [docs/adr/](docs/adr/) | Accepted historical and current architecture decisions |
| [docs/reviews/](docs/reviews/) | Non-binding independent reviews and resolution records |
| [TRIAL_WINDOWS.md](TRIAL_WINDOWS.md) | Minimal unsigned Windows artifact instructions and validation caveat |

## Validation

```bash
python3 tools/validate_docs.py
```

## License

Research Image Finder is licensed under the [Apache License 2.0](LICENSE). The license contains no
field-of-use restriction. Licensing cannot substitute for safe product scope; capability and
default workflow carry the primary abuse-resistance burden. Data licensing and provenance are
governed separately by [DATASET_POLICY.md](DATASET_POLICY.md).
