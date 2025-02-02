from pydantic import BaseModel

class TaskBase(BaseModel):
    time_slot: str
    is_over: bool = False
    to_do_list: str
    report_min: int
    progress: float
    rating: int

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int

    class Config:
        orm_mode = True