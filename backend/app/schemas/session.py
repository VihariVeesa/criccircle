from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    topic: str
    description: str | None = None
    scheduled_time: datetime
    duration_minutes: int = 60
    max_participants: int = 5
    meeting_link: str | None = None
