from datetime import datetime

from pydantic import BaseModel, Field


class ConversationBase(BaseModel):
    title: str = Field(default="新会话", max_length=255)

# 继承了 ConversationBase，所以字段还是title
class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ConversationRead(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # 让Pydantic可以以conversation.id的方式取值
    model_config = {"from_attributes": True}
