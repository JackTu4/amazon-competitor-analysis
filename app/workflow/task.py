from enum import Enum
from pydantic import BaseModel
from typing import Optional,Any,Callable
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
class Task(BaseModel):
    name: str
    status: TaskStatus=TaskStatus.PENDING
    result: Optional[Any]=None
    error: Optional[str]=None
    func:Optional[Callable]=None
    class Config:
        arbitrary_types_allowed=True

