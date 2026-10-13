"""
backend/routers/cameras.py

Camera endpoints: listing, single camera info, video streaming, evidence clips, and YOLO tracks.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse

from backend.services.dataset_service import (
    get_cameras_dict,
    get_cameras_list,
    get_camera_info,
    load_detections,
    get_map_model,
    PROJECT_ROOT,
    STATIC_PLATES_DIR,
)
from backend.services.video_service import (
    get_video_stream_response,
    get_plate_image_path,
    get_grid_video_path,
    get_or_create_evidence_clip,
)
from backend.services.plate_search_service import (
    search_by_plate,
    get_all_vehicles_list,
)

router = APIRouter()


@router.get("/api/cameras")
def get_cameras():
    """Return all camera configurations with live metadata."""
    return get_cameras_dict()


@router.get("/api/cameras/{camera_id}")
def get_single_camera(camera_id: str):
    info = get_camera_info(camera_id)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found",
        )
    return info


@router.get("/api/cameras/{camera_id}/video")
def stream_camera_video(
    camera_id: str,
    request: Request,
    quality: Optional[str] = Query("high", description="'grid', 'low', or 'high'"),
):
    """
    Serve browser-compatible H.264 MP4 video.
    When quality='grid' or 'low', serves optimized 480p sub-stream if available.
    Supports HTTP 206 partial/range responses for seeking.
    """
    info = get_camera_info(camera_id)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found",
        )
    canonical_id = info.get("camera_id", camera_id)

    if quality in ("grid", "low"):
        grid_path = get_grid_video_path(canonical_id)
        if grid_path and grid_path.exists():
            range_header = request.headers.get("range")
            return get_video_stream_response(grid_path, range_header)

    raw_path = info.get("video_path")
    if raw_path:
        video_path = PROJECT_ROOT / raw_path
        if video_path.exists():
            range_header = request.headers.get("range")
            return get_video_stream_response(video_path, range_header)

    remote_url = info.get("remote_video_url")
    if remote_url:
        return RedirectResponse(url=remote_url, status_code=307)

    raise HTTPException(
        status_code=404,
        detail=f"Video feed for '{camera_id}' is neither available locally nor configured with remote_video_url.",
    )


@router.get("/api/cameras/{camera_id}/evidence")
def get_camera_evidence_clip(
    camera_id: str,
    request: Request,
    timestamp: float = Query(..., description="Detection timestamp in seconds"),
    pre_roll: float = Query(5.0, description="Pre-roll duration in seconds (default 5)"),
    duration: float = Query(15.0, description="Total evidence clip duration in seconds (default 15)"),
):
    """
    Serve a lightweight, cached server-side trimmed MP4 clip around the detection moment.
    Eliminates client-side seeking through 500+ MB CCTV source files.
    """
    info = get_camera_info(camera_id)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Camera '{camera_id}' not found",
        )
    canonical_id = info.get("camera_id", camera_id)

    raw_path = info.get("video_path")
    video_path = (PROJECT_ROOT / raw_path) if raw_path else None
    if video_path and video_path.exists():
        clip_path = get_or_create_evidence_clip(
            camera_id=canonical_id,
            source_path=video_path,
            timestamp=timestamp,
            pre_roll=pre_roll,
            duration=duration,
        )
        range_header = request.headers.get("range")
        return get_video_stream_response(clip_path, range_header)

    remote_url = info.get("remote_video_url")
    if remote_url:
        return RedirectResponse(url=remote_url, status_code=307)

    raise HTTPException(
        status_code=404,
        detail=f"Evidence source video for '{camera_id}' not found on server.",
    )


@router.get("/api/cameras/{camera_id}/yolo-tracks")
def get_camera_yolo_tracks(
    camera_id: str,
    timestamp: float = Query(..., description="Detection timestamp in seconds"),
    plate: Optional[str] = Query(None, description="Suspect license plate string"),
    pre_roll: float = Query(5.0, description="Pre-roll duration in seconds (default 5)"),
    duration: float = Query(15.0, description="Total evidence clip duration in seconds (default 15)"),
):
    """
    Dynamically run or retrieve authentic YOLO vehicle tracking telemetry for an evidence clip.
    Returns normalized bounding box coordinates for each frame at 10-60 FPS.
    """
    from backend.services.yolo_evidence_service import get_or_create_evidence_yolo_tracks
    info = get_camera_info(camera_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    raw_path = info.get("video_path")
    if not raw_path:
        raise HTTPException(status_code=404, detail=f"No video path configured for {camera_id}")

    video_path = PROJECT_ROOT / raw_path
    clip_path = get_or_create_evidence_clip(
        camera_id=camera_id,
        source_path=video_path,
        timestamp=timestamp,
        pre_roll=pre_roll,
        duration=duration,
    )

    return get_or_create_evidence_yolo_tracks(
        camera_id=camera_id,
        clip_path=clip_path,
        timestamp=timestamp,
        plate=plate,
        pre_roll=pre_roll,
        duration=duration,
    )


@router.get("/api/plates/{image_name:path}")
def get_plate_crop(image_name: str):
    """Serve real plate crop images from static/plates."""
    path = get_plate_image_path(image_name)
    if not path or not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Plate image '{image_name}' not found",
        )
    from fastapi.responses import FileResponse
    return FileResponse(path, media_type="image/jpeg")


@router.get("/api/map/model")
def map_model():
    """Return real geo-referenced coordinate model for Junction A & B."""
    return get_map_model()
