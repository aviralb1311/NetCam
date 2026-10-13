# DRISHTI System Architecture

## Overview

DRISHTI is a city-wide visual intelligence platform for multi-camera vehicle tracking, ANPR (Automatic Number Plate Recognition), trajectory reconstruction, and urban traffic analytics. Built for Smart India Hackathon (SIH) 2026 — Problem Statement 26127.

---

## System Architecture Diagram

```
                        CCTV VIDEO STREAMS (4 Nodes)
                                     │
                                     ▼
                          Intelligent Frame Sampling
                                     │
                                     ▼
                         YOLOv8 Vehicle Detection
                                     │
                                     ▼
                      Plate Crop & Image Enhancement
              (CLAHE + Bilateral Denoising + Unsharp Masking)
                                     │
                                     ▼
                        OCR Inference & Normalization
                                     │
                                     ▼
                     Temporal Aggregation & Confidence
                                     │
                                     ▼
                  SQLite Persistence (6 Core Tables)
                                     │
                                     ▼
                    FastAPI High-Performance REST APIs
                                     │
                                     ▼
                      React 18 + Vite Cyber Dashboard
        (Surveillance Grid • GIS Journey Map • Mobility Analytics • System Validation)
```

---

## Component Architecture

### 1. Video Ingestion Layer
- **Source**: 4 CCTV camera feeds (MP4 files for development, RTSP for production)
- **Processing**: Intelligent frame sampling (3x stride) for CPU efficiency
- **Format**: H.264 MP4 with HTTP 206 Partial Content streaming

### 2. Detection & Tracking Pipeline (`backend/`, `ai/`)
- **Vehicle Detection**: YOLOv8n (COCO pretrained) — classes: car, bus, truck, motorcycle
- **Multi-Object Tracking**: ByteTrack (Ultralytics built-in) — stable unique IDs per vehicle
- **License Plate Detection**: Custom YOLOv8 plate model (`license_plate_detector.pt`)
- **Plate Recognition**: EasyOCR with Indian registration syntax normalization

### 3. Image Preprocessing Pipeline
1. **CLAHE** — Contrast Limited Adaptive Histogram Equalization
2. **Bilateral Filter Denoising** — Edge-preserving smoothing
3. **Unsharp Masking** — `cv2.addWeighted` with Gaussian blur
4. **Adaptive Otsu Thresholding**
5. **Indian Plate Normalizer** — Validates `^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$`

### 4. Data Persistence Layer
- **Database**: SQLite (`sih_traffic_intelligence.db`) — production-ready, zero-config
- **Schema**: 6 normalized tables with foreign-key integrity
- **Tables**:
  - `junctions` — Physical intersection metadata
  - `cameras` — Surveillance node configurations
  - `vehicle_tracks` — ByteTrack sequences per camera
  - `plate_detections` — OCR readings linked to tracks
  - `blacklisted_vehicles` — Operator-controlled watchlist
  - `alerts` — Real-time tactical notifications

### 5. API Layer (FastAPI)
- **Architecture**: Router-based modular design — `backend/app.py` (115 lines) includes 5 API routers
- **Endpoints**: 46 core API endpoints across cameras, vehicles, traffic, blacklist, system, and observations
- **Routers**:
  - `system.py` — health check, validation, status endpoints
  - `cameras.py` — camera list, video streaming
  - `vehicles.py` — vehicle search, trajectory reconstruction
  - `traffic.py` — time-series, OD matrix, congestion, speed analytics
  - `blacklist.py` — watchlist CRUD, alert generation
- **Interactive Docs**: Swagger UI at `/docs`
- **Validation**: Pydantic models for request/response

### 6. Frontend Dashboard (React 18 + Vite)
- **Components**: 15 core components (from 23+)
- **Surveillance Grid** — Live CCTV feeds with HTTP 206 streaming
- **GIS Journey Map** — Leaflet.js trajectory visualization with directional arrows
- **Mobility Analytics** — OD matrix, heatmap, congestion diagnostics, speed analytics
- **Blacklist Management** — Add/edit/toggle/delete with real-time alert polling
- **System Validation** — Live benchmark metrics and accuracy reports

---

## Camera Topology (Asansol Deployment)

| Camera | Junction | Coordinates | Video Source |
|--------|----------|-------------|--------------|
| junction_A_camera_01 | Vivekananda Sarani | 23.710299, 86.952779 | `dataset/junction_A/camera_01.mp4` |
| junction_A_camera_02 | Vivekananda Sarani | 23.710299, 86.952779 | `dataset/junction_A/camera_02.mp4` |
| junction_B_camera_01 | Kanyapur Link Road | 23.713932, 86.952211 | `dataset/junction_B/camera_01.mp4` |
| junction_B_camera_02 | Kanyapur Link Road | 23.713932, 86.952211 | `dataset/junction_B/camera_02.mp4` |

---

## Data Flow Summary

1. **Video frames** sampled from 4 CCTV streams
2. **YOLOv8** detects vehicles → **ByteTrack** assigns persistent IDs
3. **Plate detector** finds plates within vehicle bounding boxes
4. **Preprocessing** enhances plate crops → **EasyOCR** reads text
5. **Normalization** applies Indian plate syntax rules
6. **Temporal aggregation** selects highest-confidence read per vehicle ID
7. **SQLite** stores detections, observations, and blacklist matches
8. **FastAPI** serves REST endpoints for dashboard consumption
9. **React dashboard** visualizes live data, trajectories, analytics