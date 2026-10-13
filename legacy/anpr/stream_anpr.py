#!/usr/bin/env python3
"""
stream_anpr.py - Live ANPR streamed over HTTP to any device on the same network.

Open on your mobile / tablet / PC browser:
    http://<YOUR-PC-IP>:5000

Usage:
    python stream_anpr.py                  # auto-detect camera
    python stream_anpr.py --camera 1       # force camera index
    python stream_anpr.py --port 5000      # change port (default 5000)
    python stream_anpr.py --det-conf 0.4   # YOLO confidence threshold
    python stream_anpr.py --ocr-min-conf 0.4

Press Ctrl+C in terminal to stop.
"""

import argparse
import csv
import os
import sys
import time
import threading

import cv2
import torch
from flask import Flask, Response, render_template_string
from ultralytics import YOLO

# ── defaults ────────────────────────────────────────────────────────────────
MODEL_FILE          = "license_plate_detector.pt"
CAMERA_INDICES      = (0, 1, 2)
DETECTION_CONF      = 0.4
OCR_MIN_CONF        = 0.4
TEXT_HOLD_FRAMES    = 20
OCR_EVERY           = 2
IMGSZ               = 640
CAM_WIDTH           = 1280
CAM_HEIGHT          = 720
STREAM_PORT         = 5000
JPEG_QUALITY        = 80   # 0-100; lower = faster stream, higher = better quality

FONT        = cv2.FONT_HERSHEY_SIMPLEX
BOX_COLOR   = (0, 200, 0)
TEXT_COLOR  = (0, 255, 255)
INFO_COLOR  = (0, 165, 255)

# ── HTML page served at / ────────────────────────────────────────────────────
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live ANPR Stream</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #111; color: #eee; font-family: sans-serif; }
    header { background: #1a1a2e; padding: 14px 20px; display: flex;
             align-items: center; gap: 12px; }
    header h1 { font-size: 1.2rem; color: #00e5ff; }
    header span { font-size: .8rem; color: #aaa; }
    .stream-wrap { display: flex; justify-content: center; padding: 16px; }
    img#feed { width: 100%; max-width: 960px; border-radius: 8px;
               border: 2px solid #00e5ff; background: #000; }
    .plates { max-width: 960px; margin: 0 auto 20px; padding: 0 16px; }
    .plates h2 { font-size: 1rem; color: #00e5ff; margin-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: .85rem; }
    th { background: #1a1a2e; padding: 8px; text-align: left; }
    td { padding: 7px 8px; border-bottom: 1px solid #333; }
    tr:nth-child(even) td { background: #1a1a1a; }
    .badge { display:inline-block; padding:2px 8px; border-radius:20px;
             font-size:.75rem; font-weight:bold; }
    .hi  { background:#00c853; color:#000; }
    .med { background:#ffd600; color:#000; }
    .lo  { background:#ff5722; color:#fff; }
    footer { text-align:center; padding:12px; color:#555; font-size:.75rem; }
  </style>
</head>
<body>
  <header>
    <h1>🚗 Live ANPR Stream</h1>
    <span>Point any camera at a number plate &mdash; detection happens on the server</span>
  </header>

  <div class="stream-wrap">
    <img id="feed" src="/video_feed" alt="Live camera feed">
  </div>

  <div class="plates">
    <h2>📋 Detected Plates (auto-refresh every 3s)</h2>
    <table id="tbl">
      <thead><tr><th>#</th><th>Plate</th><th>Confidence</th><th>First Seen</th><th>Last Seen</th><th>Count</th></tr></thead>
      <tbody id="tbody"><tr><td colspan="6" style="color:#555;text-align:center">Waiting for detections…</td></tr></tbody>
    </table>
  </div>

  <footer>Stream served by stream_anpr.py &bull; press Ctrl+C in terminal to stop</footer>

  <script>
    function confClass(c){ return c>=0.7?'hi':c>=0.45?'med':'lo'; }
    async function refresh(){
      try{
        const r = await fetch('/plates_json');
        const data = await r.json();
        const tb = document.getElementById('tbody');
        if(!data.length){
          tb.innerHTML='<tr><td colspan="6" style="color:#555;text-align:center">Waiting for detections…</td></tr>';
          return;
        }
        tb.innerHTML = data.map((p,i)=>`
          <tr>
            <td>${i+1}</td>
            <td><strong>${p.plate}</strong></td>
            <td><span class="badge ${confClass(p.confidence)}">${(p.confidence*100).toFixed(0)}%</span></td>
            <td>${p.first_seen}</td>
            <td>${p.last_seen}</td>
            <td>${p.count}</td>
          </tr>`).join('');
      }catch(e){}
    }
    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>
"""

# ── globals shared between threads ──────────────────────────────────────────
app          = Flask(__name__)
frame_lock   = threading.Lock()
latest_frame = None          # JPEG bytes of the latest annotated frame
seen_lock    = threading.Lock()
seen         = {}            # plate text -> dict


# ── helpers ─────────────────────────────────────────────────────────────────
def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def open_camera(forced_index=None, width=CAM_WIDTH, height=CAM_HEIGHT):
    indices = [forced_index] if forced_index is not None else list(CAMERA_INDICES)
    for idx in indices:
        for backend in (cv2.CAP_V4L2, None):
            cap = cv2.VideoCapture(idx) if backend is None else cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                ok, frame = cap.read()
                if ok and frame is not None and frame.size > 0:
                    print(f"Camera opened: /dev/video{idx} ({frame.shape[1]}x{frame.shape[0]})")
                    return cap, idx
                cap.release()
        print(f"Camera index {idx} not usable.")
    return None, None


def preprocess_plate(plate_bgr):
    if plate_bgr is None or plate_bgr.size == 0:
        return None
    upscaled = cv2.resize(plate_bgr, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def ocr_plate(reader, plate_bgr, min_conf):
    if plate_bgr is None or plate_bgr.size == 0:
        return "", 0.0
    pre = preprocess_plate(plate_bgr)
    if pre is None:
        return "", 0.0
    try:
        readings = reader.readtext(pre)
    except Exception as exc:
        print(f"OCR error: {exc}")
        return "", 0.0
    best_text, best_conf = "", 0.0
    for _box, text, conf in readings:
        clean = "".join(ch for ch in text.upper() if ch.isalnum())
        if clean and conf > best_conf:
            best_text, best_conf = clean, conf
    return (best_text, best_conf) if best_conf >= min_conf else ("", 0.0)


def put_label(frame, text, org, color=TEXT_COLOR, scale=0.7, thickness=2):
    cv2.putText(frame, text, org, FONT, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, org, FONT, scale, color, thickness, cv2.LINE_AA)


# ── capture + inference thread ───────────────────────────────────────────────
def capture_loop(cap, plate_model, reader, args):
    global latest_frame, seen

    frame_idx     = 0
    sticky_text   = ""
    sticky_conf   = 0.0
    sticky_hold   = 0
    prev_time     = time.time()
    fps           = 0.0
    device        = pick_device()

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("Camera frame grab failed. Stopping capture thread.")
            break

        frame_idx += 1
        plates = []
        results = plate_model(frame, device=device, conf=args.det_conf,
                              imgsz=args.imgsz, verbose=False)[0]
        for b in results.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            plates.append((x1, y1, x2, y2, float(b.conf[0])))

        if plates:
            run_ocr = (frame_idx % OCR_EVERY == 0)
            for (x1, y1, x2, y2, conf) in plates:
                cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
                put_label(frame, f"plate {conf:.2f}", (x1, max(16, y1 - 24)), scale=0.55)

                if run_ocr:
                    cx1, cy1 = max(0, x1), max(0, y1)
                    cx2 = min(frame.shape[1], x2)
                    cy2 = min(frame.shape[0], y2)
                    crop = frame[cy1:cy2, cx1:cx2]
                    text, tconf = ocr_plate(reader, crop, args.ocr_min_conf)
                    if text:
                        stamp = time.strftime("%H:%M:%S")
                        with seen_lock:
                            if text not in seen:
                                print(f"[{stamp}] Plate: {text} (conf {tconf:.2f})")
                                seen[text] = {"confidence": tconf,
                                              "first_seen": stamp,
                                              "last_seen":  stamp,
                                              "count": 1}
                            else:
                                rec = seen[text]
                                rec["last_seen"]   = stamp
                                rec["count"]      += 1
                                rec["confidence"]  = max(rec["confidence"], tconf)
                        sticky_text, sticky_conf, sticky_hold = text, tconf, TEXT_HOLD_FRAMES

                if sticky_hold > 0:
                    label = f"{sticky_text} ({sticky_conf:.2f})" if sticky_text else "…"
                    put_label(frame, label, (x1, max(20, y1 - 4)))
            sticky_hold = max(0, sticky_hold - 1)
            if sticky_hold == 0:
                sticky_text, sticky_conf = "", 0.0
        else:
            put_label(frame, "No plate detected — aim camera at a plate",
                      (12, 30), color=INFO_COLOR)

        now = time.time()
        inst_fps = 1.0 / max(now - prev_time, 1e-6)
        fps = inst_fps if fps == 0 else (0.9 * fps + 0.1 * inst_fps)
        prev_time = now
        put_label(frame, f"FPS: {fps:.1f} | plates: {len(plates)}",
                  (12, frame.shape[0] - 16), color=INFO_COLOR, scale=0.6, thickness=1)

        # encode to JPEG and store for streaming
        ret, jpg = cv2.imencode(".jpg", frame,
                                [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if ret:
            with frame_lock:
                latest_frame = jpg.tobytes()


# ── Flask routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


def generate_frames():
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.05)
            continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.033)   # ~30 fps cap for the stream


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/plates_json")
def plates_json():
    import json
    with seen_lock:
        data = [{"plate": k, **v} for k, v in
                sorted(seen.items(), key=lambda kv: kv[1]["first_seen"])]
    return app.response_class(json.dumps(data), mimetype="application/json")


# ── main ─────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="ANPR streamed over HTTP to any device on the LAN.")
    p.add_argument("--camera",      type=int,   default=None)
    p.add_argument("--model",       type=str,   default=MODEL_FILE)
    p.add_argument("--det-conf",    type=float, default=DETECTION_CONF)
    p.add_argument("--ocr-min-conf",type=float, default=OCR_MIN_CONF)
    p.add_argument("--imgsz",       type=int,   default=IMGSZ)
    p.add_argument("--width",       type=int,   default=CAM_WIDTH)
    p.add_argument("--height",      type=int,   default=CAM_HEIGHT)
    p.add_argument("--port",        type=int,   default=STREAM_PORT)
    p.add_argument("--no-save",     action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    device = pick_device()
    print(f"Using device: {device}")

    if not os.path.isfile(args.model):
        print(f"ERROR: model '{args.model}' not found.")
        sys.exit(1)

    print(f"Loading plate detector '{args.model}' ...")
    plate_model = YOLO(args.model)
    plate_model.to(device)

    try:
        import easyocr
        print("Initializing EasyOCR (models already cached) ...")
        reader = easyocr.Reader(["en"], gpu=(device == "cuda"), verbose=False)
    except Exception as exc:
        print(f"ERROR: EasyOCR init failed: {exc}")
        sys.exit(1)

    cap, used_idx = open_camera(args.camera, args.width, args.height)
    if cap is None:
        print("ERROR: could not open any camera.")
        sys.exit(1)

    # start capture thread (daemon so it dies with main)
    t = threading.Thread(target=capture_loop,
                         args=(cap, plate_model, reader, args),
                         daemon=True)
    t.start()

    # print access URLs
    import socket, subprocess, re
    try:
        ips = socket.gethostbyname_ex(socket.gethostname())[2]
        ips = [i for i in ips if not i.startswith("127.")]
    except Exception:
        ips = []
    try:
        result = subprocess.check_output(["ip", "-4", "addr"], text=True)
        iface_ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)
        iface_ips = [ip for ip in iface_ips if not ip.startswith("127.")]
        all_ips = list(dict.fromkeys(ips + iface_ips))
    except Exception:
        all_ips = ips

    HOTSPOT_IP = "10.42.0.1"

    print("\n" + "="*60)
    print("  🌐  ANPR Web Stream is LIVE!")
    print("="*60)
    if HOTSPOT_IP in all_ips:
        print(f"\n  📱  MOBILE (PC Hotspot) ➜  http://{HOTSPOT_IP}:{args.port}")
        print(f"      ^ Use THIS on your phone connected to hotspot\n")
    for ip in all_ips:
        tag = "✅" if ip == HOTSPOT_IP else "🔵"
        print(f"  {tag}  http://{ip}:{args.port}")
    print(f"\n  💻  This machine  ➜  http://localhost:{args.port}")
    print("="*60)
    print("  Press Ctrl+C to stop.\n")

    try:
        app.run(host="0.0.0.0", port=args.port, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        if seen and not args.no_save:
            with open("plates.csv", "w", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["plate","confidence","first_seen","last_seen","count"])
                for text, rec in sorted(seen.items(), key=lambda kv: kv[1]["first_seen"]):
                    wr.writerow([text, round(rec["confidence"], 2),
                                 rec["first_seen"], rec["last_seen"], rec["count"]])
            print(f"Saved {len(seen)} plate(s) to plates.csv")
        print("Stopped cleanly.")


if __name__ == "__main__":
    main()
