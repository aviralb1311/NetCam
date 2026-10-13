# DRISHTI Deployment Guide

## Quick Start (Recommended)

### One-Command Launch
```bash
./start-all.sh
```

This starts the backend API and frontend dashboard. The legacy ANPR stream dashboard (port 5000) is launched separately — see [Legacy ANPR docs](legacy-anpr.md) for details.

- **Backend API** → `http://127.0.0.1:8000` (Swagger: `/docs`)
- **Frontend Dashboard** → `http://127.0.0.1:5173`

Press `Ctrl+C` to stop all services.

---

## Manual Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### 1. Clone & Enter Project
```bash
git clone <repository-url>
cd DRISHTI
```

### 2. Python Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python scripts/init_database.py
python scripts/migrate_json_to_sqlite.py
```
This creates `sih_traffic_intelligence.db` with schema and seeds 4 cameras, 2 junctions, and 144 plate detections.

### 4. Start Backend
```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Verify: `http://127.0.0.1:8000/docs`

### 5. Start ANPR Stream Dashboard
```bash
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000
```
Verify: `http://127.0.0.1:5000`

### 6. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Verify: `http://127.0.0.1:5173`

---

## Ports & Services Table

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Backend API | 8000 | http://127.0.0.1:8000 | FastAPI REST endpoints |
| API Docs | 8000 | http://127.0.0.1:8000/docs | Swagger UI |
| ANPR Stream | 5000 | http://127.0.0.1:5000 | Legacy ANPR web dashboard |
| Frontend | 5173 | http://127.0.0.1:5173 | React command center |

---

## Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Current `.env` uses SQLite (no MySQL required):
```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=sih_traffic_intelligence
USE_SQLITE=true
SQLITE_PATH=sih_traffic_intelligence.db
```

**Note**: The project now uses SQLite by default. MySQL configuration is kept for future migration.

---

## Alternative Launchers

### `run.sh` — Simple Background Launcher
```bash
./run.sh
```
Starts backend and frontend in background. Check logs in `backend.log` and `frontend.log`.

### `run_drishti_master.py` — Python Orchestrator
```bash
python run_drishti_master.py
```
Full-featured launcher with health checks, colored output, and process management.

---

## Verification Checklist

After starting services, verify:

- [ ] Backend health: `curl http://127.0.0.1:8000/api/health`
- [ ] API docs load: Open `http://127.0.0.1:8000/docs`
- [ ] Frontend loads: Open `http://127.0.0.1:5173`
- [ ] Frontend shows 4 camera feeds in Surveillance Grid
- [ ] GIS Map shows trajectories between Junction A and B
- [ ] Blacklist Management allows adding vehicles
- [ ] System Validation page shows 90.97% OCR accuracy

---

## Troubleshooting Common Issues

### Backend fails to start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Python environment
source .venv/bin/activate
python -c "import fastapi; print('OK')"
```

### Frontend shows blank page
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database errors
```bash
# Reinitialize database
rm sih_traffic_intelligence.db
python scripts/init_database.py
python scripts/migrate_json_to_sqlite.py
```

### ANPR stream not loading
```bash
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
pip install -r requirements.txt
# Ensure yolov8n.pt exists in project root
```

---

## Production Deployment Notes

### For Production (MySQL)
1. Install MySQL 8.0
2. Create database: `CREATE DATABASE sih_traffic_intelligence;`
3. Update `.env` with MySQL credentials and `USE_SQLITE=false`
4. Run `python scripts/init_database.py` and `python scripts/migrate_json_to_mysql.py`

### Docker (Future)
A `Dockerfile` and `docker-compose.yml` will be provided for containerized deployment.

### Reverse Proxy (Nginx)
Configure Nginx to proxy:
- `/api/*` → `http://127.0.0.1:8000`
- `/anpr/*` → `http://127.0.0.1:5000`
- `/` → `http://127.0.0.1:5173`

---

## File Structure for Deployment

```
DRISHTI/
├── start-all.sh              # Main launcher (use this)
├── run.sh                    # Simple launcher
├── run_drishti_master.py     # Advanced launcher
├── .env                      # Environment config
├── requirements.txt          # Python dependencies
├── sih_traffic_intelligence.db  # SQLite database (auto-created)
├── yolov8n.pt               # YOLOv8 vehicle model (6.5 MB)
├── backend/                 # FastAPI application (routers + services)
├── frontend/                # React + Vite app
├── legacy/                  # Archived legacy & experimental code
├── scripts/                 # Database init & migration
├── tests/                   # Test suites (37 tests)
├── evaluation/              # OCR benchmark (>90% accuracy)
├── benchmark/               # Latency & throughput benchmarks
├── dataset/                 # CCTV videos & metadata
├── models/                  # ML model weights
├── static/                  # Plate crop images
└── docs/                    # Documentation
```