from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    title: str
    content: str
