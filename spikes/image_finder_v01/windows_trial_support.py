"""Testable, non-GUI helpers for the disposable Windows trial shell."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from run_trial import REPOSITORY_ROOT

OUTCOME_LABELS = {
    "": "",
    "confirmed": "Confirmed by human reviewer",
    "not_found": "Not found in inspected candidates",
    "unsure": "Unsure",
}
OUTCOME_CODES = {label: code for code, label in OUTCOME_LABELS.items()}


def _within_selected_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def open_in_windows_explorer(
    source_path: str | Path,
    selected_root: str | Path,
    launcher: Callable[..., Any] = subprocess.Popen,
) -> None:
    """Open Explorer on a discovered candidate without invoking a shell."""
    source = Path(source_path).resolve(strict=True)
    root = Path(selected_root).resolve(strict=True)
    if not _within_selected_root(source, root):
        raise ValueError("candidate is outside the selected search root")
    launcher(["explorer.exe", "/select,", str(source)])


def build_trial_record(
    search_result: dict[str, Any],
    *,
    outcome: str,
    correct_source_rank: int | None,
    candidates_inspected: int | None,
    time_to_confirmation_seconds: float | None,
) -> dict[str, Any]:
    """Build path-free local telemetry; callers decide whether to persist it."""
    if outcome not in {"", "confirmed", "not_found", "unsure"}:
        raise ValueError("unknown human confirmation outcome")
    telemetry = search_result["telemetry"]
    return {
        "discovered_image_count": telemetry["discovered_image_count"],
        "decoded_image_count": telemetry["decoded_image_count"],
        "unsupported_file_count": telemetry["unsupported_file_count"],
        "failed_file_count": telemetry["failed_file_count"],
        "total_runtime_ms": telemetry["total_runtime_ms"],
        "search_runtime_ms": telemetry["search_runtime_ms"],
        "candidate_count": telemetry["candidate_count"],
        "user_confirmation_outcome": outcome or None,
        "correct_source_rank": correct_source_rank,
        "candidates_inspected_before_confirmation": candidates_inspected,
        "time_to_confirmation_seconds": time_to_confirmation_seconds,
    }


def write_trial_record(record: dict[str, Any], output_path: str | Path) -> Path:
    """Persist aggregate telemetry only after an explicit save action."""
    path = Path(output_path).expanduser().resolve(strict=False)
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError:
        pass
    else:
        raise ValueError("trial records must be saved outside the repository")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path
