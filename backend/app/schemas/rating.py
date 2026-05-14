from pydantic import BaseModel, Field


class SessionRatingCreate(BaseModel):
    rated_user_id: int
    score: int = Field(ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=500)
