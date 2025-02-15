from datetime import datetime, timedelta
from app.models import Base, User, TimeSlot
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///app.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )

# Query the existing user
user = session.query(User).filter_by(email='musavir119s@gmail.com').first()

if user is None:
    print("User not found")
else:
    num_time_slots = 1000
    time_slots = []
    for _ in range(num_time_slots):
        start_time = random_date(datetime(2024, 1, 1), datetime(2025, 12, 31))
        end_time = start_time + timedelta(hours=random.randint(1, 5))
        report_minutes = (end_time - start_time).seconds // 60

        time_slot = TimeSlot(
            date=start_time.date(),
            start_time=start_time,
            end_time=end_time,
            description=f'Time slot {_}',
            report_minutes=report_minutes,
            owner=user,
        )
        time_slots.append(time_slot)

    session.add_all(time_slots)
    session.commit()

session.close()
print("Hello")