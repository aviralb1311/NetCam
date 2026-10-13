# Plan: Codebase Cleanup, Documentation Consolidation & Organization

## Goal
Remove redundant/outdated files, consolidate documentation into a clean `/docs` folder, create a single authoritative root README, and organize the codebase for maintainability.

---

## Current State Analysis

### README Files to Evaluate
| File | Status | Action |
|------|--------|--------|
| `/README.md` (root, 172 lines) | **Primary** - Comprehensive, SIH-focused | **KEEP & ENHANCE** |
| `/SIH_READINESS.md` (root, 141 lines) | Detailed compliance matrix | **MOVE TO `/docs/`** |
| `/automatic-number-plate-detection-using-yolov8/README.md` (213 lines) | Standalone ANPR project doc | **MOVE TO `/docs/legacy-anpr.md`** |
| `/frontend/README.md` (16 lines) | Default Vite template | **DELETE** |
| `/net_cam/README.md` (36 lines) | Default Next.js template | **DELETE** |
| `/docs/FILES_TO_DELETE_AFTER_MIGRATION.md` | Migration artifact | **DELETE** |
| `/docs/MYSQL_MIGRATION_PLAN.md` | Historical migration plan | **ARCHIVE or DELETE** |
| `/docs/MYSQL_SETUP.md` | MySQL setup (now using SQLite) | **DELETE** |
| `/docs/PHASE_1_DATASET_AUDIT.md` | Historical audit | **ARCHIVE or DELETE** |
| `/docs/PHASE_3A_MATCHING_DIAGNOSTIC.md` | Historical diagnostic | **ARCHIVE or DELETE** |

### Temporary/Log Files to Clean
| File | Action |
|------|--------|
| `/anpr_stream.log` | **DELETE** (runtime log) |
| `/backend.log` | **DELETE** (runtime log) |
| `/frontend.log` | **DELETE** (runtime log) |
| `/sih_traffic_intelligence.db` | **KEEP** (production SQLite DB) |
| `/yolov8n.pt` (root, 6.5MB) | **KEEP** (YOLO weight) |
| `/test_api_backend.py` | **DELETE** (redundant with `tests/`) |

### Codebase Organization Issues
1. **`automatic-number-plate-detection-using-yolov8/`** - Standalone legacy ANPR project, embedded in root. Should be documented as legacy component or moved to separate repo.
2. **`scripts/`** - Contains migration, evaluation, init scripts - well organized
3. **`tests/`** - Good structure, keep
4. **`evaluation/` & `benchmark/`** - Keep for SIH validation
5. **`database/`** - Empty (only .gitkeep), can remove or document purpose

---

## Implementation Plan

### Phase 1: Remove Redundant Files
1. Delete `/frontend/README.md` (Vite template)
2. Delete `/net_cam/README.md` (Next.js template)
3. Delete `/docs/FILES_TO_DELETE_AFTER_MIGRATION.md`
4. Delete `/docs/MYSQL_MIGRATION_PLAN.md`
5. Delete `/docs/MYSQL_SETUP.md`
6. Delete `/docs/PHASE_1_DATASET_AUDIT.md`
7. Delete `/docs/PHASE_3A_MATCHING_DIAGNOSTIC.md`
8. Delete root log files: `anpr_stream.log`, `backend.log`, `frontend.log`
9. Delete `/test_api_backend.py`

### Phase 2: Reorganize `/docs/` Folder
Create clean documentation structure:
```
/docs/
├── architecture.md          # System architecture (from root README)
├── api-reference.md         # Backend API endpoints summary
├── deployment.md            # Setup & execution (from root README)
├── benchmarking.md          # Benchmarks & validation (from SIH_READINESS)
├── sih-compliance.md        # SIH_READINESS.md renamed
├── legacy-anpr.md           # ANPR standalone project doc
├── database-schema.md       # SQLite schema documentation
├── development.md           # Dev workflow, scripts, testing
└── troubleshooting.md       # Common issues & solutions
```

### Phase 3: Create Authoritative Root README
Single comprehensive `/README.md` covering:
- Project overview & SIH 2026 context
- Three-app architecture (backend, net_cam, frontend)
- Quick start (start-all.sh)
- Ports & services table
- Key features per app
- Links to `/docs/` for deep dives

### Phase 4: Document Legacy ANPR Component
Move ANPR README to `/docs/legacy-anpr.md` with note that it's a standalone component used by `start-all.sh` on port 5000.

---

## Validation Steps
1. Verify no broken links in new documentation
2. Confirm `start-all.sh` still works after log file cleanup
3. Verify `npm run build` in `net_cam/` and `frontend/` still pass
4. Check git status shows only intended changes

---

## Out of Scope
- Moving `automatic-number-plate-detection-using-yolov8/` to separate repo (architectural decision)
- Modifying application code (only docs & cleanup)
- Database migration (already using SQLite)

---

## Questions for User

1. **Legacy ANPR folder**: Keep `automatic-number-plate-detection-using-yolov8/` in root as-is, or move to `/docs/legacy/` or separate repo?
   - *Recommendation*: Keep in root but document it in `/docs/legacy-anpr.md` as integrated component

2. **Historical docs in `/docs/`**: Archive `MYSQL_MIGRATION_PLAN.md`, `PHASE_1_DATASET_AUDIT.md`, `PHASE_3A_MATCHING_DIAGNOSTIC.md` to a subfolder `/docs/archive/`, or delete entirely?
   - *Recommendation*: Move to `/docs/archive/` for historical reference

3. **Database folder**: Remove empty `/database/` folder (only .gitkeep)?
   - *Recommendation*: Keep with a README explaining it's for future MySQL migration

4. **Root Python files**: Keep `run_drishti_master.py` and `run.sh` as alternative launchers?
   - *Recommendation*: Keep both, document in deployment guide