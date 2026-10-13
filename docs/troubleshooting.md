# DRISHTI Troubleshooting Guide

## Quick Diagnostic

Run this first to identify the issue:
```bash
# Check core services
curl -s http://127.0.0.1:8000/api/health && echo "Backend: OK" || echo "Backend: FAIL"
curl -s http://127.0.0.1:5173 > /dev/null && echo "Frontend: OK" || echo "Frontend: FAIL"
# Optional ANPR stream (port 5000) — launched separately
curl -s http://127.0.0.1:5000/plates_json > /dev/null && echo "ANPR: OK" || echo "ANPR: SKIP (optional)"
```

---

## Backend Issues (Port 8000)

### Backend Won't Start

**Symptom**: `uvicorn` fails with import errors or port conflicts.

**Solutions**:
```bash
# 1. Check Python environment
source .venv/bin/activate
python -c "import fastapi; import sqlalchemy; print('OK')"

# 2. Check port availability
lsof -i :8000
# Kill if needed: kill -9 <PID>

# 3. Reinstall dependencies
pip install -r requirements.txt

# 4. Check for syntax errors
python -m py_compile backend/app.py
```

### Database Errors

**Symptom**: `sqlite3.OperationalError`, `sqlalchemy.exc.OperationalError`

**Solutions**:
```bash
# 1. Reset database
rm sih_traffic_intelligence.db
python scripts/init_database.py
python scripts/migrate_json_to_sqlite.py

# 2. Check database file permissions
ls -la sih_traffic_intelligence.db
# Should be readable/writable by current user

# 3. Verify schema
sqlite3 sih_traffic_intelligence.db ".schema"
```

### API Returns 500 Errors

**Symptom**: Internal server error on API calls.

**Debug Steps**:
```bash
# 1. Check backend logs
tail -f backend.log

# 2. Enable debug mode
export LOG_LEVEL=DEBUG
uvicorn backend.app:app --reload --log-level debug

# 3. Test specific endpoint
curl -v http://127.0.0.1:8000/api/cameras
```

### Video Streaming Not Working

**Symptom**: Camera feeds show broken video or 404.

**Solutions**:
```bash
# 1. Verify video files exist
ls -la dataset/junction_A/camera_01.mp4
ls -la dataset/junction_B/camera_01.mp4

# 2. Check video_service.py range request handling
# 3. Verify FFmpeg/transcoding if using raw AVI files
```

---

## ANPR Stream Issues (Port 5000)

### ANPR Dashboard Won't Load

**Symptom**: `http://127.0.0.1:5000` shows connection refused or error.

**Solutions**:
```bash
# 1. Check if process is running
ps aux | grep stream_anpr

# 2. Check ANPR logs
tail -f anpr_stream.log

# 3. Verify virtual environment
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python -c "import ultralytics; import easyocr; print('OK')"

# 4. Check model files
ls -la ../yolov8n.pt
ls -la license_plate_detector.pt

# 5. Reinstall ANPR dependencies
pip install -r requirements.txt
```

### ANPR Accuracy Issues

**Symptom**: Poor plate recognition, wrong reads.

**Solutions**:
```bash
# 1. Verify preprocessing pipeline
python -c "
from ai.plate_ocr import preprocess_plate
import cv2
img = cv2.imread('test_plate.jpg')
result = preprocess_plate(img)
cv2.imwrite('debug_preprocess.jpg', result)
"

# 2. Run evaluation to benchmark
python evaluation/evaluate_ocr.py

# 3. Check ground truth alignment
head evaluation/ground_truth.csv
```

---

## Frontend Issues (Port 5173)

### Frontend Won't Start / Blank Page

**Symptom**: `npm run dev` fails or browser shows white screen.

**Solutions**:
```bash
# 1. Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

# 2. Check for build errors
npm run build

# 3. Check browser console for errors
# Open DevTools → Console tab
```

### API Calls Failing (CORS / Network)

**Symptom**: Frontend loads but data doesn't appear, console shows CORS errors.

**Solutions**:
```bash
# 1. Verify backend is running on port 8000
curl http://127.0.0.1:8000/api/cameras

# 2. Check frontend API base URL
cat frontend/src/services/api.js
# Should use: const API_BASE = 'http://127.0.0.1:8000'

# 3. Verify CORS in backend/app.py
# Should have: app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### Camera Grid Not Showing Feeds

**Symptom**: Surveillance Grid shows placeholder/broken images.

**Solutions**:
```bash
# 1. Check video endpoint
curl -I http://127.0.0.1:8000/api/cameras/1/video
# Should return 200 or 206 with video/mp4 content-type

# 2. Verify video files are accessible
ls -la dataset/junction_A/camera_01.mp4

# 3. Check browser Network tab for failed video requests
```

### GIS Map Not Loading / No Trajectories

**Symptom**: Map loads but no routes/points visible.

**Solutions**:
```bash
# 1. Check trajectory API
curl http://127.0.0.1:8000/api/vehicles/WB37E1275/trajectory

# 2. Verify Leaflet CSS loaded
# Check browser Network for leaflet.css

# 3. Check MapView.jsx for coordinate bounds
# Cameras at: 23.710299, 86.952779 and 23.713932, 86.952211
```

---

## start-all.sh Issues

### Script Fails Partway Through

**Symptom**: `./start-all.sh` stops with error, some services not running.

**Solutions**:
```bash
# 1. Run with debug output
bash -x ./start-all.sh

# 2. Check individual service startup
# Backend:
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# ANPR:
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000

# Frontend:
cd frontend
npm run dev

# 3. Check log files for errors
cat backend.log
cat anpr_stream.log
cat frontend.log
```

### "Backend is ready" Timeout

**Symptom**: Script hangs at "Waiting for backend to become ready..."

**Solutions**:
```bash
# 1. Check if backend actually started
curl -v http://127.0.0.1:8000/api/health

# 2. Check backend.log for startup errors
cat backend.log

# 3. Increase timeout in start-all.sh (line 37)
# Change: for i in $(seq 1 30); to seq 1 60
```

### "ANPR stream dashboard" Timeout

**Symptom**: Script hangs waiting for ANPR on port 5000.

**Solutions**:
```bash
# 1. Check ANPR startup manually
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000

# 2. Check anpr_stream.log
cat anpr_stream.log

# 3. Verify plate detector model exists
ls -la ../yolov8n.pt
ls -la license_plate_detector.pt
```

---

## Database & Migration Issues

### Migration Script Fails

**Symptom**: `python scripts/migrate_json_to_sqlite.py` errors.

**Solutions**:
```bash
# 1. Check source JSON exists
ls -la dataset/metadata/detections.json
ls -la dataset/metadata/cameras.json

# 2. Run with verbose output
python scripts/migrate_json_to_sqlite.py 2>&1 | head -50

# 3. Check for duplicate key errors (idempotency)
# Script should handle re-runs gracefully
```

### MySQL Migration (Future)

**For production MySQL deployment**:
```bash
# 1. Ensure MySQL running
systemctl status mysql

# 2. Update .env
USE_SQLITE=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=sih_traffic_intelligence

# 3. Run MySQL migration
python scripts/init_database.py
python scripts/migrate_json_to_mysql.py
```

---

## Performance Issues

### High Latency / Slow Response

**Symptom**: API responses take >2 seconds, frontend feels sluggish.

**Solutions**:
```bash
# 1. Run benchmark to identify bottleneck
python benchmark/benchmark_pipeline.py

# 2. Check database indexes
sqlite3 sih_traffic_intelligence.db ".indexes"

# 3. Profile backend
# Add profiling middleware or use py-spy

# 4. Consider GPU acceleration for YOLO
# Install CUDA-enabled PyTorch
```

### High Memory Usage

**Symptom**: Python processes consuming excessive RAM.

**Solutions**:
```bash
# 1. Check frame sampling rate (currently 3x)
# Reduce in backend/app.py or video_service.py

# 2. Limit cache sizes in analytics_engine.py

# 3. Monitor with: watch -n 1 'ps aux | grep -E "python|node"'
```

---

## Environment-Specific Issues

### Windows (PowerShell)

```powershell
# Use run_drishti_master.py instead of start-all.sh
python run_drishti_master.py

# Or manually:
# 1. .venv\Scripts\Activate.ps1
# 2. uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
# 3. cd frontend; npm run dev
```

### Linux (No Display / Headless)

```bash
# For ANPR/OpenCV GUI operations
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &

# Or use CPU-only OpenCV
pip install opencv-python-headless
```

### Docker (Future)

```dockerfile
# Example Dockerfile structure
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["./start-all.sh"]
```

---

## Getting Help

### Log Locations
| Service | Log File |
|---------|----------|
| Backend | `backend.log` |
| ANPR Stream | `anpr_stream.log` |
| Frontend | `frontend.log` |

### Enable Verbose Logging
```bash
# Backend
export LOG_LEVEL=DEBUG
uvicorn backend.app:app --log-level debug

# Frontend
cd frontend
DEBUG=* npm run dev
```

### Report Issues
When reporting issues, include:
1. Output of quick diagnostic commands above
2. Relevant log file excerpts
3. Steps to reproduce
4. Environment (OS, Python version, Node version)
5. Whether using `start-all.sh` or manual startup

---

## Common Error Codes

| Error | Meaning | Resolution |
|-------|---------|------------|
| `ECONNREFUSED` | Service not running | Start the service |
| `404 Not Found` | Endpoint/resource missing | Check URL, verify data exists |
| `500 Internal Error` | Backend exception | Check backend.log |
| `CORS error` | Cross-origin blocked | Verify backend CORS config |
| `sqlite3.Locked` | DB locked by another process | Close other connections |
| `ModuleNotFoundError` | Missing dependency | `pip install -r requirements.txt` |
| `ENOENT` | File not found | Verify file paths in config |