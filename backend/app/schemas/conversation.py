from pydantic import BaseModel


class ConversationBase(BaseModel):
    title: str
