from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageRead, MessageStreamRequest
from app.services import message_service
from app.services.conversation_service import ConversationNotFoundError
from app.services.message_service import (
    MessageStreamAPIError,
    MessageStreamConfigError,
)


router = APIRouter(
    prefix="/conversations/{conversation_id}/messages",
    tags=["message"],
)


def raise_conversation_not_found(error: ConversationNotFoundError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Conversation not found",
    ) from error


@router.get("", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> list[Message]:
    try:
        return message_service.list_messages(db, conversation_id)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)


@router.post(
    "",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
) -> Message:
    try:
        return message_service.create_message(db, conversation_id, payload)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)

# 经过 payload: MessageStreamRequest后
# MessageStreamRequest(
#     messages=[
#         MessageCreate(
#             role='user',
#             content='你好'
#         ),
#         MessageCreate(
#             role='assistant',
#             content='你好，请问有什么可以帮你？'
#         )
#     ]
# )
@router.post("/stream")
def stream_message(
    conversation_id: int,
    payload: MessageStreamRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    try:
        message_service.ensure_conversation_exists(db, conversation_id)
        stream = message_service.stream_deepseek_messages(payload.messages)
        # stream是一个迭代器，里面都是yield的内容，类似
        # def test():
        #     yield "你"
        #     yield "好"
        # 通过next来取迭代器里的内容
        first_chunk = next(stream, None)
    except ConversationNotFoundError as error:
        raise_conversation_not_found(error)
    except MessageStreamConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except MessageStreamAPIError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error

    # 定义流式生成器函数（还得流式返回前端，感觉不如直接前端调大模型了...）
    def content_stream():
        if first_chunk:
            yield first_chunk
        try:
            for chunk in stream:
                yield chunk
        except MessageStreamAPIError as error:
            yield f"\n[DeepSeek error] {error.message}"

    # StreamingResponse 会边生成边发送内容
    return StreamingResponse(
        content_stream(),
        media_type="text/plain; charset=utf-8",
    )
