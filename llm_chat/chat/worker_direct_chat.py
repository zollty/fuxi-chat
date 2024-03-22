import asyncio
import json
from typing import Generator, Optional, Union, Dict, List, Iterator, Any, AsyncGenerator
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from fastchat.protocol.openai_api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    ChatMessage,
    ChatCompletionResponseChoice,
    DeltaMessage,
    ErrorResponse,
    UsageInfo,
)
import shortuuid
from fastchat.constants import ErrorCode
from fastchat.serve.openai_api_server import (app, logger, fetch_remote, get_gen_params, get_worker_address,
                                              check_requests, chat_completion_stream_generator, generate_completion,
                                              create_error_response,
                                              check_api_key, app_settings, generate_completion_stream)

import time
from pydantic import BaseModel, Field


class ChatCompletionResponseSpecial(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{shortuuid.random()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseStreamChoice]
    usage: UsageInfo


async def create_stream_chat_completion(request: ChatCompletionRequest, data_handler,
                                        err_handler=lambda e: json.dumps(e, ensure_ascii=False),
                                        success_last_handler=None, finish_handler=None):
    """Creates a completion for the chat message"""
    worker_addr = await get_worker_address(request.model)

    # print("---------------start get_gen_params-----------------")
    gen_params = await get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )
    # print("---------------end get_gen_params-----------------")
    # print(gen_params)
    finish_stream_events = []
    for i in range(request.n):
        previous_text = ""
        async for content in generate_completion_stream(gen_params, worker_addr):
            # print("---------------content-----------------")
            # print(content)
            if content["error_code"] != 0:
                content["code"] = 500
                if not content.get("message"):
                    content["message"] = "llm return error"
                yield err_handler(content)
                return
            decoded_unicode = content["text"].replace("\ufffd", "")
            delta_text = decoded_unicode[len(previous_text):]
            previous_text = (
                decoded_unicode
                if len(decoded_unicode) > len(previous_text)
                else previous_text
            )

            if len(delta_text) == 0:
                delta_text = None

            if delta_text is None:
                if content.get("finish_reason", None) is not None:
                    finish_stream_events.append({
                        "index": i,
                        "content": delta_text,
                        "finish_reason": content.get("finish_reason", None)})
                continue

            content["text"] = delta_text
            yield data_handler(content)
    # There is not "content" field in the last delta message, so exclude_none to exclude field "content".
    if finish_handler:
        for finish_chunk in finish_stream_events:
            fval = finish_handler(finish_chunk)
            if fval:
                yield fval
    if success_last_handler:
        sval = success_last_handler()
        if sval:
            yield sval


# class StreamChunk:
#     text: str = None
#     code: str = None
#     message: str = None
#     logprobs: bool = False

def stream_chat_completion(model_name: str, gen_params: Dict[str, Any], n: int, worker_addr: str) -> AsyncGenerator[dict, None]:
    """
    Event stream format:
    https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
    """
    id = f"chatcmpl-{shortuuid.random()}"
    finish_stream_events = []
    for i in range(n):
        # First chunk with role
        choice_data = ChatCompletionResponseStreamChoice(
            index=i,
            delta=DeltaMessage(role="assistant"),
            finish_reason=None,
        )
        chunk = ChatCompletionStreamResponse(
            id=id, choices=[choice_data], model=model_name
        )
        yield chunk.model_dump(exclude_unset=True)

        previous_text = ""
        for content in generate_completion_stream(gen_params, worker_addr):
            if content["error_code"] != 0:
                yield content
                return
            decoded_unicode = content["text"].replace("\ufffd", "")
            delta_text = decoded_unicode[len(previous_text):]
            previous_text = (
                decoded_unicode
                if len(decoded_unicode) > len(previous_text)
                else previous_text
            )

            if len(delta_text) == 0:
                delta_text = None
            choice_data = ChatCompletionResponseStreamChoice(
                index=i,
                delta=DeltaMessage(content=delta_text),
                finish_reason=content.get("finish_reason", None),
            )
            chunk = ChatCompletionStreamResponse(
                id=id, choices=[choice_data], model=model_name
            )
            if delta_text is None:
                if content.get("finish_reason", None) is not None:
                    finish_stream_events.append(chunk)
                continue
            yield chunk.model_dump(exclude_unset=True)
    # There is not "content" field in the last delta message, so exclude_none to exclude field "content".
    for finish_chunk in finish_stream_events:
        yield finish_chunk.model_dump(exclude_none=True)


async def not_stream_chat_completion_special2(request: ChatCompletionRequest, worker_addr, gen_params) -> AsyncGenerator[dict]:
    """Creates a completion for the chat message"""
    choices = []
    chat_completions = []
    for i in range(request.n):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        logger.exception(e)
        yield ErrorResponse(message=str(e), code=ErrorCode.INTERNAL_ERROR).dict()
        return
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            yield ErrorResponse(message=content["text"], code=content["error_code"]).dict()
            return

        choices.append(
            ChatCompletionResponseStreamChoice(
                index=i,
                delta=ChatMessage(role="assistant", content=content["text"]),
                finish_reason=content.get("finish_reason", "stop"),
            )
        )
        if "usage" in content:
            task_usage = UsageInfo.parse_obj(content["usage"])
            for usage_key, usage_value in task_usage.dict().items():
                setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    yield ChatCompletionResponseSpecial(model=request.model, choices=choices, usage=usage).model_dump(
        exclude_unset=True)


async def not_stream_chat_completion_special(request: ChatCompletionRequest, worker_addr, gen_params) -> dict:
    """Creates a completion for the chat message"""
    choices = []
    chat_completions = []
    for i in range(request.n):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        logger.exception(e)
        return ErrorResponse(message=str(e), code=ErrorCode.INTERNAL_ERROR).dict()
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return ErrorResponse(message=content["text"], code=content["error_code"]).dict()

        choices.append(
            ChatCompletionResponseStreamChoice(
                index=i,
                delta=ChatMessage(role="assistant", content=content["text"]),
                finish_reason=content.get("finish_reason", "stop"),
            )
        )
        if "usage" in content:
            task_usage = UsageInfo.parse_obj(content["usage"])
            for usage_key, usage_value in task_usage.dict().items():
                setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    return ChatCompletionResponseSpecial(model=request.model, choices=choices, usage=usage).model_dump(
        exclude_unset=True)


async def chat_iter(request: ChatCompletionRequest) -> AsyncGenerator[dict, None, Any]:
    """Creates a completion for the chat message"""
    worker_addr = await get_worker_address(request.model)

    # print("---------------start get_gen_params-----------------")
    gen_params = get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )
    # print("---------------end get_gen_params-----------------")
    # print(gen_params)

    if request.stream:
        return stream_chat_completion(request.model, gen_params, request.n, worker_addr)
    # else:
    #     return not_stream_chat_completion_special2(request, worker_addr, gen_params)


async def chat_iter33(request: ChatCompletionRequest) -> AsyncGenerator[dict]:
    """Creates a completion for the chat message"""
    worker_addr = await get_worker_address(request.model)

    # print("---------------start get_gen_params-----------------")
    gen_params = get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )
    # print("---------------end get_gen_params-----------------")
    # print(gen_params)

    yield not_stream_chat_completion_special2(request, worker_addr, gen_params)



async def not_stream_chat_completion(request: ChatCompletionRequest, worker_addr, gen_params) -> Dict:
    """Creates a completion for the chat message"""
    choices = []
    chat_completions = []
    for i in range(request.n):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        return ErrorResponse(message=str(e), code=ErrorCode.INTERNAL_ERROR).dict()
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return ErrorResponse(message=content["text"], code=content["error_code"]).dict()

        choices.append(
            ChatCompletionResponseChoice(
                index=i,
                message=ChatMessage(role="assistant", content=content["text"]),
                finish_reason=content.get("finish_reason", "stop"),
            )
        )
        if "usage" in content:
            task_usage = UsageInfo.parse_obj(content["usage"])
            for usage_key, usage_value in task_usage.dict().items():
                setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    return ChatCompletionResponse(model=request.model, choices=choices, usage=usage).model_dump(exclude_unset=True)


async def chat_iter2(request: ChatCompletionRequest) -> Iterator[Dict]:
    """Creates a completion for the chat message"""
    worker_addr = get_worker_address(request.model)

    # print("---------------start get_gen_params-----------------")
    gen_params = get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )
    # print("---------------end get_gen_params-----------------")
    # print(gen_params)

    if request.stream:
        finish_stream_events = []
        for i in range(request.n):
            previous_text = ""
            async for content in generate_completion_stream(gen_params, worker_addr):
                # print("---------------content-----------------")
                # print(content)
                if content["error_code"] != 0:
                    content["code"] = 500
                    if not content.get("message"):
                        content["message"] = "llm return error"
                    yield content
                    return
                decoded_unicode = content["text"].replace("\ufffd", "")
                delta_text = decoded_unicode[len(previous_text):]
                previous_text = (
                    decoded_unicode
                    if len(decoded_unicode) > len(previous_text)
                    else previous_text
                )

                if len(delta_text) == 0:
                    delta_text = None

                if delta_text is None:
                    if content.get("finish_reason", None) is not None:
                        finish_stream_events.append({
                            "index": i,
                            "content": delta_text,
                            "finish_reason": content.get("finish_reason", None)})
                    continue

                content["text"] = delta_text
                yield content
        # There is not "content" field in the last delta message, so exclude_none to exclude field "content".
        for finish_chunk in finish_stream_events:
            yield finish_chunk
    else:
        yield not_stream_chat_completion(request, worker_addr, gen_params)


async def create_not_stream_chat_completion(
        request: ChatCompletionRequest) -> Union[ChatCompletionResponse, JSONResponse]:
    """Creates a completion for the chat message"""
    worker_addr = await get_worker_address(request.model)

    gen_params = await get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )

    choices = []
    chat_completions = []
    for i in range(request.n):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        return create_error_response(ErrorCode.INTERNAL_ERROR, str(e))
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return create_error_response(content["error_code"], content["text"])
        choices.append(
            ChatCompletionResponseChoice(
                index=i,
                message=ChatMessage(role="assistant", content=content["text"]),
                finish_reason=content.get("finish_reason", "stop"),
            )
        )
        if "usage" in content:
            task_usage = UsageInfo.parse_obj(content["usage"])
            for usage_key, usage_value in task_usage.dict().items():
                setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    return ChatCompletionResponse(model=request.model, choices=choices, usage=usage)


@app.post("/v1/chat/completions", dependencies=[Depends(check_api_key)])
async def create_chat_completion(request: ChatCompletionRequest):
    """Creates a completion for the chat message"""
    error_check_ret = check_requests(request)
    if error_check_ret is not None:
        return error_check_ret

    worker_addr = await get_worker_address(request.model)

    gen_params = await get_gen_params(
        request.model,
        worker_addr,
        request.messages,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
        max_tokens=request.max_tokens,
        echo=False,
        stop=request.stop,
    )

    if request.stream:
        generator = chat_completion_stream_generator(
            request.model, gen_params, request.n, worker_addr
        )
        return StreamingResponse(generator, media_type="text/event-stream")

    choices = []
    chat_completions = []
    for i in range(request.n):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        return create_error_response(ErrorCode.INTERNAL_ERROR, str(e))
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return create_error_response(content["error_code"], content["text"])
        choices.append(
            ChatCompletionResponseChoice(
                index=i,
                message=ChatMessage(role="assistant", content=content["text"]),
                finish_reason=content.get("finish_reason", "stop"),
            )
        )
        if "usage" in content:
            task_usage = UsageInfo.parse_obj(content["usage"])
            for usage_key, usage_value in task_usage.dict().items():
                setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

    return ChatCompletionResponse(model=request.model, choices=choices, usage=usage)
