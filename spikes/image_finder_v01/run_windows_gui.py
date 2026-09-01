#!/usr/bin/env python3
"""Minimal Windows-oriented Tkinter shell for the disposable Image Finder trial."""
from __future__ import annotations

import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_trial import SUPPORTED_STATUS, search_trial, write_trial_report, zero_socket_guard  # noqa: E402
from windows_trial_support import (  # noqa: E402
    OUTCOME_CODES,
    OUTCOME_LABELS,
    build_trial_record,
    open_in_windows_explorer,
    write_trial_record,
)


class WindowsTrialApp:
    """Small trial UI; all retrieval remains in memory unless the user explicitly saves."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Research Image Finder — Strict Local trial")
        self.root.geometry("1080x820")
        self.result: dict[str, Any] | None = None
        self.review_started: float | None = None
        self.worker_messages: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.photos: list[tk.PhotoImage] = []

        self.query_var = tk.StringVar()
        self.directory_var = tk.StringVar()
        self.top_n_var = tk.StringVar(value="10")
        self.status_var = tk.StringVar(value="Choose one query image and one search folder or drive.")
        self.summary_var = tk.StringVar(value="No search has run.")
        self.outcome_var = tk.StringVar()
        self.rank_var = tk.StringVar()
        self.inspected_var = tk.StringVar()
        self.confirmation_time_var = tk.StringVar()

        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        warning = (
            "Ranked candidates are retrieval suggestions, not provenance conclusions. "
            "No candidate does not prove the source is absent. Confirmed provenance is a human action only. "
            "This Strict Local prototype uses zero sockets; unpublished/raw images are not uploaded."
        )
        ttk.Label(outer, text=warning, wraplength=1020, foreground="#7a4b00").pack(fill="x", pady=(0, 10))

        inputs = ttk.LabelFrame(outer, text="Local search", padding=8)
        inputs.pack(fill="x")
        inputs.columnconfigure(1, weight=1)
        ttk.Label(inputs, text="Query image").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(inputs, textvariable=self.query_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(inputs, text="Choose image…", command=self._choose_query).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Label(inputs, text="Search folder / drive").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(inputs, textvariable=self.directory_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(inputs, text="Choose folder…", command=self._choose_directory).grid(row=1, column=2, padx=(8, 0), pady=4)
        ttk.Label(inputs, text="Results").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(inputs, textvariable=self.top_n_var, values=("10", "20"), state="readonly", width=6).grid(row=2, column=1, sticky="w", pady=4)
        self.start_button = ttk.Button(inputs, text="Start Search", command=self._start_search)
        self.start_button.grid(row=2, column=2, padx=(8, 0), pady=4)

        status_row = ttk.Frame(outer)
        status_row.pack(fill="x", pady=8)
        self.progress = ttk.Progressbar(status_row, mode="indeterminate", length=180)
        self.progress.pack(side="left")
        ttk.Label(status_row, textvariable=self.status_var).pack(side="left", padx=10)

        ttk.Label(outer, textvariable=self.summary_var, wraplength=1020).pack(fill="x")
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(5, 8))
        self.coverage_button = ttk.Button(actions, text="Coverage / errors…", command=self._show_coverage, state="disabled")
        self.coverage_button.pack(side="left")
        self.report_button = ttk.Button(actions, text="Save local HTML report…", command=self._save_report, state="disabled")
        self.report_button.pack(side="left", padx=8)

        trial = ttk.LabelFrame(outer, text="Optional local human trial record (not saved automatically)", padding=8)
        trial.pack(fill="x", pady=(0, 8))
        ttk.Label(trial, text="Outcome").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            trial,
            textvariable=self.outcome_var,
            values=tuple(label for label in OUTCOME_LABELS.values() if label),
            state="readonly",
            width=34,
        ).grid(row=0, column=1, sticky="w", padx=(5, 14))
        ttk.Label(trial, text="Correct rank (if known)").grid(row=0, column=2, sticky="w")
        ttk.Entry(trial, textvariable=self.rank_var, width=7).grid(row=0, column=3, padx=(5, 14))
        ttk.Label(trial, text="Candidates inspected").grid(row=0, column=4, sticky="w")
        ttk.Entry(trial, textvariable=self.inspected_var, width=7).grid(row=0, column=5, padx=(5, 14))
        ttk.Label(trial, text="Decision time (s)").grid(row=0, column=6, sticky="w")
        ttk.Entry(trial, textvariable=self.confirmation_time_var, width=9).grid(row=0, column=7, padx=5)
        self.record_button = ttk.Button(trial, text="Save aggregate record…", command=self._save_record, state="disabled")
        self.record_button.grid(row=0, column=8, padx=(12, 0))

        result_host = ttk.Frame(outer)
        result_host.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(result_host, highlightthickness=0)
        scrollbar = ttk.Scrollbar(result_host, orient="vertical", command=self.canvas.yview)
        self.candidate_frame = ttk.Frame(self.canvas)
        self.candidate_frame.bind(
            "<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.candidate_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _choose_query(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose one query image",
            filetypes=[("Supported images", "*.png *.jpg *.jpeg *.tif *.tiff"), ("All files", "*.*")],
        )
        if selected:
            self.query_var.set(selected)

    def _choose_directory(self) -> None:
        selected = filedialog.askdirectory(title="Choose one folder or drive to search", mustexist=True)
        if selected:
            self.directory_var.set(selected)

    def _start_search(self) -> None:
        if not self.query_var.get().strip() or not self.directory_var.get().strip():
            messagebox.showerror("Missing selection", "Choose one query image and one search folder or drive.")
            return
        self._clear_candidates()
        self.result = None
        self.start_button.configure(state="disabled")
        self.coverage_button.configure(state="disabled")
        self.report_button.configure(state="disabled")
        self.record_button.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Searching recursively under the selected root…")
        worker = threading.Thread(
            target=self._search_worker,
            args=(Path(self.query_var.get()), Path(self.directory_var.get()), int(self.top_n_var.get())),
            daemon=True,
        )
        worker.start()
        self.root.after(100, self._poll_worker)

    def _search_worker(self, query: Path, directory: Path, top_n: int) -> None:
        try:
            self.worker_messages.put(("result", search_trial(query, directory, top_n)))
        except Exception as exc:  # the main thread presents filesystem/decode failures to the user
            self.worker_messages.put(("error", exc))

    def _poll_worker(self) -> None:
        try:
            kind, payload = self.worker_messages.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_worker)
            return
        self.progress.stop()
        self.start_button.configure(state="normal")
        if kind == "error":
            self.status_var.set("Search failed.")
            messagebox.showerror("Search failed", str(payload))
            return
        self.result = payload
        self.review_started = time.perf_counter()
        self.coverage_button.configure(state="normal")
        self.report_button.configure(state="normal")
        self.record_button.configure(state="normal")
        self._display_result(payload)

    def _display_result(self, result: dict[str, Any]) -> None:
        telemetry = result["telemetry"]
        self.status_var.set("Search complete. Review candidates manually.")
        self.summary_var.set(
            f"Discovered {telemetry['discovered_image_count']} supported files; "
            f"decoded {telemetry['decoded_image_count']}; unsupported {telemetry['unsupported_file_count']}; "
            f"failed {telemetry['failed_file_count']}; returned {telemetry['candidate_count']} candidates. "
            f"Search {telemetry['search_runtime_ms'] / 1000:.2f}s; total {telemetry['total_runtime_ms'] / 1000:.2f}s."
        )
        self.photos = []
        for candidate in result["candidates"]:
            self._add_candidate(candidate)

    @staticmethod
    def _photo(data_url: str) -> tk.PhotoImage:
        return tk.PhotoImage(data=data_url.split(",", 1)[1])

    def _add_candidate(self, candidate: dict[str, Any]) -> None:
        frame = ttk.LabelFrame(
            self.candidate_frame,
            text=f"Rank {candidate['rank']} — {candidate['source_filename']}",
            padding=8,
        )
        frame.pack(fill="x", pady=6)
        result = candidate["result"]
        support = result["status"] == SUPPORTED_STATUS
        label = "Geometrically supported candidate" if support else "Ranked candidate; support conditions not met"
        ttk.Label(frame, text=label, foreground="#176b46" if support else "#555555").pack(anchor="w")
        ttk.Label(frame, text=candidate["source_path"], wraplength=1000).pack(anchor="w", pady=(2, 6))

        images = ttk.Frame(frame)
        images.pack(fill="x")
        thumbnail = self._photo(candidate["thumbnail_data_url"])
        overlay = self._photo(candidate["overlay_data_url"])
        self.photos.extend([thumbnail, overlay])
        ttk.Label(images, image=thumbnail).pack(side="left", anchor="n", padx=(0, 10))
        ttk.Label(images, image=overlay).pack(side="left", anchor="n")

        diagnostics = result.get("diagnostics", {})
        text = (
            f"Affine inliers {result['inliers']} | inlier ratio {result['inlier_ratio']:.3f} | "
            f"query/source coverage {diagnostics.get('query_coverage', 0):.3f}/"
            f"{diagnostics.get('source_coverage', 0):.3f} | "
            f"median reprojection error {diagnostics.get('median_reprojection_error', 0):.3f}px"
        )
        ttk.Label(frame, text=text, wraplength=1000).pack(anchor="w", pady=5)
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w")
        ttk.Button(
            buttons,
            text="Open containing folder",
            command=lambda item=candidate: self._open_candidate(item),
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Human: confirm this source",
            command=lambda item=candidate: self._confirm_candidate(item),
        ).pack(side="left", padx=8)

    def _open_candidate(self, candidate: dict[str, Any]) -> None:
        assert self.result is not None
        try:
            open_in_windows_explorer(candidate["source_path"], self.result["directory"])
        except (FileNotFoundError, OSError, ValueError) as exc:
            messagebox.showerror("Could not open Explorer", str(exc))

    def _confirm_candidate(self, candidate: dict[str, Any]) -> None:
        self.outcome_var.set(OUTCOME_LABELS["confirmed"])
        self.rank_var.set(str(candidate["rank"]))
        self.inspected_var.set(str(candidate["rank"]))
        if self.review_started is not None:
            self.confirmation_time_var.set(f"{time.perf_counter() - self.review_started:.1f}")
        self.status_var.set(f"Human reviewer marked rank {candidate['rank']} as confirmed.")

    def _show_coverage(self) -> None:
        if self.result is None:
            return
        window = tk.Toplevel(self.root)
        window.title("Coverage and errors")
        text = tk.Text(window, width=120, height=32, wrap="word")
        text.pack(fill="both", expand=True)
        coverage = self.result["coverage"]
        sections = (
            ("Unsupported extensions", coverage.get("unsupported", [])),
            ("Decode / scan failures", coverage.get("errors", [])),
            ("Symlinks not followed", coverage.get("symlinks", [])),
        )
        for title, items in sections:
            text.insert("end", f"{title} ({len(items)})\n")
            if not items:
                text.insert("end", "  None\n")
            for item in items:
                detail = item.get("reason") or item.get("error") or item.get("action") or "reported"
                text.insert("end", f"  {item.get('path', '')}\n    {detail}\n")
            text.insert("end", "\n")
        text.configure(state="disabled")

    def _save_report(self) -> None:
        if self.result is None:
            return
        output = filedialog.askdirectory(title="Choose a local folder for report.html", mustexist=True)
        if not output:
            return
        try:
            path = write_trial_report(self.result, Path(output))
        except (FileExistsError, OSError, ValueError) as exc:
            messagebox.showerror("Could not save report", str(exc))
            return
        messagebox.showinfo("Report saved", f"Sensitive local report saved to:\n{path}")

    @staticmethod
    def _optional_int(value: str) -> int | None:
        return int(value) if value.strip() else None

    @staticmethod
    def _optional_float(value: str) -> float | None:
        return float(value) if value.strip() else None

    def _save_record(self) -> None:
        if self.result is None:
            return
        output = filedialog.asksaveasfilename(
            title="Save path-free aggregate trial record",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="image_finder_trial_record.json",
        )
        if not output:
            return
        try:
            outcome = OUTCOME_CODES.get(self.outcome_var.get(), "")
            record = build_trial_record(
                self.result,
                outcome=outcome,
                correct_source_rank=self._optional_int(self.rank_var.get()),
                candidates_inspected=self._optional_int(self.inspected_var.get()),
                time_to_confirmation_seconds=self._optional_float(self.confirmation_time_var.get()),
            )
            path = write_trial_record(record, output)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save record", str(exc))
            return
        messagebox.showinfo("Record saved", f"Path-free aggregate record saved to:\n{path}")

    def _clear_candidates(self) -> None:
        for child in self.candidate_frame.winfo_children():
            child.destroy()
        self.photos = []


def noninteractive_gui_smoke_test() -> dict[str, str]:
    """Initialize bundled Tcl and GUI symbols without requiring a desktop or opening a window."""
    with zero_socket_guard():
        interpreter = tk.Tcl()
        patchlevel = str(interpreter.eval("info patchlevel"))
        if not patchlevel:
            raise RuntimeError("Tkinter Tcl interpreter did not initialize")
        if WindowsTrialApp.__name__ != "WindowsTrialApp":
            raise RuntimeError("Windows GUI module did not initialize")
    return {
        "status": "ok",
        "tcl_patchlevel": patchlevel,
        "scope": "noninteractive_module_and_bundle_smoke_only",
    }


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--ci-smoke-test"]:
        try:
            result = noninteractive_gui_smoke_test()
        except Exception as exc:
            if sys.stderr is not None:
                print(f"non-interactive GUI smoke failed: {exc}", file=sys.stderr)
            return 1
        if sys.stdout is not None:
            print(json.dumps(result, sort_keys=True))
        return 0
    if arguments:
        raise SystemExit(f"unknown arguments: {' '.join(arguments)}")
    root = tk.Tk()
    WindowsTrialApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
