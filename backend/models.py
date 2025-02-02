from sqlalchemy import Column, Integer, String, Boolean, Float
from .database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    time_slot = Column(String, index=True)
    is_over = Column(Boolean, default=False)
    to_do_list = Column(String)
    report_min = Column(Integer)
    progress = Column(Float)
    rating = Column(Integer)