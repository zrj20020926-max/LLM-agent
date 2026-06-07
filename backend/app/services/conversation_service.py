from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate


class ConversationNotFoundError(Exception):
    pass


def get_conversation_or_raise(db: Session, conversation_id: int) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError("Conversation not found")
    return conversation


def list_conversations(db: Session) -> list[Conversation]:
    statement = select(Conversation).order_by(desc(Conversation.updated_at))
    return list(db.scalars(statement).all())


def create_conversation(
    db: Session,
    payload: ConversationCreate,
) -> Conversation:
    conversation = Conversation(
        title=payload.title or "新建会话",
    )
    db.add(conversation)
    db.commit()
    # SQLAlchemy 会重新从数据库加载该对象的最新状态
    # 会把数据库里最新的字段值覆盖到 Python 对象上
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: int) -> Conversation:
    return get_conversation_or_raise(db, conversation_id)


def update_conversation(
    db: Session,
    conversation_id: int,
    payload: ConversationUpdate,
) -> Conversation:
    conversation = get_conversation_or_raise(db, conversation_id)
    conversation.title = payload.title
    conversation.updated_at = func.now()
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_id: int) -> None:
    conversation = get_conversation_or_raise(db, conversation_id)
    db.delete(conversation)
    db.commit()
