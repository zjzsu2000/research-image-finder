# ADR-0009 — The exact Strict Local capability and trust boundary

- **Status:** Accepted
- **Date:** 2026-08-30
- **Amends:** [ADR-0001](0001-local-first-and-egress-chokepoint.md) §§1 and 5 (the local-first
  principle and the chokepoint stand; the capability definition below replaces ADR-0001's wording)
- **Relates to:** [PRIVACY.md](../../PRIVACY.md), [ARCHITECTURE.md §§5–7](../../ARCHITECTURE.md), AC-1, AC-2
- **Origin:** [Codex Phase 1 design review](../reviews/2026-08-30-codex-phase1-design-review.md) §2.2

## Context

The Phase 1 documentation made two claims that cannot both hold. `README.md` and `PRIVACY.md`
promised "no network request of any kind, for any reason, including DNS." `ARCHITECTURE.md` and
ADR-0001 simultaneously permitted loopback HTTP to a local model server such as Ollama or a
llama.cpp server. **Loopback HTTP is a socket.** The headline guarantee and the feature list
contradicted each other.

The proposed enforcement was also weaker than advertised. Monkeypatching `socket.socket` and
linting imports catches Python-level networking in our own package. It does not catch sockets
opened by native libraries, by subprocesses, through `ctypes`, via proxy environment variables,
or by dependencies outside the linted package. `PolicyGate.allow_write` has the same limitation
for filesystem writes performed by native code or subprocesses.

An overstated privacy guarantee is worse than a narrower accurate one, especially for the
unpublished, pre-patent, clinical, and sponsor-restricted material this tool exists to handle.
A compliance reviewer who finds one overstatement discounts every other claim we make.

## Decision

### 1. Strict Local, by default, opens no socket at all

The default V0.1 configuration uses `NullBackend`, loads no model, and makes **zero socket calls
of any address family**. This is the configuration the headline promise describes, and it is the
configuration AC-1 tests.

### 2. Local Model IPC is a separately named capability that exits the zero-socket claim

Using a local model server is a distinct, explicitly enabled capability called **Local Model
IPC**. Enabling it:

- is never a default, never auto-detected, and never reached by fallback;
- **explicitly and visibly exits the zero-socket claim**, stated in those terms in the CLI at
  enable time, in `run.json`, in every affected finding's provenance, and in the report;
- restricts connections to **literal loopback addresses** (`127.0.0.1`, `::1`) — no hostnames, so
  no DNS resolution occurs; no proxy environment variables are honoured; no redirects are
  followed;
- records `endpoint_class` (`loopback` | `local_process`) in `models_used`.

The zero-socket promise and the local-model feature are therefore never asserted about the same
run.

### 3. A local model server is a separately trusted processor

We can guarantee what *our* process sends and where. We cannot guarantee what a third-party
inference server does with what it receives — it may log prompts, persist a cache, or itself have
network access. Documentation must say this plainly rather than implying that "local" transfers
our guarantee to someone else's binary.

A model served from another machine on the lab network is **not** local for these purposes and is
rejected.

### 4. Enforcement is OS-level, not language-level

AC-1 is tested under **OS-enforced denial of AF_INET/AF_INET6 and DNS**, covering the whole
process tree — dependencies, native code, and subprocesses — not by a Python monkeypatch alone.
The monkeypatch and the import-linter contract remain as fast in-development checks and as defense
in depth, not as the guarantee.

AC-2 is tested by a **syscall-level filesystem audit** in isolated `HOME`/`TMP`/`XDG` directories,
covering dependencies and subprocesses, and including symlink and path-traversal escape attempts.
Outputs are written with restrictive permissions. Installation-time writes are tested separately
from runtime writes.

### 5. Stated limits of the guarantee

The following are **outside** what the application can enforce, and are documented as such rather
than implied away:

- OS backups, antivirus, search indexing, and cloud-synced directories that observe the run or
  corpus directory — the user chooses where output lands, and that choice is a data-handling
  decision;
- the behaviour of a local model server (§3);
- a malicious PDF exploiting a parser vulnerability — offline operation reduces exfiltration
  impact but does not prevent exploitation ([PRIVACY.md §11](../../PRIVACY.md));
- encryption at rest.

## Rationale

- **The default path keeps the strongest honest promise.** "This run opened no socket" is a
  complete, testable, OS-verifiable statement, and it describes what most users will actually run.
- **Separating the capability preserves both.** Users who want a local LLM get one; users who need
  the absolute guarantee are not silently downgraded, because enabling the capability announces
  itself in the run record.
- **OS-level enforcement tests the property we claim**, rather than the subset of it that Python
  can observe.
- **Naming the limits is what makes the rest credible.** A privacy specification that admits what
  it cannot control is one a compliance officer can actually verify and accept.

## Consequences

**Positive.** The headline promise becomes exactly true for the default configuration. Every claim
in PRIVACY.md maps to a mechanism or is explicitly marked out of scope. The user-facing
`preflight verify-privacy` command can report a precise result rather than a reassuring one. The
run manifest can distinguish a zero-socket run from a Local Model IPC run at a glance.

**Negative.** CI becomes more complex — OS-level network denial and syscall auditing are
platform-specific and harder to run everywhere than a monkeypatch, so the matrix narrows to named
supported platforms. Marketing copy is longer and more qualified. Users enabling a local model
lose the simplest version of the promise, and must be told so at the moment they enable it, which
is friction we are choosing on purpose.

**Documentation debt (tracked).** README, PRIVACY.md §§2–5 and 8–10, and ARCHITECTURE.md §§5–7 are
updated for consistency with this ADR now; the fuller privacy rewrite covering native/subprocess
behaviour, synced directories, and report active content is scheduled before production
implementation.

## Alternatives considered

- **Zero non-loopback egress, with loopback inside Strict Local.** A coherent and defensible
  definition, and the simpler single-mode option. Rejected because it weakens the default promise
  from "no socket is opened" to "nothing leaves the machine" for *every* user, including the
  majority who never enable a model — spending the strongest claim on a minority feature.
- **Zero IP sockets; Unix-domain or in-process models only.** The strongest guarantee, and worth
  revisiting. Rejected for V0.1 because it excludes Ollama's normal HTTP interface and most local
  inference servers, which would make the optional-LLM story impractical.
- **Keep the original wording and treat loopback as "not really network."** Rejected: it is
  exactly the kind of definitional convenience that destroys trust when a reviewer notices.
- **Drop local LLM support entirely from V0.1.** Considered seriously; it would make the
  contradiction vanish. Rejected because narration quality materially affects the benign-explanation
  presentation that [PRODUCT.md §8](../../PRODUCT.md) treats as a safety feature — but note that
  AC-7 guarantees the product remains fully functional without it.
