from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MessageCreate(BaseModel):
    sender: str
    text: Optional[str] = None
    timestamp: datetime


class MessageResponse(BaseModel):
    id: int
    sender: str
    text: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True


class ThreadCreate(BaseModel):
    thread_id: str
    created_at: datetime


class ThreadResponse(BaseModel):
    id: int
    thread_id: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True
