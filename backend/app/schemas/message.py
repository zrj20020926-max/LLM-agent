from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(min_length=1)


class MessageRead(MessageCreate):
    id: int
    conversation_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageStreamRequest(BaseModel):
    messages: list[MessageCreate] = Field(min_length=1)

    # 当所有字段校验完成后，再执行这个函数
    @model_validator(mode="after")
    def reject_tool_messages(self) -> "MessageStreamRequest":
        if any(message.role == "tool" for message in self.messages):
            raise ValueError("Message stream does not support tool messages yet")
        return self
