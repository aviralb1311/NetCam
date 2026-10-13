# DRISHTI Development Guide

## Overview

This document describes the development workflow, project structure, scripts, testing procedures, and contribution guidelines for DRISHTI.

---

## Project Structure

```
DRISHTI/
├── ai/                              # AI model interfaces
│   ├── plate_ocr.py                 # OCR preprocessing & normalization
│   └── test_yolo.py                 # YOLO testing utilities
├── backend/                         # FastAPI application
│   ├── app.py                       # Main application (115 lines) — includes 5 routers
│   ├── routers/                     # Modular API routers (46 endpoints total)
│   │   ├── system.py                # Health, validation, status endpoints
│   │   ├── cameras.py               # Camera list, video streaming
│   │   ├── vehicles.py              # Vehicle search, trajectory
│   │   ├── traffic.py               # Time-series, OD, congestion, speed
│   │   └── blacklist.py             # Watchlist CRUD, alerts
│   ├── database/
│   │   ├── connection.py            # SQLite connection pool
│   │   └── models.py                # SQLAlchemy ORM models
│   └── services/
│       ├── analytics_engine.py      # Traffic analytics (OD, RCI, speed)
│       ├── blacklist_service.py     # Watchlist management
│       ├── alert_service.py         # Alert generation & polling
│       ├── database_service.py      # SQLite persistence (renamed from mysql_database_service.py)
│       ├── dataset_service.py       # Camera metadata & JSON fallback
│       └── video_service.py         # HTTP 206 video streaming
├── legacy/                          # Archived experimental & legacy code
│   ├── backend/                     # Archived backend services
│   └── components/                  # Archived frontend components
├── frontend/                        # React 18 + Vite dashboard
│   ├── src/
│   │   ├── App.jsx                  # Main command center
│   │   ├── App.css                  # Cyber theme styling
│   │   ├── components/              # 15 core components
│   │   │   ├── CameraGrid.jsx       # Live CCTV feeds
│   │   │   ├── MapView.jsx          # Leaflet GIS trajectory map
│   │   │   ├── VehicleSearch.jsx    # Vehicle search
│   │   │   ├── VehicleDetailModal.jsx
│   │   │   ├── BlacklistManager.jsx # Watchlist UI
│   │   │   ├── AlertCenter.jsx      # Real-time alerts
│   │   │   ├── SystemValidationPage.jsx
│   │   │   ├── TrafficAnalyticsPage.jsx
│   │   │   ├── FullMapModal.jsx
│   │   │   ├── EvidencePlaybackModal.jsx
│   │   │   ├── LiveAnprStream.jsx
│   │   │   ├── GlobalRegistry.jsx
│   │   │   ├── BlacklistModal.jsx
│   │   │   ├── CyberLoadingScreen.jsx
│   │   │   └── VahanCard.jsx
│   │   └── services/
│   │       └── api.js               # REST API client
├── scripts/                         # Automation scripts
│   ├── init_database.py             # Schema creation & seeding
│   ├── migrate_json_to_sqlite.py    # Data migration (SQLite)
│   └── migrate_json_to_mysql.py     # Data migration (MySQL)
├── tests/                           # Automated test suites (37 tests)
│   ├── test_sih_pipeline.py         # Core SIH pipeline (10 tests)
│   ├── test_api_endpoints.py        # API endpoints (14 tests)
│   └── test_mysql_database.py       # Database schema (15 tests, 14 pass)
├── start-all.sh                     # Main launcher
├── requirements.txt                 # Python dependencies
├── sih_traffic_intelligence.db      # SQLite database
├── dataset/                         # CCTV videos & metadata
├── evaluation/                      # OCR accuracy evaluation
├── benchmark/                       # Performance benchmarks
└── docs/                            # Documentation
```

---

## Development Workflow

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd DRISHTI

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..

# Legacy ANPR environment (optional)
cd automatic-number-plate-detection-using-yolov8
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 2. Database Initialization

```bash
# Initialize schema & seed data
python scripts/init_database.py

# Migrate detection data
python scripts/migrate_json_to_sqlite.py
```

### 3. Running Services

**Option A: All-in-one (Recommended)**
```bash
./start-all.sh
```

**Option B: Manual (for debugging)**
```bash
# Terminal 1: Backend
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: ANPR Stream
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 4. Making Changes

**Backend Changes** (`backend/`):
- Edit files in `backend/routers/` for API endpoints
- Edit `services/` for business logic
- Edit `database/models.py` for schema changes (then re-run `init_database.py`)

**Frontend Changes** (`frontend/src/`):
- Components in `components/`
- API client in `services/api.js`
- Styles in `App.css`

**AI Pipeline Changes** (`ai/`, `evaluation/`, `benchmark/`):
- Modify preprocessing in `ai/plate_ocr.py`
- Add evaluation metrics in `evaluation/evaluate_ocr.py`
- Extend benchmarks in `benchmark/benchmark_pipeline.py`

---

## Scripts Reference

### Database Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `init_database.py` | Create tables, seed junctions/cameras | `python scripts/init_database.py` |
| `migrate_json_to_sqlite.py` | Migrate JSON detections to SQLite | `python scripts/migrate_json_to_sqlite.py` |
| `migrate_json_to_mysql.py` | Migrate to MySQL (production) | `python scripts/migrate_json_to_mysql.py` |

### Evaluation Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `evaluation/evaluate_ocr.py` | OCR accuracy benchmark | `evaluation/evaluation_report.json` |
| `evaluation/extract_plate_crops.py` | Extract plate crops from video | `evaluation/crops/` |

### Benchmark Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `benchmark/benchmark_pipeline.py` | End-to-end latency & throughput | `benchmark/benchmark_report.json` |

---

## Testing

### Run All Tests (37 tests)
```bash
# Core SIH pipeline (10 tests)
python tests/test_sih_pipeline.py

# API endpoints (14 tests)
python tests/test_api_endpoints.py

# Database schema & queries (15 tests, 14 pass - see known issues)
python tests/test_mysql_database.py
```

### Test Categories

**`test_sih_pipeline.py`** — End-to-end validation:
- Camera configuration loading
- Video streaming functionality
- YOLO detection operational
- Plate detection functional
- OCR normalization working
- Cross-camera trajectory reconstruction
- Blacklist matching & alerts
- Traffic analytics (OD, heatmap, congestion)
- Database persistence integrity
- Frontend-backend integration

**`test_api_endpoints.py`** — REST API verification:
- All 15+ endpoints return 200 OK
- Response schema validation
- Error handling (404, 400, 500)
- Pagination & filtering

**`test_mysql_database.py`** — Database validation:
- Table creation & indexes
- Foreign key constraints
- Seed data integrity
- Query performance
- Migration idempotency

### Adding New Tests

1. Create test file in `tests/` following naming convention
2. Use `pytest` style with descriptive test names
3. Run with `python tests/your_test.py` (or `pytest tests/your_test.py`)

---

## Code Style & Conventions

### Python (Backend)
- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for public functions

```python
def calculate_speed(distance_m: float, time_sec: float) -> float:
    """Calculate speed in km/h from distance and time.
    
    Args:
        distance_m: Distance in meters.
        time_sec: Time in seconds.
        
    Returns:
        Speed in km/h, or 0.0 if time_sec <= 0.
    """
    if time_sec <= 0:
        return 0.0
    return (distance_m / time_sec) * 3.6
```

### JavaScript/React (Frontend)
- **Formatter**: Prettier
- **Linter**: ESLint (React recommended)
- **Components**: Functional with hooks
- **State**: React Context + useReducer for global state

### Git Conventions
- **Branch naming**: `feature/`, `fix/`, `docs/`, `refactor/`
- **Commit messages**: Conventional Commits
  - `feat: add OD matrix endpoint`
  - `fix: resolve plate normalization bug`
  - `docs: update deployment guide`
  - `refactor: extract analytics service`

---

## Debugging Tips

### Backend Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn backend.app:app --reload --log-level debug

# Check database directly
sqlite3 sih_traffic_intelligence.db
.tables
SELECT * FROM plate_detections LIMIT 5;
```

### Frontend Debugging
- Open browser DevTools → Console for API errors
- Network tab → inspect `/api/*` requests
- React DevTools extension for component inspection

### Database Issues
```bash
# Reset database completely
rm sih_traffic_intelligence.db
python scripts/init_database.py
python scripts/migrate_json_to_sqlite.py
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate `.venv`, run `pip install -r requirements.txt` |
| Port 8000 in use | `lsof -i :8000` → kill process |
| Frontend blank page | `cd frontend && rm -rf node_modules && npm install` |
| ANPR not loading | Check `automatic-number-plate-detection-using-yolov8/venv` exists |
| Low OCR accuracy | Verify `evaluation/ground_truth.csv` matches crops |

---

## Adding New Features

### New API Endpoint
1. Add route in a file under `backend/routers/`
2. Register router in `backend/app.py` via `include_router()`
3. Add service logic in `backend/services/`
4. Add Pydantic models for request/response
5. Write test in `tests/test_api_endpoints.py`
6. Update `docs/api-reference.md`

### New Frontend View
1. Create component in `frontend/src/components/`
2. Add to `App.jsx` routing/layout
3. Add API calls in `frontend/src/services/api.js`
4. Style in `App.css`

### New Analytics Metric
1. Add calculation in `backend/services/analytics_engine.py`
2. Expose via new endpoint in `backend/app.py`
3. Add frontend display in `AnalyticsPanel.jsx` or new component
4. Document in `docs/architecture.md`

---

## Performance Optimization

### Backend
- Use connection pooling (already configured in `database/connection.py`)
- Add database indexes for new query patterns
- Cache expensive computations (OD matrix, heatmap)
- Consider Redis for session/alert caching

### Frontend
- Code-split with `React.lazy()` for large components
- Memoize expensive renders with `React.memo()`
- Virtualize long lists (blacklist, alerts)
- Debounce search inputs

### Database
- Current: SQLite (single file, zero config)
- Production: MySQL 8.0 with connection pooling
- Indexes on `normalized_plate`, `timestamp_sec`, `camera_id`
- Partition `plate_detections` by date for large datasets

---

## Release Checklist

Before SIH demo or release:

- [ ] All 37 tests pass (36/37 — 1 pre-existing video path failure)
- [ ] `python evaluation/evaluate_ocr.py` → >90% accuracy
- [ ] `python benchmark/benchmark_pipeline.py` → <500ms latency
- [ ] `./start-all.sh` launches all 3 services successfully
- [ ] Frontend loads at `http://127.0.0.1:5173`
- [ ] 4 camera feeds visible in Surveillance Grid
- [ ] GIS Map shows trajectories
- [ ] Blacklist alerts trigger in real-time
- [ ] System Validation page displays live metrics
- [ ] Documentation updated (`docs/`)