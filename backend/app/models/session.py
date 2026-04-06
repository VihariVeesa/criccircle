from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    host_name = Column(String, nullable=False)
    scheduled_time = Column(DateTime, default=datetime.utcnow)
    max_participants = Column(Integer, default=5)