from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
)
from app.schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_or_404(db: Session, conversation_id: int) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation

# Depends(get_db) 不是在定义时立即执行 get_db()
# 它是一个声明，告诉 FastAPI："我需要一个依赖，请帮我解析它"
# FastAPI 会在请求到来时调用 get_db()，把返回值赋给 db 参数
@router.get("", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    #  返回SQLAlchemy model 对象， 会通过response_model=list[ConversationRead]转成对应的JSON对象
    statement = select(Conversation).order_by(desc(Conversation.updated_at))
    return list(db.scalars(statement).all())


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    # payload必须是ConversationCreate类型。默认ConversationCreate()创建新对象
    payload: ConversationCreate = ConversationCreate(),
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = Conversation(
        title=payload.title or "新会话",
    )
    db.add(conversation)
    db.commit()
    # 将数据库中的新值同步回 Python 对象
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> Conversation:
    return get_conversation_or_404(db, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    conversation.title = payload.title
    conversation.updated_at = func.now()
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    conversation = get_conversation_or_404(db, conversation_id)
    db.delete(conversation)
    db.commit()
    return {"ok": True}


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> list[Message]:
    get_conversation_or_404(db, conversation_id)
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(db.scalars(statement).all()) 


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
) -> Message:
    conversation = get_conversation_or_404(db, conversation_id)
    message = Message(
        conversation_id=conversation.id,
        role=payload.role,
        content=payload.content,
    )
    conversation.updated_at = func.now()
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
