# DRISHTI — City-Wide Visual Intelligence for Vehicle Tracking & Mobility Analysis

**Smart India Hackathon (SIH) 2026 — Problem Statement 26127**  
*City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics*

DRISHTI is an enterprise-grade visual intelligence platform delivering multi-camera vehicle detection, high-accuracy automatic number-plate recognition (ANPR), cross-camera trajectory reconstruction, real-time blacklist alerts, and GIS mobility analytics for smart cities.

---

## 🏛️ Three-App Architecture

| Application | Port | Technology | Purpose |
|-------------|------|------------|---------|
| **Backend API** | 8000 | FastAPI + SQLite | REST endpoints, detection pipeline, analytics |
| **Frontend Dashboard** | 5173 | React 18 + Vite | Cyber command center (Surveillance, GIS, Analytics, Blacklist, Validation) |
| **ANPR Stream** | 5000 | YOLOv8 + EasyOCR | Legacy live ANPR web dashboard (separate launch)

```
CCTV Streams → YOLOv8 Detection → ByteTrack Tracking → Plate Detection → OCR + Normalization
                                                              ↓
SQLite Persistence ← FastAPI REST API ← Frontend Dashboard
                                                              ↓
                                          ANPR Stream Dashboard (Port 5000)
```

---

## 🚀 Quick Start

### One-Command Launch (Recommended)
```bash
./start-all.sh
```

This starts the backend API and frontend dashboard. The legacy ANPR stream dashboard (port 5000) is launched separately — see [Legacy ANPR docs](docs/legacy-anpr.md) for details.
```
==================================================
NetCam — Full Stack Online
==================================================
  Frontend URL : http://127.0.0.1:5173
  Backend URL  : http://127.0.0.1:8000
  Log URL      : file:///path/to/backend.log
==================================================
Press Ctrl+C to stop all services.
==================================================
```

### Manual Startup
```bash
# Terminal 1: Backend
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3 (optional): Legacy ANPR Stream
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000
```

---

## 📊 Key Features

### Backend API (`http://127.0.0.1:8000`)
- **46 REST endpoints** for cameras, vehicles, traffic, blacklist, alerts
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **SQLite persistence** with 6 normalized tables
- **Real-time video streaming** with HTTP 206 support

### Frontend Dashboard (`http://127.0.0.1:5173`)
- **Surveillance Grid** — 4 live CCTV feeds with range streaming
- **GIS Journey Map** — Leaflet.js trajectory visualization with speed badges
- **Mobility Analytics** — OD matrix, congestion heatmap, speed analytics
- **Blacklist Management** — Add/edit/toggle vehicles, real-time alert polling
- **System Validation** — Live OCR accuracy (90.97%) and latency benchmarks

### ANPR Stream (`http://127.0.0.1:5000`)
- Legacy standalone ANPR web interface
- Live plate detection + OCR overlay
- Integrated via `start-all.sh`

---

## 🎯 SIH 2026 Compliance — All 15 Requirements ✅

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | High-Accuracy ANPR + OCR | 🟢 | Multi-stage enhancement (CLAHE, bilateral, unsharp) |
| 2 | **>90% OCR Accuracy** | 🟢 | **90.97% Exact Match** (131/144 plates) |
| 3 | Real-Time Throughput | 🟢 | 4.5 FPS equivalent, 450ms pipeline latency |
| 4 | Cross-Camera Tracking | 🟢 | 4 cameras, 2 junctions, plate-based association |
| 5 | Interactive GIS Map | 🟢 | Leaflet.js with routes, arrows, speed badges |
| 6 | Traffic Analytics | 🟢 | Volumes, unique vehicles, density, peaks |
| 7 | Origin-Destination Matrix | 🟢 | Live `/api/traffic/od` with travel times |
| 8 | Congestion Diagnostics | 🟢 | Relative Congestion Index (RCI) |
| 9 | Speed Analytics | 🟢 | Haversine + physical plausibility bounds |
| 10 | Geospatial Heatmap | 🟢 | Real-time density layer |
| 11 | Blacklist → Alert Pipeline | 🟢 | Auto alerts, flashing beacon, dismiss controls |
| 12 | Evidence Dossiers | 🟢 | Plate crops in `static/plates/` with metadata |
| 13 | Relational Persistence | 🟢 | SQLite (6 tables, indexed, FK integrity) |
| 14 | Robust REST APIs | 🟢 | 46 endpoints, Swagger, Pydantic validation |
| 15 | Frontend Integration | 🟢 | React 18 cyber command center, 5 views |

---

## 📁 Repository Structure

```
DRISHTI/
├── start-all.sh              # Main launcher (USE THIS)
├── run.sh                    # Simple background launcher
├── run_drishti_master.py     # Advanced Python launcher
├── .env                      # Environment config (SQLite by default)
├── requirements.txt          # Python dependencies
├── sih_traffic_intelligence.db  # SQLite database (auto-created)
├── yolov8n.pt               # YOLOv8 vehicle model (6.5 MB)
├── backend/                 # FastAPI application (5 routers, 46 endpoints)
├── frontend/                # React + Vite dashboard
├── legacy/                  # Archived legacy & experimental code
├── scripts/                 # Database init & migration
├── tests/                   # 37 automated tests (36 pass, 1 known failure)
├── evaluation/              # OCR benchmark (>90% accuracy)
├── benchmark/               # Latency & throughput benchmarks
├── dataset/                 # CCTV videos & metadata
├── models/                  # ML model weights
├── static/                  # Plate crop images
└── docs/                    # Documentation
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/architecture.md`](docs/architecture.md) | System architecture & data flow |
| [`docs/api-reference.md`](docs/api-reference.md) | Complete REST API reference |
| [`docs/deployment.md`](docs/deployment.md) | Setup, execution, troubleshooting |
| [`docs/benchmarking.md`](docs/benchmarking.md) | OCR accuracy & pipeline benchmarks |
| [`docs/sih-compliance.md`](docs/sih-compliance.md) | Full SIH 26127 compliance matrix |
| [`docs/legacy-anpr.md`](docs/legacy-anpr.md) | Legacy ANPR component documentation |
| [`docs/database-schema.md`](docs/database-schema.md) | SQLite schema & query examples |
| [`docs/development.md`](docs/development.md) | Dev workflow, scripts, testing |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common issues & solutions |
| [`docs/legacy.md`](docs/legacy.md) | Archived modules & components |

---

## 🧪 Verification & Testing

### Run All Tests (37 tests)
```bash
python tests/test_sih_pipeline.py      # 10 core pipeline tests
python tests/test_api_endpoints.py     # 14 API endpoint tests
python tests/test_mysql_database.py    # 15 database tests (14 pass, 1 known failure)
```

### Reproduce Benchmarks
```bash
# OCR Accuracy (>90% requirement)
python evaluation/evaluate_ocr.py
# → 90.97% exact match, 98.27% character accuracy

# Pipeline Latency & Throughput
python benchmark/benchmark_pipeline.py
# → 450.1 ms total latency, 4.5 FPS stream equivalent
```

### System Validation Page
Open `http://127.0.0.1:5173` → Click **System Validation** in header for live metrics.

---

## ⚙️ Configuration

### Environment (`.env`)
```env
# SQLite (default, zero-config)
USE_SQLITE=true
SQLITE_PATH=sih_traffic_intelligence.db

# MySQL (for production)
# USE_SQLITE=false
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=sih_traffic_intelligence
```

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- 4 GB+ RAM recommended

---

## 🔧 Alternative Launchers

| Script | Use Case |
|--------|----------|
| `./start-all.sh` | **Primary** — all services, health checks, clean UI |
| `./run.sh` | Simple background launcher |
| `python run_drishti_master.py` | Advanced orchestration with colored output |

---

## 📦 Production Deployment Notes

1. **Database**: Switch `.env` to MySQL (`USE_SQLITE=false`)
2. **Reverse Proxy**: Nginx → `/api/*` to port 8000, `/` to port 5173
3. **Process Manager**: systemd or PM2 for service management
4. **SSL**: Terminate at reverse proxy
5. **Docker**: `Dockerfile` + `docker-compose.yml` (future)

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Run tests (`python tests/test_sih_pipeline.py`)
4. Submit PR with description

---

## 📄 License

SIH 2026 Project — Problem Statement 26127  
Team DRISHTI — Visual Intelligence for Smart Cities