from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("user_id", "session_id", name="uq_session_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    removed_at = Column(DateTime, nullable=True)
    removed_reason = Column(String, nullable=True)

    user = relationship("User", back_populates="participations")
    session = relationship("Session", back_populates="participants")
