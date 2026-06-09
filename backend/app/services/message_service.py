import json
import logging
import re
import time
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
from app.services.tool_service import TOOLS_SCHEMA, execute_tool

logger = logging.getLogger(__name__)


@dataclass
class MessageStreamAPIError(Exception):
    status_code: int
    message: str


class MessageStreamConfigError(Exception):
    pass


MAX_DEEPSEEK_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1
RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


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

# 如果模型直接回答：边收到边 yield 给前端，如果模型要调用工具：收集 tool_calls
# 后端执行工具，把工具结果再发给 DeepSeek，DeepSeek 基于工具结果生成最终回答
# 继续流式返回给前端
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
    request_messages = [message.model_dump() for message in messages]
    # 组装第一次请求 DeepSeek 的 payload
    payload = {
        "model": deepseek_model,
        "messages": request_messages,
        "stream": True,
        "tools": TOOLS_SCHEMA,
        "tool_choice": choose_tool_choice(request_messages),
    }

    # 用来收集工具调用，因为流式返回时，工具调用参数不是一次性完整返回的
    tool_calls: dict[int, dict] = {}

    for chunk in stream_deepseek_payload(payload, deepseek_api_key, deepseek_base_url):
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        content = delta.get("content")
        if content:
            # 如果有普通文本，直接返回给前端
            yield stream_event("content", content=content)

        for tool_call_delta in delta.get("tool_calls") or []:
            index = tool_call_delta.get("index", 0)
            tool_call = tool_calls.setdefault(
                index,
                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
            )
            if tool_call_delta.get("id"):
                tool_call["id"] = tool_call_delta["id"]
            if tool_call_delta.get("type"):
                tool_call["type"] = tool_call_delta["type"]

            function_delta = tool_call_delta.get("function") or {}
            if function_delta.get("name"):
                tool_call["function"]["name"] += function_delta["name"]
            if function_delta.get("arguments"):
                tool_call["function"]["arguments"] += function_delta["arguments"]

    if not tool_calls:
        return

    ordered_tool_calls = [tool_calls[index] for index in sorted(tool_calls)]
    tool_messages = []
    for tool_call in ordered_tool_calls:
        name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]
        result = execute_tool(name, arguments)
        yield stream_event(
            "tool_call",
            name=name,
            arguments=arguments,
            result=result,
        )
        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result,
            }
        )

    followup_payload = {
        "model": deepseek_model,
        "messages": [
            *request_messages,
            {
                "role": "assistant",
                "content": "",
                "tool_calls": ordered_tool_calls,
            },
            *tool_messages,
        ],
        "stream": True,
    }

    for chunk in stream_deepseek_payload(
        followup_payload,
        deepseek_api_key,
        deepseek_base_url,
    ):
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        content = delta.get("content")
        if content:
            yield stream_event("content", content=content)


def stream_event(event_type: str, **payload) -> str:
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def choose_tool_choice(messages: list[dict]) -> str | dict:
    latest_user_message = next(
        (message["content"] for message in reversed(messages) if message["role"] == "user"),
        "",
    )

    # 如果用户消息里出现了类似 123+456、10 * 5 这样的数学表达式，就自动选择 calculator 工具
    if re.search(r"\d+\s*[\+\-\*/%]\s*\d+", latest_user_message):
        return {
            "type": "function",
            "function": {"name": "calculator"},
        }

    if any(keyword in latest_user_message for keyword in ("几点", "现在时间", "当前时间", "time")):
        return {
            "type": "function",
            "function": {"name": "get_current_time"},
        }

    return "auto"

# 向大模型发送请求，返回一个yield的生成器
def stream_deepseek_payload(
    payload: dict,
    deepseek_api_key: str,
    deepseek_base_url: str,
) -> Iterator[dict]:
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
        response = open_deepseek_stream_with_retry(request)
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

            yield chunk
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


def open_deepseek_stream_with_retry(request: Request):
    delay_seconds = INITIAL_RETRY_DELAY_SECONDS
    last_error: HTTPError | URLError | None = None

    for attempt in range(MAX_DEEPSEEK_RETRIES + 1):
        try:
            return urlopen(request, timeout=60)
        except HTTPError as error:
            last_error = error
            if not should_retry_http_error(error) or attempt == MAX_DEEPSEEK_RETRIES:
                # 把当前捕获到的异常原封不动地继续抛出去
                raise

            # 消费响应体直接读并释放连接资源
            error.read()
            logger.warning(
                "DeepSeek request failed with status %s, retrying in %s seconds",
                error.code,
                delay_seconds,
            )
        except URLError as error:
            last_error = error
            if attempt == MAX_DEEPSEEK_RETRIES:
                raise

            logger.warning(
                "DeepSeek network error, retrying in %s seconds: %s",
                delay_seconds,
                error.reason,
            )

        time.sleep(delay_seconds)
        delay_seconds *= 2

    raise last_error


def should_retry_http_error(error: HTTPError) -> bool:
    return error.code in RETRYABLE_HTTP_STATUS_CODES
