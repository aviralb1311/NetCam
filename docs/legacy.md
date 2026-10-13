# DRISHTI Legacy Code Archive

## Overview

The `legacy/` directory contains archived backend services and frontend components that have been removed from the active codebase but preserved for historical reference and potential future use.

---

## What's in `legacy/`

| Path | Type | Original Purpose | Status |
|------|------|-----------------|--------|
| `legacy/backend/` | Python modules | Experimental backend services | Archived — not imported |
| `legacy/components/` | React components | Experimental/legacy UI components | Archived — not imported |

---

## Archived Backend Services (`legacy/backend/`)

### Removed Services
- `mysql_database_service.py` — MySQL-specific database service (replaced by `database_service.py` using SQLite)
- `pipeline_service.py` — End-to-end CV pipeline orchestration (CPU-intensive, replaced by pre-computed detections)
- `model_service.py` — YOLOv8 model loading and inference wrapper
- `ocr_service.py` — EasyOCR inference and confidence scoring
- `tracking_service.py` — ByteTrack vehicle tracking integration
- `stream_service.py` — OpenCV video stream processing
- `export_service.py` — Batch export of trajectories and evidence

### Rationale
These services were archived because:
1. Detection data is pre-computed and stored in SQLite for development/demo
2. ML dependencies (torch, ultralytics, easyocr) removed from `requirements.txt`
3. Core API now uses modular routers + thin services for DB access only

---

## Archived Frontend Components (`legacy/components/`)

### Removed Components
| Component | Original Purpose | Replacement |
|-----------|-----------------|-------------|
| `DrishtiGptCopilot.jsx` | AI copilot chat interface | Removed (unused) |
| `AnalyticsSection.jsx` | Dashboard analytics section | Functionality covered by `TrafficAnalyticsPage` |
| `VehicleTrajectoryTracker.jsx` | Cross-camera trajectory visualization | Integrated into `MapView` |
| `PredictiveInterception.jsx` | Predictive vehicle interception | Removed (unused) |
| `JourneyRoute.jsx` | Route visualization | Integrated into `MapView` |
| `JourneyTimeline.jsx` | Timeline view of vehicle journey | Integrated into `VehicleDetailModal` |
| `EvidenceDossier.jsx` | Evidence dossier compilation | Replaced by `EvidencePlaybackModal` |
| `EChallan.jsx` | E-challan issuance UI | Removed (unused) |
| `CorridorTelemetry.jsx` | Corridor-level telemetry | Removed (unused) |
| `AiPipelineStatus.jsx` | AI pipeline status monitor | Removed (unused) |

### Active Frontend Components (15 total)
| Component | Purpose |
|-----------|---------|
| `CameraGrid.jsx` | Live CCTV feeds with HTTP 206 streaming |
| `MapView.jsx` | Leaflet.js GIS trajectory map |
| `VehicleSearch.jsx` | Vehicle plate search |
| `VehicleDetailModal.jsx` | Vehicle detail view |
| `VahanCard.jsx` | VAHAN 4.0 RC details display |
| `BlacklistManager.jsx` | Watchlist management UI |
| `BlacklistModal.jsx` | Add/edit blacklist entry modal |
| `AlertCenter.jsx` | Real-time alerts panel |
| `TrafficAnalyticsPage.jsx` | Traffic analytics dashboard |
| `SystemValidationPage.jsx` | System validation & benchmarks |
| `GlobalRegistry.jsx` | Global registry view |
| `FullMapModal.jsx` | Full-screen map modal |
| `EvidencePlaybackModal.jsx` | Evidence playback modal |
| `LiveAnprStream.jsx` | Live ANPR stream viewer |
| `CyberLoadingScreen.jsx` | Loading screen component |

---

## Backend Router Structure

The active FastAPI backend uses a modular router design:

| Router | File | Endpoints |
|--------|------|-----------|
| Cameras | `backend/routers/cameras.py` | Camera list, video streaming |
| Vehicles | `backend/routers/vehicles.py` | Search, trajectory |
| Traffic | `backend/routers/traffic.py` | Time-series, OD, congestion, speed |
| Blacklist | `backend/routers/blacklist.py` | CRUD, alerts |
| System | `backend/routers/system.py` | Health, validation |

Total: **46 API endpoints** across 5 routers.

---

## Frontend API Client

The frontend API client (`frontend/src/services/api.js`) exposes only the endpoints needed by active components. All archived API functions have been removed — the client is now minimal and focused.
