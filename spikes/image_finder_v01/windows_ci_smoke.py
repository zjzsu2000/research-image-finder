#!/usr/bin/env python3
"""Non-interactive Windows CI smoke test for the disposable GUI trial."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from image_finder.core import is_windows_network_path  # noqa: E402
from run_windows_gui import noninteractive_gui_smoke_test  # noqa: E402
from windows_trial_support import open_in_windows_explorer  # noqa: E402


def main() -> int:
    if os.name != "nt" or sys.platform != "win32":
        raise RuntimeError("windows_ci_smoke.py must run on Windows")

    gui_result = noninteractive_gui_smoke_test()
    if not is_windows_network_path(Path(r"\\server\research\images")):
        raise AssertionError("UNC root was not classified as a network path")

    with tempfile.TemporaryDirectory(prefix="image_finder_windows_smoke_") as tmp:
        root = Path(tmp) / "selected"
        outside = Path(tmp) / "outside"
        root.mkdir()
        outside.mkdir()
        candidate = root / "candidate.png"
        other = outside / "other.png"
        candidate.write_bytes(b"smoke")
        other.write_bytes(b"smoke")
        calls: list[list[str]] = []
        open_in_windows_explorer(candidate, root, launcher=lambda arguments: calls.append(arguments))
        expected = [["explorer.exe", "/select,", str(candidate.resolve())]]
        if calls != expected:
            raise AssertionError(f"unexpected Explorer command: {calls!r}")
        try:
            open_in_windows_explorer(other, root, launcher=lambda arguments: calls.append(arguments))
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-root Explorer selection was not rejected")

    print(
        json.dumps(
            {
                "status": "ok",
                "gui": gui_result,
                "explorer_command": expected[0][:2] + ["<selected-root-candidate>"],
                "unc_rejected": True,
                "scope": "windows_ci_noninteractive_only_not_interactive_user_validation",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
