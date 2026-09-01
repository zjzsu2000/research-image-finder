#!/usr/bin/env python3
"""Lightweight documentation and schema validation. Standard library only.

Checks, in order:
  1. every .json under schemas/ parses
  2. the example findings satisfy the parts of finding.schema.json we can check
     without a JSON Schema library (required keys, enums, consts, patterns)
  3. no forbidden vocabulary (aggregate scores, misconduct terms, `severity`)
     appears as a key or string value anywhere in schemas/ or the examples,
     except the two exact schema-mandated disclaimer constants
  4. every relative markdown link in the docs resolves to a file that exists

Run:  python3 tools/validate_docs.py
Exit: 0 on success, 1 on any failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN = re.compile(
    r"(?i)\b("
    r"severity|integrity_score|fraud_score|risk_score|trust_score|overall_score|"
    r"document_rating|confidence_of_misconduct|fraud|misconduct|fabrication|"
    r"falsification|plagiarism|cheating|guilty|verdict"
    r")\b"
)

# Places where the forbidden vocabulary is legitimately present because the file's
# job is to prohibit it. Everything else must be clean.
DENYLIST_EXEMPT_PATHS = {
    "schemas/finding.schema.json",       # contains the denylist regex itself
    "schemas/run_manifest.schema.json",  # ditto
}

# Two schema-mandated constants deliberately contain the word "misconduct" because
# their entire purpose is to disclaim it. They are exact, fixed strings enforced by
# `const` in the schemas, so exempting them by exact match cannot widen the hole:
# any deviation from the constant fails the const check in check_example_findings().
DISCLAIMER_CONSTANTS = {
    "Ordering hint for human review. NOT a probability, likelihood, or indication of misconduct.",
    "Research Preflight produces findings for human review. It does not detect or determine "
    "research misconduct. The absence of findings does not verify integrity.",
}

DOCS = [
    "README.md", "PRODUCT.md", "MVP.md", "ARCHITECTURE.md", "PRIVACY.md",
    "FINDING_SCHEMA.md", "DATASET_POLICY.md", "EVALUATION.md", "ROADMAP.md",
]

errors: list[str] = []
checks = 0


def fail(msg: str) -> None:
    errors.append(msg)


def ok() -> None:
    global checks
    checks += 1


# --------------------------------------------------------------------------- 1
def check_json_parses() -> list[Path]:
    files = sorted((ROOT / "schemas").rglob("*.json"))
    if not files:
        fail("no JSON files found under schemas/")
    for f in files:
        try:
            json.loads(f.read_text(encoding="utf-8"))
            ok()
        except json.JSONDecodeError as exc:
            fail(f"{f.relative_to(ROOT)}: invalid JSON: {exc}")
    return files


# --------------------------------------------------------------------------- 2
def walk_strings(node, path="$"):
    """Yield (json_path, kind, value) for every key and string value."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield f"{path}.{k}", "key", k
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, "value", node


def check_example_findings(schema: dict) -> None:
    props = schema["properties"]
    required = schema["required"]
    examples = sorted((ROOT / "schemas" / "examples").glob("finding_*.json"))
    if not examples:
        fail("no example findings found in schemas/examples/")
    for f in examples:
        doc = json.loads(f.read_text(encoding="utf-8"))
        rel = f.relative_to(ROOT)

        for key in required:
            if key not in doc:
                fail(f"{rel}: missing required key '{key}'")
            else:
                ok()

        for key in doc:
            if key not in props:
                fail(f"{rel}: unknown top-level key '{key}' (additionalProperties: false)")

        # enums and consts on top-level scalar fields
        for key, spec in props.items():
            if key not in doc:
                continue
            if "enum" in spec and doc[key] not in spec["enum"]:
                fail(f"{rel}: {key}={doc[key]!r} not in enum")
            elif "const" in spec and doc[key] != spec["const"]:
                fail(f"{rel}: {key} does not match required const text")
            elif "pattern" in spec and isinstance(doc[key], str):
                if not re.match(spec["pattern"], doc[key]):
                    fail(f"{rel}: {key}={doc[key]!r} fails pattern {spec['pattern']}")
            else:
                continue
            ok()

        # evidence must be a registered, tagged family
        kinds = {
            d["properties"]["kind"]["const"]
            for d in schema["$defs"].values()
            if isinstance(d, dict) and "properties" in d and "kind" in d["properties"]
        }
        kind = doc.get("evidence", {}).get("kind")
        if kind not in kinds:
            fail(f"{rel}: evidence.kind={kind!r} is not a registered evidence family")
        else:
            ok()

        # minItems on the required narrative arrays
        for key in ("possible_benign_explanations", "recommended_verification", "locations"):
            if len(doc.get(key, [])) < 1:
                fail(f"{rel}: {key} must have at least one entry")
            else:
                ok()

        # strict-local provenance invariant (AC-11)
        prov = doc.get("provenance", {})
        if prov.get("mode") == "strict_local" and prov.get("external_services_used"):
            fail(f"{rel}: strict_local run records external_services_used")
        else:
            ok()

        # narrative_source consistency
        ns = doc.get("narrative_source", {})
        if ns.get("mode") == "template" and ns.get("model") is not None:
            fail(f"{rel}: narrative_source.mode=template must have model=null")
        elif ns.get("mode") == "llm" and not isinstance(ns.get("model"), dict):
            fail(f"{rel}: narrative_source.mode=llm must name a model")
        else:
            ok()

        # image findings must carry visual evidence (AC-10)
        if doc.get("finding_type", "").startswith("image."):
            roles = {a["role"] for a in doc.get("evidence_assets", [])}
            missing = {"crop_a", "crop_b", "overlay"} - roles
            if missing:
                fail(f"{rel}: image finding missing evidence assets: {sorted(missing)}")
            else:
                ok()


# --------------------------------------------------------------------------- 3
def check_denylist(files: list[Path]) -> None:
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if rel in DENYLIST_EXEMPT_PATHS:
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        hits = [
            (p, kind, v)
            for p, kind, v in walk_strings(doc)
            if FORBIDDEN.search(v) and not (kind == "value" and v in DISCLAIMER_CONSTANTS)
        ]
        if hits:
            for p, kind, v in hits:
                fail(f"{rel}: forbidden vocabulary in {kind} at {p}: {v!r}")
        else:
            ok()


# --------------------------------------------------------------------------- 4
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")


def check_markdown_links() -> None:
    md_files = [ROOT / d for d in DOCS] + sorted((ROOT / "docs").rglob("*.md"))
    for f in md_files:
        if not f.exists():
            fail(f"missing expected document: {f.relative_to(ROOT)}")
            continue
        text = f.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (f.parent / target).resolve()
            if not resolved.exists():
                fail(f"{f.relative_to(ROOT)}: broken link -> {target}")
            else:
                ok()


def main() -> int:
    files = check_json_parses()
    schema_path = ROOT / "schemas" / "finding.schema.json"
    if schema_path.exists():
        check_example_findings(json.loads(schema_path.read_text(encoding="utf-8")))
    check_denylist(files)
    check_markdown_links()

    if errors:
        print(f"FAIL — {len(errors)} problem(s), {checks} checks passed\n")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"OK — {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
