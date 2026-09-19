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
    provenance: str = "pre_metadata_frame"


def decide_source_background_route(
    image: Image.Image,
    *,
    meaningful_ratio_threshold: float = 0.0001,
    transparent_alpha_threshold: int = 254,
) -> TransparencyDecision:
    """Classify source-frame transparency before alpha-generating cleanup.

    This decision must be captured after frame extraction/border cropping and before
    metadata removal or any other operation that can introduce transparent pixels.
    Later cleanup-generated alpha must never redefine the source routing decision.
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
            reason="source frame has no alpha channel",
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
            reason="meaningful source transparency exists; preserve alpha",
        )

    return TransparencyDecision(
        route=BackgroundRoute.REMOVE_BACKGROUND,
        has_alpha_channel=True,
        meaningful_transparency=False,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        transparent_pixel_ratio=ratio,
        reason="source alpha is effectively opaque",
    )


def decide_background_route(
    image: Image.Image,
    *,
    meaningful_ratio_threshold: float = 0.0001,
    transparent_alpha_threshold: int = 254,
) -> TransparencyDecision:
    """Compatibility alias for source-phase routing.

    Callers must invoke this only on the pre-metadata frame. New orchestration code
    should prefer ``decide_source_background_route`` to make provenance explicit.
    """
    return decide_source_background_route(
        image,
        meaningful_ratio_threshold=meaningful_ratio_threshold,
        transparent_alpha_threshold=transparent_alpha_threshold,
    )
