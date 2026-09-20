from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

import cv2
import numpy as np
from PIL import Image


class OpaqueBackgroundStatus(StrEnum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    SAFE_REMOVE = "SAFE_REMOVE"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class OpaqueBackgroundPlan:
    status: OpaqueBackgroundStatus
    background_kind: str
    boundary_dark_fraction: float
    hard_removed_pixel_count: int
    hard_removed_ratio: float
    fringe_adjusted_pixel_count: int
    remaining_visible_pixel_count: int
    remaining_visible_ratio: float
    transparency_ratio: float
    mask_sha256: str | None
    reasons: tuple[str, ...]
    alpha: Image.Image | None = None


def _meaningful_transparency_ratio(image: Image.Image) -> float:
    alpha = np.asarray(image.convert("RGBA").getchannel("A"), dtype=np.uint8)
    return float(np.mean(alpha <= 8))


def _boundary_samples(rgb: np.ndarray) -> np.ndarray:
    return np.concatenate((rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]), axis=0)


def _edge_connected(mask: np.ndarray) -> np.ndarray:
    binary = mask.astype(np.uint8)
    count, labels = cv2.connectedComponents(binary, connectivity=8)
    if count <= 1:
        return np.zeros_like(mask, dtype=bool)
    edge_labels = np.unique(
        np.concatenate((labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]))
    )
    edge_labels = edge_labels[edge_labels != 0]
    if edge_labels.size == 0:
        return np.zeros_like(mask, dtype=bool)
    return np.isin(labels, edge_labels)


def _mask_hash(mask: np.ndarray) -> str:
    return sha256(mask.astype(np.uint8).tobytes(order="C")).hexdigest()


def plan_opaque_background_removal(
    image: Image.Image,
    *,
    hard_dark_threshold: int = 70,
    boundary_dark_fraction_threshold: float = 0.90,
    max_removed_ratio: float = 0.90,
    min_remaining_visible_ratio: float = 0.05,
    fringe_radius: int = 2,
    fringe_max_value: int = 150,
    fringe_max_chroma: int = 55,
) -> OpaqueBackgroundPlan:
    """Plan conservative edge-connected opaque-background removal.

    Only dark pixels connected to the image boundary gain hard-removal authority.
    Enclosed dark artwork remains untouched.
    """
    if not 0 <= hard_dark_threshold <= 255:
        raise ValueError("hard_dark_threshold must be in [0, 255]")
    if not 0 <= boundary_dark_fraction_threshold <= 1:
        raise ValueError("boundary_dark_fraction_threshold must be in [0, 1]")
    if not 0 <= max_removed_ratio <= 1:
        raise ValueError("max_removed_ratio must be in [0, 1]")
    if not 0 <= min_remaining_visible_ratio <= 1:
        raise ValueError("min_remaining_visible_ratio must be in [0, 1]")
    if fringe_radius < 0:
        raise ValueError("fringe_radius must be non-negative")

    source_transparency = _meaningful_transparency_ratio(image)
    if source_transparency > 0.001:
        return OpaqueBackgroundPlan(
            status=OpaqueBackgroundStatus.NOT_ELIGIBLE,
            background_kind="already_transparent",
            boundary_dark_fraction=0.0,
            hard_removed_pixel_count=0,
            hard_removed_ratio=0.0,
            fringe_adjusted_pixel_count=0,
            remaining_visible_pixel_count=image.width * image.height,
            remaining_visible_ratio=1.0,
            transparency_ratio=source_transparency,
            mask_sha256=None,
            reasons=("source already contains meaningful transparency",),
            alpha=None,
        )

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    height, width = rgb.shape[:2]
    total = height * width
    max_channel = rgb.max(axis=2)
    min_channel = rgb.min(axis=2)
    boundary = _boundary_samples(rgb)
    boundary_dark_fraction = float(np.mean(boundary.max(axis=1) <= hard_dark_threshold))

    if boundary_dark_fraction < boundary_dark_fraction_threshold:
        return OpaqueBackgroundPlan(
            status=OpaqueBackgroundStatus.REVIEW,
            background_kind="unsupported_or_nonuniform_boundary",
            boundary_dark_fraction=boundary_dark_fraction,
            hard_removed_pixel_count=0,
            hard_removed_ratio=0.0,
            fringe_adjusted_pixel_count=0,
            remaining_visible_pixel_count=total,
            remaining_visible_ratio=1.0,
            transparency_ratio=0.0,
            mask_sha256=None,
            reasons=("boundary is not sufficiently uniform/dark for automatic removal",),
            alpha=None,
        )

    hard_candidate = max_channel <= hard_dark_threshold
    hard_background = _edge_connected(hard_candidate)
    removed_count = int(np.count_nonzero(hard_background))
    removed_ratio = removed_count / total if total else 0.0
    remaining_count = total - removed_count
    remaining_ratio = remaining_count / total if total else 0.0

    if removed_count == 0:
        status = OpaqueBackgroundStatus.REVIEW
        reasons = ("no edge-connected dark background was proven",)
    elif removed_ratio > max_removed_ratio:
        status = OpaqueBackgroundStatus.REVIEW
        reasons = ("proposed background removal exceeds safety ceiling",)
    elif remaining_ratio < min_remaining_visible_ratio:
        status = OpaqueBackgroundStatus.REVIEW
        reasons = ("too little visible foreground would remain after removal",)
    else:
        status = OpaqueBackgroundStatus.SAFE_REMOVE
        reasons = ("edge-connected dark background is proven and bounded",)

    alpha = np.full((height, width), 255, dtype=np.uint8)
    alpha[hard_background] = 0
    fringe_count = 0
    if status == OpaqueBackgroundStatus.SAFE_REMOVE and fringe_radius > 0:
        kernel_size = (fringe_radius * 2) + 1
        dilated = cv2.dilate(
            hard_background.astype(np.uint8),
            np.ones((kernel_size, kernel_size), dtype=np.uint8),
            iterations=1,
        ).astype(bool)
        fringe = dilated & ~hard_background
        chroma = max_channel.astype(np.int16) - min_channel.astype(np.int16)
        eligible_fringe = fringe & (max_channel < fringe_max_value) & (chroma < fringe_max_chroma)
        scaled = np.clip(
            ((max_channel.astype(np.float32) - hard_dark_threshold) / max(1, fringe_max_value - hard_dark_threshold))
            * 255.0,
            0,
            255,
        ).astype(np.uint8)
        alpha[eligible_fringe] = np.minimum(alpha[eligible_fringe], scaled[eligible_fringe])
        fringe_count = int(np.count_nonzero(eligible_fringe))

    alpha_image = Image.fromarray(alpha, mode="L") if status == OpaqueBackgroundStatus.SAFE_REMOVE else None
    transparency_ratio = float(np.mean(alpha <= 8)) if alpha_image is not None else 0.0
    return OpaqueBackgroundPlan(
        status=status,
        background_kind="edge_connected_dark",
        boundary_dark_fraction=boundary_dark_fraction,
        hard_removed_pixel_count=removed_count,
        hard_removed_ratio=removed_ratio,
        fringe_adjusted_pixel_count=fringe_count,
        remaining_visible_pixel_count=remaining_count,
        remaining_visible_ratio=remaining_ratio,
        transparency_ratio=transparency_ratio,
        mask_sha256=_mask_hash(hard_background) if removed_count else None,
        reasons=reasons,
        alpha=alpha_image,
    )


def apply_opaque_background_removal(
    image: Image.Image,
    plan: OpaqueBackgroundPlan,
) -> Image.Image:
    if plan.status != OpaqueBackgroundStatus.SAFE_REMOVE or plan.alpha is None:
        raise ValueError("opaque background plan is not safe to apply")
    rgba = image.convert("RGBA")
    if rgba.size != plan.alpha.size:
        raise ValueError("opaque background alpha shape does not match image")
    rgba.putalpha(plan.alpha)
    return rgba
