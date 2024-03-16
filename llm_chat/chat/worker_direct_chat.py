import asyncio
import json
from typing import Generator, Optional, Union, Dict, List, Any, Tuple

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from fastchat.protocol.openai_api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ErrorResponse,
    ChatCompletionResponseChoice,
    UsageInfo,
)

from fastchat.constants import ErrorCode
from fastchat.serve.openai_api_server import (app, logger, fetch_remote, get_gen_params, get_worker_address,
                                              check_requests, chat_completion_stream_generator, generate_completion,
                                              create_error_response,
                                              check_api_key, app_settings, generate_completion_stream)
# import cachetools
# # 创建一个带 TTL 的缓存对象
# ttl_cache = cachetools.TTLCache(maxsize=100, ttl=60)
#
#
# async def get_worker_address(model_name: str) -> str:
#     """
#     Get worker address based on the requested model
#
#     :param model_name: The worker's model name
#     :return: Worker address from the controller
#     :raises: :class:`ValueError`: No available worker for requested model
#     """
#     if worker_addr := ttl_cache.get("worker_addr", None):
#         return worker_addr
#
#     controller_address = app_settings.controller_address
#     worker_addr = await fetch_remote(
#         controller_address + "/get_worker_address", {"model": model_name}, "address"
#     )
#
#     # No available worker
#     if worker_addr == "":
#         raise ValueError(f"No available worker for {model_name}")
#     logger.debug(f"model_name: {model_name}, worker_addr: {worker_addr}")
#     ttl_cache["worker_addr"] = worker_addr
#     return worker_addr


# async def get_gen_params(*args, **kwargs) -> Dict[str, Any]:
#     gen_params = await get_gen_params2(*args, **kwargs)
#     if not gen_params["max_new_tokens"] or gen_params["max_new_tokens"] <= 0:
#         gen_params["max_new_tokens"] = 1024 * 1024
#     return gen_params


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
