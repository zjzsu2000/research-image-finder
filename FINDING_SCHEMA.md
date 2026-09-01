# FINDING_SCHEMA.md — The Canonical Finding

Status: **approved, schema_version 0.1.0**
Last updated: 2026-08-30
Machine-readable: [`schemas/finding.schema.json`](schemas/finding.schema.json),
[`schemas/run_manifest.schema.json`](schemas/run_manifest.schema.json)

The `Finding` is the interchange format of this project. Detectors produce it, the report renders
it, triage annotates it, and any future integration consumes it. It is designed to be **stable,
open, and safe to quote out of context** — because it will be quoted out of context.

---

## 1. Governing principles

| Principle | How the schema enforces it |
| --- | --- |
| **Observation, not inference** | `finding_type` names what was *measured*. `image.duplicate_region_pair`, never `possible_image_reuse`. Inference lives in hedged prose. |
| **Review priority, not severity** | The field is `review_priority`. `severity` is **forbidden** by the schema. A sibling `review_priority_note` ships with every finding restating that it is not a probability of misconduct. |
| **No aggregate score** | No integrity score, fraud score, document rating, or risk index exists at any level. Validation *fails* if such a key appears. |
| **Evidence required** | `evidence` is required, is a tagged union, and must contain machine-checkable values sufficient to re-derive the finding. |
| **Provenance required** | `provenance` is required: timestamp, tool version, mode, `external_services_used`, `models_used`, source document hashes. |
| **Reproduction required** | `reproduction` records the detector, version, and exact parameters needed to recompute the finding. |
| **Human triage required** | `triage` is required and defaults to `{"status": "open"}`. A finding is never self-resolving. |
| **Narrative attribution** | `narrative_source` is required whenever prose fields are populated, and names the model if one wrote them. |
| **No misconduct vocabulary** | A denylist test rejects `fraud`, `misconduct`, `fabrication`, `falsification`, `cheating`, `plagiarism`, `guilty`, `intent` and `severity` in any key or enum value. |

---

## 2. Top-level structure

```jsonc
{
  "schema_version": "0.1.0",       // required
  "id": "f_<16 hex>",              // required — content-derived, stable across runs
  "run_id": "run_<ts>_<short>",    // required
  "finding_type": "image.duplicate_region_pair",   // required, dotted, observation-named
  "review_priority": "high",       // required: info | low | medium | high
  "review_priority_note": "...",   // required, constant text (see §4)
  "detector": { ... },             // required: name, version, params_hash
  "locations": [ ... ],            // required, ≥1
  "evidence": { ... },             // required, tagged by `kind`
  "evidence_assets": [ ... ],      // optional; required for image findings
  "why_flagged": "...",            // required
  "possible_benign_explanations": [ ... ],   // required, ≥1
  "recommended_verification": [ ... ],       // required, ≥1
  "narrative_source": { ... },     // required
  "triage": { ... },               // required
  "reproduction": { ... },         // required
  "provenance": { ... },           // required
  "related_finding_ids": [ ... ]   // optional
}
```

### Finding IDs are content-derived

`id = "f_" + sha256(detector.name ‖ detector.version ‖ canonical(locations) ‖
canonical(evidence.identity_fields))[:16]`

Timestamps, run IDs, absolute paths, and prose are **excluded** from the hash. This is what lets
triage decisions survive re-runs, lets two runs be diffed, and satisfies AC-3.

### `finding_type` namespace

Dotted, `family.observation`. Registered families:

| Family | Types |
| --- | --- |
| `image` | `duplicate_region_pair`, `corpus_region_match`, `panel_contains_panel` |
| `numeric` | `sample_size_disagreement`, `proportion_arithmetic_mismatch`, `value_disagreement_across_locations` |
| `stats` | `pvalue_inconsistent_with_statistic`, `mean_inconsistent_with_granularity` |
| `reference` | `cited_not_listed`, `listed_not_cited`, `duplicate_entry`, `malformed_entry` |
| `coverage` | `figure_referenced_not_extracted`, `panel_segmentation_fallback`, `table_grid_unrecoverable` |

`coverage.*` findings are emitted at `review_priority: "info"` and describe **limits of the
analysis**, not properties of the manuscript. They exist so that gaps are visible rather than
silent ([MVP.md §6](MVP.md)).

Adding a type requires: an observation-named identifier, a registered `evidence.kind`, and unit
tests over its evidence contract.

---

## 3. Field reference

### `detector`
```jsonc
{ "name": "image.within_document", "version": "0.1.0", "params_hash": "a41c…" }
```
`params_hash` is a stable hash of the full effective parameter set, so a threshold change is
visible in the record.

### `locations` *(≥1)*
```jsonc
{
  "role": "a",                     // a | b | primary | context
  "doc_id": "subject",             // "subject" or a corpus document id
  "doc_role": "subject",           // subject | corpus
  "page": 7,                       // 1-indexed
  "figure_label": "Figure 3B",     // as printed, or null
  "panel_id": "p_f3_b",            // internal, or null
  "bbox": [112, 340, 398, 562],    // panel bbox in page points
  "region_bbox": [140, 360, 300, 470],   // matched sub-region, or null
  "char_span": [18422, 18461],     // global character offsets, or null
  "table_id": null, "cell": null,
  "quoted_text": "n = 24 mice"     // short verbatim span, or null
}
```
Every finding must be traceable to a page, and to a figure/panel or a character span.

### `review_priority`
`info | low | medium | high`. **Ordering hint for a human review queue.** Provisional V0.1 rules
(to be re-baselined after spike S3 — [EVALUATION.md](EVALUATION.md)):

| Priority | Image findings | Numeric / reference findings |
| --- | --- | --- |
| `high` | inlier_ratio ≥ 0.70, overlap ≥ 0.25 of either panel, content type in {micrograph, blot, photo}, not an inset, not a recurring-control candidate | recomputation disagrees beyond rounding tolerance and both sources are unambiguous |
| `medium` | above thresholds but cross-paper (corpus) match, or a non-identity transform with moderate inlier ratio | disagreement within a plausible rounding or convention band |
| `low` | recurring-control candidate, plot/schematic content type, or small matched area | single-mention anomaly, or ambiguous referent |
| `info` | inset/containment relationship reported for completeness | `coverage.*`, and applicability notes |

Priority is assigned by a **rule table in Layer 1**. An LLM may never set or alter it
([ARCHITECTURE.md §3](ARCHITECTURE.md)).

### `review_priority_note` *(required, constant)*
> "Ordering hint for human review. NOT a probability, likelihood, or indication of misconduct."

Required on every finding so the caveat survives any partial extraction of the JSON.

### `evidence` *(required, tagged union — see §5)*
Must be sufficient to re-derive the finding without re-running the tool. Numeric values are
rounded to a fixed precision so they compare equal across runs (AC-3).

### `evidence_assets`
```jsonc
[ { "role": "crop_a", "path": "evidence/f_9c2ab41e/crop_a.png", "sha256": "…",
    "media_type": "image/png" } ]
```
Paths are **relative to the run directory**. Required for `image.*` findings: at minimum
`crop_a`, `crop_b`, `overlay` — because AC-10 requires a human to adjudicate by looking.

### `why_flagged`
One or two sentences stating **what was measured** and why it crossed a threshold. Never states or
implies intent. Contrast:

- ✅ "A region of Figure 3B aligns to a region of Figure 5D under a horizontal flip with 142
  geometrically consistent feature matches (86% inlier ratio). The panels are captioned as
  different experimental conditions."
- ❌ "Figure 3B appears to have been fraudulently duplicated and flipped."

### `possible_benign_explanations` *(≥1, required)*
Never empty. The report renders these at **equal visual weight** to the flag
([PRODUCT.md §8](PRODUCT.md)). If a detector cannot articulate a benign explanation, that is
evidence the detector is not ready to ship.

### `recommended_verification` *(≥1, required)*
Concrete **human** actions: retrieve original acquisition files, compare capture timestamps, ask
the person who assembled the panel, add a disclosure sentence to the legend. Never a conclusion,
never an escalation to a third party.

### `narrative_source` *(required)*
```jsonc
{ "mode": "template", "model": null }
{ "mode": "llm", "model": { "backend": "ollama", "id": "qwen2.5:14b", "digest": "sha256:…" } }
```
A reader must always be able to tell whether a human-written template or a model wrote the prose.

### `triage` *(required)*
```jsonc
{
  "status": "open",              // open | real_issue | legitimate_reuse | false_positive | unsure
  "reason": null,                // see DATASET_POLICY.md §6 reason labels
  "reviewer_note": null,
  "updated_at": null
}
```
Statuses and reason labels are **shared with the future expert-review label schema**
([DATASET_POLICY.md §6](DATASET_POLICY.md)) so that, if a user ever opts in to donate labels, the
vocabulary already matches. Note that `real_issue` means *a real technical issue requiring
action* — a wrong file inserted during figure assembly is a real issue and is not misconduct.

### `reproduction` *(required)*
```jsonc
{ "detector": "image.within_document", "version": "0.1.0",
  "params": { "min_inliers": 30, "ratio_test": 0.75, "ransac_reproj_px": 3.0, "seed": 0 },
  "input_digests": { "panel_a": "sha256:…", "panel_b": "sha256:…" } }
```

### `provenance` *(required)*
```jsonc
{
  "timestamp_utc": "2026-08-30T17:45:03Z",
  "tool_version": "0.1.0",
  "schema_version": "0.1.0",
  "mode": "strict_local",              // strict_local | hybrid_privacy | cloud_assisted
  "external_services_used": [],        // MUST be [] in strict_local (AC-11)
  "models_used": [],                   // backend, id, digest — empty unless a model ran
  "index_version": "corpus-0.1.0",     // or null
  "source_documents": [ { "doc_id": "subject", "sha256": "…", "basename": "manuscript.pdf" } ]
}
```

---

## 4. Forbidden by construction

Validation **fails** if any of the following appear as a key, enum value, or emitted string in a
finding or run manifest:

- `severity` *(use `review_priority`)*
- `integrity_score`, `fraud_score`, `risk_score`, `confidence_of_misconduct`, `document_rating`,
  `overall_score`, `trust_score`, or any document-level aggregate
- `fraud`, `misconduct`, `fabrication`, `falsification`, `plagiarism`, `cheating`, `guilty`,
  `intent`, `deliberate`, `verdict`

**One deliberate exception, worth stating explicitly:** the constants
`review_priority_note` and the run manifest's `notice` contain the word *misconduct*, because
their entire purpose is to disclaim it. Both are fixed `const` strings enforced by the schema, so
the exemption is by exact match and cannot widen: any deviation from the constant fails
validation. The denylist otherwise applies to keys and values without exception.

There is deliberately **no document-level summary object** in the schema. The run manifest carries
counts by priority for rendering, and counts are not a score — but no field ranks, grades, or
rates a document or an author.

---

## 5. Evidence families

`evidence.kind` selects the family. Each has required fields validated independently.

### 5.1 `image_region_match`
Emitted by `image.duplicate_region_pair`, `image.corpus_region_match`, `image.panel_contains_panel`.

| Field | Type | Meaning |
| --- | --- | --- |
| `method` | enum | `ORB+RANSAC` \| `SIFT+RANSAC` \| `NCC` \| `phase_correlation` |
| `inlier_count` | int | geometrically consistent correspondences |
| `inlier_ratio` | float 0–1 | inliers / matches after ratio test |
| `overlap_area_frac_a` / `_b` | float 0–1 | matched region as a fraction of each panel |
| `phash_hamming` | int \| null | prefilter distance (diagnostic only) |
| `ncc_peak` | float \| null | for the low-texture path |
| `estimated_transform` | object | `{type, flip_x, flip_y, rotation_deg, scale}` |
| `homography` | 3×3 \| null | the estimated mapping |
| `panel_content_type` | object | `{a, b}` heuristic classes |
| `inset_relationship` | bool | one panel is a magnification of the other |
| `recurring_control_candidate` | bool | panel matches ≥3 others in the same document |
| `same_work_candidate` | bool \| null | corpus doc appears to be a version of the subject |

### 5.2 `stat_recomputation`
Emitted by `stats.*`.

`test` (`t`\|`F`\|`chi2`\|`r`\|`grim`) · `reported` (verbatim string) ·
`parsed` (`{statistic, df1, df2, n, tail, reported_p}`) · `recomputed` (`{p}` or `{feasible_means}`)
· `discrepancy` · `tolerance` · `rounding_model` · `assumptions` (array, e.g. `["two_tailed",
"uncorrected"]`) · `source_span`.

`assumptions` is required and rendered in the report, because most statistical false positives are
assumption mismatches (one-tailed tests, multiplicity corrections, unusual df conventions).

### 5.3 `numeric_disagreement`
Emitted by `numeric.*`.

`quantity` (e.g. `sample_size`) · `referent` (the entity the values describe, plus how it was
resolved) · `observations` (array of `{value, unit, location_index, quoted_text}`) ·
`relation` (`equality_expected` \| `arithmetic`) · `computed` (for arithmetic) ·
`referent_resolution` (`exact_label_match` \| `same_sentence` \| `same_table_row`) ·
`ambiguity_notes`.

> `referent_resolution` is required, and only high-confidence resolution strategies are permitted
> in V0.1. This field is the mechanism that keeps numeric checking from sliding into general NLP
> consistency checking ([MVP.md §3](MVP.md)).

### 5.4 `reference_integrity`
Emitted by `reference.*`.

`check` (`cited_not_listed` \| `listed_not_cited` \| `duplicate_entry` \| `malformed_entry`) ·
`citation_marker` · `bibliography_index` · `raw_entry` · `parsed_fields` ·
`duplicate_of` · `parser_confidence` · `resolution_source: "offline_document_only"`.

`resolution_source` is fixed to `"offline_document_only"` in V0.1 — a permanent record that no
external database was consulted, and the extension point for a future network-enabled mode.

---

## 6. Examples

### 6.1 Image finding — high priority
See [`schemas/examples/finding_image_high.json`](schemas/examples/finding_image_high.json).

```json
{
  "schema_version": "0.1.0",
  "id": "f_9c2ab41e7d3f0a11",
  "run_id": "run_20260830T174501Z_3f9a",
  "finding_type": "image.duplicate_region_pair",
  "review_priority": "high",
  "review_priority_note": "Ordering hint for human review. NOT a probability, likelihood, or indication of misconduct.",
  "detector": { "name": "image.within_document", "version": "0.1.0", "params_hash": "a41c9f22" },
  "locations": [
    { "role": "a", "doc_id": "subject", "doc_role": "subject", "page": 7,
      "figure_label": "Figure 3B", "panel_id": "p_f3_b",
      "bbox": [112, 340, 398, 562], "region_bbox": [140, 360, 300, 470] },
    { "role": "b", "doc_id": "subject", "doc_role": "subject", "page": 11,
      "figure_label": "Figure 5D", "panel_id": "p_f5_d",
      "bbox": [90, 120, 376, 342], "region_bbox": [118, 140, 278, 250] }
  ],
  "evidence": {
    "kind": "image_region_match",
    "method": "ORB+RANSAC",
    "inlier_count": 142, "inlier_ratio": 0.86,
    "overlap_area_frac_a": 0.41, "overlap_area_frac_b": 0.39,
    "phash_hamming": 18, "ncc_peak": null,
    "estimated_transform": { "type": "similarity", "flip_x": true, "flip_y": false,
                             "rotation_deg": 0.4, "scale": 0.97 },
    "homography": [[0.97, 0.01, 12.4], [-0.01, 0.97, -3.2], [0.0, 0.0, 1.0]],
    "panel_content_type": { "a": "micrograph", "b": "micrograph" },
    "inset_relationship": false, "recurring_control_candidate": false,
    "same_work_candidate": null
  },
  "evidence_assets": [
    { "role": "crop_a", "path": "evidence/f_9c2ab41e7d3f0a11/crop_a.png", "sha256": "3a1f…", "media_type": "image/png" },
    { "role": "crop_b", "path": "evidence/f_9c2ab41e7d3f0a11/crop_b.png", "sha256": "9b02…", "media_type": "image/png" },
    { "role": "overlay", "path": "evidence/f_9c2ab41e7d3f0a11/overlay.png", "sha256": "c74d…", "media_type": "image/png" }
  ],
  "why_flagged": "A region of Figure 3B aligns to a region of Figure 5D under a horizontal flip with 142 geometrically consistent feature matches (86% inlier ratio), covering about 40% of each panel. The two panels are captioned as different experimental conditions.",
  "possible_benign_explanations": [
    "The same control condition is legitimately shown in both figures",
    "Both panels derive from the same source image, with reuse intended but not stated in the legend",
    "A panel was placed in the wrong slot during figure assembly"
  ],
  "recommended_verification": [
    "Locate the original acquisition files for both panels and compare capture timestamps and filenames",
    "Ask the person who assembled the figure which experiment each panel came from",
    "If the reuse is intended, state it explicitly in the figure legend before submission"
  ],
  "narrative_source": { "mode": "template", "model": null },
  "triage": { "status": "open", "reason": null, "reviewer_note": null, "updated_at": null },
  "reproduction": {
    "detector": "image.within_document", "version": "0.1.0",
    "params": { "min_inliers": 30, "ratio_test": 0.75, "ransac_reproj_px": 3.0, "seed": 0 },
    "input_digests": { "panel_a": "sha256:1f0c…", "panel_b": "sha256:77ad…" }
  },
  "provenance": {
    "timestamp_utc": "2026-08-30T17:45:03Z", "tool_version": "0.1.0", "schema_version": "0.1.0",
    "mode": "strict_local", "external_services_used": [], "models_used": [], "index_version": null,
    "source_documents": [ { "doc_id": "subject", "sha256": "sha256:be31…", "basename": "manuscript.pdf" } ]
  }
}
```

### 6.2 Numeric finding — medium priority
See [`schemas/examples/finding_numeric_medium.json`](schemas/examples/finding_numeric_medium.json).
An `n` disagreement between the methods section and a figure legend, where the referent was
resolved by exact label match — the only resolution strategy strong enough to justify a flag.
Its benign explanations name the most likely cause first (**exclusions applied after enrolment**),
because that is usually what happened.

### 6.3 Benign / low-priority finding
See [`schemas/examples/finding_image_low_benign.json`](schemas/examples/finding_image_low_benign.json).
A panel matching four others in the same manuscript — a recurring loading control. The detector
sets `recurring_control_candidate: true`, priority drops to `low`, and the first benign
explanation states the likely cause outright:

> "This panel matches four other panels in the manuscript, which is the expected pattern for a
> shared loading control or a reference condition displayed alongside multiple treatments."

This case is worth studying: it is the single most common image match in real manuscripts, it is
almost always benign, and **how it is presented determines whether the tool is trusted or
deleted.**

---

## 7. Versioning and compatibility

`schema_version` follows semver. Adding an optional field is a minor bump; adding a required
field, removing a field, or changing an enum's meaning is a major bump. Detector versions are
independent of the schema version.

`schemas/examples/*.json` are validated against `schemas/finding.schema.json` in CI, so the
examples in this document cannot silently drift from the contract.

The schema is intended to be **open and stable even if other components are not**, because its
value is as an interchange format between labs, tools, and — eventually — institutions
([PRODUCT.md §11](PRODUCT.md)).
