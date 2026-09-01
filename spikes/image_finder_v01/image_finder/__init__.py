"""Disposable Research Image Finder spike implementation."""

from .core import (
    ALGORITHMS,
    Coverage,
    HARDENED_CONFIG,
    ImageRecord,
    VerificationConfig,
    discover_images,
    decode_image,
    is_windows_network_path,
    match_pair,
    png_data_url,
    render_overlay_png,
    render_thumbnail_png,
    write_overlay,
)

__all__ = [
    "ALGORITHMS", "Coverage", "HARDENED_CONFIG", "ImageRecord", "VerificationConfig", "discover_images", "decode_image",
    "is_windows_network_path",
    "match_pair", "png_data_url", "render_overlay_png", "render_thumbnail_png", "write_overlay",
]
