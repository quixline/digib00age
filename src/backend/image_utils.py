"""
image_utils.py — Shared safe image opening (BUG-038).

Pillow's decompression-bomb check fires inside Image.open() itself, right
after the format header is parsed — before .load()/.resize() ever run. A
handful of real comic scan pages exceed Pillow's default pixel-count
threshold, which today only raises a UserWarning but could become a hard
DecompressionBombError in a future Pillow release.

open_image_capped() / open_image_capped_path() pre-check the parsed size and,
for oversized JPEGs, use Image.draft() to decode directly at reduced
resolution instead of materializing a full-size bitmap before it's ever
resized down. Non-JPEG formats can't use draft(), but in practice that only matters in the
1x-2x band: Pillow's own decompression-bomb check hard-raises
DecompressionBombError (not just a warning) for ANY format once pixel count
exceeds 2x MAX_IMAGE_PIXELS, before Image.open() ever returns — so anything
past that point is already rejected by Pillow itself, regardless of format.
"""

import logging
import warnings
from io import BytesIO
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

SOFT_LIMIT = Image.MAX_IMAGE_PIXELS


def open_image_capped(data: bytes) -> Optional[Image.Image]:
    """Bytes-based variant — for images read out of an archive entry."""
    return _open_capped(BytesIO(data))


def open_image_capped_path(path: str) -> Optional[Image.Image]:
    """Path-based variant — for images already extracted to disk."""
    return _open_capped(path)


def _open_capped(src) -> Optional[Image.Image]:
    """Open an image, downscaling via JPEG draft-mode decode if it exceeds
    Pillow's decompression-bomb threshold. Returns None (never raises) if
    the image can't be safely opened — callers treat this like any other
    unreadable/corrupt image."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        try:
            img = Image.open(src)
        except Image.DecompressionBombError as exc:
            logger.warning("Rejected oversized page image: %s", exc)
            return None
        w, h = img.size
        if w * h > SOFT_LIMIT and img.format == "JPEG":
            img.draft(img.mode, (w // 2, h // 2))
            logger.warning(
                "Downscaled oversized page image via JPEG draft mode "
                "(%dx%d px, %.1fM pixels)", w, h, w * h / 1e6
            )
    return img
