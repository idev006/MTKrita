from __future__ import annotations

from .exporter import export_png_atomic
from .frame_pipeline import FramePipelineConfig
from .frame_pipeline_m3 import process_frame_with_m3
from .m2_executor import M2FrameTaskExecutor
from .m2_task_descriptor import M2_FRAME_TASK_TYPE, M2PipelineConfigSnapshot
from .worker_tasks import ExecuteTaskRequest, TaskExecutor


def build_builtin_task_executor(request: ExecuteTaskRequest) -> TaskExecutor | None:
    """Return a statically registered built-in executor for an approved task type.

    Task payloads never select modules, callables, import paths, or arbitrary code.
    """
    if request.descriptor.get("task_type") != M2_FRAME_TASK_TYPE:
        return None
    return M2FrameTaskExecutor(
        frame_processor=process_frame_with_m3,
        config_factory=build_frame_pipeline_config,
        png_writer=export_png_atomic,
    )


def build_frame_pipeline_config(snapshot: M2PipelineConfigSnapshot) -> FramePipelineConfig:
    return FramePipelineConfig(
        target_size=(snapshot.target_width, snapshot.target_height),
        margin=snapshot.margin,
        remove_border=snapshot.remove_border,
        remove_metadata=snapshot.remove_metadata,
        border_auto_threshold=snapshot.border_auto_threshold,
        metadata_auto_threshold=snapshot.metadata_auto_threshold,
    )
