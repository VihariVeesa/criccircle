from pydantic import BaseModel, Field


class OnboardingUpdate(BaseModel):
    role: str
    bio: str | None = Field(default=None, max_length=300)
    rules_accepted: bool = False
