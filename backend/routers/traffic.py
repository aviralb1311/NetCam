"""
backend/routers/traffic.py

Traffic analytics, time series, OD matrix, heatmap, and observations.
"""

from collections import defaultdict
from fastapi import APIRouter, Query

from backend.services.analytics_engine import analytics_engine

router = APIRouter()


@router.get("/api/analytics")
@router.get("/api/analytics/overview")
def get_analytics_overview():
    """Return complete suite of traffic intelligence analytics calculated from real detections."""
    return analytics_engine.compute_all_analytics()


@router.get("/api/analytics/cameras")
def get_camera_analytics():
    """Return per-camera volume, density, and congestion metrics."""
    data = analytics_engine.compute_all_analytics()
    return data.get("camera_volumes", [])


@router.get("/api/analytics/traffic")
def get_traffic_time_series():
    """Return 15-second time series buckets and peak traffic period."""
    data = analytics_engine.compute_all_analytics()
    return {
        "time_series": data.get("traffic_time_series", []),
        "peak_period": data.get("peak_traffic_period"),
    }


@router.get("/api/analytics/od")
def get_origin_destination():
    """Return full Origin-Destination (OD) transition matrix with vehicle counts and travel times."""
    data = analytics_engine.compute_all_analytics()
    return {
        "od_matrix": data.get("origin_destination_matrix", []),
        "cross_flows": data.get("cross_flows", []),
    }


@router.get("/api/analytics/congestion")
def get_congestion_analytics():
    """Return Relative Congestion Index and bottleneck alerts."""
    data = analytics_engine.compute_all_analytics()
    return {
        "bottlenecks": data.get("bottlenecks", []),
        "junction_volumes": data.get("junction_volumes", []),
        "camera_volumes": data.get("camera_volumes", []),
    }


@router.get("/api/analytics/speed")
def get_speed_analytics():
    """Return mathematically estimated vehicle speed statistics using Haversine distance."""
    data = analytics_engine.compute_all_analytics()
    return {
        "speed_summary": data.get("speed_analytics", {}),
        "speed_samples": data.get("speed_samples", []),
    }


@router.get("/api/analytics/bottlenecks")
def get_bottlenecks():
    """Return bottleneck congestion alerts."""
    data = analytics_engine.compute_all_analytics()
    return data.get("bottlenecks", [])


@router.get("/api/analytics/cross-flows")
def get_cross_flows():
    """Return cross-junction traffic flow patterns."""
    data = analytics_engine.compute_all_analytics()
    return data.get("cross_flows", [])


# ============================================================
# EXTENDED TRAFFIC, OBSERVATIONS & SYSTEM VALIDATION ENDPOINTS
# (SIH 2026 PS 26127 COMPLIANCE)
# ============================================================

@router.get("/api/traffic/summary")
def get_traffic_summary():
    """Return consolidated traffic metrics, KPIs and duration statistics."""
    data = analytics_engine.compute_all_analytics()
    return data.get("kpis", {})


@router.get("/api/traffic/timeseries")
def get_traffic_timeseries(
    interval: str = Query("15s", description="Bucket size: '15s', '1m', '5m', '15m'")
):
    """Return traffic volume time series aggregated by temporal bucket size."""
    data = analytics_engine.compute_all_analytics()
    base_series = data.get("traffic_time_series", [])

    if interval == "15s" or not base_series:
        return {
            "interval": "15s",
            "time_series": base_series,
            "peak_period": data.get("peak_traffic_period"),
        }

    interval_sec_map = {"1m": 60, "5m": 300, "15m": 900}
    target_sec = interval_sec_map.get(interval, 60)

    aggregated = []
    bucket_counts = defaultdict(int)
    bucket_cams = defaultdict(lambda: defaultdict(int))

    for item in base_series:
        s_sec = item["start_sec"]
        bucket_idx = int(s_sec // target_sec)
        bucket_counts[bucket_idx] += item["active_vehicle_count"]
        for c_id, c_cnt in item.get("camera_breakdown", {}).items():
            bucket_cams[bucket_idx][c_id] += c_cnt

    for b_idx in sorted(bucket_counts.keys()):
        t_start = b_idx * target_sec
        t_end = (b_idx + 1) * target_sec
        aggregated.append({
            "window_index": b_idx,
            "start_sec": t_start,
            "end_sec": t_end,
            "time_label": f"{int(t_start // 60):02d}:{int(t_start % 60):02d}",
            "active_vehicle_count": bucket_counts[b_idx],
            "camera_breakdown": dict(bucket_cams[b_idx]),
        })

    peak = max(aggregated, key=lambda x: x["active_vehicle_count"]) if aggregated else None
    return {
        "interval": interval,
        "time_series": aggregated,
        "peak_period": peak,
    }


@router.get("/api/traffic/heatmap")
def get_traffic_heatmap():
    """Return real geospatial heatmap density points calculated from camera coordinates and vehicle volumes."""
    data = analytics_engine.compute_all_analytics()
    cam_vols = data.get("camera_volumes", [])
    max_vol = max((c.get("vehicle_count", 0) for c in cam_vols), default=1) or 1

    heatmap_points = []
    for c in cam_vols:
        lat = c.get("lat")
        lng = c.get("lng")
        cnt = c.get("vehicle_count", 0)
        norm_intensity = round(min(1.0, max(0.1, cnt / float(max_vol))), 3)
        if lat and lng:
            heatmap_points.append({
                "camera_id": c.get("camera_id"),
                "camera_name": c.get("camera_name"),
                "junction_name": c.get("junction_name"),
                "lat": lat,
                "lng": lng,
                "intensity": norm_intensity,
                "vehicle_count": cnt,
                "relative_congestion_index": c.get("relative_congestion_index", 0),
            })
    return {
        "status": "success",
        "point_count": len(heatmap_points),
        "points": heatmap_points,
    }


@router.get("/api/traffic/od")
def get_traffic_od_matrix():
    """Return Origin-Destination transition volume and speeds."""
    data = analytics_engine.compute_all_analytics()
    return {
        "od_matrix": data.get("origin_destination_matrix", []),
        "cross_flows": data.get("cross_flows", []),
    }


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/api/dashboard")
def dashboard_overview():
    """Consolidated endpoint for dashboard initial load."""
    from backend.services.dataset_service import get_cameras_dict
    cameras = get_cameras_dict()
    ana = analytics_engine.compute_all_analytics()
    from backend.services.watchlist_service import watchlist_service
    wl = watchlist_service.get_watchlist()
    return {
        "system": {
            "title": "DRISHTI City-Wide Traffic Intelligence System",
            "status": "ONLINE",
            "cameras_online": len(cameras),
            "version": "3.5.0",
        },
        "cameras": cameras,
        "analytics": ana,
        "kpis": ana.get("kpis", {}),
        "watchlist_count": len(wl),
    }
