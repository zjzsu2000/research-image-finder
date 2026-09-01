# PRODUCT.md — Research Image Finder

Status: **approved V0.1 product direction; design remediation in progress**
Last updated: 2026-08-31

Research Image Finder is the first, deliberately narrow MVP in the broader Research Preflight
project. This document is the current product boundary. Broader manuscript-preflight concepts are
future options, not V0.1 commitments.

## 1. Problem statement

Researchers often know that the source of a published or assembled figure panel still exists on
one of their computers, shared folders, or external drives, but no longer know its filename or
location. Recovering it means manually opening years of folders and comparing images by eye.

The V0.1 job is:

> Reduce the repeated manual work of locating and visually comparing a researcher's own source
> images when checking figure provenance.

The product is not trying to decide whether an image relationship is scientifically legitimate.
It helps the researcher find likely source files so that the researcher can inspect provenance,
metadata, experimental context, and records that are not visible in pixels.

## 2. Target users and authorization boundary

**Primary:** a researcher, PI, lab manager, or trainee trying to recover the source of a figure
panel from local research files they are authorized to access.

**Secondary:** a lab team performing self-audit or pre-submission provenance checks on its own
materials.

The V0.1 authorization model is structural:

1. the user supplies the query image;
2. the user explicitly selects one or more local search roots;
3. the operating system already grants the user access to those files.

The software cannot prove legal or institutional authority. It can avoid supplying discovery,
crawling, or profiling workflows that make unauthorized third-party investigation convenient.

## 3. Primary workflow

1. The user selects or drops a query image, such as a cropped panel from a paper or slide.
2. The user selects a local folder or mounted external drive containing authorized source files.
3. The tool inventories supported images inside that explicit scope and reports skipped or
   unreadable files.
4. Candidate generation narrows the search; deterministic geometric verification measures local
   correspondence and plausible transforms.
5. The results view shows top candidate source files with thumbnails, exact paths, matched regions,
   transform evidence, and limitations.
6. The user opens the original file and confirms or rejects the provenance relationship.

The unit of value is not “a problem found.” It is **time saved locating the correct original
file**, with enough evidence to decide what to inspect next.

## 4. Product principle: self-audit first

> **Self-audit first; investigation workflows are out of scope.**

This principle is enforced through the product surface, not only through policy text. V0.1 does
not provide:

- author-name, DOI, PubMed, ORCID, or publication-list search;
- publisher crawling or automatic paper download;
- automatic construction of a third-party author's paper corpus;
- cross-internet scanning or remote image search;
- bulk scanning of a researcher's publication history;
- author, lab, institution, or manuscript rankings;
- aggregate ratings or allegation-generating prose;
- automated contact with journals, institutions, employers, or funders.

General image-matching methods are public, and an open-source license cannot guarantee that nobody
will fork the code for another purpose. The project's responsibility is narrower and practical:
do not build the dangerous last-mile workflow or make it the default path.

## 5. Positioning and language

Research Image Finder is a **local source-image retrieval and provenance-review aid**.

It returns candidate matches. A candidate means only that the software measured visual
correspondence strong enough to make the file worth human inspection. It does not establish:

- that the candidate is the acquisition original;
- that reuse or transformation was disclosed;
- that two images belong to the same experiment;
- that any scientific use was appropriate or inappropriate;
- that the absence of a candidate proves the source is missing.

The UI and exports name observations: `candidate source`, `matched region`, `estimated transform`,
`review rank`, and `verification needed`. They do not name intent or adjudicate scientific conduct.

## 6. Privacy and local-first behavior

Strict Local is the default and only V0.1 mode. The default process uses `NullBackend`, loads no
model, and opens zero sockets. It performs no telemetry, remote lookup, update check, model
download, or crash upload.

Reads are limited to the query file and roots explicitly selected for that run or index. Writes
are limited to a selected index/output root. The tool does not silently widen scope to the home
directory, sibling directories, mounted volumes, cloud folders, or symlink targets outside the
selected roots.

The guarantee covers application behavior, not operating-system backup, indexing, antivirus,
cloud synchronization chosen by the user, disk encryption, or the behavior of unrelated software.
See [PRIVACY.md](PRIVACY.md) and
[ADR-0009](docs/adr/0009-strict-local-capability-and-trust-boundary.md).

## 7. Evidence and human determination

Deterministic matching owns every returned candidate. Cheap similarity signals may generate
candidates, but only the verification path may produce match evidence. Candidate-generator recall
is measured against an exhaustive or otherwise declared oracle before it may prune comparisons.

Observed recurrence, inset containment, same-work identity, adjacency, or likely repeated controls
may annotate, group, or lower a result's review priority. They must not erase a scientifically
reviewable match merely because a heuristic suggests legitimate reuse. Only technical
non-comparability may exclude a region. The final legitimate-reuse determination belongs to the
human reviewer. See [ADR-0010](docs/adr/0010-no-benign-inference-from-observed-patterns.md).

## 8. Exact V0.1 wedge

> **One query image, one or more explicitly selected authorized local roots, and a ranked set of
> visually verified candidate source files for human confirmation.**

V0.1 includes:

- local query-image ingest;
- bounded file discovery and decoder coverage reporting;
- a local, rebuildable index if the spikes show it is useful;
- candidate retrieval and deterministic geometric verification;
- top candidate thumbnails, paths, matched regions, and open-file action;
- a minimal local result artifact with run provenance and coverage;
- zero-socket privacy verification.

V0.1 excludes:

- manuscript PDF extraction and automatic panel segmentation;
- within-manuscript duplicate scanning;
- prior-paper or publication-history corpora;
- numeric, statistical, citation, and reference checks;
- LLMs, embeddings requiring model weights, and custom model training;
- persistent report triage and institutional workflow;
- network-enabled modes.

These exclusions are scope choices, not judgments that the broader ideas have no value.

## 9. Why the broader Research Preflight is paused

The previous design combined figure extraction, panel segmentation, within-document matching,
paper-corpus search, numeric and reference checks, report triage, optional local models, and
packaging. Each capability introduced a separate technical or safety gate before the product had
validated its smallest real user job.

The narrower Image Finder removes several open research problems from the first MVP:

- the user supplies the query, so PDF figure extraction is not a dependency;
- the user selects the source directory, so literature crawling and author discovery are absent;
- the output is retrieval evidence, so the product need not classify scientific legitimacy;
- no LLM is needed;
- a real end-to-end success is directly observable: the user finds the source file.

That is enough evidence to justify pausing the larger platform while the smaller workflow is
tested with researchers.

## 10. Evidence-led expansion path

Expansion happens only after actual use establishes the next job:

1. **Image Finder:** locate one source image from one query.
2. **Figure provenance:** locate sources for several user-selected panels.
3. **Manuscript self-check:** extract panels from the user's own manuscript and assist provenance
   review.
4. **Research Preflight:** consider additional self-audit checks only after separate safety and
   validity gates.

No stage implies author profiling, third-party publication crawling, or automated adjudication.
The former private “lab history” concept, if reconsidered, must be phrased and implemented as
**papers or folders the user is authorized to review**, never as “enter a researcher name and
crawl their history.”

## 11. Open-source boundary

The intended open-source primitive is local, folder-scoped image retrieval with inspectable
matching and privacy behavior. The project does not plan to package:

- mass literature acquisition;
- public-person or author profiling;
- cross-paper accusation workflows;
- “most concerning” leaderboards;
- automatically generated institutional reports.

License language may reinforce intended use but is not treated as a technical control. Default
workflow, accepted inputs, outputs, documentation, examples, and integration surface must all
support the self-audit boundary.

## 12. Success and discovery questions

The first success criterion is qualitative and concrete: a researcher uses a real query against
an authorized local directory and finds the source file faster than manual browsing, with evidence
they understand and trust.

Questions to answer before expanding scope:

1. What kinds of query images are used: clean exports, screenshots, cropped paper panels, or
   compressed slide images?
2. What file types and directory sizes occur on real lab drives?
3. How often is the desired source a raw acquisition format rather than PNG/JPEG/TIFF?
4. How many candidates will a researcher inspect before abandoning the search?
5. Is a file path and thumbnail enough, or is metadata/time/folder context essential?
6. Does the user need one-off scanning, a reusable index, or both?
7. Does the next real need involve several explicitly selected panels, and if so how are they
   supplied?
8. Which unsupported or unreadable-file cases most often hide the desired source?

Answers should change the next scope decision. They are not invitations to build the broader
platform in advance.
