from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .border import detect_border, remove_border
from .content import analyze_alpha_content
from .fit import fit_rgba_to_canvas
from .line_profile import validate_static_sticker
from .metadata import detect_corner_metadata, remove_detected_metadata
from .models import Finding, FrameResult, FrameStatus, ProcessingMode
from .routing import BackgroundRoute, TransparencyDecision, decide_source_background_route


@dataclass(frozen=True)
class FramePipelineConfig:
    target_size: tuple[int, int] = (370, 320)
    margin: int = 10
    remove_border: bool = True
    remove_metadata: bool = True
    border_auto_threshold: float = 0.995
    metadata_auto_threshold: float = 0.72


@dataclass(frozen=True)
class FramePipelineOutput:
    image: Image.Image
    result: FrameResult
    transparency: TransparencyDecision


def _finding(code: str, message: str, **measurements: object) -> Finding:
    return Finding(code=code, severity="REVIEW", message=message, measurements=dict(measurements))


def process_frame(
    image: Image.Image,
    *,
    index: int,
    row: int,
    column: int,
    extraction_rect: tuple[int, int, int, int] | None = None,
    config: FramePipelineConfig | None = None,
) -> FramePipelineOutput:
    """Run the M2 frame workflow without opaque-background segmentation.

    Source transparency is captured after optional border cropping and before any
    metadata cleanup that can introduce alpha. Opaque frames intentionally stop in
    REVIEW until the M3 background-removal provider is available.
    """
    cfg = config or FramePipelineConfig()
    working = image.copy()
    actions: list[str] = []
    findings: list[Finding] = []

    if cfg.remove_border:
        border = detect_border(working)
        if border.detected:
            if border.confidence < cfg.border_auto_threshold:
                findings.append(
                    _finding(
                        "BORDER.LOW_CONFIDENCE",
                        "Border evidence is insufficient for automatic removal",
                        confidence=border.confidence,
                    )
                )
                decision = decide_source_background_route(working)
                return FramePipelineOutput(
                    image=working,
                    transparency=decision,
                    result=FrameResult(
                        index=index,
                        row=row,
                        column=column,
                        status=FrameStatus.REVIEW,
                        extraction_rect=extraction_rect,
                        processing_mode=(
                            ProcessingMode.TRANSPARENT
                            if decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
                            else ProcessingMode.OPAQUE
                        ),
                        findings=findings,
                        actions=actions,
                    ),
                )
            working = remove_border(
                working,
                border,
                auto_threshold=cfg.border_auto_threshold,
            )
            actions.append("REMOVE_BORDER")

    # SSOT/ADR-023: capture source-frame routing before alpha-generating cleanup.
    source_decision = decide_source_background_route(working)

    if cfg.remove_metadata:
        metadata = detect_corner_metadata(working)
        if metadata.mask is not None and metadata.bbox is not None:
            if metadata.confidence < cfg.metadata_auto_threshold:
                findings.append(
                    _finding(
                        "METADATA.LOW_CONFIDENCE",
                        "Metadata evidence is insufficient for automatic removal",
                        confidence=metadata.confidence,
                    )
                )
            else:
                working = remove_detected_metadata(
                    working,
                    metadata,
                    auto_threshold=cfg.metadata_auto_threshold,
                )
                actions.append("REMOVE_FRAME_METADATA")
        elif "ambiguous" in metadata.reason.lower():
            findings.append(
                _finding(
                    "METADATA.AMBIGUOUS",
                    "Multiple metadata candidates require review",
                    confidence=metadata.confidence,
                )
            )

    mode = (
        ProcessingMode.TRANSPARENT
        if source_decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
        else ProcessingMode.OPAQUE
    )

    if findings:
        return FramePipelineOutput(
            image=working,
            transparency=source_decision,
            result=FrameResult(
                index=index,
                row=row,
                column=column,
                status=FrameStatus.REVIEW,
                extraction_rect=extraction_rect,
                processing_mode=mode,
                findings=findings,
                actions=actions,
            ),
        )

    if source_decision.route == BackgroundRoute.REMOVE_BACKGROUND:
        findings.append(
            _finding(
                "BACKGROUND.REMOVAL_REQUIRED",
                "Opaque source frame requires the M3 background-removal stage",
                source_provenance=source_decision.provenance,
            )
        )
        return FramePipelineOutput(
            image=working,
            transparency=source_decision,
            result=FrameResult(
                index=index,
                row=row,
                column=column,
                status=FrameStatus.REVIEW,
                extraction_rect=extraction_rect,
                processing_mode=ProcessingMode.OPAQUE,
                findings=findings,
                actions=actions,
            ),
        )

    content = analyze_alpha_content(working)
    if content.bbox is None:
        findings.append(_finding("CONTENT.EMPTY", "No visible sticker content was detected"))
        return FramePipelineOutput(
            image=working,
            transparency=source_decision,
            result=FrameResult(
                index=index,
                row=row,
                column=column,
                status=FrameStatus.FAIL,
                extraction_rect=extraction_rect,
                processing_mode=ProcessingMode.TRANSPARENT,
                findings=findings,
                actions=actions,
            ),
        )

    fitted = fit_rgba_to_canvas(working, cfg.target_size, margin=cfg.margin)
    if fitted.scale != 1.0 or fitted.offset != (0, 0):
        actions.append("SMART_FIT")
    working = fitted.image

    validation = validate_static_sticker(working)
    if not validation.valid:
        findings.extend(
            _finding(code=f"EXPORT.{code}", message=f"Export profile violation: {code}")
            for code in validation.findings
        )
        status = FrameStatus.REVIEW
    else:
        status = FrameStatus.AUTO_FIXED if actions else FrameStatus.PASS

    final_content = analyze_alpha_content(working)
    return FramePipelineOutput(
        image=working,
        transparency=source_decision,
        result=FrameResult(
            index=index,
            row=row,
            column=column,
            status=status,
            extraction_rect=extraction_rect,
            processing_mode=ProcessingMode.TRANSPARENT,
            content_bbox=final_content.bbox,
            findings=findings,
            actions=actions,
        ),
    )
