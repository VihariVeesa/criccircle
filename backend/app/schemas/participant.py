from pydantic import BaseModel

class JoinSession(BaseModel):
    user_id: int
    session_id: int