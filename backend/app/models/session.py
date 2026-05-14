from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, default=60, nullable=False)
    max_participants = Column(Integer, default=5, nullable=False)
    meeting_link = Column(String, nullable=True)
    status = Column(String, default="scheduled", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    host = relationship("User", back_populates="hosted_sessions")
    participants = relationship(
        "Participant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    ratings = relationship(
        "Rating",
        back_populates="session",
        cascade="all, delete-orphan",
    )
