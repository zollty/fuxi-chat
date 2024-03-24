from sse_starlette.sse import EventSourceResponse
import json
from typing import Dict, List, Optional, Union, AsyncGenerator

from jian.llm_chat.config import default_model, default_temperature
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, chat_iter, chat_iter_given_txt



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

    if type(request.messages) is list:
        messages = request.messages
        for message in messages:
            print(message)
            if message.get("role") == "user":
                content = message.get("content")
                if content is not None and content=="help":
                    ret_text = "帮助文档\n\n1、输入cmd查看"
                    async def coro_chat_iter1() -> AsyncGenerator[str, None]:
                        async for item in chat_iter_given_txt(ret_text, stream=stream, model_name=model_name):
                            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

                    return EventSourceResponse(coro_chat_iter1())

    async def coro_chat_iter2() -> AsyncGenerator[str, None]:
        async for item in chat_iter(request):
            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

    return EventSourceResponse(coro_chat_iter2())
