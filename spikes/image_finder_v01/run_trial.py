#!/usr/bin/env python3
"""Disposable Strict Local user-trial runner for Research Image Finder V0.1.

The command writes one self-contained HTML report outside the repository. It does not persist an
index, machine-readable per-file results, or a trial record. The user may explicitly download a
path-free aggregate trial record from the report after completing human review.
"""
from __future__ import annotations

import argparse
import html
import json
import socket
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from image_finder.core import (  # noqa: E402
    HARDENED_CONFIG,
    SUPPORTED_EXTENSIONS,
    ImageRecord,
    VerificationConfig,
    decode_image,
    discover_images,
    is_windows_network_path,
    match_prepared,
    png_data_url,
    prepare_features,
    render_overlay_png,
    render_thumbnail_png,
)

SUPPORTED_STATUS = "geometrically_supported_candidate"


@contextmanager
def zero_socket_guard() -> Iterator[None]:
    """Fail closed if spike code attempts to create any socket."""
    original_socket = socket.socket
    original_socketpair = socket.socketpair
    original_connection = socket.create_connection

    def denied(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("Strict Local violation: socket creation attempted")

    socket.socket = denied  # type: ignore[assignment]
    socket.socketpair = denied  # type: ignore[assignment]
    socket.create_connection = denied  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket = original_socket
        socket.socketpair = original_socketpair
        socket.create_connection = original_connection


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_output(output_dir: Path) -> Path:
    output = output_dir.expanduser().resolve(strict=False)
    if _inside(output, REPOSITORY_ROOT):
        raise ValueError("trial output must be outside the repository to prevent accidental commit")
    report = output / "report.html"
    if report.exists():
        raise FileExistsError(f"refusing to overwrite existing trial report: {report}")
    return output


def _query_record(path: Path) -> ImageRecord:
    if is_windows_network_path(path):
        raise ValueError("query must be on a local drive, not a UNC or mapped network drive")
    query = path.expanduser().resolve(strict=True)
    if not query.is_file():
        raise ValueError(f"query is not a file: {query}")
    if query.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported query extension: {query.suffix or '(none)'}")
    return ImageRecord(query, query.parent, query.name, query.suffix.lower())


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _coverage_rows(items: list[dict[str, str]], kind: str) -> str:
    if not items:
        return f'<tr><td>{html.escape(kind)}</td><td colspan="2">None</td></tr>'
    rows = []
    for item in items:
        detail = item.get("reason") or item.get("error") or item.get("action") or "reported"
        rows.append(
            "<tr>"
            f"<td>{html.escape(kind)}</td>"
            f"<td class=\"path\">{html.escape(item.get('path', ''))}</td>"
            f"<td>{html.escape(detail)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _candidate_card(candidate: dict[str, Any]) -> str:
    result = candidate["result"]
    diagnostics = result.get("diagnostics", {})
    support = result["status"] == SUPPORTED_STATUS
    label = "Geometrically supported candidate" if support else "Ranked candidate; support conditions not met"
    condition_failures = [name for name, passed in result.get("conditions", {}).items() if not passed]
    failure_text = ", ".join(condition_failures) or result.get("failure_reason") or "none"
    return f"""
    <article class="candidate">
      <h3>Rank {candidate['rank']}: {html.escape(label)}</h3>
      <p class="path">{html.escape(candidate['source_path'])}</p>
      <div class="images">
        <figure><img src="{candidate['thumbnail_data_url']}" alt="Candidate thumbnail"><figcaption>Candidate thumbnail</figcaption></figure>
        <figure><img src="{candidate['overlay_data_url']}" alt="Query and candidate matching-region overlay"><figcaption>Query (left) and candidate (right); green polygon is the estimated query region when available.</figcaption></figure>
      </div>
      <table class="diagnostics">
        <tr><th>Machine classification</th><td>{html.escape(result['status'])}</td></tr>
        <tr><th>Affine inliers</th><td>{result['inliers']}</td></tr>
        <tr><th>Inlier ratio</th><td>{_fmt(result['inlier_ratio'])}</td></tr>
        <tr><th>Query / source coverage</th><td>{_fmt(diagnostics.get('query_coverage'))} / {_fmt(diagnostics.get('source_coverage'))}</td></tr>
        <tr><th>Median reprojection error</th><td>{_fmt(diagnostics.get('median_reprojection_error'))} px</td></tr>
        <tr><th>Mutual correspondences</th><td>{result['mutual_matches']}</td></tr>
        <tr><th>Support conditions not met</th><td>{html.escape(failure_text)}</td></tr>
      </table>
    </article>
    """


def render_report(
    *,
    query_path: Path,
    directory: Path,
    candidates: list[dict[str, Any]],
    coverage: dict[str, Any],
    timing_ms: dict[str, float],
) -> str:
    """Render a self-contained report with no external resources or data submission."""
    candidate_html = "".join(_candidate_card(item) for item in candidates)
    if not candidate_html:
        candidate_html = (
            '<p class="notice">No displayable candidate was produced. This does not establish '
            "that a source is absent.</p>"
        )
    coverage_html = "".join(
        [
            _coverage_rows(coverage.get("unsupported", []), "Unsupported extension"),
            _coverage_rows(coverage.get("errors", []), "Decode/scan error"),
            _coverage_rows(coverage.get("symlinks", []), "Symlink not followed"),
        ]
    )
    total_runtime = timing_ms["total"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research Image Finder — local trial report</title>
  <style>
    body {{ font: 16px/1.45 system-ui, sans-serif; max-width: 1120px; margin: 2rem auto; padding: 0 1rem; color: #17202a; }}
    h1, h2, h3 {{ line-height: 1.2; }}
    .notice {{ border-left: 5px solid #8a5a00; background: #fff7df; padding: .9rem 1rem; }}
    .local {{ border-left-color: #176b46; background: #eaf8f1; }}
    .candidate {{ border-top: 2px solid #d8dde3; padding: 1.2rem 0; }}
    .images {{ display: grid; grid-template-columns: minmax(180px, .7fr) minmax(360px, 2fr); gap: 1rem; align-items: start; }}
    figure {{ margin: 0; }} img {{ width: 100%; height: auto; border: 1px solid #bbc3cc; }}
    figcaption {{ font-size: .85rem; color: #4b5563; }}
    table {{ width: 100%; border-collapse: collapse; margin: .8rem 0; }}
    th, td {{ text-align: left; vertical-align: top; border-bottom: 1px solid #d8dde3; padding: .45rem; }}
    th {{ width: 14rem; }} .path {{ overflow-wrap: anywhere; font-family: ui-monospace, monospace; }}
    label {{ display: block; margin: .7rem 0; }} input, select {{ margin-left: .5rem; }}
    button {{ padding: .6rem .9rem; }}
    @media (max-width: 760px) {{ .images {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>Research Image Finder — Strict Local trial</h1>
  <p class="notice"><strong>Candidates are retrieval suggestions, not provenance conclusions.</strong>
  Machine ranking and geometric support do not confirm that any file is the source.</p>
  <p class="notice"><strong>No candidate does not prove the source is absent.</strong>
  Unsupported formats, weak visual features, transformations, or ranking limits can all hide a relevant file.</p>
  <p class="notice local"><strong>All processing for this Strict Local prototype occurred locally with zero sockets.</strong>
  This report has no external resources and submits no data. It contains local paths and embedded display images; keep or delete it as sensitive local material.</p>

  <h2>Run coverage and timing</h2>
  <table>
    <tr><th>Query</th><td class="path">{html.escape(str(query_path))}</td></tr>
    <tr><th>Selected directory</th><td class="path">{html.escape(str(directory))}</td></tr>
    <tr><th>Supported files discovered</th><td>{coverage['discovered']}</td></tr>
    <tr><th>Files decoded</th><td>{coverage['decoded']}</td></tr>
    <tr><th>Unsupported files</th><td>{len(coverage.get('unsupported', []))}</td></tr>
    <tr><th>Failed files</th><td>{len(coverage.get('errors', []))}</td></tr>
    <tr><th>Returned candidates</th><td>{len(candidates)}</td></tr>
    <tr><th>Algorithm / geometry</th><td>SIFT / affine, exhaustive</td></tr>
    <tr><th>Total runtime</th><td>{total_runtime:.3f} ms</td></tr>
    <tr><th>Search runtime</th><td>{timing_ms['search']:.3f} ms</td></tr>
    <tr><th>Discovery</th><td>{timing_ms['discovery']:.3f} ms</td></tr>
    <tr><th>File decode</th><td>{timing_ms['file_decode']:.3f} ms</td></tr>
    <tr><th>Descriptor extraction</th><td>{timing_ms['descriptor_extraction']:.3f} ms</td></tr>
    <tr><th>Pair matching</th><td>{timing_ms['pair_matching']:.3f} ms</td></tr>
    <tr><th>Geometric support</th><td>{timing_ms['geometric_verification']:.3f} ms</td></tr>
    <tr><th>Report image rendering</th><td>{timing_ms['overlay_rendering']:.3f} ms</td></tr>
  </table>

  <h2>Top {len(candidates)} ranked candidates</h2>
  {candidate_html}

  <h2>Coverage and errors</h2>
  <p>Unsupported files, decode failures, and skipped symlinks are explicit; none is silently treated as searched image content.</p>
  <table><tr><th>Kind</th><th>Path</th><th>Coverage result</th></tr>{coverage_html}</table>

  <h2>Human trial record</h2>
  <p>Only human review can confirm a source. “Not found” records that this review stopped without confirmation; it is not an absence claim.
  Nothing is transmitted or saved automatically. The button downloads only aggregate fields and excludes all paths and images.</p>
  <form id="trial-form">
    <label>Directory image count <input id="directory-count" type="number" readonly value="{coverage['discovered']}"></label>
    <label>Total runtime (ms) <input id="runtime" type="number" readonly value="{total_runtime:.3f}"></label>
    <label>Correct source rank, if known <input id="correct-rank" type="number" min="1" step="1"></label>
    <label>Candidates inspected before decision <input id="inspected" type="number" min="0" step="1" required></label>
    <label>Time to decision (seconds) <input id="confirmation-time" type="number" min="0" step="0.1" required></label>
    <label>Human outcome
      <select id="outcome" required>
        <option value="">Choose…</option>
        <option value="confirmed">Confirmed by human reviewer</option>
        <option value="not_found">Not found in inspected candidates</option>
        <option value="unsure">Unsure</option>
      </select>
    </label>
    <button type="submit">Download aggregate trial record</button>
  </form>
  <script>
    'use strict';
    const trialStarted = performance.now();
    const seconds = document.getElementById('confirmation-time');
    const timer = setInterval(() => {{ if (document.activeElement !== seconds) seconds.value = ((performance.now() - trialStarted) / 1000).toFixed(1); }}, 500);
    document.getElementById('trial-form').addEventListener('submit', (event) => {{
      event.preventDefault(); clearInterval(timer);
      const rankText = document.getElementById('correct-rank').value;
      const record = {{
        discovered_image_count: Number(document.getElementById('directory-count').value),
        decoded_image_count: {coverage['decoded']},
        unsupported_file_count: {len(coverage.get('unsupported', []))},
        failed_file_count: {len(coverage.get('errors', []))},
        total_runtime_ms: Number(document.getElementById('runtime').value),
        search_runtime_ms: {timing_ms['search']:.3f},
        candidate_count: {len(candidates)},
        correct_source_rank: rankText === '' ? null : Number(rankText),
        candidates_inspected_before_confirmation: Number(document.getElementById('inspected').value),
        time_to_confirmation_seconds: Number(seconds.value),
        outcome: document.getElementById('outcome').value
      }};
      const blob = new Blob([JSON.stringify(record, null, 2)], {{type: 'application/json'}});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob); link.download = 'image_finder_trial_record.json'; link.click();
      URL.revokeObjectURL(link.href);
    }});
  </script>
</body>
</html>
"""


def search_trial(query_path: Path, directory: Path, top_n: int = 10) -> dict[str, Any]:
    """Run the frozen retrieval baseline entirely in memory under a zero-socket guard."""
    if top_n not in {10, 20}:
        raise ValueError("top_n must be 10 or 20")
    query_record = _query_record(query_path)
    selected_directory = directory.expanduser().resolve(strict=True)

    with zero_socket_guard():
        total_started = time.perf_counter()
        discovery_started = time.perf_counter()
        source_records, coverage = discover_images(selected_directory)
        discovery_ms = (time.perf_counter() - discovery_started) * 1000

        decode_started = time.perf_counter()
        query_gray, decoded_query = decode_image(query_record)
        query_decode_ms = (time.perf_counter() - decode_started) * 1000
        if query_gray is None:
            raise ValueError(f"query decode failed: {decoded_query.error}")

        descriptor_started = time.perf_counter()
        query_features = prepare_features(query_gray, "sift")
        query_descriptor_ms = (time.perf_counter() - descriptor_started) * 1000

        prepared: list[tuple[ImageRecord, Any, dict[str, Any]]] = []
        source_decode_ms = 0.0
        source_descriptor_ms = 0.0
        for record in source_records:
            started = time.perf_counter()
            source_gray, decoded = decode_image(record)
            source_decode_ms += (time.perf_counter() - started) * 1000
            if source_gray is None:
                coverage.errors.append({"path": str(record.path), "error": decoded.error or "decode failed"})
                continue
            started = time.perf_counter()
            source_features = prepare_features(source_gray, "sift")
            source_descriptor_ms += (time.perf_counter() - started) * 1000
            prepared.append((decoded, source_gray, source_features))
        coverage.decoded = len(prepared)

        config = VerificationConfig(**{**HARDENED_CONFIG.__dict__, "transform_model": "affine"})
        results: list[tuple[dict[str, Any], ImageRecord, Any]] = []
        for source_record, source_gray, source_features in prepared:
            result = match_prepared(
                query_features,
                source_features,
                "sift",
                {"digest": decoded_query.digest},
                {"digest": source_record.digest},
                config,
            )
            results.append((result, source_record, source_gray))
        results.sort(
            key=lambda item: (
                item[0]["status"] != SUPPORTED_STATUS,
                -item[0]["score"],
                -item[0]["inliers"],
                -item[0]["mutual_matches"],
                item[1].digest or "",
            )
        )
        search_ms = (time.perf_counter() - total_started) * 1000

        render_started = time.perf_counter()
        candidates = []
        for rank, (result, source_record, source_gray) in enumerate(results[:top_n], start=1):
            candidates.append(
                {
                    "rank": rank,
                    "source_filename": source_record.path.name,
                    "source_path": str(source_record.path),
                    "result": result,
                    "thumbnail_data_url": png_data_url(render_thumbnail_png(source_gray)),
                    "overlay_data_url": png_data_url(render_overlay_png(query_gray, source_gray, result)),
                }
            )
        overlay_ms = (time.perf_counter() - render_started) * 1000
        pair_ms = sum(item[0]["timing_ms"]["pair_matching"] for item in results)
        geometry_ms = sum(item[0]["timing_ms"]["geometric_verification"] for item in results)
        total_ms = (time.perf_counter() - total_started) * 1000
        timing_ms = {
            "discovery": round(discovery_ms, 3),
            "file_decode": round(query_decode_ms + source_decode_ms, 3),
            "descriptor_extraction": round(query_descriptor_ms + source_descriptor_ms, 3),
            "pair_matching": round(pair_ms, 3),
            "geometric_verification": round(geometry_ms, 3),
            "overlay_rendering": round(overlay_ms, 3),
            "search": round(search_ms, 3),
            "total": round(total_ms, 3),
        }
    return {
        "query_path": query_record.path,
        "directory": selected_directory,
        "coverage": coverage.as_dict(),
        "candidates": candidates,
        "timing_ms": timing_ms,
        "telemetry": {
            "discovered_image_count": coverage.discovered,
            "decoded_image_count": coverage.decoded,
            "unsupported_file_count": len(coverage.unsupported),
            "failed_file_count": len(coverage.errors),
            "total_runtime_ms": timing_ms["total"],
            "search_runtime_ms": timing_ms["search"],
            "candidate_count": len(candidates),
            "geometrically_supported_candidate_count": sum(
                item["result"]["status"] == SUPPORTED_STATUS for item in candidates
            ),
            "user_confirmation_outcome": None,
        },
    }


def write_trial_report(search_result: dict[str, Any], output_dir: Path) -> Path:
    """Write an explicitly requested local report; no other trial artifact is persisted."""
    output = _validate_output(output_dir)
    report_html = render_report(
        query_path=search_result["query_path"],
        directory=search_result["directory"],
        candidates=search_result["candidates"],
        coverage=search_result["coverage"],
        timing_ms=search_result["timing_ms"],
    )
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "report.html"
    report_path.write_text(report_html, encoding="utf-8")
    return report_path


def run_trial(query_path: Path, directory: Path, output_dir: Path, top_n: int = 10) -> dict[str, Any]:
    """Run retrieval and write the command-line trial's explicitly requested local report."""
    search_result = search_trial(query_path, directory, top_n)
    report_path = write_trial_report(search_result, output_dir)
    return {
        "report": str(report_path),
        "directory_image_count": search_result["telemetry"]["discovered_image_count"],
        "decoded_image_count": search_result["telemetry"]["decoded_image_count"],
        "candidate_count": search_result["telemetry"]["candidate_count"],
        "geometrically_supported_candidate_count": search_result["telemetry"][
            "geometrically_supported_candidate_count"
        ],
        "timing_ms": search_result["timing_ms"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a disposable Strict Local image retrieval trial")
    parser.add_argument("query", type=Path, help="one PNG, JPEG, or supported TIFF query image")
    parser.add_argument("directory", type=Path, help="one explicitly selected local directory")
    parser.add_argument("--top-n", type=int, choices=(10, 20), default=10)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="report directory outside the repository (default: /private/tmp with timestamp)",
    )
    args = parser.parse_args()
    output = args.output or Path("/private/tmp") / f"image_finder_trial_{time.strftime('%Y%m%d_%H%M%S')}"
    try:
        summary = run_trial(args.query, args.directory, output, args.top_n)
    except (FileNotFoundError, NotADirectoryError, OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
