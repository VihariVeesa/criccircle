from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    google_sub = Column(String, unique=True, index=True, nullable=True)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_scope = Column(Text, nullable=True)
    google_token_expires_at = Column(DateTime, nullable=True)
    role = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    rules_accepted_at = Column(DateTime, nullable=True)
    average_rating = Column(Float, default=0.0, nullable=False)
    ratings_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    hosted_sessions = relationship("Session", back_populates="host")
    participations = relationship("Participant", back_populates="user")
    ratings_given = relationship(
        "Rating",
        foreign_keys="Rating.rater_user_id",
        back_populates="rater",
    )
    ratings_received = relationship(
        "Rating",
        foreign_keys="Rating.rated_user_id",
        back_populates="rated_user",
    )
