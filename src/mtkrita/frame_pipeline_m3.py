from __future__ import annotations

from PIL import Image

from .frame_pipeline import FramePipelineConfig, FramePipelineOutput, process_frame
from .models import Finding, FrameResult, FrameStatus, ProcessingMode
from .opaque_background import (
    OpaqueBackgroundPlan,
    OpaqueBackgroundStatus,
    apply_opaque_background_removal,
    plan_opaque_background_removal,
)
from .routing import BackgroundRoute, decide_source_background_route


def _background_evidence(plan: OpaqueBackgroundPlan) -> dict[str, object]:
    return {
        "m3_background_status": plan.status.value,
        "m3_background_kind": plan.background_kind,
        "m3_boundary_dark_fraction": plan.boundary_dark_fraction,
        "m3_hard_removed_pixel_count": plan.hard_removed_pixel_count,
        "m3_hard_removed_ratio": plan.hard_removed_ratio,
        "m3_fringe_adjusted_pixel_count": plan.fringe_adjusted_pixel_count,
        "m3_remaining_visible_pixel_count": plan.remaining_visible_pixel_count,
        "m3_remaining_visible_ratio": plan.remaining_visible_ratio,
        "m3_transparency_ratio": plan.transparency_ratio,
        "m3_mask_sha256": plan.mask_sha256,
        "m3_background_reasons": plan.reasons,
    }


def process_frame_with_m3(
    image: Image.Image,
    *,
    index: int,
    row: int,
    column: int,
    extraction_rect: tuple[int, int, int, int] | None = None,
    extraction_method: str | None = None,
    extraction_confidence: float | None = None,
    config: FramePipelineConfig | None = None,
) -> FramePipelineOutput:
    """Run M3 opaque-background conversion, then reuse the verified M2 frame pipeline."""
    source_decision = decide_source_background_route(image)
    if source_decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND:
        return process_frame(
            image,
            index=index,
            row=row,
            column=column,
            extraction_rect=extraction_rect,
            extraction_method=extraction_method,
            extraction_confidence=extraction_confidence,
            config=config,
        )

    plan = plan_opaque_background_removal(image)
    if plan.status != OpaqueBackgroundStatus.SAFE_REMOVE:
        finding = Finding(
            code="BACKGROUND.REMOVAL_AMBIGUOUS",
            severity="REVIEW",
            message="Opaque source background is not eligible for automatic edge-connected removal",
            measurements={"reasons": plan.reasons},
        )
        result = FrameResult(
            index=index,
            row=row,
            column=column,
            status=FrameStatus.REVIEW,
            extraction_rect=extraction_rect,
            extraction_method=extraction_method,
            extraction_confidence=extraction_confidence,
            processing_mode=ProcessingMode.OPAQUE,
            findings=[finding],
            actions=[],
            evidence={
                "source_background_route": source_decision.route.value,
                "source_route_provenance": source_decision.provenance,
                **_background_evidence(plan),
            },
        )
        return FramePipelineOutput(image=image.copy(), result=result, transparency=source_decision)

    transparent = apply_opaque_background_removal(image, plan)
    output = process_frame(
        transparent,
        index=index,
        row=row,
        column=column,
        extraction_rect=extraction_rect,
        extraction_method=extraction_method,
        extraction_confidence=extraction_confidence,
        config=config,
    )
    output.result.processing_mode = ProcessingMode.OPAQUE
    output.result.actions.insert(0, "REMOVE_OPAQUE_BACKGROUND")
    output.result.evidence.update(
        {
            "source_background_route": source_decision.route.value,
            "source_route_provenance": source_decision.provenance,
            **_background_evidence(plan),
        }
    )
    if output.result.status == FrameStatus.PASS:
        output.result.status = FrameStatus.AUTO_FIXED
    return output
