from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.conversation import Conversation
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
)
from app.services import conversation_service
from app.services.conversation_service import ConversationNotFoundError

router = APIRouter(prefix="/conversations", tags=["conversations"])


def raise_conversation_not_found(error: ConversationNotFoundError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Conversation not found",
    ) from error


# [
#     Conversation(
#         id=1,
#         title="聊天1",
#         user_id=123,
#         secret_token="xxx"
#     )
# ]

# 通过response_model转化成（将SQLAlchemy ORM 模型类转化成给前端看的Response Schema）

# [
#   {
#     "id": 1,
#     "title": "聊天1"
#   }
# ]
@router.get("", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    return conversation_service.list_conversations(db)


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    # 要求payload是ConversationCreate格式，没有的话默认创建一个ConversationCreate
    payload: ConversationCreate = ConversationCreate(),
    db: Session = Depends(get_db),
) -> Conversation:
    return conversation_service.create_conversation(db, payload)


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> Conversation:
    try:
        return conversation_service.get_conversation(db, conversation_id)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
) -> Conversation:
    try:
        return conversation_service.update_conversation(db, conversation_id, payload)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    try:
        conversation_service.delete_conversation(db, conversation_id)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)
    return {"ok": True}
