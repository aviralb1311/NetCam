"""
backend/routers/vehicles.py

Vehicle search, registry, journey reconstruction, and evidence endpoints.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse

from backend.services.dataset_service import (
    get_cameras_dict,
    get_cameras_list,
    get_camera_info,
    load_detections,
    get_analytics,
    get_map_model,
    PROJECT_ROOT,
    STATIC_PLATES_DIR,
)
from backend.services.plate_search_service import (
    search_by_plate,
    get_all_vehicles_list,
)
from backend.services.video_service import (
    get_video_stream_response,
    get_plate_image_path,
    get_grid_video_path,
    get_or_create_evidence_clip,
)
from backend.services.analytics_engine import analytics_engine
from backend.services.watchlist_service import watchlist_service, normalize_plate

from backend.database.connection import is_db_connected
from backend.services.search_service import MySQLSearchService

router = APIRouter()


# ============================================================
# DATA MODELS
# ============================================================

class WatchlistCreateRequest(BaseModel):
    plate: str = Field(..., min_length=2, description="Vehicle license plate to monitor or blacklist")
    status: str = Field(default="blacklisted", description="'blacklisted' or 'monitored'")
    reason: Optional[str] = Field(default="Registered via API", description="Reason for watchlist entry")
    priority: Optional[str] = Field(default="HIGH", description="Priority level: HIGH, MEDIUM, LOW")


class BlacklistCreateRequest(BaseModel):
    plate: str = Field(..., min_length=2, description="License plate to blacklist")
    reason: str = Field(default="Wanted / suspicious vehicle", description="Reason for blacklisting")
    priority: str = Field(default="HIGH", description="Priority level: HIGH, MEDIUM, LOW")
    status: Optional[str] = Field(default="ACTIVE", description="'ACTIVE' or 'INACTIVE'")
    is_active: Optional[bool] = Field(default=True, description="True for active surveillance")
    notes: Optional[str] = Field(default=None, description="Optional operational notes")


class BlacklistStatusUpdateRequest(BaseModel):
    is_active: bool


class BlacklistUpdateRequest(BaseModel):
    reason: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# ============================================================
# VEHICLE SEARCH & REGISTRY
# ============================================================

def _enrich_vehicle_record(res: Dict[str, Any]) -> Dict[str, Any]:
    """Attach journey metadata to vehicle record (core SIH enrichment)."""
    if not isinstance(res, dict) or not res.get("found"):
        return res
    return res


@router.get("/api/vehicles/search")
def search(
    q: Optional[str] = Query(
        None,
        description="Search by vehicle license plate number or track ID",
    ),
    plate: Optional[str] = Query(
        None,
        description="Search directly by license plate",
    ),
):
    """
    Search complete dataset for a license plate.
    Prioritizes database when connected.
    Gracefully falls back to local in-memory dataset if database is offline.
    """
    query_str = (plate or q or "").strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="Query parameter 'q' or 'plate' is required.")

    if is_db_connected():
        db_res = MySQLSearchService.search_vehicle(query_str)
        if db_res:
            return _enrich_vehicle_record(db_res)

    result = search_by_plate(query_str)
    return _enrich_vehicle_record(result)


@router.get("/api/vehicles/{plate_or_id}")
def get_single_vehicle(plate_or_id: str):
    """Retrieve full vehicle dossier and trajectory by plate or track ID."""
    if is_db_connected():
        db_res = MySQLSearchService.search_vehicle(plate_or_id)
        if db_res:
            return _enrich_vehicle_record(db_res)

    result = search_by_plate(plate_or_id)
    if not result or not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Vehicle '{plate_or_id}' not found.")
    return _enrich_vehicle_record(result)


@router.get("/api/vehicles")
def vehicles(
    matched_only: bool = Query(
        False,
        description="Filter to vehicles seen across multiple cameras",
    ),
    has_plate: Optional[bool] = Query(
        None,
        description="Filter vehicles with detected license plates",
    ),
    camera_id: Optional[str] = Query(
        None,
        description="Filter vehicles that appeared in specific camera",
    ),
    junction_id: Optional[str] = Query(
        None,
        description="Filter vehicles that appeared in specific junction",
    ),
    vehicle_type: Optional[str] = Query(
        None,
        description="Filter by vehicle type (car, truck, bus, etc.)",
    ),
    q: Optional[str] = Query(
        None,
        description="Filter by plate or ID substring",
    ),
    sort_by: str = Query(
        "default",
        description="Sorting order: 'default', 'observations', 'cameras', 'first_seen', 'plate'",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)",
    ),
    page_size: Optional[int] = Query(
        None,
        ge=1,
        le=500,
        description="Page size limit",
    ),
    limit: int = Query(
        500,
        description="Max vehicles to return if page_size is not specified",
    ),
):
    """Return detected vehicles and plate identities for Global Registry with pagination and filters."""
    effective_limit = page_size or limit
    return get_all_vehicles_list(
        limit=effective_limit,
        page=page,
        page_size=page_size,
        matched_only=matched_only,
        has_plate=has_plate,
        camera_id=camera_id,
        junction_id=junction_id,
        vehicle_type=vehicle_type,
        q=q,
        sort_by=sort_by,
    )


@router.get("/api/vehicles/{plate}/journey")
def vehicle_journey(plate: str):
    """Alias endpoint returning full journey reconstruct for a plate."""
    result = search_by_plate(plate)
    if not result.get("found"):
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle with plate '{plate}' not found",
        )
    return result.get("journey", {})


@router.get("/api/vehicles/{plate}/trajectory")
def get_vehicle_trajectory(plate: str):
    """Return chronological GIS trajectory observations for plate."""
    res = search_by_plate(plate)
    if not res.get("found"):
        raise HTTPException(status_code=404, detail=f"Vehicle '{plate}' not found")

    trajectory = res.get("journey", {}).get("trajectory", []) or res.get("trajectory", [])
    return {
        "plate": res.get("plate"),
        "normalized_plate": res.get("normalized_plate"),
        "vehicle_type": res.get("vehicle_type", "car"),
        "observation_count": len(trajectory),
        "trajectory": trajectory,
    }


@router.get("/api/evidence/{plate}")
def get_vehicle_evidence(plate: str):
    """Retrieve full evidence snapshots and CCTV audit trail for a license plate."""
    res = search_by_plate(plate)
    if not res.get("found"):
        raise HTTPException(status_code=404, detail=f"Evidence for '{plate}' not found")
    return {
        "plate": res.get("plate"),
        "normalized_plate": res.get("normalized_plate"),
        "evidence_dossier": res.get("evidence", {}),
        "occurrences": res.get("occurrences", []),
    }


@router.patch("/api/detections/{detection_id}/review")
def review_plate_detection(
    detection_id: str,
    corrected_plate: str = Body(..., embed=True, description="Operator-verified plate string"),
    reviewer_notes: Optional[str] = Body(None, embed=True)
):
    """Human-in-the-loop review mechanism to correct low-confidence or difficult plates."""
    from datetime import datetime, timezone
    norm_corrected = normalize_plate(corrected_plate)
    if not norm_corrected:
        raise HTTPException(status_code=400, detail="Corrected plate cannot be empty")

    updated = False
    if is_db_connected():
        from backend.database.connection import SessionLocal
        from backend.database.models import PlateDetection
        session = SessionLocal()
        try:
            det = session.query(PlateDetection).filter(
                (PlateDetection.id == int(detection_id)) if detection_id.isdigit() else False
            ).first()
            if det:
                det.plate_text = corrected_plate.upper().strip()
                det.normalized_plate = norm_corrected
                det.ocr_confidence = 1.0
                session.commit()
                updated = True
        except Exception:
            session.rollback()
        finally:
            session.close()

    return {
        "success": True,
        "detection_id": detection_id,
        "corrected_plate": corrected_plate.upper().strip(),
        "normalized_plate": norm_corrected,
        "status": "OPERATOR_VERIFIED",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "database_updated": updated,
    }


@router.get("/api/observations")
def get_observations(
    limit: int = Query(100, ge=1, le=1000, description="Max observations to return"),
    camera_id: Optional[str] = Query(None, description="Filter by camera"),
    plate: Optional[str] = Query(None, description="Filter by plate substring"),
):
    """Retrieve atomic vehicle observations from database (or JSON catalog)."""
    if is_db_connected():
        from backend.database.connection import SessionLocal
        from backend.database.models import PlateDetection, Camera, Junction
        from sqlalchemy import select, desc
        session = SessionLocal()
        try:
            q = (
                select(PlateDetection, Camera, Junction)
                .join(Camera, PlateDetection.camera_id == Camera.id)
                .join(Junction, Camera.junction_id == Junction.id)
            )
            if camera_id:
                q = q.filter(Camera.camera_code == camera_id)
            if plate:
                q = q.filter(PlateDetection.normalized_plate.like(f"%{normalize_plate(plate)}%"))
            q = q.order_by(desc(PlateDetection.timestamp_sec)).limit(limit)

            rows = session.execute(q).all()
            results = []
            for det, cam, junc in rows:
                results.append({
                    "id": det.id,
                    "plate": det.plate_text,
                    "normalized_plate": det.normalized_plate,
                    "camera_id": cam.camera_code,
                    "camera_name": cam.camera_name,
                    "junction_id": junc.junction_code,
                    "junction_name": junc.name,
                    "lat": cam.latitude,
                    "lng": cam.longitude,
                    "timestamp_sec": det.timestamp_sec,
                    "confidence": det.ocr_confidence,
                    "plate_image": f"/api/plates/{Path(det.plate_image).name}" if det.plate_image else None,
                })
            return results
        finally:
            session.close()

    dets = load_detections()
    cameras = get_cameras_dict()
    results = []
    for d in dets:
        if not d.get("plate"):
            continue
        cid = d.get("camera_id")
        if camera_id and cid != camera_id:
            continue
        p = d.get("plate", "")
        if plate and normalize_plate(plate) not in normalize_plate(p):
            continue
        cam = cameras.get(cid, {})
        results.append({
            "id": d.get("detection_id"),
            "plate": p,
            "normalized_plate": normalize_plate(p),
            "camera_id": cid,
            "camera_name": cam.get("camera_name", cid),
            "junction_id": d.get("junction_id", ""),
            "junction_name": cam.get("junction_name", d.get("junction_id", "")),
            "lat": cam.get("lat", 23.710299),
            "lng": cam.get("lng", 86.952779),
            "timestamp_sec": d.get("timestamp_sec", 0.0),
            "confidence": d.get("ocr_confidence", 0.9),
            "plate_image": f"/api/plates/{Path(d.get('plate_image')).name}" if d.get("plate_image") else None,
        })
        if len(results) >= limit:
            break
    return results
