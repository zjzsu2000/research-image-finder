# Architecture Decision Records

Each ADR records one decision: its **Context**, the **Decision**, the **Rationale**, the
**Consequences** (positive *and* negative), and the **Alternatives considered**.

These are not documentation of the code — they are the reasoning that the code must not casually
discard. An ADR is changed by writing a new ADR that supersedes it, never by editing it to match
what someone built.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-local-first-and-egress-chokepoint.md) | Local-first with a single network-egress chokepoint | Accepted |
| [0002](0002-no-aggregate-integrity-score.md) | No aggregate integrity, fraud, or risk score | Accepted |
| [0003](0003-observation-named-finding-types.md) | Finding types name observations, not inferences | Accepted |
| [0004](0004-deterministic-vs-llm-boundary.md) | Deterministic / pretrained-ML / LLM layer boundary | Accepted |
| [0005](0005-geometric-verification-over-perceptual-hashing.md) | Geometric verification is primary; pHash is a prefilter | Accepted *(gated on S3)* |
| [0006](0006-sqlite-plus-numpy-corpus-index.md) | SQLite + NumPy memmap corpus index; no vector DB | Accepted |
| [0007](0007-no-custom-model-training-in-v0.1.md) | No custom model training in V0.1 | Accepted |
| [0008](0008-private-user-data-is-not-training-data.md) | Private user data is not training data | Accepted |

ADR-0005 is marked *gated on S3*: it is the current decision, and spike S3
([EVALUATION.md](../../EVALUATION.md)) exists specifically to test the premise it rests on. If the
measurement contradicts it, the ADR is revised rather than quietly ignored.
