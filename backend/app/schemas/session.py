from pydantic import BaseModel
from datetime import datetime

class SessionCreate(BaseModel):
    topic: str
    host_name: str
    scheduled_time: datetime
    max_participants: int