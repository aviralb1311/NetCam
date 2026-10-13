# DRISHTI Database Schema

## Overview

DRISHTI uses SQLite (`sih_traffic_intelligence.db`) as the primary database for the SIH 2026 demonstration. The schema consists of 6 normalized tables with full foreign-key integrity and indexes for query performance.

> **Note**: The project was originally designed for MySQL 8.0. The SQLite schema maintains the same table structure and relationships. MySQL migration scripts are preserved in `scripts/` for future deployment.

---

## Entity Relationship Diagram

```
junctions (2)
    │
    ├──< cameras (4)
    │       │
    │       ├──< vehicle_tracks (914)
    │       │       │
    │       │       └──< plate_detections (144)
    │       │               │
    │       │               └──< vehicle_observations (144)
    │       │
    │       └──< blacklist_events (5)
    │
    └──< blacklisted_vehicles (2)
            │
            └──< blacklist_events (5)
                    │
                    └──< alerts (5)
```

---

## Table Definitions

### 1. `junctions`
Physical intersection metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `junction_code` | VARCHAR(64) | UNIQUE, NOT NULL | e.g., `junction_A`, `junction_B` |
| `name` | VARCHAR(128) | NOT NULL | e.g., `Junction A` |
| `latitude` | DECIMAL(10,7) | NOT NULL | GPS latitude |
| `longitude` | DECIMAL(10,7) | NOT NULL | GPS longitude |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Seed Data**:
```sql
INSERT INTO junctions (junction_code, name, latitude, longitude) VALUES
('junction_A', 'Junction A', 23.710299, 86.952779),
('junction_B', 'Junction B', 23.713932, 86.952211);
```

---

### 2. `cameras`
Surveillance camera node configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `camera_code` | VARCHAR(64) | UNIQUE, NOT NULL | e.g., `junction_A_camera_01` |
| `camera_name` | VARCHAR(128) | NOT NULL | e.g., `Camera 01` |
| `junction_id` | INTEGER | FK → junctions.id, NOT NULL | Parent junction |
| `video_path` | VARCHAR(255) | NOT NULL | Path to MP4 video file |
| `latitude` | DECIMAL(10,7) | NOT NULL | Camera GPS latitude |
| `longitude` | DECIMAL(10,7) | NOT NULL | Camera GPS longitude |
| `status` | VARCHAR(32) | DEFAULT 'ACTIVE' | Camera status |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Indexes**: `idx_cameras_junction_id` on `junction_id`

**Seed Data**:
```sql
INSERT INTO cameras (camera_code, camera_name, junction_id, video_path, latitude, longitude) VALUES
('junction_A_camera_01', 'Camera 01', 1, 'dataset/junction_A/camera_01.mp4', 23.710299, 86.952779),
('junction_A_camera_02', 'Camera 02', 1, 'dataset/junction_A/camera_02.mp4', 23.710299, 86.952779),
('junction_B_camera_01', 'Camera 01', 2, 'dataset/junction_B/camera_01.mp4', 23.713932, 86.952211),
('junction_B_camera_02', 'Camera 02', 2, 'dataset/junction_B/camera_02.mp4', 23.713932, 86.952211);
```

---

### 3. `vehicle_tracks`
ByteTrack vehicle track sequences per camera.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `camera_id` | INTEGER | FK → cameras.id, NOT NULL | Source camera |
| `track_id` | INTEGER | NOT NULL | ByteTrack-assigned ID |
| `vehicle_type` | VARCHAR(32) | DEFAULT 'car' | Vehicle class |
| `first_frame` | INTEGER | DEFAULT 0 | First detection frame |
| `last_frame` | INTEGER | DEFAULT 0 | Last detection frame |
| `first_timestamp` | DECIMAL(8,2) | NOT NULL | First detection time (sec) |
| `last_timestamp` | DECIMAL(8,2) | NOT NULL | Last detection time (sec) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**: `idx_vehicle_tracks_camera_track` on `(camera_id, track_id)`

---

### 4. `plate_detections`
OCR plate recognition readings linked to vehicle tracks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `vehicle_track_id` | INTEGER | FK → vehicle_tracks.id, NULLABLE | Associated track |
| `camera_id` | INTEGER | FK → cameras.id, NOT NULL | Source camera |
| `detection_code` | VARCHAR(64) | NULLABLE | e.g., `DET_000382` |
| `plate_text` | VARCHAR(32) | NULLABLE | Raw OCR string (e.g., `WB 37 E 1275`) |
| `normalized_plate` | VARCHAR(32) | NULLABLE, INDEXED | Normalized (e.g., `WB37E1275`) |
| `ocr_confidence` | DECIMAL(5,4) | DEFAULT 0.0 | OCR confidence score |
| `plate_detection_confidence` | DECIMAL(5,4) | DEFAULT 0.0 | Plate detector confidence |
| `timestamp_sec` | DECIMAL(8,2) | NOT NULL, INDEXED | Detection timestamp |
| `frame_number` | INTEGER | DEFAULT 0 | Video frame number |
| `plate_image` | VARCHAR(255) | NULLABLE | Path to plate crop image |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**:
- `idx_plate_detections_normalized` on `normalized_plate`
- `idx_plate_detections_timestamp` on `timestamp_sec`
- `idx_plate_detections_camera` on `camera_id`

---

### 5. `blacklisted_vehicles`
Operator-controlled watchlist registry.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `plate_number` | VARCHAR(32) | NOT NULL | Display plate (e.g., `WB37E1275`) |
| `normalized_plate` | VARCHAR(32) | NOT NULL, INDEXED | Normalized plate |
| `reason` | VARCHAR(255) | NOT NULL | Blacklist reason |
| `priority` | VARCHAR(16) | DEFAULT 'HIGH' | `HIGH`, `MEDIUM`, `LOW` |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active status |
| `notes` | TEXT | NULLABLE | Additional notes |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Constraints**: UNIQUE on `(normalized_plate, is_active)`

**Indexes**: `idx_blacklisted_normalized` on `normalized_plate`

**Seed Data**:
```sql
INSERT INTO blacklisted_vehicles (plate_number, normalized_plate, reason, priority) VALUES
('WB37E1275', 'WB37E1275', 'Stolen vehicle', 'HIGH'),
('JH10CS2095', 'JH10CS2095', 'Wanted suspect', 'HIGH');
```

---

### 6. `alerts`
Real-time tactical alert queue for dashboard.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `alert_type` | VARCHAR(64) | NOT NULL | `BLACKLISTED_VEHICLE`, `ROUTE_ANOMALY`, `CONGESTION` |
| `severity` | VARCHAR(16) | DEFAULT 'HIGH' | `CRITICAL`, `WARNING`, `INFO` |
| `plate_number` | VARCHAR(32) | NULLABLE | Associated plate |
| `camera_id` | INTEGER | FK → cameras.id, NULLABLE | Source camera |
| `junction_id` | INTEGER | FK → junctions.id, NULLABLE | Source junction |
| `plate_detection_id` | INTEGER | FK → plate_detections.id, NULLABLE | Source detection |
| `message` | TEXT | NOT NULL | Alert description |
| `is_read` | BOOLEAN | DEFAULT FALSE | Read status |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Alert timestamp |

**Indexes**:
- `idx_alerts_created` on `created_at`
- `idx_alerts_unread` on `is_read` WHERE `is_read = 0`

---

## Additional Tables (MySQL Migration)

The following tables exist in the MySQL migration schema (`scripts/migrate_json_to_mysql.py`) but are not actively used in the current SQLite implementation:

### `vehicle_observations`
Normalized spatial-temporal events for trajectory mapping.
- Links `plate_detections` to `cameras` and `junctions`
- Includes `direction` field for GIS visualization

### `blacklist_events`
Audit log of every blacklisted vehicle detection.
- Links `blacklisted_vehicles` to `plate_detections` and `cameras`
- Includes `confidence`, `status` (`UNRESOLVED`, `ACKNOWLEDGED`, `RESOLVED`)

### `processing_runs`
Pipeline execution telemetry.
- Tracks video processing runs, frames processed, detection counts

### `system_settings`
Configurable operational parameters.
- Key-value store for runtime configuration

---

## Initialization Scripts

### `scripts/init_database.py`
- Creates database and all tables via SQLAlchemy
- Seeds `junctions` (2) and `cameras` (4)
- Idempotent — safe to run multiple times

### `scripts/migrate_json_to_sqlite.py`
- Migrates detection data from `dataset/metadata/detections.json`
- Inserts 914 vehicle tracks, 144 plate detections
- Evaluates blacklist matches and generates alerts
- Idempotent — checks existing records to avoid duplicates

---

## Query Examples

### Get Vehicle Trajectory
```sql
SELECT c.camera_name, j.name as junction_name, 
       pd.timestamp_sec, pd.normalized_plate,
       c.latitude, c.longitude
FROM plate_detections pd
JOIN cameras c ON pd.camera_id = c.id
JOIN junctions j ON c.junction_id = j.id
WHERE pd.normalized_plate = 'WB37E1275'
ORDER BY pd.timestamp_sec;
```

### Get Active Blacklist Alerts
```sql
SELECT a.*, c.camera_name, j.name as junction_name
FROM alerts a
LEFT JOIN cameras c ON a.camera_id = c.id
LEFT JOIN junctions j ON a.junction_id = j.id
WHERE a.is_read = 0
ORDER BY a.created_at DESC;
```

### Traffic Volume by Junction
```sql
SELECT j.name, COUNT(pd.id) as detection_count
FROM plate_detections pd
JOIN cameras c ON pd.camera_id = c.id
JOIN junctions j ON c.junction_id = j.id
GROUP BY j.id, j.name;
```

---

## Backup & Recovery

```bash
# Backup
sqlite3 sih_traffic_intelligence.db .dump > backup.sql

# Restore
sqlite3 sih_traffic_intelligence.db < backup.sql
```

---

## Migration to MySQL (Future)

For production deployment with MySQL 8.0:

1. Update `.env` with MySQL credentials and `USE_SQLITE=false`
2. Run `python scripts/init_database.py` (creates MySQL schema)
3. Run `python scripts/migrate_json_to_mysql.py` (full data migration)
4. Schema includes additional tables: `vehicle_observations`, `blacklist_events`, `processing_runs`, `system_settings`

See `scripts/migrate_json_to_mysql.py` for complete MySQL schema definition.