from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import TimeSlot  # Assuming models.py defines the SQLAlchemy ORM model

# Create a new session
db: Session = SessionLocal()

# Generate and insert bulk data
time_slots = []
base_time = datetime(2025, 2, 12, 8, 0, 0)  # Starting at 8 AM

for i in range(1, 101):  # Insert 100 records
    start_time = base_time + timedelta(minutes=i * 15)  # 15-minute intervals
    end_time = start_time + timedelta(minutes=30)  # 30-minute slots
    status = ["not_started", "in_progress", "completed"][i % 3]  # Cycle through statuses

    time_slot = TimeSlot(
        start_time=start_time,
        end_time=end_time,
        description=f"Time Slot {i}",
        report_minutes=(i % 10) * 5,  # Some random report minutes
        status=status,
        owner_id=(i % 5) + 1  # Assigning to owners 1-5
    )

    time_slots.append(time_slot)

# Bulk insert
db.bulk_save_objects(time_slots)
db.commit()
db.close()

print("Inserted 100 time slots successfully.")
