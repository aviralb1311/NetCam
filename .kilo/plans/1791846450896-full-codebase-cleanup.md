# Plan: Full Codebase Cleanup & Organization

## Goal
Transform the DRISHTI repository into a minimalist, well-organized monorepo with clear separation of concerns, removing redundancy, dead code, and organizational debt while preserving all SIH 2026 compliance capabilities.

---

## Current State Summary

### Root Directory (27 items - Target: ~12)
- **Runtime logs**: `anpr_stream.log`, `backend.log`, `frontend.log` (should be gitignored)
- **Triple launchers**: `start-all.sh`, `run.sh`, `run_drishti_master.py` → consolidate to 1
- **Duplicate weights**: `yolov8n.pt` (root, 6.5MB) + ANPR folder copy
- **Legacy docs**: `SIH_READINESS.md` (replaced by `docs/sih-compliance.md`)
- **Platform configs**: `Aptfile`, `nixpacks.toml`, `Procfile` → pick one or remove
- **Separate apps in subdirs**: `net_cam/` (Next.js), `automatic-number-plate-detection-using-yolov8/` (legacy ANPR)

### Backend (`backend/` - 67KB `app.py` monolith)
- **17 service files** - many overlapping/legacy (MySQL vs SQLite, LLM copilots, etc.)
- **Pipeline modules** - cross-camera matching, ReID, ANPR, tracking (some unused)
- **Config** - single `camera_config.py`

### Frontend (`frontend/` - 223KB `App.css`, 26KB `App.jsx`)
- **27 components** - some experimental (LLM copilot, predictive interception, e-challan)
- **Large CSS** - could be modularized

### Data & Assets
- **Duplicate plates**: `static/plates/` + `static/plates_full_backup/`
- **Evaluation crops**: 4000+ images in `evaluation/crops/` (not version-controlled properly)
- **Model weights**: `models/license_plate.pt` (5.4MB) duplicates ANPR's `license_plate_detector.pt`

### Tests (7 files - Target: 3)
- Core: `test_sih_pipeline.py`, `test_api_endpoints.py`, `test_mysql_database.py`
- **Experimental/LLM**: `test_all_prompts.py`, `test_drishti_gpt.py`, `test_gemini_copilot_live.py`, `test_live_anpr.py`

### Scripts (10 files - Target: 2)
- Keep: `init_database.py`, `migrate_json_to_sqlite.py`
- Archive: 8 one-off/data-processing scripts

---

## Implementation Plan

### Phase 1: Root Directory Cleanup (No Dependencies)
**Goal**: Reduce root to essential files only

| Action | Command | Validation |
|--------|---------|------------|
| Remove runtime logs | `rm anpr_stream.log backend.log frontend.log` | Files gone |
| Remove duplicate SIH_READINESS.md | `rm SIH_READINESS.md` | `docs/sih-compliance.md` exists |
| Consolidate launchers → keep `start-all.sh` | `rm run.sh run_drishti_master.py` | `start-all.sh` works |
| Remove platform configs | `rm Aptfile nixpacks.toml Procfile` | No deployment breakage |
| Remove duplicate yolov8n.pt from ANPR folder | `rm automatic-number-plate-detection-using-yolov8/yolov8n.pt` | Root copy remains |
| Update `.gitignore` | Add patterns (see below) | `git status` clean |

**New `.gitignore` additions:**
```gitignore
# Runtime
*.log
*.db
*.sqlite

# Large assets (use Git LFS or external)
*.pt
*.onnx

# Build artifacts
frontend/dist/
frontend/node_modules/
net_cam/.next/
net_cam/node_modules/

# Python
__pycache__/
*.pyc
.venv/
venv/

# Evaluation data
evaluation/crops/

# Static duplicates
static/plates_full_backup/

# IDE/OS
.DS_Store
.vscode/
.idea/
```

---

### Phase 2: Extract Separate Repositories (Independent)
**Goal**: Remove `net_cam/` and legacy ANPR from monorepo

#### 2A: `net_cam/` → Separate Repository
- **Action**: This is a complete Next.js 14 app with own `.git`, `package.json`, `tsconfig.json`
- **Steps**:
  1. Create new GitHub repo: `drishti-net-cam` or similar
  2. Push `net_cam/` contents as root of new repo
  3. Update any cross-references in DRISHTI docs
  4. Remove `net_cam/` from DRISHTI
  5. Add to `.gitignore` if keeping locally for reference

#### 2B: `automatic-number-plate-detection-using-yolov8/` → Archive or Separate Repo
- **Decision needed**: Archive as `legacy/anpr/` (docs only) OR separate repo
- **If archive**: Keep only `README.md`, `requirements.txt`, `stream_anpr.py` (used by `start-all.sh`), remove `.git`, `venv/`, `*.pt`, `demo.gif`, `cert.*`, `plates.csv`, `__pycache__`
- **If separate repo**: Same as net_cam - push to new repo
- **Recommendation**: Archive as `legacy/anpr/` since `start-all.sh` depends on `stream_anpr.py`

---

### Phase 3: Backend Consolidation (Depends on Phase 1)
**Goal**: Modularize `app.py` (67KB → split routers), remove dead services

#### 3A: Split `app.py` into Domain Routers
```
backend/
├── app.py                 # FastAPI app factory, middleware, lifespan
├── routers/
│   ├── __init__.py
│   ├── cameras.py         # /api/cameras, /api/cameras/{id}/video
│   ├── vehicles.py        # /api/observations, /api/vehicles/{plate}/trajectory, /api/vehicles/search
│   ├── traffic.py         # /api/traffic/timeseries, /api/traffic/heatmap, /api/traffic/od, /api/traffic/congestion
│   ├── blacklist.py       # /api/blacklist*, /api/alerts*
│   └── system.py          # /api/health, /api/system/validation
├── services/
│   ├── __init__.py
│   ├── analytics_engine.py      # KEEP - core analytics
│   ├── blacklist_service.py     # KEEP - watchlist CRUD
│   ├── alert_service.py         # KEEP - alert generation/polling
│   ├── search_service.py        # KEEP - vehicle search/trajectory
│   ├── dataset_service.py       # KEEP - camera metadata, JSON fallback
│   ├── video_service.py         # KEEP - HTTP 206 streaming
│   ├── watchlist_service.py     # KEEP - OCR normalization (rename: plate_normalizer.py)
│   └── yolo_evidence_service.py # KEEP - evidence handling
├── database/
│   ├── connection.py
│   └── models.py
└── config/
    └── camera_config.py
```

#### 3B: Remove/Archive Dead Services
| File | Action | Reason |
|------|--------|--------|
| `drishti_gpt_service.py` (72KB) | Archive → `legacy/` | LLM copilot, not core SIH |
| `live_anpr_service.py` (30KB) | Archive → `legacy/` | Duplicates legacy ANPR |
| `mysql_alert_service.py` | **DELETE** | Using SQLite, not MySQL |
| `mysql_blacklist_service.py` | **DELETE** | Using SQLite |
| `mysql_search_service.py` | **DELETE** | Using SQLite |
| `plate_search_service.py` | **DELETE** | Legacy fallback, merged into search_service |
| `anomaly_service.py` | Archive | Not used in SIH compliance |
| `evidence_certificate.py` | Archive | Not core |
| `signal_retiming_engine.py` | Archive | Not core |
| `vahan_service.py` (17KB) | Archive | RTO integration, not SIH core |
| `signal_retiming_engine.py` | Archive | Not core |

#### 3C: Pipeline Cleanup
| File | Action |
|------|--------|
| `annotation_loader.py` | Keep (used by migration) |
| `calibration.py` | Keep |
| `cross_camera_match.py` | Keep (core ReID) |
| `global_path_validator.py` | Keep |
| `plate_anpr.py` | Keep |
| `vehicle_reid.py` | Keep |
| `vehicle_tracker.py` | Keep |
| `temporal_ocr_voting.py` | Keep |
| `test_video.py` | Delete (test file in pipeline) |

---

### Phase 4: Frontend Cleanup (Independent)
**Goal**: Remove experimental components, modularize CSS

#### 4A: Component Audit - Keep vs Archive
| Keep (Core SIH) | Archive (Experimental) |
|-----------------|------------------------|
| `CameraGrid.jsx` | `DrishtiGptCopilot.jsx` + `.css` |
| `MapView.jsx` | `PredictiveInterceptionCard.jsx` |
| `TrafficAnalyticsPage.jsx` | `EChallanModal.jsx` |
| `BlacklistManagement.jsx` + `BlacklistModal.jsx` | `CorridorTelemetryHub.jsx` |
| `AlertCenter.jsx` | `AiPipelineVisualizer.jsx` |
| `SystemValidationPage.jsx` | `JourneyRouteSummary.jsx` |
| `VehicleDetailModal.jsx` | `JourneyTimeline.jsx` |
| `VehicleSearch.jsx` | |
| `GlobalRegistry.jsx` | |
| `Header.jsx` | |
| `PoliceDossierModal.jsx` | |
| `EvidencePlaybackModal.jsx` | |
| `FullMapModal.jsx` | |
| `JunctionCameraInspector.jsx` | |
| `KpiStrip.jsx` | |
| `LiveAnprStream.jsx` | |
| `SystemHealth.jsx` | |
| `DrishtiEyeLogo.jsx` | |
| `VahanCard.jsx` | |
| `ErrorBoundary.jsx` | |
| `CyberLoadingScreen.jsx` | |

#### 4B: CSS Modularization
- Split `App.css` (223KB) into component-scoped CSS modules or keep single file with clear sections
- Remove unused styles from archived components

#### 4C: Remove Build Artifacts
- `rm -rf frontend/dist/`
- Ensure `node_modules/` in `.gitignore`

---

### Phase 5: Data & Assets Cleanup (Independent)
**Goal**: Remove duplicates, externalize large data

| Action | Command | Notes |
|--------|---------|-------|
| Remove duplicate plates backup | `rm -rf static/plates_full_backup/` | Keep `static/plates/` |
| Remove duplicate model weight | `rm models/license_plate.pt` | Keep ANPR's `license_plate_detector.pt` |
| Remove empty `models/` dir | `rmdir models/` | After above |
| Remove empty `database/` dir | `rmdir database/` | Only `.gitkeep` inside |
| Archive evaluation crops | `mv evaluation/crops/ ../legacy/evaluation_crops/` | Or add to `.gitignore` |
| Remove evaluation README | `rm evaluation/README.md` | Redundant |

---

### Phase 6: Tests Cleanup (Independent)
**Goal**: Keep only core validation tests

| Keep | Archive/Delete |
|------|----------------|
| `test_sih_pipeline.py` | `test_all_prompts.py` |
| `test_api_endpoints.py` | `test_drishti_gpt.py` |
| `test_mysql_database.py` | `test_gemini_copilot_live.py` |
| | `test_live_anpr.py` |

Move archived to `legacy/tests/` or delete.

---

### Phase 7: Scripts Cleanup (Independent)
**Goal**: Keep only essential automation

| Keep | Archive |
|------|---------|
| `init_database.py` | `evaluate_ocr.py` → move to `evaluation/` |
| `migrate_json_to_sqlite.py` | `extract_all_camera_tracks.py` |
| | `extract_cam04.py` |
| | `fix_plate_timestamps.py` |
| | `generate_grid_videos.py` |
| | `infer_single_camera.py` |
| | `live_webcam_anpr.py` |
| | `process_dataset.py` |

Move archived to `legacy/scripts/` or delete.

---

### Phase 8: Documentation Finalization (Depends on Phases 1-7)
**Goal**: Ensure `docs/` reflects final structure

- Update `docs/architecture.md` with new backend router structure
- Update `docs/deployment.md` with single launcher
- Update `docs/development.md` with new test/scripts structure
- Add `docs/legacy.md` documenting archived components
- Verify all internal links in `README.md` resolve

---

## Dependency Graph

```
Phase 1 (Root) ──────┬──→ Phase 3 (Backend)
                     ├──→ Phase 4 (Frontend)
                     ├──→ Phase 5 (Data/Assets)
                     ├──→ Phase 6 (Tests)
                     └──→ Phase 7 (Scripts)

Phase 2 (Extract) ───┴──→ Independent (can run anytime)

Phase 8 (Docs) ──────←── Depends on all above
```

---

## Validation Checklist (Post-Cleanup)

### Functional
- [ ] `./start-all.sh` starts all 3 services (Backend:8000, ANPR:5000, Frontend:5173)
- [ ] Backend health: `curl http://127.0.0.1:8000/api/health` → 200 OK
- [ ] All 15+ API endpoints respond (test via Swagger `/docs`)
- [ ] Frontend loads at `http://127.0.0.1:5173`
- [ ] 4 camera feeds visible in Surveillance Grid
- [ ] GIS Map shows trajectories between junctions
- [ ] Blacklist alerts trigger in real-time
- [ ] System Validation page displays live metrics (90.97% OCR)

### Test Suite
- [ ] `python tests/test_sih_pipeline.py` → 10/10 PASS
- [ ] `python tests/test_api_endpoints.py` → 14/14 PASS
- [ ] `python tests/test_mysql_database.py` → 14/15 PASS (1 pre-existing video file issue)

### Benchmarks
- [ ] `python evaluation/evaluate_ocr.py` → 90.97% exact match
- [ ] `python benchmark/benchmark_pipeline.py` → <500ms latency (if videos present)

### Repository Hygiene
- [ ] `git status` shows only intended changes
- [ ] No `*.log`, `*.db`, `node_modules/`, `__pycache__/`, `*.pt` tracked
- [ ] Root directory ≤ 15 files/dirs
- [ ] `backend/app.py` < 500 lines (router imports only)
- [ ] `frontend/src/components/` ≤ 15 files

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking `start-all.sh` ANPR integration | Test after Phase 2B; keep `stream_anpr.py` in legacy archive |
| Backend router split breaks imports | Do incrementally; test each router; keep `app.py` as factory |
| Frontend component removal breaks App.jsx | Audit imports in `App.jsx` before deleting components |
| Git history loss on extracted repos | Use `git filter-repo` or `git subtree split` to preserve history |
| Missing video files for benchmarks | Document as pre-existing; not a regression |

---

## Out of Scope
- Moving `net_cam/` to separate GitHub repo (user must create repo and push)
- Moving legacy ANPR to separate repo (recommend archiving in `legacy/`)
- Setting up Git LFS for model weights
- CI/CD pipeline updates
- Docker/containerization
- MySQL migration (keep SQLite for SIH demo)

---

## Open Questions (Require User Decisions)

1. **`net_cam/`**: Create separate GitHub repo? (Recommended: Yes - it's a complete independent app)
2. **Legacy ANPR**: Archive as `legacy/anpr/` or separate repo? (Recommended: Archive - `start-all.sh` depends on it)
3. **Model weights**: Use Git LFS for `yolov8n.pt` (6.5MB) and `license_plate_detector.pt` (6.2MB)? Or keep in repo?
4. **Evaluation crops**: Delete from git, store in cloud/DVC, or keep in `legacy/`?
5. **Experimental backend services** (LLM copilots, Vahan, signal retiming): Archive to `legacy/` or delete?
6. **Experimental frontend components** (LLM copilot, predictive interception, e-challan): Archive or delete?

---

## Recommended Decisions

| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| net_cam | Separate repo | Independent Next.js app, different stack, own git history |
| Legacy ANPR | Archive as `legacy/anpr/` | `start-all.sh` uses `stream_anpr.py`; keeps demo working |
| Model weights | Git LFS | Keeps repo clone fast; weights are binary assets |
| Evaluation crops | Delete from git, document external location | 4000+ images bloat repo; not needed for demo |
| Experimental backend | Archive to `legacy/services/` | Preserves work; keeps core clean |
| Experimental frontend | Archive to `legacy/components/` | Preserves work; keeps core clean |

---

## Plan File Location
Saved to: `.kilo/plans/1791846450896-full-codebase-cleanup.md`