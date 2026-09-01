#!/usr/bin/env python3
"""Run the Verification Hardening Spike on synthetic positives and hard negatives."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from image_finder.core import (HARDENED_CONFIG, decode_image, discover_images,
                               match_prepared, prepare_features, write_overlay,
                               VerificationConfig)
from run_benchmark import make_source, save_image


def hard_negative(seed: int, kind: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    image = np.full((180, 240, 3), 245, dtype=np.uint8)
    if kind == "repeated_texture":
        for y in range(10, 180, 20):
            for x in range(10, 240, 20):
                cv2.circle(image, (x + (y % 9), y), 6, (70 + seed % 20,) * 3, -1)
    elif kind == "plot_grid_axes":
        for x in range(20, 240, 20): cv2.line(image, (x, 15), (x, 165), (180, 180, 180), 1)
        for y in range(25, 166, 20): cv2.line(image, (15, y), (230, y), (180, 180, 180), 1)
        cv2.line(image, (15, 165), (230, 165), (20, 20, 20), 3)
        cv2.line(image, (15, 15), (15, 165), (20, 20, 20), 3)
    elif kind == "text_heavy":
        for line in range(9):
            cv2.putText(image, f"control measurement {seed}-{line}", (8, 22 + line * 17),
                        cv2.FONT_HERSHEY_SIMPLEX, .42, (20, 20, 20), 1)
    elif kind == "generic_blot_strip":
        image[:] = 232
        for x in range(18, 238, 28):
            cv2.rectangle(image, (x, 18), (x + 14, 160), (210, 210, 210), -1)
            for y in (45, 80, 120): cv2.ellipse(image, (x + 7, y), (6, 3), 0, 0, 360, (30, 30, 30), -1)
    elif kind == "blank_background":
        image[:] = 205
        for _ in range(6):
            x, y = int(rng.integers(10, 230)), int(rng.integers(10, 170))
            cv2.circle(image, (x, y), 2, (208, 208, 208), -1)
    elif kind == "nearby_microscopy":
        image = make_source(seed + 4000, "microscopy")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


HARD_KINDS = ("repeated_texture", "plot_grid_axes", "text_heavy", "generic_blot_strip",
              "blank_background", "nearby_microscopy")


def make_hard_directory(root: Path, count: int = 120) -> Path:
    directory = root / "hard_negative_sources"
    directory.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        kind = HARD_KINDS[index % len(HARD_KINDS)]
        extension = (".png", ".jpg", ".tif")[index % 3]
        save_image(directory / f"source_{index:04d}_{kind}{extension}", hard_negative(index, kind), extension)
    return directory


def write_query(root: Path, name: str, image: np.ndarray) -> Path:
    path = root / "queries" / f"query_{name}.png"
    save_image(path, image, ".png")
    return path


def decode_and_prepare(records, algorithm):
    decode_ms = 0.0
    descriptor_ms = 0.0
    prepared = []
    for record in records:
        start = time.perf_counter()
        gray, decoded = decode_image(record)
        decode_ms += (time.perf_counter() - start) * 1000
        if gray is None:
            continue
        start = time.perf_counter()
        prepared.append((decoded, prepare_features(gray, algorithm)))
        descriptor_ms += (time.perf_counter() - start) * 1000
    return prepared, decode_ms, descriptor_ms


def search(query_path, directory, algorithm, model, output, target_digest=None, slice_name="unknown", split="heldout"):
    discovery_start = time.perf_counter()
    query_records, _ = discover_images(query_path.parent)
    source_records, coverage = discover_images(directory)
    discovery_ms = (time.perf_counter() - discovery_start) * 1000
    query_record = next(r for r in query_records if r.path.resolve() == query_path.resolve())
    start = time.perf_counter()
    query_gray, query_record = decode_image(query_record)
    query_decode_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    query_features = prepare_features(query_gray, algorithm)
    query_descriptor_ms = (time.perf_counter() - start) * 1000
    prepared, decode_ms, descriptor_ms = decode_and_prepare(source_records, algorithm)
    config = VerificationConfig(**{**HARDENED_CONFIG.__dict__, "transform_model": model})
    results = []
    for record, features in prepared:
        results.append(match_prepared(query_features, features, algorithm,
                                      {"path": str(query_path), "digest": query_record.digest},
                                      {"path": str(record.path), "digest": record.digest}, config))
    results.sort(key=lambda item: (-item["score"], -item["inliers"], item["source"].get("digest") or ""))
    target_ranks = [i + 1 for i, item in enumerate(results) if target_digest and item["source"].get("digest") == target_digest]
    render_start = time.perf_counter()
    for index, item in enumerate(results[:2], start=1):
        source_path = Path(item["source"]["path"])
        source_gray, _ = decode_image(next(r for r in source_records if r.path == source_path))
        write_overlay(query_gray, source_gray, item, output / f"{algorithm}_{model}_{query_path.stem}_top{index}.png")
    render_ms = (time.perf_counter() - render_start) * 1000
    pair_ms = sum(item["timing_ms"]["pair_matching"] for item in results)
    geo_ms = sum(item["timing_ms"]["geometric_verification"] for item in results)
    return {
        "split": split, "slice": slice_name, "algorithm": algorithm, "transform_model": model,
        "directory_size": len(source_records), "coverage": {**coverage.as_dict(), "decoded": len(prepared)},
        "query": query_path.name, "top1": bool(target_ranks and target_ranks[0] <= 1),
        "top5": bool(target_ranks and target_ranks[0] <= 5),
        "top10_recovery": bool(target_ranks and target_ranks[0] <= 10),
        "target_rank": target_ranks[0] if target_ranks else None,
        "geometrically_supported_candidate_count": sum(
            item["status"] == "geometrically_supported_candidate" for item in results
        ),
        "timing_ms": {"discovery": round(discovery_ms, 3), "file_decode": round(query_decode_ms + decode_ms, 3),
                       "descriptor_extraction": round(query_descriptor_ms + descriptor_ms, 3),
                       "pair_matching": round(pair_ms, 3), "geometric_verification": round(geo_ms, 3),
                       "overlay_rendering": round(render_ms, 3)},
        "top10": results[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/private/tmp/image_finder_hardening"))
    parser.add_argument("--size", type=int, default=1000)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    source_dir = root / "positive_sources"
    source_dir.mkdir()
    for index in range(args.size):
        extension = (".png", ".jpg", ".tif")[index % 3]
        save_image(source_dir / f"source_{index:05d}{extension}", make_source(index, ("microscopy", "blot", "plot")[index % 3]), extension)
    positive_base = make_source(0, "microscopy")
    positive_specs = [
        ("identity", positive_base, "tuning"),
        ("crop", positive_base[25:155, 35:210], "tuning"),
        ("resize", cv2.resize(positive_base, (180, 135)), "tuning"),
        ("rotate", cv2.warpAffine(positive_base, cv2.getRotationMatrix2D((120, 90), 5, 1), (240, 180)), "heldout"),
        ("flip", np.ascontiguousarray(positive_base[:, ::-1]), "heldout"),
        ("brightness_contrast", cv2.convertScaleAbs(positive_base, alpha=1.25, beta=25), "heldout"),
    ]
    queries = [(write_query(root, name, image), name, split, source_dir / "source_00000.png") for name, image, split in positive_specs]
    hard_dir = make_hard_directory(root)
    for kind in HARD_KINDS:
        queries.append((write_query(root, f"hard_{kind}", hard_negative(999 + HARD_KINDS.index(kind), kind)), kind, "tuning" if kind in HARD_KINDS[:3] else "heldout", None))
    output = root / "overlays"
    results = []
    models = ("affine", "homography")
    for query, name, split, target_path in queries:
        directory = source_dir if target_path else hard_dir
        for algorithm in ("orb", "sift"):
            for model in models:
                target_digest = None
                if target_path:
                    target_record = next(r for r in discover_images(directory)[0] if r.path == target_path)
                    _, target_record = decode_image(target_record)
                    target_digest = target_record.digest
                results.append(search(query, directory, algorithm, model, output, target_digest, name, split))
    (root / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(root), "runs": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
