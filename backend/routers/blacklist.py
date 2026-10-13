"""
backend/routers/blacklist.py

Alert center, blacklist CRUD, and watchlist management endpoints.
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse

from backend.services.dataset_service import (
    get_cameras_dict,
    get_cameras_list,
    get_camera_info,
    load_detections,
    PROJECT_ROOT,
)
from backend.services.video_service import get_plate_image_path
from backend.services.analytics_engine import analytics_engine
from backend.services.watchlist_service import watchlist_service, normalize_plate
from backend.services.search_service import MySQLSearchService
from backend.services.alert_service import MySQLAlertService
from backend.services.blacklist_service import MySQLBlacklistService

from backend.database.connection import is_db_connected

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
# ALERTS & ANOMALIES
# ============================================================

@router.get("/api/alerts")
def get_all_alerts():
    """
    Consolidated real alert center:
    1. Blacklisted / monitored vehicle alerts from database (or in-memory fallback)
    2. Congestion bottleneck alerts from relative congestion index
    """
    cameras = get_cameras_dict()
    detections = load_detections()
    analytics_data = analytics_engine.compute_all_analytics()

    bottlenecks = analytics_data.get("bottlenecks", [])

    formatted_blacklist_alerts = []
    unread_count = 0

    if is_db_connected():
        db_alerts = MySQLAlertService.get_alerts(unread_only=False, limit=100)
        unread_count = MySQLAlertService.get_unread_count()
        for a in db_alerts:
            formatted_blacklist_alerts.append({
                "id": a["id"],
                "alert_id": a["id"],
                "category": "BLACKLIST",
                "title": f"Blacklisted Vehicle: {a['plate_number']}",
                "priority": a["severity"],
                "severity": a["severity"],
                "description": a["message"],
                "camera_id": a["camera_code"],
                "camera_name": a["camera_name"],
                "junction_name": a["junction_name"],
                "plate": a["plate_number"],
                "timestamp_sec": a.get("timestamp_sec", 0.0),
                "confidence": a.get("confidence", 0.95),
                "plate_image_url": get_plate_image_path(a.get("plate_image")) if a.get("plate_image") else None,
                "is_read": a.get("is_read", False),
                "created_at": a.get("created_at"),
            })
    else:
        wl_alerts = watchlist_service.generate_alerts(detections, cameras)
        for a in wl_alerts:
            formatted_blacklist_alerts.append({
                "id": a["alert_id"],
                "alert_id": a["alert_id"],
                "category": "BLACKLIST",
                "title": f"Target Vehicle Alert: {a['plate']}",
                "priority": a["priority"],
                "severity": a["priority"],
                "description": a["reason"],
                "camera_id": a["camera_id"],
                "camera_name": a["camera_name"],
                "junction_name": a["junction_name"],
                "plate": a["plate"],
                "timestamp_sec": a["timestamp_sec"],
                "confidence": a["confidence"],
                "plate_image_url": a.get("plate_image_url"),
                "is_read": False,
                "created_at": None,
            })
        unread_count = len(formatted_blacklist_alerts)

    formatted_bottleneck_alerts = [
        {
            "id": f"BOTTLENECK_{b['camera_id']}",
            "alert_id": f"BOTTLENECK_{b['camera_id']}",
            "category": "CONGESTION",
            "title": f"Bottleneck Alert: {b['camera_name']}",
            "priority": b["severity"],
            "severity": b["severity"],
            "description": b["reason"],
            "camera_id": b["camera_id"],
            "camera_name": b["camera_name"],
            "junction_name": b["junction_name"],
            "plate": None,
            "timestamp_sec": 0.0,
            "confidence": 1.0,
            "is_read": False,
            "created_at": None,
        }
        for b in bottlenecks
    ]

    all_sorted = sorted(
        [*formatted_blacklist_alerts, *formatted_bottleneck_alerts],
        key=lambda x: (
            0 if x.get("is_read") is False else 1,
            0 if x["priority"] in ("HIGH", "CRITICAL") else 1,
            -x["timestamp_sec"]
        )
    )

    return {
        "total_alerts": len(all_sorted),
        "unread_count": unread_count,
        "blacklist_alerts": formatted_blacklist_alerts,
        "anomaly_alerts": [],
        "congestion_alerts": formatted_bottleneck_alerts,
        "all_alerts_sorted": all_sorted,
    }


@router.get("/api/alerts/unread")
def get_unread_alerts():
    """Poll unread alerts from database for live dashboard notification center."""
    if is_db_connected():
        unread = MySQLAlertService.get_alerts(unread_only=True, limit=20)
        return {
            "unread_count": len(unread),
            "alerts": unread,
            "data_source": "database (sih_traffic_intelligence)",
        }
    return {
        "unread_count": 0,
        "alerts": [],
        "data_source": "offline_fallback",
    }


@router.post("/api/alerts/{alert_id}/read")
@router.patch("/api/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    """Acknowledge / mark an alert as read in database."""
    if is_db_connected():
        success = MySQLAlertService.mark_as_read(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert ID {alert_id} not found.")
        return {"success": True, "alert_id": alert_id, "status": "read"}
    return {"success": True, "alert_id": alert_id, "status": "acknowledged"}


@router.post("/api/alerts/read-all")
def mark_all_alerts_read():
    """Mark all unread alerts as read in database."""
    if is_db_connected():
        count = MySQLAlertService.mark_all_read()
        return {"success": True, "cleared_count": count}
    return {"success": True, "cleared_count": 0}


# ============================================================
# WATCHLIST CRUD (LEGACY COMPATIBILITY)
# ============================================================

@router.get("/api/watchlist")
def get_watchlist():
    """Return all configured watchlist and blacklist entries."""
    return watchlist_service.get_watchlist()


@router.post("/api/watchlist", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(entry: WatchlistCreateRequest):
    """Add a license plate to the persistent watchlist."""
    try:
        created = watchlist_service.add_entry(
            plate=entry.plate,
            status=entry.status,
            reason=entry.reason or "Registered via command center",
            priority=entry.priority or "HIGH",
        )
        return {"success": True, "entry": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/watchlist/{plate}")
def delete_from_watchlist(plate: str):
    """Remove a license plate from the persistent watchlist."""
    deleted = watchlist_service.delete_entry(plate)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Plate '{plate}' not found in watchlist",
        )
    return {"success": True, "message": f"Plate '{plate}' removed from watchlist"}


# ============================================================
# BLACKLIST CRUD
# ============================================================

@router.get("/api/blacklist")
def get_blacklist(
    status_filter: Optional[str] = Query(None, alias="status", description="'active', 'inactive', or None for all"),
    priority: Optional[str] = Query(None, description="'HIGH', 'MEDIUM', 'LOW'"),
):
    """Retrieve all blacklisted vehicles from database with detection count and last seen metadata."""
    if is_db_connected():
        return MySQLBlacklistService.get_all_blacklisted(filter_status=status_filter, priority=priority)

    wl = watchlist_service.get_watchlist()
    detections = load_detections()
    cameras = get_cameras_dict()

    plate_detections = {}
    for d in detections:
        p = normalize_plate(d.get("plate", ""))
        if p:
            plate_detections.setdefault(p, []).append(d)

    results = []
    for i, item in enumerate(wl):
        norm_p = normalize_plate(item.get("plate", ""))
        dets_for_p = plate_detections.get(norm_p, [])
        det_count = len(dets_for_p)
        last_seen = None
        if dets_for_p:
            latest_det = max(dets_for_p, key=lambda x: float(x.get("timestamp_sec", 0.0)))
            cid = latest_det.get("camera_id")
            cam = cameras.get(cid, {})
            last_seen = {
                "timestamp_sec": latest_det.get("timestamp_sec"),
                "camera_code": cid,
                "camera_name": cam.get("camera_name", cid),
                "junction_name": cam.get("junction_name", latest_det.get("junction_id", "Vivekananda Sarani")),
                "detected_at": None,
            }

        is_active = item.get("is_active") if "is_active" in item else (item.get("status") == "blacklisted")
        entry_priority = item.get("priority", "HIGH").upper()

        if status_filter == "active" and not is_active:
            continue
        if status_filter == "inactive" and is_active:
            continue
        if priority and entry_priority != priority.upper():
            continue

        results.append({
            "id": i + 1,
            "plate_number": item["plate"],
            "normalized_plate": norm_p,
            "reason": item.get("reason", "Watchlist entry"),
            "priority": entry_priority,
            "is_active": is_active,
            "notes": item.get("notes"),
            "created_at": item.get("added_at"),
            "detection_count": det_count,
            "last_seen": last_seen,
        })
    return results


@router.post("/api/blacklist", status_code=status.HTTP_201_CREATED)
def add_blacklist(entry: BlacklistCreateRequest):
    """Add a vehicle to the operator blacklist (database primary with retroactive event matching)."""
    try:
        active_flag = entry.is_active if entry.is_active is not None else (entry.status != "INACTIVE")
        if is_db_connected():
            res = MySQLBlacklistService.add_blacklisted_vehicle(
                plate_number=entry.plate,
                reason=entry.reason,
                priority=entry.priority,
                notes=entry.notes,
                is_active=active_flag,
            )
            try:
                watchlist_service.add_entry(entry.plate, status="blacklisted" if active_flag else "monitored", reason=entry.reason, priority=entry.priority)
            except Exception:
                pass
            return {"success": True, "entry": res}
        else:
            created = watchlist_service.add_entry(
                plate=entry.plate,
                status="blacklisted" if active_flag else "monitored",
                reason=entry.reason,
                priority=entry.priority,
            )
            return {"success": True, "entry": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to blacklist: {e}")


@router.get("/api/blacklist/{vehicle_id}")
def get_single_blacklist(vehicle_id: int):
    """Retrieve full details for a single blacklisted vehicle including occurrences and alerts."""
    if is_db_connected():
        details = MySQLBlacklistService.get_blacklist_details(vehicle_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")
        return details

    wl = watchlist_service.get_watchlist()
    if 0 <= vehicle_id - 1 < len(wl):
        item = wl[vehicle_id - 1]
        return {
            "id": vehicle_id,
            "plate_number": item["plate"],
            "normalized_plate": normalize_plate(item["plate"]),
            "reason": item.get("reason", "Watchlist entry"),
            "priority": item.get("priority", "HIGH"),
            "is_active": item.get("is_active", item.get("status") == "blacklisted"),
            "occurrences": [],
            "alerts": [],
        }
    raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")


@router.patch("/api/blacklist/{vehicle_id}/status")
def toggle_blacklist_status(vehicle_id: int, payload: BlacklistStatusUpdateRequest):
    """Activate or deactivate a blacklisted vehicle without deleting the record."""
    if is_db_connected():
        updated = MySQLBlacklistService.update_blacklisted_vehicle(vehicle_id, is_active=payload.is_active)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")
        return {"success": True, "entry": updated}

    wl = watchlist_service.get_watchlist()
    if 0 <= vehicle_id - 1 < len(wl):
        wl[vehicle_id - 1]["is_active"] = payload.is_active
        wl[vehicle_id - 1]["status"] = "blacklisted" if payload.is_active else "inactive"
        watchlist_service._save_watchlist(wl)
        return {"success": True, "entry": wl[vehicle_id - 1]}
    raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")


@router.put("/api/blacklist/{vehicle_id}")
def update_blacklist(vehicle_id: int, entry: BlacklistUpdateRequest):
    """Update a blacklisted vehicle's details or active status."""
    if is_db_connected():
        updated = MySQLBlacklistService.update_blacklisted_vehicle(
            vehicle_id=vehicle_id,
            reason=entry.reason,
            priority=entry.priority,
            is_active=entry.is_active,
            notes=entry.notes,
        )
        if not updated:
            raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")
        return {"success": True, "entry": updated}

    wl = watchlist_service.get_watchlist()
    if 0 <= vehicle_id - 1 < len(wl):
        item = wl[vehicle_id - 1]
        if entry.is_active is not None:
            item["is_active"] = entry.is_active
            item["status"] = "blacklisted" if entry.is_active else "inactive"
        if entry.reason is not None:
            item["reason"] = entry.reason
        if entry.priority is not None:
            item["priority"] = entry.priority
        if entry.notes is not None:
            item["notes"] = entry.notes
        watchlist_service._save_watchlist(wl)
        return {"success": True, "entry": item}
    raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")


@router.delete("/api/blacklist/{vehicle_id}")
def delete_blacklist(vehicle_id: int):
    """Permanently delete a vehicle from the blacklist."""
    if is_db_connected():
        deleted = MySQLBlacklistService.delete_blacklisted_vehicle(vehicle_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")
        return {"success": True, "message": f"Blacklisted vehicle ID {vehicle_id} deleted."}

    wl = watchlist_service.get_watchlist()
    if 0 <= vehicle_id - 1 < len(wl):
        removed = wl.pop(vehicle_id - 1)
        watchlist_service._save_watchlist(wl)
        return {"success": True, "message": f"Blacklisted vehicle {removed.get('plate')} deleted."}
    raise HTTPException(status_code=404, detail=f"Blacklisted vehicle ID {vehicle_id} not found.")


@router.get("/api/blacklist/{plate}/events")
def get_blacklist_events(plate: str):
    """Get all detection events and timestamps across cameras for a blacklisted license plate."""
    if is_db_connected():
        events = MySQLBlacklistService.get_events_for_plate(plate)
        if events:
            return {"plate": plate, "events": events, "count": len(events)}

    from backend.services.plate_search_service import search_by_plate
    journey = search_by_plate(plate)
    events = []
    if journey and journey.get("trajectory"):
        for ev in journey["trajectory"]:
            events.append({
                "id": ev.get("event_id") or ev.get("detection_id"),
                "camera_code": ev.get("camera_id"),
                "camera_name": ev.get("camera_name"),
                "junction_name": ev.get("junction_name"),
                "timestamp_sec": ev.get("timestamp_sec"),
                "time_str": f"T+{ev.get('timestamp_sec', 0.0):.1f}s",
                "ocr_confidence": ev.get("ocr_confidence", 0.95),
                "plate_image": ev.get("plate_image_url") or ev.get("plate_image"),
                "event_type": "INTERCEPTION",
                "message": f"Optical sighting of {plate} at {ev.get('camera_name', ev.get('camera_id'))}",
            })
    return {"plate": plate, "events": events, "count": len(events)}
