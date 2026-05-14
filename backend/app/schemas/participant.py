from pydantic import BaseModel


class RemovalRequest(BaseModel):
    reason: str | None = None
