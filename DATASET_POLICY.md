# DATASET_POLICY.md — Research Image Finder and future Research Preflight

Status: **binding policy, v0.1**
Last updated: 2026-08-31

This document defines what data may and may not be used for **evaluation, benchmarking, model
development, and future specialized-model training** in Research Image Finder and any later
Research Preflight work. V0.1 is folder-scoped source-image retrieval; manuscript-specific policy
below remains binding for any future expansion and does not place manuscript scanning in scope.

It exists to prevent a specific, tempting, and wrong shortcut:

> Retraction Watch → download the retracted paper → treat every figure and panel in it as "bad" →
> train a classifier.

That pipeline is **methodologically invalid**, and it additionally creates legal, scientific, and
reputational risk. A model trained that way does not learn to detect image duplication. It learns
to predict *which papers attract controversy* — a correlate of journal, field, era, figure count,
and image quality — and it will fail in exactly the situations that matter.

This policy is binding on humans and on coding agents working in this repository.

---

## 1. Retraction is not ground truth

**A retracted paper is a candidate source for investigation. Nothing more.**

Do not infer:

- ❌ retracted paper ⇒ all figures are problematic
- ❌ panel from a retracted paper ⇒ positive training example
- ❌ corrected paper ⇒ the correction concerned images

A retraction may concern any of: authorship disputes, plagiarised text, missing or invalid ethics
approval, consent problems, duplicate publication, statistical or analytical errors, data
availability failures, honest error found by the authors themselves, publisher error, one specific
figure, one specific panel, or issues with no relationship whatsoever to image integrity.

**Labels must be assigned at the narrowest defensible level:**

```
paper → figure → panel → region → finding type
```

If a retraction notice says "Figure 4b was duplicated from Figure 2a," then the label attaches to
**that region pair and that finding type** — not to Figure 4, not to the paper, and not to the
other eleven panels that were never questioned.

If the notice does not localize the problem, the item is `candidate_only` (§2) and cannot be used
as positive supervision.

---

## 2. Public allegation is not confirmed ground truth

PubPeer comments, preprint commentary, social-media threads, blog posts, and third-party reports
are legitimate and valuable for **candidate discovery**. They are not labels. Commenters are often
right and sometimes wrong, and the record rarely distinguishes the two.

### Label support and domain realism are separate *(canonical)*

The former A–F “confidence hierarchy” mixed two different questions:

1. **How strongly is this particular label supported?**
2. **How closely does this item resemble the deployment distribution?**

Synthetic transformations have exact labels but limited field realism. Expert-reviewed real pairs
may have less certain labels but much higher deployment relevance. Treating either dimension as a
single ordinal ranking produces misleading dataset summaries, so every item records both.

**Label-support class:**

| Code | Name | Definition | Permitted use |
| --- | --- | --- | --- |
| **A** | `synthetic_ground_truth` | An exact, known transformation generated from legitimately usable source material. Ground truth by construction for that transform. | Training, evaluation, thresholds, regression tests; never presented alone as field performance |
| **B** | `confirmed_issue` | A localized figure/panel/region relationship explicitly documented by an authoritative source or author acknowledgement. | Training, evaluation |
| **C** | `expert_reviewed` | A specific finding labeled by a qualified domain expert with sufficient evidence. | Training, evaluation, with reviewer agreement recorded where applicable |
| **D** | `weak_label` | A plausible issue supported by public discussion or indirect evidence, not independently confirmed. | Analysis and targeted evaluation slices; never silently mixed into high-support supervision |
| **E** | `candidate_only` | Material identified for manual review; carries no correctness assertion. | Discovery and triage only; never supervised training data, positive or negative |
| **F** | `no_known_issue_control` | Material selected for false-alarm estimation, with its construction and review limits recorded. This is not a confirmed negative label. | Evaluation and false-alarm estimation; training only under an explicit noisy-negative design |

The letter is a stable class code, **not an ordinal claim that A is globally “better” than B or C**.

**Domain-realism class:**

| Name | Meaning |
| --- | --- |
| `synthetic_transform` | Generated manipulation with exact geometry; limited real-world preparation artifacts |
| `public_real_localized` | Real published, localized relationship with lawful source access |
| `public_real_control` | Real published no-known-issue control; findings reviewed but negatives not proven |
| `donated_published` | Real already-published material donated with authority and consent provenance |
| `donated_unpublished` | Real unpublished material under a written agreement; highest sensitivity |

**Mixing rule:** `weak_label` and `candidate_only` data must never be silently mixed into
high-support supervised training. Using class D material in training requires an explicit,
documented experimental design that states the noise assumption, keeps the weak-labeled subset
separately identifiable, and reports results with and without it. Class E is never training data.
Class F is not a clean negative and must remain identifiable in every analysis.

Every **evaluation or training** item records both `label_support_class` and `domain_realism`.
Product test fixtures use fixture-specific metadata and are not promoted into evaluation or
training merely by adding these fields. An evaluation/training dataset whose items do not record
both is ineligible.

---

## 3. Private unpublished user data is not training data

**Strict-local query images, source folders, source images, paths, indexes, descriptors,
intermediate artifacts, candidate results, and any user confirmations are NOT training data. By
default and by construction.** The same rule applies to future manuscripts, extracted figures and
panels, lab corpora, findings, and triage decisions.

- No silent collection.
- No telemetry-based harvesting.
- No background upload.
- No "help us improve the model" default-on setting.
- No “anonymized” derivative of user files collected without explicit consent — descriptors,
  hashes, crops, thumbnails, paths, and indexes are derived from user material and remain user
  data.

User material may enter a future dataset **only** through explicit, informed opt-in that states:
what specific items are shared, for what purpose, with what retention, whether the items may be
redistributed, and how consent can be withdrawn. Consent is per-item or per-corpus, revocable,
and recorded alongside the data.

**Consent from the operator is necessary but not automatically sufficient.** A PI may not have
unilateral authority to donate a trainee's, coauthor's, patient's, sponsor's, institution's, or
publisher's material. A future donation workflow must record the donor's authority, relevant IP
and publication rights, sponsor/IRB or data-use restrictions, and any required coauthor or data-
subject approvals. If authority cannot be established, the material is ineligible regardless of
technical de-identification.

“Revocable” must be stated precisely. Raw and derived dataset items can be deleted from future
training runs after withdrawal. A model already trained or released may not be practically
untrained; the consent record must state the withdrawal cutoff, whether retraining is required,
and what happens to already distributed model artifacts. Do not promise retroactive erasure that
the model-development process cannot demonstrate.

**Preference order for future data collection**, most to least preferred:

1. Openly licensed public corpora (§5, §8)
2. Synthetic ground truth we construct (§5)
3. Donated **already-published** figures, with license provenance
4. Donated **structured findings and triage dispositions** without image bytes — potentially high
   value for review ranking/grouping, with less exposure than raw imagery
5. Donated unpublished material — only under a written design-partner agreement, and only when
   nothing above suffices

**Privacy-by-default is a product invariant even though it slows the model-training flywheel.**
We accept that we will learn less, more slowly, than a vendor that harvests. See
[PRODUCT.md §§6 and 11](PRODUCT.md), [PRIVACY.md](PRIVACY.md), and
[ADR-0008](docs/adr/0008-private-user-data-is-not-training-data.md).

---

## 4. Four kinds of datasets — never interchangeable

These are distinct concepts with distinct rules. Do not treat one as another.

| Kind | Purpose | Lives in | Committed to repo? | Notes |
| --- | --- | --- | --- | --- |
| **Product test fixtures** | Deterministic unit/integration tests | `tests/fixtures/` | **Yes** — must be small and openly licensed | Chosen for *code path coverage*, not statistical representativeness |
| **Evaluation / benchmark** | Measuring detector quality against acceptance criteria | `eval/corpora/` (manifests + fetch scripts) | **Manifests only** — not the bytes | Chosen for representativeness; must never be tuned against to the point of overfitting |
| **Model-training data** | Future supervised training | Outside the repo, versioned separately | **No** | Requires §12 gate approval before it exists |
| **User production data** | A user's query images, authorized source folders, index, and results; future manuscript/corpus data | The user's machine only | **Never** | Not ours; see §3 |

Three rules that follow, each of which has been violated by many projects:

1. **Acceptable for testing ≠ acceptable for training.** A fixture chosen because it exercises a
   parser branch tells you nothing about real-world distribution.
2. **Public ≠ redistributable.** Freely readable on a publisher's website says nothing about the
   right to copy it into a repository. See §8.
3. **Usable locally ≠ safe to commit.** A researcher may lawfully hold a PDF that they may not
   republish. Local use and redistribution are separate permissions.

A fourth rule specific to evaluation: **the evaluation corpus must not become the training
corpus.** If evaluation material is ever used for training, a fresh held-out evaluation set must
be constructed, and the change documented.

---

## 5. Prefer synthetic ground truth early

For image matching and source retrieval, V0.1 and early research **strongly prefer synthetic
transformation benchmarks**. This is not a compromise — for measuring a geometric matcher, it is
the *better* instrument, because the ground truth is exact and the transform parameters are known.

Take an openly licensed scientific panel and generate controlled variants:

- crop (parameterized by retained area fraction)
- horizontal flip · vertical flip
- rotation (small, and 90° multiples)
- scale (up and down)
- JPEG compression at varying quality
- brightness change · contrast change
- partial-region reuse (a sub-region pasted into an unrelated panel)
- combinations of the above, in a recorded order

Record exact ground truth for every generated item:

```jsonc
{
  "synthetic_item_id": "syn_00412",
  "source_image_id": "pmc_oa_PMC1234567_fig3_p2",
  "source_license": "CC-BY-4.0",
  "transformation_sequence": ["crop", "horizontal_flip", "jpeg"],
  "transform_params": { "crop": { "retained_area": 0.62, "origin": [0.14, 0.08] },
                        "horizontal_flip": {}, "jpeg": { "quality": 72 } },
  "known_overlap_region_source": [140, 360, 300, 470],
  "known_overlap_region_target": [ 12,  40, 172, 150],
  "expected_relationship": "region_duplicate",
  "expected_detectable": true
}
```

This gives cleaner labels than "this paper was retracted," it scales without legal exposure, and
it produces the precision/recall curves that AC-5 needs. It is also the only way to measure
*graceful degradation* — the point at which crop aggressiveness or JPEG quality defeats the matcher.

**Known limitation, stated up front:** synthetic transforms have a domain gap from real-world
figure reuse. Real reuse involves re-screenshotting, re-compositing, resampling through
presentation software, contrast adjustment during figure prep, and physical differences between
two genuinely distinct images of the same sample. Synthetic benchmarks establish a *ceiling*, not
a field performance estimate. Level B and C data (§2) is what closes that gap, and there will not
be much of it early.

---

## 6. Future expert-feedback dataset

This is a **future Research Preflight** human-review label proposal. Image Finder V0.1 does not
persist adjudication or collect reviewer labels. The existing `triage.status` and `triage.reason`
in [FINDING_SCHEMA.md](FINDING_SCHEMA.md) are deferred design artifacts, not an Image Finder data
collection surface.

### Top-level labels
`real_issue` · `legitimate_reuse` · `false_positive` · `unsure`

`real_issue` means **a real technical issue that requires action before submission** — a wrong
file inserted during figure assembly is a real issue, and it is not misconduct.

### Reason labels
`same_control` · `same_experiment` · `inset_or_magnification` · `adjacent_or_serial_image` ·
`disclosed_reuse` · `preprint_to_publication` · `accidental_duplication` · `wrong_file_inserted` ·
`possible_manipulation` · `extraction_error` · `segmentation_error` · `detector_error` ·
`insufficient_evidence` · `other`

Note the deliberate distribution: **eight of these describe benign or tooling-caused outcomes.**
That reflects the real base rate, and a labeling vocabulary that did not would bias every
downstream model toward suspicion.

### Vocabulary prohibition

**Do not make `fraud` or `misconduct` a routine classifier label.** The tool observes technical
relationships between images and numbers. Intent is not observable from a figure, and a label set
containing "fraud" invites a model that predicts it — which is precisely the product we have
committed not to build ([PRODUCT.md §§4–5](PRODUCT.md),
[ADR-0003](docs/adr/0003-observation-named-finding-types.md)).

`possible_manipulation` is the strongest permitted label, it is hedged deliberately, and it is a
statement about the image, not the author.

### Highest-value future model

The most valuable future classifier is a **review-ranking and grouping aid** learned from
`legitimate_reuse` dispositions and their reason labels — for example, a model that recognizes the
recurrence pattern typical of a loading control and presents the related pairs as one calm review
group. It improves review efficiency and presentation precision, which govern adoption
([MVP.md §5](MVP.md)), and it can only be built from honest human triage.

It must not silently suppress an observed relationship. A learned assertion of benignity has the
same scientific-validity problem as a hand-written suppression rule; the relationship remains in
the evidence set and the model may only propose grouping or ordering subject to deterministic
constraints ([ADR-0010](docs/adr/0010-no-benign-inference-from-observed-patterns.md)).

---

## 7. Provenance requirements

Every dataset item records, where applicable:

```jsonc
{
  "dataset_item_id": "…",
  "source_type": "pmc_oa | publisher | benchmark | synthetic | donated | local_corpus",
  "source_identifier": { "doi": null, "pmid": null, "pmcid": null, "url": null, "local_id": null },
  "license": "CC-BY-4.0 | CC0 | proprietary | unknown",
  "copyright_status": "…",
  "redistributable": "yes | no | unknown",
  "image_bytes_redistributable": "yes | no | unknown",
  "derived_features_only": false,          // true = we keep hashes/descriptors, not pixels
  "paper_level_status": "no_known_issue | corrected | retracted | expression_of_concern | unknown",
  "figure_label": "Figure 3",
  "panel_label": "B",
  "region": [140, 360, 300, 470],
  "label": "region_duplicate | no_issue | …",
  "label_support_class": "A | B | C | D | E | F",  // §2 support class, not an ordinal rank
  "domain_realism": "synthetic_transform | public_real_localized | public_real_control | donated_published | donated_unpublished",
  "label_source": "retraction_notice_url | reviewer_id | synthetic_generator | …",
  "reviewer_identity_or_class": "domain_expert_imaging | tool_author | anonymous_partner",
  "review_date": "2026-08-30",
  "supporting_evidence_reference": "…",
  "transformation_metadata": null,          // required for synthetic items (§5)
  "consent_record": null,                   // required for donated items (§3)
  "authority_record": null,                 // required for donated items (§3)
  "split_group_key": "…"                    // §10
}
```

An evaluation or training item missing `license`, `label_support_class`, `domain_realism`, or
`split_group_key` is not eligible for use. Donated items additionally require both
`consent_record` and `authority_record`.

---

## 8. Licensing and redistribution

**Publicly accessible does not mean freely redistributable.**

Before storing or distributing any source figure:

- verify the license of the *specific article* — note that PMC Open Access is not uniformly
  licensed, and per-article terms vary (CC-BY, CC-BY-NC, and more restrictive);
- prefer PMC Open Access and other clearly licensed sources;
- retain license metadata with the item, permanently;
- **do not bundle publisher PDFs or figures into this repository** unless redistribution is
  clearly permitted, and record the basis for that conclusion.

Where redistribution is not permitted, store instead:

- metadata and identifiers (DOI/PMCID/figure label),
- content hashes,
- derived features (descriptors, embeddings, perceptual hashes),
- **scripts that reproduce the dataset from lawful sources** on a user's own machine.

This is the approach SciSp-C takes for exactly this reason, and it is the right pattern: the
benchmark travels as a recipe, not as a copy.

**Do not ship a crawler for publisher content in V0.1.** Fetch scripts used by maintainers to
reproduce an openly licensed evaluation benchmark are acceptable; they are not a product feature
and must not become a general-purpose scraper, author-search surface, or third-party corpus
builder.

Note also that the *code* license and the *data* license are separate questions. Evaluation
manifests may be committed under the repository license; the material they point to is governed
by its own terms.

---

## 9. Caution on positive and negative labels

**A "clean" published paper is not proven clean.** It is a paper against which no issue has been
raised. Those are different statements, and the difference matters when computing a false-positive
rate.

Therefore:

- Negative examples are described as **controls / no-known-issue samples**, not as ground-truth
  negatives — unless they are synthetic, where "no relationship exists" is true by construction.
- **Absence of a PubPeer comment or a retraction is not a negative label.** It is absence of
  evidence, and it correlates with visibility, field, journal, and time since publication.
- Reported false-positive rates must be stated as "false alarms against a no-known-issue control
  set," with the control set's construction described. Anything stronger overstates what was
  measured.
- Symmetrically: a detector missing a real duplication in a no-known-issue paper is invisible to
  us. Recall measured on control sets is not recall.

---

## 10. Dataset leakage and split policy

For detector evaluation **and** any future model training, split at the appropriate provenance
level, never randomly by item. Evaluation tuning, validation, and frozen held-out partitions are
pre-registered before threshold work begins; moving an item after inspecting results invalidates
the affected held-out result.

Avoid:

- panels from the same figure appearing in both train and test;
- figures from the same paper crossing the split;
- near-identical preprint and published versions crossing the split;
- multiple papers sharing a duplicated source image crossing the split, when evaluating
  image-reuse detection — this is the subtle one, and it is the leak most likely to produce an
  impressive, meaningless number.

Prefer grouping by:

- **source image lineage** (all derivatives of one original stay together — mandatory for
  synthetic data, where every variant of a source panel shares one group key);
- **paper**, only for future manuscript-derived evaluation;
- possibly **lab / author cluster**, only when a future benchmark explicitly concerns
  generalization rather than the folder-scoped V0.1 workflow.

`split_group_key` (§7) exists to make this enforceable. A single item may need several group keys
(source lineage, paper/version family, lab/author cluster); the split assignment uses the
transitive closure so any shared group keeps items together. **Leakage checks must be implemented,
run, and their results documented alongside every reported metric.** A detector or model report
without a leakage check is not a result.

---

## 11. V0.1 decision

**Research Image Finder V0.1 does not train or load custom or pretrained models.**
See [ADR-0007](docs/adr/0007-no-custom-model-training-in-v0.1.md).

V0.1 may use only model-free deterministic methods such as:

- deterministic image matching (perceptual hashing, ORB/SIFT + RANSAC, NCC/phase correlation)
- classical computer vision (thresholding, projection, contour analysis)

V0.1 does not include pretrained embeddings, a local LLM, a local model server, downloaded model
weights, or a model-dependent candidate path. Future model evaluation requires a new product-scope
decision in addition to the gate below.

Custom specialized models are considered only after **all five** of the following hold:

1. the detector pipeline is empirically validated on the evaluation corpus;
2. useful class-B/C labels with recorded domain realism exist in sufficient quantity;
3. dataset provenance and licensing are clear and recorded per item;
4. an evaluation benchmark is defined **first**, with splits and leakage checks;
5. there is evidence that a trained model improves precision or recall **over the tuned classical
   baseline** — not over an untuned strawman.

Condition 5 deserves emphasis. Comparing a new model against a poorly configured baseline is the
most common way projects convince themselves to adopt a model they did not need.

---

## 12. Model-development gate

Before any custom model training begins, a short written proposal must be committed to
`docs/model-proposals/` and answer every question below. Training that begins without it is out
of policy.

1. **What exact prediction task are we training?** State inputs, outputs, and the unit of
   prediction (panel pair? region? figure?).
2. **Why is a deterministic or classical method insufficient?** Give the measured baseline
   numbers, on the defined benchmark, with the tuning that was tried.
3. **What is the decision this model informs**, and what happens when it is wrong in each
   direction? Quantify the asymmetry ([MVP.md §5](MVP.md)).
4. **What data will be used?** Enumerate sources, label-support classes and domain-realism classes
   (§2), item counts per class, and licensing status per source (§7, §8).
5. **How were labels produced?** By whom, with what evidence, and with what inter-rater agreement
   where more than one reviewer was involved.
6. **What is the split policy and the leakage check?** Name the `split_group_key` and the test
   that verifies no group crosses the split (§10).
7. **What is the evaluation benchmark, and was it defined before training?** Point to the
   committed benchmark definition and its commit hash.
8. **What is the acceptance bar** — the specific precision/recall improvement over the classical
   baseline that would justify adoption, decided in advance?
9. **How does the model preserve product invariants?** Specifically: reproducibility (AC-3), the
   Layer-2 rule that a model hit alone is never a finding
   ([ARCHITECTURE.md §3](ARCHITECTURE.md)), and priority assignment remaining in Layer 1.
10. **What is the failure and rollback plan?** How is the model versioned in
    `provenance.models_used`, and how does a user disable it?
11. **What are the privacy implications?** Confirm no user production data is involved absent §3
    opt-in, and record both consent and authority-to-donate for any donated item, including the
    withdrawal and already-trained-model policy.
12. **Who reviews and approves this proposal**, and on what date?

Approval is recorded in the proposal document itself. A rejected or withdrawn proposal stays in
the directory with its outcome noted — the record of what we decided *not* to train is as useful
as the record of what we did.
