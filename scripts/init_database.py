"""
scripts/init_database.py

Initializes SQLite database `sih_traffic_intelligence.db`, creates all 10 normalized tables,
and seeds the 2 junctions and 4 CCTV cameras with accurate GIS coordinates.
Safe to execute multiple times (idempotent).
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.connection import Base, engine
from backend.database.models import (
    Junction,
    Camera,
    SystemSetting,
)


def seed_core_topology(engine):
    """Seed Junction A & B, the 4 cameras, and default system settings."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Seed Junctions
        junctions_data = [
            {
                "junction_code": "junction_A",
                "name": "Junction A — South Gate Quad",
                "latitude": 23.710299,
                "longitude": 86.952779,
            },
            {
                "junction_code": "junction_B",
                "name": "Junction B — North Gate Quad",
                "latitude": 23.713932,
                "longitude": 86.952211,
            },
        ]

        junction_map = {}
        for j_data in junctions_data:
            existing = session.execute(
                select(Junction).filter_by(junction_code=j_data["junction_code"])
            ).scalar_one_or_none()

            if not existing:
                j_obj = Junction(**j_data)
                session.add(j_obj)
                session.flush()
                junction_map[j_data["junction_code"]] = j_obj.id
                print(f"[+] Seeded Junction: {j_data['junction_code']} (ID: {j_obj.id})")
            else:
                junction_map[j_data["junction_code"]] = existing.id
                print(f"[-] Junction already exists: {j_data['junction_code']} (ID: {existing.id})")

        # 2. Seed Cameras
        cameras_data = [
            {
                "camera_code": "junction_A_camera_01",
                "camera_name": "Junction A — Camera 01 (Inbound Entry)",
                "junction_id": junction_map["junction_A"],
                "video_path": "dataset/junction_A/camera_01.mp4",
                "latitude": 23.710299,
                "longitude": 86.952779,
                "status": "active",
            },
            {
                "camera_code": "junction_A_camera_02",
                "camera_name": "Junction A — Camera 02 (Outbound Exit)",
                "junction_id": junction_map["junction_A"],
                "video_path": "dataset/junction_A/camera_02.mp4",
                "latitude": 23.710293,
                "longitude": 86.952695,
                "status": "active",
            },
            {
                "camera_code": "junction_B_camera_01",
                "camera_name": "Junction B — Camera 01 (Inbound Entry)",
                "junction_id": junction_map["junction_B"],
                "video_path": "dataset/junction_B/camera_01.mp4",
                "latitude": 23.713932,
                "longitude": 86.952211,
                "status": "active",
            },
            {
                "camera_code": "junction_B_camera_02",
                "camera_name": "Junction B — Camera 02 (Outbound Exit)",
                "junction_id": junction_map["junction_B"],
                "video_path": "dataset/junction_B/camera_02.mp4",
                "latitude": 23.713929,
                "longitude": 86.952144,
                "status": "active",
            },
        ]

        for c_data in cameras_data:
            existing = session.execute(
                select(Camera).filter_by(camera_code=c_data["camera_code"])
            ).scalar_one_or_none()

            if not existing:
                c_obj = Camera(**c_data)
                session.add(c_obj)
                session.flush()
                print(f"[+] Seeded Camera: {c_data['camera_code']} (ID: {c_obj.id})")
            else:
                # Keep coordinates and video_path up to date
                existing.latitude = c_data["latitude"]
                existing.longitude = c_data["longitude"]
                existing.video_path = c_data["video_path"]
                print(f"[-] Camera updated/exists: {c_data['camera_code']} (ID: {existing.id})")

        # 3. Seed Default System Settings
        settings = [
            ("system_name", "SIH 2026 Traffic Intelligence Platform", "Platform Title"),
            ("speed_limit_kmh", "60.0", "City Arterial Speed Limit in km/h"),
            ("ocr_confidence_threshold", "0.50", "Minimum OCR confidence to record observation"),
            ("alert_poll_interval_sec", "3", "Frontend polling interval for live alerts"),
        ]

        for k, v, desc in settings:
            existing = session.execute(
                select(SystemSetting).filter_by(setting_key=k)
            ).scalar_one_or_none()
            if not existing:
                session.add(SystemSetting(setting_key=k, setting_value=v, description=desc))

        session.commit()
        print("[+] Core topology & settings committed successfully.")

    except Exception as e:
        session.rollback()
        print(f"[!] Error seeding topology: {e}")
        raise
    finally:
        session.close()


def main():
    print("==================================================")
    print("SIH 2026: SQLite Database Initializer")
    print("==================================================")

    if not engine:
        print("[!] Database engine is not configured.")
        sys.exit(1)

    print("[*] Creating all 10 relational tables and indexes...")
    Base.metadata.create_all(engine)
    print("[+] All tables verified / created.")

    print("[*] Seeding core junctions and cameras...")
    seed_core_topology(engine)

    print("==================================================")
    print("[SUCCESS] DATABASE INITIALIZATION COMPLETE & SIH-READY")
    print("==================================================")


if __name__ == "__main__":
    main()