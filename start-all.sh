#!/usr/bin/env bash
# start-all.sh — Start backend (SQLite), ANPR stream dashboard, and frontend dev server
set -e

cd "$(dirname "$0")"

# 1. Initialize database if it doesn't exist
if [ ! -f sih_traffic_intelligence.db ]; then
    echo "[*] Creating SQLite database and seeding topology..."
    python scripts/init_database.py
else
    echo "[-] Database already exists, skipping init"
fi

# 2. Migrate JSON data to SQLite (idempotent)
echo "[*] Running data migration (idempotent)..."
python scripts/migrate_json_to_sqlite.py

# 3. Start backend in background
echo "[*] Starting backend on http://127.0.0.1:8000 ..."
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"

# 4. Start ANPR stream dashboard in background (legacy archived component)
echo "[*] Starting ANPR stream dashboard on http://127.0.0.1:5000 ..."
cd legacy/anpr
# Use project venv if available, else system python
if [ -f ../../.venv/bin/python ]; then
    PYTHON=../../.venv/bin/python
else
    PYTHON=python
fi
$PYTHON stream_anpr.py --port 5000 > ../anpr_stream.log 2>&1 &
ANPR_PID=$!
cd ../..
echo "    ANPR PID: $ANPR_PID"

# 5. Wait for backend to be ready
echo "[*] Waiting for backend to become ready..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
        echo "[+] Backend is ready"
        break
    fi
    sleep 1
done

# 6. Wait for ANPR stream dashboard to be ready
echo "[*] Waiting for ANPR stream dashboard to become ready..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:5000/plates_json > /dev/null 2>&1; then
        echo "[+] ANPR stream dashboard is ready"
        break
    fi
    sleep 1
done

# 7. Start frontend in background
echo "[*] Starting frontend on http://127.0.0.1:5173 ..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 8. Wait for frontend to be ready
echo "[*] Waiting for frontend to become ready..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:5173 > /dev/null 2>&1; then
        echo "[+] Frontend is ready"
        break
    fi
    sleep 1
done

# 9. Clean TUI summary — only the 4 URLs
echo ""
echo "=================================================="
echo "NetCam — Full Stack Online"
echo "=================================================="
echo "  Frontend URL : http://127.0.0.1:5173"
echo "  Backend URL  : http://127.0.0.1:8000"
echo "  Output URL   : http://127.0.0.1:5000"
echo "  Log URL      : file://$(pwd)/backend.log"
echo "=================================================="
echo "Press Ctrl+C to stop all services."
echo "=================================================="

# Keep script alive, forward signals to child processes
trap 'kill $BACKEND_PID $ANPR_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM
wait