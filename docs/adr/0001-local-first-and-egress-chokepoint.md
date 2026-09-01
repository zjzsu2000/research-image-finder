# ADR-0001 — Local-first architecture with a single network-egress chokepoint

- **Status:** Accepted
- **Date:** 2026-08-30
- **Relates to:** [PRIVACY.md](../../PRIVACY.md), [ARCHITECTURE.md §5–§7](../../ARCHITECTURE.md), AC-1, AC-2

## Context

Research Preflight ingests unpublished manuscripts: unfiled patent material, embargoed clinical
results, and figures that may contain patient-identifiable imagery. For a large share of the
target users, uploading that file to any third party is prohibited outright by institutional
policy, sponsor agreement, IRB protocol, or law.

A privacy claim of the form "we don't store your data" is an unverifiable assertion about someone
else's servers. Our users — and their compliance officers — cannot audit it.

Meanwhile, network access is the easiest thing in a codebase to acquire accidentally. A DOI
lookup here, a model download there, an analytics library pulled in transitively, a report
template that references a web font. Each is individually defensible and collectively fatal to
the guarantee.

## Decision

1. **Strict Local is the default and the only mode implemented in V0.1.** No outbound connection
   of any kind, including DNS, update checks, model downloads, or telemetry.
2. **All network capability lives in exactly one module, `preflight.net`.** No other module in the
   codebase may import a networking library. In V0.1 every function in it raises under Strict
   Local.
3. **`PolicyGate` mediates every capability-bearing action** — network, egress, model use, and
   filesystem writes. A denial raises and aborts the run; it never warns-and-continues and never
   silently falls back.
4. **The guarantee is enforced by tests, not review discipline:**
   - an `import-linter` contract forbidding networking imports outside `preflight.net`;
   - an end-to-end test running the complete pipeline with `socket.socket` monkeypatched to raise;
   - a static scan of generated HTML for external URLs, so a report cannot phone home when opened;
   - `preflight verify-privacy`, which runs these checks **on the user's own machine**.
5. **Loopback is not an exception.** Talking to a local model server is local IPC over a socket. It
   is permitted only through `preflight.net`'s loopback-restricted path, requires an explicit
   `allow_model` decision, validates that the endpoint actually resolves to loopback at connect
   time, and is recorded in `models_used`.

## Rationale

- **It converts a promise into a property.** "No socket is opened" is testable by the person who
  needs the guarantee. That is a categorically stronger claim than a privacy policy.
- **A chokepoint is the only structure that survives contributors.** Distributed permission checks
  decay; a single module with a lint rule and a socket-blocked test does not.
- **Air-gapped and network-restricted environments are a large, underserved market segment**, not
  an edge case. Designing for them costs little and opens hospital, pharma, and defense-adjacent
  research.
- **A user-runnable verification command changes the sales conversation** from trust to
  demonstration.

## Consequences

**Positive.** The privacy guarantee is auditable, testable, and demonstrable. Air-gapped
deployment is nearly free. There is no data-breach surface, because there is no collected data.
The architecture stays simple: no request signing, no retry logic, no rate limiting, no secret
management.

**Negative.** Online reference validation, DOI resolution, and retraction lookup are impossible in
V0.1 — a real capability loss (see ADR-0003's sibling decision in ROADMAP's divergence table).
There is no telemetry, so we learn nothing about field false-positive rates unless users tell us
(accepted in [PRODUCT.md §12](../../PRODUCT.md)). Model weights must be user-provisioned. Every
future networked feature must pass through the chokepoint and a PolicyGate decision, which is
friction — deliberately.

**Ongoing obligation.** Dependencies must be audited for import-time or first-use network access;
the socket-blocked end-to-end test is the backstop that catches them.

## Alternatives considered

- **Cloud-first with strong privacy commitments.** Rejected: unverifiable, and disqualifying for a
  large share of target users regardless of how good the commitments are.
- **Local-first with opt-in telemetry, default off.** Rejected for V0.1: the collection code's
  mere existence is a credibility liability that must be re-defended in every procurement review.
  Absent code is a stronger claim than disabled code.
- **A network layer with per-call permission checks, no chokepoint.** Rejected: not statically
  verifiable, and it decays as contributors add call sites.
- **Sandboxing or OS-level network denial instead of application-level enforcement.** Rejected as
  the *primary* mechanism — not portable, not user-visible, and it cannot distinguish a permitted
  loopback model call from a prohibited external one. It remains a fine defense in depth.
