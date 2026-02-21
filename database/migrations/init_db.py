"""
Initialize database - creates all tables and seeds rooms.
Run once: python database/migrations/init_db.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.connection import engine, Base
from database.models import RoomDB, GuestDB, ReservationDB, ChatSessionDB, ChatMessageDB
from database.repository import HotelRepository
from sqlalchemy.orm import Session
from models import Room

def init_db():
    """Create all tables."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")

def seed_rooms():
    """Seed default hotel rooms."""
    with Session(engine) as db:
        repo = HotelRepository(db)

        # Check if rooms already exist
        existing = repo.get_all_rooms()
        if existing:
            print(f"⚠️  Rooms already exist ({len(existing)} rooms). Skipping seed.")
            return

        # Add default rooms
        default_rooms = [
            Room("101", "Standard", 100, 2),
            Room("102", "Standard", 100, 2),
            Room("201", "Deluxe",   150, 4),
            Room("301", "Suite",    250, 6),
        ]

        for room in default_rooms:
            repo.add_room(room)
            print(f"  ✅ Added Room {room.room_number} ({room.room_type})")

        print(f"✅ Seeded {len(default_rooms)} rooms!")

def reset_database():
    print("Resetting database...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database reset complete.")

if __name__ == "__main__":
    reset_database()
    init_db()
    seed_rooms()
    print("\n🏨 Database ready!")

