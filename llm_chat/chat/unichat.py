from sse_starlette.sse import EventSourceResponse
import json
from typing import Dict, List, Optional, Union, AsyncGenerator

from jian.llm_chat.config import default_model, default_temperature
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, chat_iter


async def unichat(request: ChatCompletionRequest):
    """Creates a completion for the chat message"""
    model_name = request.model
    stream = request.stream
    if not model_name or model_name == "auto":
        model_name = default_model()
        request.model = model_name

    error_check_ret = check_requests(request)
    if error_check_ret is not None:
        return error_check_ret

    async def coro_chat_iter2() -> AsyncGenerator[str, None]:
        async for item in chat_iter(request):
            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

    return EventSourceResponse(coro_chat_iter2())
