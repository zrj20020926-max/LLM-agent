from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(min_length=1)


class MessageRead(MessageCreate):
    id: int
    conversation_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
