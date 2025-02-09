from pydantic import BaseModel

class Analytics(BaseModel):
    total_tasks: int
    completed_tasks: int
    total_time_spent: int 