from __future__ import annotations

import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_finder.core import (
    decode_image,
    discover_images,
    is_windows_network_path,
    match_pair,
    write_overlay,
)
from run_microscopy_trial_slice import EVIDENCE_SCOPE, evaluate_slice
from run_trial import REPOSITORY_ROOT, run_trial, search_trial
from windows_trial_support import build_trial_record, open_in_windows_explorer


def textured() -> np.ndarray:
    image = np.zeros((180, 240), dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (220, 160), 140, 3)
    for x in range(35, 220, 23):
        cv2.circle(image, (x, 65 + (x % 31)), 9, 220, -1)
    cv2.putText(image, "SOURCE 17", (30, 145), cv2.FONT_HERSHEY_SIMPLEX, .8, 255, 2)
    return image


class SpikeTests(unittest.TestCase):
    def test_strict_local_zero_socket_for_discovery_decode_and_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            query = root / "query.png"
            Image.fromarray(textured()).save(query)
            records, _ = discover_images(root)
            original = socket.socket
            def denied(*args, **kwargs):
                raise AssertionError("socket attempted in Strict Local spike")
            socket.socket = denied
            try:
                record = next(item for item in records if item.path.resolve() == query.resolve())
                gray, decoded = decode_image(record)
                self.assertEqual(decoded.status, "decoded")
                result = match_pair(gray, gray, "orb")
                self.assertEqual(result["status"], "geometrically_supported_candidate")
            finally:
                socket.socket = original

    def test_selected_root_and_symlink_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "selected"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            Image.fromarray(textured()).save(root / "inside.jpg")
            Image.fromarray(textured()).save(outside / "outside.png")
            try:
                (root / "link_inside.png").symlink_to(root / "inside.jpg")
                (root / "link_outside.png").symlink_to(outside / "outside.png")
            except OSError as exc:
                self.skipTest(f"symlink creation is unavailable on this Windows setup: {exc}")
            records, coverage = discover_images(root)
            self.assertEqual([r.relative_path for r in records], ["inside.jpg"])
            actions = {item["action"] for item in coverage.symlinks}
            self.assertEqual(actions, {"not_followed", "out_of_scope_rejected"})

    def test_windows_junction_cannot_be_selected_as_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("image_finder.core.os.path.isjunction", return_value=True, create=True):
                with self.assertRaisesRegex(ValueError, "symlink or Windows junction"):
                    discover_images(tmp)

    def test_windows_unc_paths_are_rejected_without_access(self):
        self.assertTrue(is_windows_network_path(Path(r"\\server\research\images")))

    def test_unsupported_tiff_variant_is_explicit_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "multipage.tiff"
            with Image.new("L", (32, 32), 0) as first, Image.new("L", (32, 32), 1) as second:
                first.save(path, save_all=True, append_images=[second], format="TIFF")
            records, coverage = discover_images(root)
            gray, decoded = decode_image(records[0])
            self.assertIsNone(gray)
            self.assertEqual(decoded.status, "error")
            self.assertIn("unsupported TIFF variant", decoded.error)
            self.assertEqual(coverage.discovered, 1)

    def test_overlay_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            query = textured()
            result = match_pair(query, query, "sift")
            path = Path(tmp) / "overlay.png"
            write_overlay(query, query, result, path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 100)

    def test_trial_report_is_local_retrieval_output_with_human_only_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            query = root / "query.png"
            directory = root / "selected"
            output = root / "report-output"
            directory.mkdir()
            Image.fromarray(textured()).save(query)
            Image.fromarray(textured()).save(directory / "known-source.png")
            Image.fromarray(np.rot90(textured()).copy()).save(directory / "other.jpg")
            (directory / "unsupported.bmp").write_bytes(b"not scanned")
            with Image.new("L", (16, 16), 0) as first, Image.new("L", (16, 16), 1) as second:
                first.save(
                    directory / "unsupported-variant.tiff",
                    save_all=True,
                    append_images=[second],
                    format="TIFF",
                )

            summary = run_trial(query, directory, output, top_n=10)
            report = Path(summary["report"]).read_text(encoding="utf-8")
            self.assertEqual(summary["directory_image_count"], 3)
            self.assertIn("Candidates are retrieval suggestions, not provenance conclusions.", report)
            self.assertIn("No candidate does not prove the source is absent.", report)
            self.assertIn(
                "All processing for this Strict Local prototype occurred locally with zero sockets.",
                report,
            )
            self.assertIn("geometrically_supported_candidate", report)
            self.assertIn(str((directory / "known-source.png").resolve()), report)
            self.assertIn("unsupported.bmp", report)
            self.assertIn("unsupported-variant.tiff", report)
            self.assertIn("data:image/png;base64,", report)
            self.assertIn("candidates_inspected_before_confirmation", report)
            self.assertIn("time_to_confirmation_seconds", report)
            self.assertNotIn('"confirmed_source"', report)
            self.assertNotIn("https://", report)
            self.assertNotIn("http://", report)
            self.assertIn("Search runtime", report)
            self.assertIn("Unsupported files", report)

    def test_trial_refuses_output_inside_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            query = root / "query.png"
            directory = root / "selected"
            directory.mkdir()
            Image.fromarray(textured()).save(query)
            Image.fromarray(textured()).save(directory / "source.png")
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                run_trial(query, directory, REPOSITORY_ROOT / "forbidden-trial-output", top_n=10)

    def test_in_memory_search_telemetry_and_saved_record_exclude_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            query = root / "query.png"
            directory = root / "selected"
            directory.mkdir()
            Image.fromarray(textured()).save(query)
            Image.fromarray(textured()).save(directory / "source.png")
            (directory / "notes.txt").write_text("unsupported", encoding="utf-8")
            result = search_trial(query, directory, top_n=10)
            telemetry = result["telemetry"]
            self.assertEqual(telemetry["discovered_image_count"], 1)
            self.assertEqual(telemetry["decoded_image_count"], 1)
            self.assertEqual(telemetry["unsupported_file_count"], 1)
            self.assertEqual(telemetry["candidate_count"], 1)
            self.assertIsNone(telemetry["user_confirmation_outcome"])
            record = build_trial_record(
                result,
                outcome="confirmed",
                correct_source_rank=1,
                candidates_inspected=1,
                time_to_confirmation_seconds=3.2,
            )
            serialized = str(record)
            self.assertEqual(record["user_confirmation_outcome"], "confirmed")
            self.assertNotIn(str(root), serialized)
            self.assertNotIn("source.png", serialized)

    def test_windows_explorer_selection_rechecks_selected_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "selected"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            source = root / "candidate.png"
            other = outside / "other.png"
            Image.fromarray(textured()).save(source)
            Image.fromarray(textured()).save(other)
            calls = []
            open_in_windows_explorer(source, root, launcher=lambda arguments: calls.append(arguments))
            self.assertEqual(calls, [["explorer.exe", "/select,", str(source.resolve())]])
            with self.assertRaisesRegex(ValueError, "outside the selected search root"):
                open_in_windows_explorer(other, root, launcher=lambda arguments: calls.append(arguments))

    def test_synthetic_microscopy_trial_slice_is_explicitly_non_field_evidence(self):
        for kind in ("brightfield", "immunofluorescence"):
            result = evaluate_slice(kind, source_count=6)
            self.assertEqual(result["evidence_scope"], EVIDENCE_SCOPE)
            self.assertTrue(result["top5_recovery"])
            self.assertLessEqual(result["target_rank"], 5)


if __name__ == "__main__":
    unittest.main()
