# Plan: Migrate DRISHTI from MySQL to SQLite

## Goal
Replace MySQL database with SQLite for zero-configuration local development while maintaining full functionality.

## Files to Modify

### 1. `backend/database/connection.py`
- Change `DATABASE_URL` to use SQLite (`sqlite:///sih_traffic_intelligence.db`)
- Remove MySQL-specific connection pooling options (`pool_pre_ping`, `pool_recycle`, `pool_size`, `max_overflow`, `connect_args`)
- Add `connect_args={"check_same_thread": False}` for SQLite thread safety
- Enable foreign key constraints with event listener: `PRAGMA foreign_keys = ON`
- Update `is_db_connected()` to test SQLite connection

### 2. `scripts/init_database.py`
- Remove `pymysql` import and `ensure_database_exists()` function (SQLite creates file automatically)
- Simplify `main()` to use the shared `engine` from `backend.database.connection`
- Keep `seed_core_topology()` logic (it's database-agnostic)
- Update print messages to reflect SQLite

### 3. `scripts/migrate_json_to_mysql.py` → `scripts/migrate_json_to_sqlite.py`
- Rename file
- Update imports and print messages
- Remove MySQL-specific references in comments/docstrings
- Logic remains identical (uses SQLAlchemy ORM)

### 4. `requirements.txt`
- Remove `pymysql>=1.1.0` (no longer needed for SQLite)
- Keep all other dependencies

### 5. `.env.example`
- Remove MySQL configuration variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
- Add optional `DATABASE_URL` example for SQLite: `sqlite:///sih_traffic_intelligence.db`

### 5. `.env` (user's local config)
- User will copy `.env.example` to `.env` - no MySQL credentials needed

## Files That Work Unchanged (Database-Agnostic)
All service files use SQLAlchemy ORM and work with SQLite:
- `backend/services/mysql_blacklist_service.py` 
- `backend/services/mysql_search_service.py`
- `backend/services/mysql_alert_service.py`
- `backend/services/watchlist_service.py`
- `backend/services/analytics_engine.py`
- All other services

## Validation Plan
1. Run `python scripts/init_database.py` - should create `sih_traffic_intelligence.db` file
2. Run `python scripts/migrate_json_to_sqlite.py` - should populate tables
3. Run `python tests/test_api_endpoints.py` - all 14 tests should pass
4. Run `python tests/test_sih_pipeline.py` - all 10 tests should pass
5. Start backend: `uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload`
6. Verify `/api/health` returns healthy status with SQLite
7. Verify `/api/system/validation` shows database telemetry

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Foreign keys not enforced in SQLite | Add event listener to enable `PRAGMA foreign_keys = ON` on every connection |
| `BigInteger` auto-increment behavior | SQLite uses `INTEGER PRIMARY KEY` which auto-increments correctly |
| Concurrent access in FastAPI | Use `check_same_thread=False` in connect_args |
| DateTime handling | SQLite stores as TEXT, SQLAlchemy handles conversion |

## Out of Scope
- Frontend changes (none needed)
- Video file serving (unchanged)
- Model schema changes (current models work with SQLite)
- Production deployment (this is for local dev)