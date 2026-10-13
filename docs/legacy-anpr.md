# Legacy ANPR Component

## Overview

The `automatic-number-plate-detection-using-yolov8/` directory contains a standalone legacy ANPR (Automatic Number Plate Recognition) project that is integrated into the DRISHTI platform via the `start-all.sh` launcher. It runs as a separate service on **port 5000**.

> **Note**: This is a legacy component from a separate repository (originally by Rahul Adidravid). It is included as a supplementary ANPR stream dashboard for the SIH 2026 demonstration.

---

## Component Details

| Property | Value |
|----------|-------|
| **Directory** | `automatic-number-plate-detection-using-yolov8/` |
| **Service Port** | 5000 |
| **Entry Point** | `stream_anpr.py` |
| **Dependencies** | Own virtual environment (`venv/`) |
| **Models Required** | `license_plate_detector.pt`, `yolov8n.pt` (from project root) |

---

## Features

- **Vehicle Detection** — Cars, buses, trucks, motorcycles (YOLOv8)
- **Multi-Object Tracking** — ByteTrack stable unique IDs
- **License Plate Detection** — Custom YOLOv8 plate model
- **Plate Recognition (OCR)** — EasyOCR with image preprocessing
- **Live Webcam ANPR** — Real-time from laptop camera
- **Annotated Output** — Video + CSV export of plate numbers

---

## Pipeline Architecture

```
Video frame
   ↓
[1] Vehicle Detection      (YOLOv8, COCO pretrained)
   ↓
[2] Vehicle Tracking       (ByteTrack → unique ID per vehicle)
   ↓
[3] Plate Detection        (custom YOLOv8 plate model, inside vehicle box)
   ↓
[4] Plate Recognition      (preprocess + EasyOCR → plate text)
   ↓
[5] Annotate video + log plates to CSV
```

**Key Design Choices**:
- `model.track()` combines detection + tracking for stable IDs
- Plate detected *inside* each vehicle box, then cropped, upscaled, grayscaled before OCR
- Best (highest-confidence) plate read per vehicle ID is kept for stability

---

## Tech Stack

`Python` · `YOLOv8 (Ultralytics)` · `ByteTrack` · `OpenCV` · `EasyOCR` · `PyTorch`

Runs on GPU (CUDA), Apple Silicon (MPS), or CPU — device auto-detected.

---

## Project Structure

```
automatic-number-plate-detection-using-yolov8/
├── phase1_detect_track.py     # Vehicle detection + tracking + counting
├── phase2_anpr.py             # ANPR → saves plates to CSV
├── phase2_anpr_video.py       # Full inference VIDEO (box + ID + plate + text)
├── stream_anpr.py             # LIVE web ANPR dashboard (used by start-all.sh)
├── live_anpr.py               # Live webcam ANPR (camera → detect → OCR → display)
├── license_plate_detector.pt  # Custom YOLOv8 license-plate model
├── requirements.txt
├── venv/                      # Isolated Python environment
└── README.md                  # Original documentation (see below)
```

---

## How It's Used in DRISHTI

The `start-all.sh` script launches this component as the **ANPR Stream Dashboard**:

```bash
# From start-all.sh (lines 25-33)
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
python stream_anpr.py --port 5000 > ../anpr_stream.log 2>&1 &
ANPR_PID=$!
deactivate
cd ..
```

**Access**: `http://127.0.0.1:5000`

---

## Manual Execution

### Prerequisites
```bash
cd automatic-number-plate-detection-using-yolov8
source venv/bin/activate
pip install -r requirements.txt
```

Ensure `yolov8n.pt` exists in project root (6.5 MB, downloaded automatically on first run).

### Run Modes

**1. Vehicle Detection + Tracking + Count**
```bash
python phase1_detect_track.py
# → output_phase1.mp4
```

**2. ANPR → Plate Numbers to CSV**
```bash
python phase2_anpr.py
# → plates.csv (vehicle_id, plate, confidence)
```

**3. Full Inference Video (Box + ID + Plate + Text)**
```bash
python phase2_anpr_video.py
# → output_anpr.mp4 + plates.csv
```

**4. Live Webcam ANPR**
```bash
python live_anpr.py
# Press 'q' or ESC to quit
# Options: --camera 1, --show-crop, --det-conf 0.5 --ocr-min-conf 0.5
```

**5. Web ANPR Dashboard (used by start-all.sh)**
```bash
python stream_anpr.py --port 5000
# Open http://127.0.0.1:5000
```

---

## Installation on Fedora Linux

```bash
# System prerequisites for venv + OpenCV GUI
sudo dnf install python3 python3-pip python3-devel gcc-c++ mesa-libGL libglvnd

git clone https://github.com/Rahul-Adidravid/automatic-number-plate-detection-using-yolov8.git
cd automatic-number-plate-detection-using-yolov8

python3 -m venv venv
source venv/bin/activate

# CPU-only install (recommended if no NVIDIA GPU)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

## Known Limitations

- **EasyOCR** trained on scene text, not plate-specific fonts — accuracy drops with blur, glare, small plates, strong angle, or low light
- **Indian formats** (`MH12AB1234`-style) work, but no format validation — foreign/mis-formatted plates may read incorrectly
- **CPU inference** ~5–10 FPS at 1280×720; CUDA GPU raises substantially
- **Plate detector** detects plate regions only; vehicle make/model and jurisdiction out of scope

---

## Original Documentation

The original README from this component is preserved below for reference:

---

# 🚗 Vehicle Detection, Tracking & ANPR (Automatic Number Plate Recognition)

A real-time computer vision system that **detects vehicles, tracks them across frames, locates their number plates, and reads the plate text** from traffic video. Built for smart-city / traffic-analytics use cases.

> Part of an ongoing Smart Traffic Monitoring system. Speed estimation and traffic-violation detection are on the roadmap.

---

## 🎬 Demo

![demo](demo.gif)

*The system draws a box + unique ID on each vehicle, locates the number plate, and overlays the recognized plate number.*

---

## ✨ Features

- **Vehicle detection** — cars, buses, trucks, motorcycles (YOLOv8)
- **Multi-object tracking** — each vehicle gets a stable unique ID (ByteTrack)
- **Unique vehicle counting** — no double counting
- **License plate detection** — custom YOLOv8 plate model
- **Plate recognition (OCR)** — reads plate text (EasyOCR) with image preprocessing
- **Annotated output video** + **CSV export** of plate numbers per vehicle

---

## 🧠 How It Works (pipeline)

```
Video frame
   ↓
[1] Vehicle Detection      (YOLOv8, COCO pretrained)
   ↓
[2] Vehicle Tracking       (ByteTrack → unique ID per vehicle)
   ↓
[3] Plate Detection        (custom YOLOv8 plate model, inside each vehicle box)
   ↓
[4] Plate Recognition      (preprocess + EasyOCR → plate text)
   ↓
[5] Annotate video + log plates to CSV
```

**Key design choices**
- `model.track()` combines detection + tracking so each vehicle keeps the same ID across frames.
- The plate is detected *inside* each vehicle box, then cropped, upscaled and grayscaled before OCR for cleaner reads.
- The **best (highest-confidence) plate read per vehicle ID** is kept, so the displayed plate is stable.

---

## 🛠️ Tech Stack

`Python` · `YOLOv8 (Ultralytics)` · `ByteTrack` · `OpenCV` · `EasyOCR` · `PyTorch`

Runs on GPU (CUDA), Apple Silicon (MPS), or CPU — device is auto-detected.

---

## 📁 Project Structure

```
smart-traffic-anpr/
├── phase1_detect_track.py     # vehicle detection + tracking + counting
├── phase2_anpr.py             # ANPR → saves plates to CSV
├── phase2_anpr_video.py       # full inference VIDEO (box + ID + plate + text)
├── live_anpr.py               # LIVE webcam ANPR (camera → detect → OCR → display)
├── license_plate_detector.pt  # custom YOLOv8 license-plate model
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/Rahul-Adidravid/automatic-number-plate-detection-using-yolov8.git
cd automatic-number-plate-detection-using-yolov8

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Add a traffic video named `traffic.mp4` in the folder.
(The vehicle model `yolov8n.pt` downloads automatically on first run.)

---

## ▶️ How to Run

**1. Vehicle detection + tracking + count**
```bash
python phase1_detect_track.py
# → output_phase1.mp4
```

**2. ANPR → plate numbers to CSV**
```bash
python phase2_anpr.py
# → plates.csv  (vehicle_id, plate, confidence)
```

**3. Full inference video (box + ID + plate + text overlaid)**
```bash
python phase2_anpr_video.py
# → output_anpr.mp4 + plates.csv
```

---

## 📷 Live Webcam ANPR (`live_anpr.py`)

Real-time plate detection + OCR directly from your laptop webcam (Linux / Fedora):

```bash
python live_anpr.py
```

Pipeline: **camera frame → YOLOv8 plate detection → plate crop → EasyOCR → overlay**.
Press **`q`** (or ESC) in the video window to quit.

Options:
```bash
python live_anpr.py --camera 1      # force a camera index (default: tries 0, 1, 2)
python live_anpr.py --show-crop     # extra debug window with the preprocessed plate crop
python live_anpr.py --det-conf 0.5 --ocr-min-conf 0.5
```

Camera failures are never silently replaced by a video file — the program prints the diagnosed cause and exits.

### Installation on Fedora Linux

```bash
# system prerequisites for a venv + OpenCV GUI
sudo dnf install python3 python3-pip python3-devel gcc-c++ mesa-libGL libglvnd

git clone https://github.com/Rahul-Adidravid/automatic-number-plate-detection-using-yolov8.git
cd automatic-number-plate-detection-using-yolov8

python3 -m venv venv
source venv/bin/activate

# CPU-only install (recommended if you have no NVIDIA GPU — avoids multi-GB CUDA wheels)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt      # ultralytics, opencv-python, easyocr, numpy

python live_anpr.py
```

`license_plate_detector.pt` (single class `license_plate`) is included in the repo — no download needed. `yolov8n.pt` is only needed by the phase 1/2 video scripts.

### If the camera cannot be opened

1. **Permissions** — add your user to the `video` group, then log out/in:
   ```bash
   sudo usermod -aG video $USER
   ```
2. **Device check** — list and inspect cameras (needs `sudo dnf install v4l-utils`):
   ```bash
   v4l2-ctl --list-devices
   ls -l /dev/video*
   ```
3. **Busy camera** — close Zoom/Cheese/browser tabs using the webcam.
4. **Wrong index** — try `python live_anpr.py --camera 1` (or `2`).
5. **VM / remote sessions** — passthrough the USB camera to the VM; `/dev/video0` will not exist inside the VM otherwise.

### If `license_plate_detector.pt` is missing

Any YOLOv8 detector with the single `license_plate` class works as a drop-in replacement. Known sources:

- `keremberke/yolov8n-license-plate-detection` or `koushik-ai/yolov8-license-plate-detection` on Hugging Face (click **Files → best.pt → Download**, rename to `license_plate_detector.pt`)
- The weights from the original tutorial repo `computervisioneng/automatic-number-plate-recognition-python-yolov8`
- Train your own on a Roboflow *License Plate* dataset (YOLOv8 `train()` → `runs/detect/train/weights/best.pt`)

### Known limitations

- EasyOCR is trained on scene text, not plate-specific fonts — accuracy drops with blur, glare, small plates, strong angle, or low light. Close-up, straight-on plates read best.
- Indian formats (`MH12AB1234`-style) work, but no format validation is applied — foreign/mis-formatted plates may read incorrectly rather than being rejected.
- CPU inference runs at roughly 5–10 FPS at 1280×720 (measured on this repo's test machine); a CUDA GPU raises this substantially.
- The plate detector detects *plate regions* only; vehicle make/model and plate jurisdiction are out of scope.

---

## 📊 Output

- **Annotated video** — vehicles boxed + tracked with IDs + plate boxes + recognized plate numbers
- **plates.csv** — each detected vehicle with its best-read plate number and confidence

---

## 🗺️ Roadmap

- [x] Vehicle detection + tracking + counting
- [x] License plate detection + OCR (ANPR)
- [ ] Speed estimation (reference-line method)
- [ ] Violation detection (speeding, wrong-way)
- [ ] Analytics dashboard + Docker deployment

---

## 🔒 Privacy Note

For real deployments, license plates and faces should be anonymized/blurred in stored output, in line with applicable data-protection regulations.

---

## 👤 Author

**Rahul Adidravid** — Computer Vision / AI Engineer  
📧 dravidrahul734@gmail.com · 🔗 [LinkedIn](https://linkedin.com/in/rahul-adidravid)

---

## Integration Notes for DRISHTI

- This component runs independently with its own virtual environment
- Shares `yolov8n.pt` from project root (symlinked or copied)
- The `stream_anpr.py` serves a web dashboard on port 5000
- Not directly integrated with DRISHTI's SQLite database or FastAPI backend
- Provides supplementary live ANPR visualization for demo purposes