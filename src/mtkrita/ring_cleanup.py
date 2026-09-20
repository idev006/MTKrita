from __future__ import annotations

import numpy as np
from PIL import Image

from .closed_ring import ClosedRingPlan, ClosedRingStatus


def apply_closed_ring_cleanup(image: Image.Image, plan: ClosedRingPlan) -> Image.Image:
    """Apply one verified SAFE_RING mask to a private transparent working copy."""
    if plan.status != ClosedRingStatus.SAFE_RING or plan.mask is None:
        raise ValueError("closed-ring cleanup requires SAFE_RING")
    if plan.mask.size != image.size:
        raise ValueError("closed-ring mask size does not match frame")

    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8).copy()
    mask = np.asarray(plan.mask.convert("L"), dtype=np.uint8)
    alpha[mask > 0] = 0
    rgba.putalpha(Image.fromarray(alpha))
    return rgba
