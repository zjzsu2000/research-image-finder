from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TIFF_MODES = {"L", "RGB", "RGBA"}
ALGORITHMS = ("orb", "sift")


@dataclass(frozen=True)
class VerificationConfig:
    """Pre-registered hardening parameters; changing them creates a new experiment."""
    ratio_threshold: float = 0.75
    mutual: bool = True
    min_tentative_matches: int = 8
    min_inliers: int = 10
    min_inlier_ratio: float = 0.45
    min_query_coverage: float = 0.08
    min_source_coverage: float = 0.02
    max_median_reprojection_error: float = 3.0
    max_forward_backward_error: float = 3.0
    transform_model: str = "affine"
    max_area_ratio: float = 25.0
    min_area_ratio: float = 0.02


HARDENED_CONFIG = VerificationConfig()


@dataclass
class Coverage:
    root: str
    discovered: int = 0
    decoded: int = 0
    unsupported: list[dict[str, str]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    symlinks: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "discovered": self.discovered,
            "decoded": self.decoded,
            "unsupported": self.unsupported,
            "errors": self.errors,
            "symlinks": self.symlinks,
        }


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    root: Path
    relative_path: str
    extension: str
    status: str = "discovered"
    error: str | None = None
    digest: str | None = None
    width: int | None = None
    height: int | None = None
    mode: str | None = None
    frame_count: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "root": str(self.root),
            "relative_path": self.relative_path,
            "extension": self.extension,
            "status": self.status,
            "error": self.error,
            "digest": self.digest,
            "width": self.width,
            "height": self.height,
            "mode": self.mode,
            "frame_count": self.frame_count,
        }


def _canonical_root(root: Path) -> Path:
    root = root.expanduser()
    if is_windows_network_path(root):
        raise ValueError("selected root must be a local drive, not a UNC or mapped network drive")
    is_junction = getattr(os.path, "isjunction", lambda _path: False)
    if root.is_symlink() or is_junction(root):
        raise ValueError("selected root must not itself be a symlink or Windows junction")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return root


def is_windows_network_path(path: str | Path) -> bool:
    """Identify Windows UNC and mapped remote-drive paths without opening them."""
    candidate = Path(path).expanduser()
    raw = str(candidate)
    if raw.startswith("\\\\") or raw.startswith("//"):
        return True
    if os.name != "nt" or not candidate.drive:
        return False
    try:
        import ctypes

        drive_type_remote = 4
        return ctypes.windll.kernel32.GetDriveTypeW(str(candidate.anchor)) == drive_type_remote
    except (AttributeError, OSError):
        return False


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root)
        return True
    except ValueError:
        return False


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_images(root: str | Path) -> tuple[list[ImageRecord], Coverage]:
    """Enumerate only supported raster files under one canonical root.

    Unsupported files and out-of-root symlink attempts are coverage records. No file content is
    opened here, and no network-capable operation is used.
    """
    canonical = _canonical_root(Path(root))
    coverage = Coverage(str(canonical))
    records: list[ImageRecord] = []
    stack = [canonical]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name)
        except OSError as exc:
            coverage.errors.append({"path": str(directory), "error": f"scan: {exc}"})
            continue
        for entry in entries:
            path = Path(entry.path)
            is_junction = getattr(os.path, "isjunction", lambda _path: False)
            if entry.is_symlink() or is_junction(path):
                target = path.resolve(strict=False)
                item = {"path": str(path), "target": str(target)}
                if _inside(target, canonical):
                    coverage.symlinks.append({**item, "action": "not_followed"})
                else:
                    coverage.symlinks.append({**item, "action": "out_of_scope_rejected"})
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError as exc:
                coverage.errors.append({"path": str(path), "error": f"stat: {exc}"})
                continue
            extension = path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                coverage.unsupported.append({"path": str(path), "reason": "unsupported_extension"})
                continue
            relative = path.relative_to(canonical).as_posix()
            record = ImageRecord(path, canonical, relative, extension)
            records.append(record)
            coverage.discovered += 1
    records.sort(key=lambda r: r.relative_path)
    return records, coverage


def decode_image(record: ImageRecord) -> tuple[np.ndarray | None, ImageRecord]:
    """Decode PNG/JPEG and a deliberately small, explicit TIFF subset."""
    try:
        with Image.open(record.path) as image:
            frame_count = int(getattr(image, "n_frames", 1))
            mode = image.mode
            if record.extension in {".tif", ".tiff"}:
                if frame_count != 1:
                    raise ValueError(f"unsupported TIFF variant: frame_count={frame_count}")
                if mode not in TIFF_MODES:
                    raise ValueError(f"unsupported TIFF variant: mode={mode}")
            elif mode not in {"1", "L", "LA", "RGB", "RGBA", "P"}:
                raise ValueError(f"unsupported raster mode: {mode}")
            rgb = image.convert("RGB")
            array = np.asarray(rgb, dtype=np.uint8)
            updated = ImageRecord(
                **{**record.__dict__, "status": "decoded", "error": None,
                   "digest": _digest(record.path), "width": image.width,
                   "height": image.height, "mode": mode, "frame_count": frame_count}
            )
            return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY), updated
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        updated = ImageRecord(**{**record.__dict__, "status": "error", "error": str(exc)})
        return None, updated


def _features(gray: np.ndarray, algorithm: str):
    if algorithm == "orb":
        detector = cv2.ORB_create(nfeatures=2500, scaleFactor=1.2, nlevels=8, fastThreshold=12)
    elif algorithm == "sift":
        detector = cv2.SIFT_create(nfeatures=0, nOctaveLayers=3, contrastThreshold=0.04,
                                   edgeThreshold=10, sigma=1.6)
    else:
        raise ValueError(f"unknown algorithm: {algorithm}")
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    return keypoints or [], descriptors


def _resize(gray: np.ndarray, max_edge: int = 1600) -> np.ndarray:
    height, width = gray.shape[:2]
    scale = min(1.0, max_edge / max(height, width))
    if scale == 1.0:
        return gray
    return cv2.resize(gray, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)


def prepare_features(gray: np.ndarray, algorithm: str) -> dict[str, Any]:
    """Extract one image's features for reuse during an exhaustive benchmark."""
    normalized = _resize(gray)
    keypoints, descriptors = _features(normalized, algorithm)
    return {"gray": normalized, "keypoints": keypoints, "descriptors": descriptors}


def _ratio_matches(qdesc: np.ndarray, sdesc: np.ndarray, algorithm: str, threshold: float):
    norm = cv2.NORM_HAMMING if algorithm == "orb" else cv2.NORM_L2
    matcher = cv2.BFMatcher(norm)
    pairs = matcher.knnMatch(qdesc, sdesc, k=2)
    return [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < threshold * pair[1].distance]


def _coverage(points: np.ndarray, shape: tuple[int, int]) -> float:
    if len(points) < 2:
        return 0.0
    height, width = shape[:2]
    x0, y0 = points.min(axis=0)
    x1, y1 = points.max(axis=0)
    return float(max(0.0, x1 - x0) * max(0.0, y1 - y0) / max(1.0, width * height))


def match_prepared(query_features: dict[str, Any], source_features: dict[str, Any], algorithm: str,
                  query_meta: dict[str, Any] | None = None,
                  source_meta: dict[str, Any] | None = None,
                  config: VerificationConfig = HARDENED_CONFIG) -> dict[str, Any]:
    """Match every supplied source with a preregistered evidence conjunction."""
    started = time.perf_counter()
    query = query_features["gray"]
    source = source_features["gray"]
    qkp, qdesc = query_features["keypoints"], query_features["descriptors"]
    skp, sdesc = source_features["keypoints"], source_features["descriptors"]
    result: dict[str, Any] = {
        "diagnostic_schema": "image_finder_spike_result_v1",
        "algorithm": algorithm,
        "verification_config": config.__dict__,
        "status": "ranked_candidate_without_geometric_support",
        "query": query_meta or {}, "source": source_meta or {},
        "keypoints": {"query": len(qkp), "source": len(skp)},
        "tentative_matches": 0, "mutual_matches": 0, "inliers": 0,
        "inlier_ratio": 0.0, "score": 0.0, "transform": None,
        "matched_region": None, "failure_reason": None,
        "conditions": {}, "diagnostics": {},
        "timing_ms": {"pair_matching": 0.0, "geometric_verification": 0.0, "total": 0.0},
    }
    if qdesc is None or sdesc is None:
        result["failure_reason"] = "insufficient_features"
        result["timing_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
        return result
    pair_started = time.perf_counter()
    forward = _ratio_matches(qdesc, sdesc, algorithm, config.ratio_threshold)
    reverse = _ratio_matches(sdesc, qdesc, algorithm, config.ratio_threshold) if config.mutual else []
    reverse_map = {m.queryIdx: m.trainIdx for m in reverse}
    matches = [m for m in forward if not config.mutual or reverse_map.get(m.trainIdx) == m.queryIdx]
    matches = sorted(matches, key=lambda match: match.distance)[:80]
    result["tentative_matches"] = len(forward)
    result["mutual_matches"] = len(matches)
    result["timing_ms"]["pair_matching"] = round((time.perf_counter() - pair_started) * 1000, 3)
    if len(matches) < config.min_tentative_matches:
        result["failure_reason"] = "too_few_mutual_matches"
        result["timing_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
        return result

    geo_started = time.perf_counter()
    qpts = np.float32([qkp[m.queryIdx].pt for m in matches])
    spts = np.float32([skp[m.trainIdx].pt for m in matches])
    if config.transform_model == "affine":
        matrix, mask = cv2.estimateAffine2D(qpts, spts, method=cv2.RANSAC, ransacReprojThreshold=3.0,
                                            maxIters=2000, confidence=0.995, refineIters=10)
        projected = cv2.transform(qpts.reshape(-1, 1, 2), matrix).reshape(-1, 2) if matrix is not None else None
        inverse = cv2.invertAffineTransform(matrix) if matrix is not None else None
    elif config.transform_model == "similarity":
        matrix, mask = cv2.estimateAffinePartial2D(qpts, spts, method=cv2.RANSAC, ransacReprojThreshold=3.0,
                                                   maxIters=2000, confidence=0.995, refineIters=10)
        projected = cv2.transform(qpts.reshape(-1, 1, 2), matrix).reshape(-1, 2) if matrix is not None else None
        inverse = cv2.invertAffineTransform(matrix) if matrix is not None else None
    elif config.transform_model == "homography":
        matrix, mask = cv2.findHomography(qpts, spts, cv2.RANSAC, 3.0, maxIters=2000, confidence=0.995)
        projected = cv2.perspectiveTransform(qpts.reshape(-1, 1, 2), matrix).reshape(-1, 2) if matrix is not None else None
        inverse = np.linalg.inv(matrix) if matrix is not None else None
    else:
        raise ValueError(f"unknown transform model: {config.transform_model}")
    result["timing_ms"]["geometric_verification"] = round((time.perf_counter() - geo_started) * 1000, 3)
    if matrix is None or mask is None or projected is None or inverse is None:
        result["failure_reason"] = "geometric_model_failed"
        result["timing_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
        return result
    inlier_mask = mask.ravel().astype(bool)
    inlier_q, inlier_s, inlier_projected = qpts[inlier_mask], spts[inlier_mask], projected[inlier_mask]
    inliers = int(inlier_mask.sum())
    inlier_ratio = inliers / len(matches)
    if inliers == 0:
        result["inliers"] = 0
        result["inlier_ratio"] = 0.0
        result["failure_reason"] = "no_geometric_inliers"
        result["timing_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
        return result
    residual = np.linalg.norm(inlier_projected - inlier_s, axis=1)
    try:
        if config.transform_model == "homography":
            back_projected = cv2.perspectiveTransform(inlier_s.reshape(-1, 1, 2), inverse).reshape(-1, 2)
        else:
            back_projected = cv2.transform(inlier_s.reshape(-1, 1, 2), inverse).reshape(-1, 2)
        backward = np.linalg.norm(back_projected - inlier_q, axis=1)
    except (cv2.error, AttributeError, ValueError):
        backward = np.full(len(inlier_q), np.inf, dtype=np.float64)
    q_coverage = _coverage(inlier_q, query.shape)
    s_coverage = _coverage(inlier_s, source.shape)
    polygon_input = np.float32([[[0, 0], [query.shape[1], 0], [query.shape[1], query.shape[0]], [0, query.shape[0]]]])
    if config.transform_model == "homography":
        polygon = cv2.perspectiveTransform(polygon_input, matrix)[0]
    else:
        polygon = cv2.transform(polygon_input, matrix)[0]
    area_ratio = abs(float(cv2.contourArea(polygon)) / max(1.0, query.shape[0] * query.shape[1]))
    finite = bool(np.isfinite(polygon).all() and np.isfinite(matrix).all())
    conditions = {
        "minimum_correspondence": len(matches) >= config.min_tentative_matches,
        "minimum_inliers": inliers >= config.min_inliers,
        "inlier_ratio": inlier_ratio >= config.min_inlier_ratio,
        "query_spatial_coverage": q_coverage >= config.min_query_coverage,
        "source_spatial_coverage": s_coverage >= config.min_source_coverage,
        "reprojection_residual": float(np.median(residual)) <= config.max_median_reprojection_error,
        "forward_backward_consistency": float(np.median(backward)) <= config.max_forward_backward_error,
        "finite_transform": finite,
        "transform_area_plausible": config.min_area_ratio <= area_ratio <= config.max_area_ratio,
    }
    result["inliers"] = inliers
    result["inlier_ratio"] = round(inlier_ratio, 6)
    result["score"] = round(inliers * inlier_ratio * max(q_coverage, 1e-6), 6)
    result["transform"] = np.asarray(matrix).round(6).tolist()
    result["matched_region"] = {"source_polygon": polygon.round(2).tolist()}
    result["conditions"] = conditions
    result["diagnostics"] = {
        "query_coverage": round(q_coverage, 6), "source_coverage": round(s_coverage, 6),
        "median_reprojection_error": round(float(np.median(residual)), 6),
        "median_forward_backward_error": round(float(np.median(backward)), 6),
        "area_ratio": round(area_ratio, 6),
    }
    if all(conditions.values()):
        result["status"] = "geometrically_supported_candidate"
    else:
        result["failure_reason"] = "verification_conjunction_failed"
    result["timing_ms"]["total"] = round((time.perf_counter() - started) * 1000, 3)
    return result


def match_pair(query: np.ndarray, source: np.ndarray, algorithm: str,
               query_meta: dict[str, Any] | None = None,
               source_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Exhaustive local-feature verification for one query/source pair."""
    return match_prepared(prepare_features(query, algorithm), prepare_features(source, algorithm), algorithm,
                          query_meta, source_meta)


def render_overlay_png(
    query: np.ndarray,
    source: np.ndarray,
    result: dict[str, Any],
    max_edge: int = 420,
) -> bytes:
    """Render side-by-side retrieval evidence without assigning provenance."""
    query = _resize(query, max_edge=max_edge)
    source = _resize(source, max_edge=max_edge)
    left = cv2.cvtColor(query, cv2.COLOR_GRAY2BGR) if query.ndim == 2 else query.copy()
    right = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR) if source.ndim == 2 else source.copy()
    polygon = result.get("matched_region", {}).get("source_polygon") if result.get("matched_region") else None
    if polygon:
        points = np.asarray(polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(right, [points], True, (0, 220, 0), 3)
    height = max(left.shape[0], right.shape[0])
    canvas = np.zeros((height, left.shape[1] + right.shape[1], 3), dtype=np.uint8)
    canvas[:left.shape[0], :left.shape[1]] = left
    canvas[:right.shape[0], left.shape[1]:] = right
    cv2.putText(canvas, "query", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 255), 2)
    cv2.putText(canvas, "source", (left.shape[1] + 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 255), 2)
    encoded, buffer = cv2.imencode(".png", canvas)
    if not encoded:
        raise OSError("could not encode overlay")
    return buffer.tobytes()


def render_thumbnail_png(image: np.ndarray, max_edge: int = 360) -> bytes:
    """Render an in-memory PNG thumbnail for a local trial report."""
    height, width = image.shape[:2]
    scale = min(1.0, max_edge / max(height, width))
    resized = image if scale == 1.0 else cv2.resize(
        image, (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    encoded, buffer = cv2.imencode(".png", resized)
    if not encoded:
        raise OSError("could not encode thumbnail")
    return buffer.tobytes()


def png_data_url(payload: bytes) -> str:
    """Return a self-contained data URL; no external asset or network fetch is needed."""
    return "data:image/png;base64," + base64.b64encode(payload).decode("ascii")


def write_overlay(query: np.ndarray, source: np.ndarray, result: dict[str, Any], output: str | Path) -> None:
    """Write a local side-by-side visual diagnostic for spike benchmarks."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render_overlay_png(query, source, result))


def write_jsonl(records: Iterable[dict[str, Any]], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
