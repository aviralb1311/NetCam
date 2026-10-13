# DRISHTI API Reference

Base URL: `http://127.0.0.1:8000`
Interactive Docs: `http://127.0.0.1:8000/docs`

---

## Camera Endpoints

### `GET /api/cameras`
List all camera nodes with metadata.

**Response:**
```json
[
  {
    "id": 1,
    "camera_code": "junction_A_camera_01",
    "camera_name": "Camera 01",
    "junction_id": 1,
    "video_path": "dataset/junction_A/camera_01.mp4",
    "latitude": 23.710299,
    "longitude": 86.952779,
    "status": "ACTIVE"
  }
]
```

### `GET /api/cameras/{camera_id}/video`
Stream video file with HTTP 206 Partial Content support.

**Headers:** `Range: bytes=0-1023`
**Response:** Video stream (video/mp4)

---

## Vehicle & Detection Endpoints

### `GET /api/observations`
List all plate detections with pagination.

**Query Parameters:**
- `limit` (default: 100)
- `offset` (default: 0)
- `camera_id` (optional filter)
- `normalized_plate` (optional filter)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "camera_id": 1,
      "normalized_plate": "WB37E1275",
      "plate_text": "WB 37 E 1275",
      "ocr_confidence": 0.92,
      "timestamp_sec": 123.45,
      "plate_image": "static/plates/WB37E1275_001.jpg"
    }
  ],
  "total": 144
}
```

### `GET /api/vehicles/{normalized_plate}/trajectory`
Get cross-camera trajectory for a specific vehicle.

**Response:**
```json
{
  "plate": "WB37E1275",
  "observations": [
    {
      "camera_id": 1,
      "camera_name": "Camera 01",
      "junction_name": "Junction A",
      "latitude": 23.710299,
      "longitude": 86.952779,
      "timestamp_sec": 123.45,
      "direction": "APPROACHING"
    },
    {
      "camera_id": 3,
      "camera_name": "Camera 01",
      "junction_name": "Junction B",
      "latitude": 23.713932,
      "longitude": 86.952211,
      "timestamp_sec": 156.78,
      "direction": "DEPARTING"
    }
  ],
  "total_cameras": 2,
  "total_distance_m": 408.3,
  "average_speed_kmh": 48.0
}
```

### `GET /api/vehicles/search`
Search vehicles by plate (partial match supported).

**Query Parameters:**
- `q` — Search query (plate number)

**Response:**
```json
{
  "results": [
    {
      "normalized_plate": "WB37E1275",
      "detection_count": 3,
      "first_seen": 123.45,
      "last_seen": 156.78,
      "cameras": [1, 3],
      "is_blacklisted": false
    }
  ]
}
```

---

## Traffic Analytics Endpoints

### `GET /api/traffic/timeseries`
Time-series vehicle volume data.

**Query Parameters:**
- `camera_id` (optional)
- `interval_sec` (default: 60)

**Response:**
```json
[
  {"timestamp": 0, "count": 12},
  {"timestamp": 60, "count": 18},
  {"timestamp": 120, "count": 15}
]
```

### `GET /api/traffic/heatmap`
Real-time density heatmap across all cameras.

**Response:**
```json
{
  "points": [
    {"lat": 23.710299, "lng": 86.952779, "weight": 45},
    {"lat": 23.713932, "lng": 86.952211, "weight": 32}
  ]
}
```

### `GET /api/traffic/od`
Origin-Destination matrix with travel times.

**Response:**
```json
{
  "matrix": [
    {
      "origin_junction": "Junction A",
      "destination_junction": "Junction B",
      "volume": 28,
      "avg_travel_time_sec": 33.3,
      "avg_speed_kmh": 48.0,
      "distance_m": 408.3
    }
  ]
}
```

### `GET /api/traffic/congestion`
Relative Congestion Index (RCI) per junction.

**Response:**
```json
[
  {
    "junction_id": 1,
    "junction_name": "Junction A",
    "rci": 1.45,
    "current_volume": 45,
    "baseline_volume": 31,
    "status": "CONGESTED"
  }
]
```

---

## Blacklist & Alert Endpoints

### `GET /api/blacklist`
List all blacklisted vehicles.

**Response:**
```json
[
  {
    "id": 1,
    "plate_number": "WB37E1275",
    "normalized_plate": "WB37E1275",
    "reason": "Stolen vehicle",
    "priority": "HIGH",
    "is_active": true,
    "detection_count": 3,
    "last_detected": "2026-09-12T14:30:00"
  }
]
```

### `POST /api/blacklist`
Add a new blacklisted vehicle.

**Request Body:**
```json
{
  "plate_number": "WB37E1275",
  "reason": "Suspicious activity",
  "priority": "HIGH",
  "notes": "Reported by traffic police"
}
```

### `PATCH /api/blacklist/{id}`
Update blacklist entry.

**Request Body:**
```json
{
  "reason": "Updated reason",
  "priority": "MEDIUM",
  "is_active": false
}
```

### `DELETE /api/blacklist/{id}`
Delete or deactivate blacklist entry.

### `GET /api/alerts`
List all alerts (paginated).

**Query Parameters:**
- `unread_only` (boolean, default: false)
- `limit` (default: 50)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "alert_type": "BLACKLISTED_VEHICLE",
      "severity": "CRITICAL",
      "plate_number": "WB37E1275",
      "camera_id": 1,
      "message": "Blacklisted vehicle WB37E1275 detected at Junction A Camera 01",
      "is_read": false,
      "created_at": "2026-09-12T14:30:00"
    }
  ],
  "unread_count": 3
}
```

### `POST /api/alerts/{id}/read`
Mark alert as read.

---

## System Endpoints

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-09-12T14:30:00"
}
```

### `GET /api/system/validation`
System validation metrics for SIH compliance.

**Response:**
```json
{
  "ocr_accuracy": {
    "exact_match_pct": 90.97,
    "character_accuracy_pct": 98.27,
    "avg_confidence_pct": 90.6,
    "meets_sih_requirement": true
  },
  "pipeline_latency_ms": 450.1,
  "active_cameras": 4,
  "indexed_detections": 144,
  "test_suite_pass_rate": "36/37 (1 pre-existing video path failure)"
}
```

---

## Error Responses

All endpoints return standard error format:
```json
{
  "detail": "Error description",
  "status_code": 404
}
```

Common HTTP status codes:
- `200` — Success
- `400` — Bad Request (validation error)
- `404` — Not Found
- `500` — Internal Server Error
- `503` — Service Unavailable (database disconnected)