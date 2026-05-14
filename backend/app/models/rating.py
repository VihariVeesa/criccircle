from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "rater_user_id",
            "rated_user_id",
            name="uq_session_rater_rated",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    rater_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rated_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="ratings")
    rater = relationship("User", foreign_keys=[rater_user_id], back_populates="ratings_given")
    rated_user = relationship(
        "User",
        foreign_keys=[rated_user_id],
        back_populates="ratings_received",
    )
