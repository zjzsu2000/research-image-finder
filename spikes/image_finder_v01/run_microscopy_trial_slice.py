#!/usr/bin/env python3
"""Run a tiny synthetic microscopy-like retrieval slice without making field claims."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_trial import search_trial  # noqa: E402

EVIDENCE_SCOPE = "synthetic_microscopy_like_trial_fixture_only_no_field_performance_claim"


def microscopy_like(seed: int, kind: str) -> np.ndarray:
    """Generate deterministic visual texture; this is not scientific microscopy data."""
    rng = np.random.default_rng(seed)
    height, width = 240, 320
    if kind == "brightfield":
        image = np.full((height, width, 3), (232, 239, 224), dtype=np.uint8)
        noise = rng.normal(0, 4, size=image.shape[:2]).astype(np.int16)
        image = np.clip(image.astype(np.int16) + noise[..., None], 0, 255).astype(np.uint8)
        for _ in range(55):
            x, y = int(rng.integers(12, width - 12)), int(rng.integers(12, height - 12))
            axes = (int(rng.integers(5, 14)), int(rng.integers(4, 10)))
            angle = float(rng.integers(0, 180))
            stain = (
                int(rng.integers(105, 165)),
                int(rng.integers(80, 135)),
                int(rng.integers(130, 190)),
            )
            cv2.ellipse(image, (x, y), axes, angle, 0, 360, stain, 1)
            cv2.circle(image, (x, y), max(1, min(axes) // 3), (95, 70, 125), -1)
    elif kind == "immunofluorescence":
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:] = rng.integers(0, 8, size=(height, width, 1), dtype=np.uint8)
        for _ in range(42):
            x, y = int(rng.integers(10, width - 10)), int(rng.integers(10, height - 10))
            radius = int(rng.integers(3, 10))
            channel = int(rng.integers(0, 3))
            colour = [0, 0, 0]
            colour[channel] = int(rng.integers(145, 255))
            cv2.circle(image, (x, y), radius, tuple(colour), -1)
            cv2.circle(image, (x, y), radius + 2, tuple(max(10, value // 3) for value in colour), 1)
        for _ in range(18):
            point = (int(rng.integers(5, width - 5)), int(rng.integers(5, height - 5)))
            cv2.circle(image, point, 1, (180, 180, 180), -1)
    else:
        raise ValueError(f"unknown synthetic microscopy-like kind: {kind}")
    return image


def _save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    Image.fromarray(rgb).save(path)


def evaluate_slice(kind: str, source_count: int = 12) -> dict[str, object]:
    """Evaluate one generated crop query; all fixture bytes are deleted after the run."""
    with tempfile.TemporaryDirectory(prefix=f"image_finder_{kind}_") as tmp:
        root = Path(tmp)
        sources = root / "sources"
        target = sources / "source_000.png"
        for index in range(source_count):
            extension = (".png", ".jpg", ".tif")[index % 3]
            _save(sources / f"source_{index:03d}{extension}", microscopy_like(1000 + index, kind))
        target_image = microscopy_like(1000, kind)
        query = root / f"query_{kind}_synthetic_crop.png"
        _save(query, target_image[28:216, 36:286])
        result = search_trial(query, sources, top_n=10)
        target_path = str(target.resolve())
        ranks = [item["rank"] for item in result["candidates"] if item["source_path"] == target_path]
        return {
            "content_slice": kind,
            "evidence_scope": EVIDENCE_SCOPE,
            "source_count": source_count,
            "query_transform": "crop",
            "target_rank": ranks[0] if ranks else None,
            "top5_recovery": bool(ranks and ranks[0] <= 5),
            "candidate_count": result["telemetry"]["candidate_count"],
            "search_runtime_ms": result["telemetry"]["search_runtime_ms"],
        }


def main() -> int:
    results = [evaluate_slice("brightfield"), evaluate_slice("immunofluorescence")]
    print(json.dumps({"evidence_scope": EVIDENCE_SCOPE, "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
