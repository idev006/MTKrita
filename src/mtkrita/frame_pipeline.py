from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .border import BorderDetection, detect_border, remove_border
from .content import analyze_alpha_content
from .fit import fit_rgba_to_canvas
from .line_profile import validate_static_sticker
from .metadata import MetadataDetection, detect_corner_metadata, remove_detected_metadata
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


def _route_evidence(decision: TransparencyDecision) -> dict[str, object]:
    return {
        "background_route": decision.route.value,
        "route_provenance": decision.provenance,
        "has_alpha_channel": decision.has_alpha_channel,
        "meaningful_transparency": decision.meaningful_transparency,
        "alpha_min": decision.alpha_min,
        "alpha_max": decision.alpha_max,
        "transparent_pixel_ratio": decision.transparent_pixel_ratio,
        "route_reason": decision.reason,
    }


def _border_evidence(detection: BorderDetection) -> dict[str, object]:
    sides: dict[str, object] = {}
    for name in ("left", "top", "right", "bottom"):
        side = getattr(detection, name)
        if side is None:
            continue
        sides[name] = {
            "offset": side.offset,
            "thickness": side.thickness,
            "color": side.color,
            "confidence": side.confidence,
            "contact_risk": side.contact_risk,
            "contact_fraction": side.contact_fraction,
            "contact_ranges": side.contact_ranges,
        }
    return {
        "border_detected": detection.detected,
        "border_confidence": detection.confidence,
        "border_contact_risk": detection.contact_risk,
        "border_sides": sides,
    }


def _metadata_evidence(detection: MetadataDetection) -> dict[str, object]:
    return {
        "metadata_confidence": detection.confidence,
        "metadata_reason": detection.reason,
        "metadata_bbox": detection.bbox,
        "metadata_candidate_count": detection.candidate_count,
        "metadata_anchored_candidate_count": detection.anchored_candidate_count,
        "metadata_area_ratio": detection.area_ratio,
        "metadata_fill_ratio": detection.fill_ratio,
        "metadata_compactness": detection.compactness,
        "metadata_anchor_distance": detection.anchor_distance,
        "metadata_dominance_margin": detection.dominance_margin,
    }


def _early_review(
    working: Image.Image,
    *,
    index: int,
    row: int,
    column: int,
    extraction_rect: tuple[int, int, int, int] | None,
    extraction_method: str | None,
    extraction_confidence: float | None,
    findings: list[Finding],
    actions: list[str],
    evidence: dict[str, object],
) -> FramePipelineOutput:
    decision = decide_source_background_route(working)
    evidence.update(_route_evidence(decision))
    mode = (
        ProcessingMode.TRANSPARENT
        if decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
        else ProcessingMode.OPAQUE
    )
    return FramePipelineOutput(
        image=working,
        transparency=decision,
        result=FrameResult(
            index=index,
            row=row,
            column=column,
            status=FrameStatus.REVIEW,
            extraction_rect=extraction_rect,
            extraction_method=extraction_method,
            extraction_confidence=extraction_confidence,
            processing_mode=mode,
            findings=findings,
            actions=actions,
            evidence=evidence,
        ),
    )


def process_frame(
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
    """Run the M2 frame workflow without opaque-background segmentation."""
    cfg = config or FramePipelineConfig()
    working = image.copy()
    actions: list[str] = []
    findings: list[Finding] = []
    evidence: dict[str, object] = {}

    if cfg.remove_border:
        border = detect_border(working)
        evidence.update(_border_evidence(border))
        if border.detected:
            if border.contact_risk:
                findings.append(
                    _finding(
                        "BORDER.CONTACT_RISK",
                        "Border may be connected to artwork or metadata; automatic crop refused",
                    )
                )
                return _early_review(
                    working,
                    index=index,
                    row=row,
                    column=column,
                    extraction_rect=extraction_rect,
                    extraction_method=extraction_method,
                    extraction_confidence=extraction_confidence,
                    findings=findings,
                    actions=actions,
                    evidence=evidence,
                )
            if border.confidence < cfg.border_auto_threshold:
                findings.append(
                    _finding(
                        "BORDER.LOW_CONFIDENCE",
                        "Border evidence is insufficient for automatic removal",
                        confidence=border.confidence,
                    )
                )
                return _early_review(
                    working,
                    index=index,
                    row=row,
                    column=column,
                    extraction_rect=extraction_rect,
                    extraction_method=extraction_method,
                    extraction_confidence=extraction_confidence,
                    findings=findings,
                    actions=actions,
                    evidence=evidence,
                )
            working = remove_border(working, border, auto_threshold=cfg.border_auto_threshold)
            actions.append("REMOVE_BORDER")

    # ADR-023: capture source routing before metadata cleanup can create alpha.
    source_decision = decide_source_background_route(working)
    evidence.update(_route_evidence(source_decision))

    if cfg.remove_metadata:
        metadata = detect_corner_metadata(working)
        evidence.update(_metadata_evidence(metadata))
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
                    working, metadata, auto_threshold=cfg.metadata_auto_threshold
                )
                actions.append("REMOVE_FRAME_METADATA")
        elif "ambiguous" in metadata.reason.lower():
            findings.append(
                _finding(
                    "METADATA.AMBIGUOUS",
                    "Multiple anchored metadata candidates require review",
                    confidence=metadata.confidence,
                    dominance_margin=metadata.dominance_margin,
                )
            )

    mode = (
        ProcessingMode.TRANSPARENT
        if source_decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
        else ProcessingMode.OPAQUE
    )
    common = {
        "index": index,
        "row": row,
        "column": column,
        "extraction_rect": extraction_rect,
        "extraction_method": extraction_method,
        "extraction_confidence": extraction_confidence,
        "processing_mode": mode,
        "findings": findings,
        "actions": actions,
        "evidence": evidence,
    }

    if findings:
        return FramePipelineOutput(
            image=working,
            transparency=source_decision,
            result=FrameResult(status=FrameStatus.REVIEW, **common),
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
            result=FrameResult(status=FrameStatus.REVIEW, **common),
        )

    content = analyze_alpha_content(working)
    evidence["pre_fit_content_bbox"] = content.bbox
    evidence["pre_fit_occupancy_ratio"] = content.occupancy_ratio
    evidence["pre_fit_touches_edge"] = content.touches_edge
    if content.bbox is None:
        findings.append(_finding("CONTENT.EMPTY", "No visible sticker content was detected"))
        return FramePipelineOutput(
            image=working,
            transparency=source_decision,
            result=FrameResult(status=FrameStatus.FAIL, **common),
        )

    fitted = fit_rgba_to_canvas(working, cfg.target_size, margin=cfg.margin)
    evidence["fit_scale"] = fitted.scale
    evidence["fit_offset"] = fitted.offset
    if fitted.scale != 1.0 or fitted.offset != (0, 0):
        actions.append("SMART_FIT")
    working = fitted.image

    validation = validate_static_sticker(working)
    evidence["export_findings"] = validation.findings
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
        result=FrameResult(status=status, content_bbox=final_content.bbox, **common),
    )
