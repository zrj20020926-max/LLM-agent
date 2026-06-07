import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.conversation_service import get_conversation_or_raise

logger = logging.getLogger(__name__)


@dataclass
class MessageStreamAPIError(Exception):
    status_code: int
    message: str


class MessageStreamConfigError(Exception):
    pass


def ensure_conversation_exists(db: Session, conversation_id: int) -> None:
    get_conversation_or_raise(db, conversation_id)


def list_messages(db: Session, conversation_id: int) -> list[Message]:
    get_conversation_or_raise(db, conversation_id)
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(db.scalars(statement).all())


def create_message(
    db: Session,
    conversation_id: int,
    payload: MessageCreate,
) -> Message:
    conversation = get_conversation_or_raise(db, conversation_id)
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


def stream_deepseek_messages(
    messages: list[MessageCreate],
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> Iterator[str]:
    deepseek_api_key = api_key or settings.DEEPSEEK_API_KEY
    if not deepseek_api_key:
        raise MessageStreamConfigError(
            "DeepSeek API Key is missing. Set DEEPSEEK_API_KEY in backend/.env or environment variables."
        )

    deepseek_base_url = (base_url or settings.DEEPSEEK_BASE_URL).rstrip("/")
    deepseek_model = model or settings.DEEPSEEK_MODEL
    payload = {
        "model": deepseek_model,
        # model_dump把一个模型对象转换成 普通 Python 字典
        "messages": [message.model_dump() for message in messages],
        "stream": True,
    }
    request = Request(
        f"{deepseek_base_url}/chat/completions",
        # json.dumps() 把 Python dict 转成 JSON 字符串
        # .encode("utf-8") 转成字节流，因为 urllib.request 需要 bytes 类型的 body
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {deepseek_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    # 返回SSE流（很多行）
    # data: {"choices":[{"delta":{"content":"你"}}]}
    # data: {"choices":[{"delta":{"content":"好"}}]}
    # data: {"choices":[{"delta":{"content":"！"}}]}
    # data: [DONE]

    response = None
    try:
        response = urlopen(request, timeout=60)
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line or not line.startswith("data:"):
                continue

            data = line.removeprefix("data:").strip()
            if data == "[DONE]":
                break

            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse DeepSeek stream chunk: %s", data)
                continue

            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                yield content
    except GeneratorExit:
        logger.info("Client disconnected from message stream")
        raise
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise MessageStreamAPIError(error.code, body or error.reason) from error
    except URLError as error:
        raise MessageStreamAPIError(502, f"DeepSeek network error: {error.reason}") from error
    finally:
        if response is not None:
            response.close()
