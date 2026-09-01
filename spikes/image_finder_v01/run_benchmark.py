#!/usr/bin/env python3
"""Generate a tiny deterministic benchmark and run exhaustive ORB/SIFT searches.

All generated files/results are written outside the repository by default. This is disposable
spike code, not a production command.
"""
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
from image_finder.core import decode_image, discover_images, match_prepared, prepare_features, write_overlay


def make_source(seed: int, content: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    image = np.zeros((180, 240, 3), dtype=np.uint8)
    if content == "microscopy":
        image[:] = rng.integers(15, 45, size=3, dtype=np.uint8)
        for _ in range(80):
            x, y = int(rng.integers(8, 232)), int(rng.integers(8, 172))
            radius = int(rng.integers(2, 8))
            cv2.circle(image, (x, y), radius, tuple(int(v) for v in rng.integers(80, 255, size=3)), -1)
    elif content == "blot":
        image[:] = 235
        for lane in range(5):
            x = 28 + lane * 42
            cv2.rectangle(image, (x, 28), (x + 25, 155), (210, 210, 210), -1)
            for band in range(3):
                y = 45 + band * 34 + int(rng.integers(-4, 5))
                cv2.ellipse(image, (x + 12, y), (10, 4), 0, 0, 360, (20, 20, 20), -1)
    else:
        image[:] = 250
        points = np.cumsum(rng.normal(0, 8, size=(28, 2)), axis=0)
        points -= points.min(axis=0)
        points *= np.array([220 / max(points[:, 0].max(), 1), 130 / max(points[:, 1].max(), 1)])
        points += [10, 25]
        cv2.polylines(image, [points.astype(np.int32)], False, (40, 80, 190), 3)
        cv2.line(image, (10, 155), (230, 155), (50, 50, 50), 2)
        cv2.line(image, (10, 25), (10, 155), (50, 50, 50), 2)
    cv2.putText(image, f"S{seed:02d}", (12, 174), cv2.FONT_HERSHEY_SIMPLEX, .5, (10, 120, 10), 1)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def save_image(path: Path, array: np.ndarray, extension: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.fromarray(array)
    image.save(path, format={".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".tif": "TIFF"}[extension])


def make_benchmark(root: Path, size: int) -> tuple[Path, dict[str, str]]:
    directory = root / f"directory_{size}"
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    target_digest = None
    source_info: dict[str, str] = {}
    contents = ["microscopy", "blot", "plot"]
    for index in range(size):
        content = contents[index % len(contents)]
        seed = index
        extension = [".png", ".jpg", ".tif"][index % 3]
        path = directory / f"source_{index:05d}{extension}"
        save_image(path, make_source(seed, content), extension)
        if index == 0:
            target_digest = str(path)
            source_info = {"content_type": content, "path": str(path)}
    assert target_digest
    return directory, source_info


def make_queries(root: Path) -> list[tuple[Path, str, str]]:
    base = make_source(0, "microscopy")
    query_specs = [
        ("identity", base),
        ("crop", base[25:155, 35:210]),
        ("resize", cv2.resize(base, (180, 135), interpolation=cv2.INTER_AREA)),
        ("rotate", cv2.warpAffine(base, cv2.getRotationMatrix2D((120, 90), 5, 1.0), (240, 180), borderValue=0)),
        ("flip", np.ascontiguousarray(base[:, ::-1])),
        ("brightness_contrast", cv2.convertScaleAbs(base, alpha=1.25, beta=25)),
        ("absent_hard_negative", make_source(999, "microscopy")),
    ]
    paths = []
    for name, image in query_specs:
        path = root / "queries" / f"query_{name}.png"
        save_image(path, image, ".png")
        paths.append((path, name, "microscopy"))
    return paths


def run_search(query_path: Path, directory: Path, algorithm: str, output: Path, target_path: str) -> dict:
    query_record = next(r for r in discover_images(query_path.parent)[0] if r.path == query_path)
    query_gray, query_record = decode_image(query_record)
    source_records, coverage = discover_images(directory)
    query_features = prepare_features(query_gray, algorithm)
    prepared = []
    decode_started = time.perf_counter()
    for record in source_records:
        gray, decoded = decode_image(record)
        if gray is not None:
            prepared.append((decoded, prepare_features(gray, algorithm)))
        elif decoded.error:
            coverage.errors.append({"path": str(record.path), "error": decoded.error})
    coverage.decoded = len(prepared)
    decode_ms = (time.perf_counter() - decode_started) * 1000
    started = time.perf_counter()
    results = []
    for record, features in prepared:
        result = match_prepared(query_features, features, algorithm,
                                {"path": str(query_path), "digest": query_record.digest},
                                {"path": str(record.path), "digest": record.digest})
        results.append(result)
    elapsed_ms = (time.perf_counter() - started) * 1000
    results.sort(key=lambda r: (-r["score"], -r["inliers"], r["source"].get("digest") or ""))
    ranks = []
    if target_path is not None:
        target_digest = next(r.digest for r, _ in prepared if str(r.path) == target_path)
        ranks = [i + 1 for i, result in enumerate(results) if result["source"].get("digest") == target_digest]
    top = results[:10]
    for index, result in enumerate(top[:3], start=1):
        source_path = Path(result["source"]["path"])
        source_gray, _ = decode_image(next(r for r in source_records if r.path == source_path))
        write_overlay(query_gray, source_gray, result, output / f"{algorithm}_{query_path.stem}_top{index}.png")
    return {
        "algorithm": algorithm,
        "query": query_path.name,
        "transform": query_path.stem.removeprefix("query_"),
        "directory_size": len(source_records),
        "coverage": coverage.as_dict(),
        "decode_ms": round(decode_ms, 3),
        "search_ms": round(elapsed_ms, 3),
        "top1": bool(ranks and ranks[0] <= 1),
        "top5": bool(ranks and ranks[0] <= 5),
        "top10": bool(ranks and ranks[0] <= 10),
        "target_rank": ranks[0] if ranks else None,
        "geometrically_supported_candidate_count": sum(
            result["status"] == "geometrically_supported_candidate" for result in results
        ),
        "top10_results": top,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/private/tmp/image_finder_v01"))
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 5000])
    parser.add_argument("--large-query-count", type=int, default=2,
                        help="number of transform queries at the largest directory size")
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    queries = make_queries(root)
    all_results = []
    for size in args.sizes:
        directory, source_info = make_benchmark(root, size)
        selected_queries = queries if size != max(args.sizes) else queries[:args.large_query_count]
        for query_path, _, _ in selected_queries:
            for algorithm in ("orb", "sift"):
                target = None if query_path.stem.endswith("absent_hard_negative") else source_info["path"]
                all_results.append(run_search(query_path, directory, algorithm, root / "overlays", target))
    (root / "results.json").write_text(json.dumps(all_results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(root), "runs": len(all_results), "results": all_results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
