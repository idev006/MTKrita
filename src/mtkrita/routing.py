from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from PIL import Image


class BackgroundRoute(StrEnum):
    SKIP_REMOVE_BACKGROUND = "skip_remove_background"
    REMOVE_BACKGROUND = "remove_background"


@dataclass(frozen=True)
class TransparencyDecision:
    route: BackgroundRoute
    has_alpha_channel: bool
    meaningful_transparency: bool
    alpha_min: int | None
    alpha_max: int | None
    transparent_pixel_ratio: float
    reason: str


def decide_background_route(
    image: Image.Image,
    *,
    meaningful_ratio_threshold: float = 0.0001,
    transparent_alpha_threshold: int = 254,
) -> TransparencyDecision:
    """Choose whether background removal is required.

    An alpha channel alone is not enough. A fully opaque RGBA image must still be
    routed to background removal. Conversely, an image with meaningful transparent
    pixels should preserve its existing alpha and skip segmentation by default.
    """
    if not 0 <= meaningful_ratio_threshold <= 1:
        raise ValueError("meaningful_ratio_threshold must be between 0 and 1")
    if not 0 <= transparent_alpha_threshold <= 254:
        raise ValueError("transparent_alpha_threshold must be between 0 and 254")

    has_alpha = "A" in image.getbands() or "transparency" in image.info
    if not has_alpha:
        return TransparencyDecision(
            route=BackgroundRoute.REMOVE_BACKGROUND,
            has_alpha_channel=False,
            meaningful_transparency=False,
            alpha_min=None,
            alpha_max=None,
            transparent_pixel_ratio=0.0,
            reason="input has no alpha channel",
        )

    alpha = image.convert("RGBA").getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    histogram = alpha.histogram()
    pixel_count = image.width * image.height
    transparent_count = sum(histogram[: transparent_alpha_threshold + 1])
    ratio = transparent_count / pixel_count if pixel_count else 0.0
    meaningful = ratio >= meaningful_ratio_threshold and alpha_min <= transparent_alpha_threshold

    if meaningful:
        return TransparencyDecision(
            route=BackgroundRoute.SKIP_REMOVE_BACKGROUND,
            has_alpha_channel=True,
            meaningful_transparency=True,
            alpha_min=alpha_min,
            alpha_max=alpha_max,
            transparent_pixel_ratio=ratio,
            reason="meaningful transparency already exists; preserve alpha",
        )

    return TransparencyDecision(
        route=BackgroundRoute.REMOVE_BACKGROUND,
        has_alpha_channel=True,
        meaningful_transparency=False,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        transparent_pixel_ratio=ratio,
        reason="alpha channel exists but background is effectively opaque",
    )
