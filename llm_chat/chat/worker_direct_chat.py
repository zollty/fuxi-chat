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


class ChatCompletionResult:
    stream_response: ChatCompletionStreamResponse
    normal_response: ChatCompletionResponse
    error_response: Dict

    def __init__(self, stream_response: ChatCompletionStreamResponse = None,
                 normal_response: ChatCompletionResponse = None, error_response: Dict = None):
        self.stream_response = stream_response
        self.normal_response = normal_response
        self.error_response = error_response

    def to_json(self, text_key: str = "answer") -> Union[str, None]:
        if self.stream_response:
            print(self.stream_response.model_dump())
            if choices := self.stream_response.choices:
                if text := choices[0].delta.content:
                    return json.dumps({text_key: text}, ensure_ascii=False)
            return None
        if self.normal_response:
            if self.normal_response.choices:
                answer = self.normal_response.choices[0].message.content
                return json.dumps({text_key: answer}, ensure_ascii=False)
            return None
        if self.error_response:
            return json.dumps(self.error_response, ensure_ascii=False)

    def to_stream_json(self, text_key: str = "answer") -> Union[str, None]:
        if self.stream_response:
            if choices := self.stream_response.choices:
                if text := choices[0].delta.content:
                    return json.dumps({text_key: text}, ensure_ascii=False)
            return None
        if self.error_response:
            return json.dumps(self.error_response, ensure_ascii=False)

    def to_stream_json_append(self, append_info: dict, text_key: str = "answer") -> Union[str, None]:
        if self.stream_response:
            if choices := self.stream_response.choices:
                if text := choices[0].delta.content:
                    return json.dumps({text_key: text} | append_info, ensure_ascii=False)
            return None
        if self.error_response:
            return json.dumps(self.error_response, ensure_ascii=False)

    def to_normal_json(self, text_key: str = "answer", append_info: dict = None) -> Union[str, None]:
        if self.normal_response:
            if self.normal_response.choices:
                answer = self.normal_response.choices[0].message.content
                if append_info:
                    return json.dumps({text_key: answer} | append_info, ensure_ascii=False)
                return json.dumps({text_key: answer}, ensure_ascii=False)
            return None
        if self.error_response:
            return json.dumps(self.error_response, ensure_ascii=False)

    def to_openai_dict(self) -> dict:
        if self.stream_response:
            return self.stream_response.model_dump(exclude_unset=True)
        if self.normal_response:
            return self.normal_response.model_dump(exclude_unset=True)
        if self.error_response:
            return self.error_response

    def to_message_text(self) -> str:
        return self.normal_response.choices[0].message.content


async def stream_chat_completion(model_name: str, gen_params: Dict[str, Any], n: int, worker_addr: str) -> \
        AsyncGenerator[ChatCompletionResult, None]:
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
        yield ChatCompletionResult(stream_response=chunk)

        previous_text = ""
        async for content in generate_completion_stream(gen_params, worker_addr):
            if content["error_code"] != 0:
                content["code"] = 500
                if not content.get("message"):
                    content["message"] = "llm return error"
                yield ChatCompletionResult(error_response=content)
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
            yield ChatCompletionResult(stream_response=chunk)
    # There is not "content" field in the last delta message, so exclude_none to exclude field "content".
    for finish_chunk in finish_stream_events:
        yield ChatCompletionResult(stream_response=finish_chunk)


async def not_stream_chat_completion(request: ChatCompletionRequest, worker_addr,
                                     gen_params) -> ChatCompletionResult:
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
        return ChatCompletionResult(error_response=ErrorResponse(message=str(e), code=ErrorCode.INTERNAL_ERROR).dict())
    usage = UsageInfo()
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return ChatCompletionResult(
                error_response=ErrorResponse(message=content["text"], code=content["error_code"]).dict())

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

    return ChatCompletionResult(
        normal_response=ChatCompletionResponse(model=request.model, choices=choices, usage=usage))


async def chat_iter(request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionResult, None]:
    """Creates a completion for the chat message"""
    if request.model == 'Qwen1.5-7B-Chat':
        request.model = 'Qwen2-7B-Instruct'

    print(json.dumps(request.model_dump(), ensure_ascii=False))
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
    # print(gen_params)
    # print("---------------end get_gen_params-----------------")

    if request.stream:
        async for j in stream_chat_completion(request.model, gen_params, request.n, worker_addr):
            yield j
    else:
        res = await not_stream_chat_completion(request, worker_addr, gen_params)
        yield res


async def coro_chat_iter(request: ChatCompletionRequest, text_key: str = "answer") -> AsyncGenerator[str, None]:
    stream = request.stream
    async for item in chat_iter(request):
        if stream:
            if ret := item.to_stream_json(text_key=text_key):
                yield ret
        else:
            yield item.to_normal_json(text_key=text_key)


async def chat_iter_given_txt(ret_text: str, stream: bool = True, model_name: str = None) \
        -> AsyncGenerator[ChatCompletionResult, None]:
    """Creates a completion for the given message"""
    id = f"chatcmpl-{shortuuid.random()}"
    i = 0
    if stream:
        # First chunk with role
        choice_data = ChatCompletionResponseStreamChoice(
            index=i,
            delta=DeltaMessage(role="assistant"),
            finish_reason=None,
        )
        chunk = ChatCompletionStreamResponse(
            id=id, choices=[choice_data], model=model_name
        )
        yield ChatCompletionResult(stream_response=chunk)

        choice_data = ChatCompletionResponseStreamChoice(
            index=i,
            delta=DeltaMessage(content=ret_text),
            finish_reason=None,
        )
        chunk = ChatCompletionStreamResponse(
            id=id, choices=[choice_data], model=model_name
        )
        yield ChatCompletionResult(stream_response=chunk)

        choice_data = ChatCompletionResponseStreamChoice(
            index=i,
            delta=DeltaMessage(),
            finish_reason="stop",
        )
        chunk = ChatCompletionStreamResponse(
            id=id, choices=[choice_data], model=model_name
        )
        yield ChatCompletionResult(stream_response=chunk)
    else:
        choices = [ChatCompletionResponseChoice(
            index=i,
            message=ChatMessage(role="assistant", content=ret_text),
            finish_reason="stop",
        )]
        usage = UsageInfo()
        usage.prompt_tokens = 10
        usage.completion_tokens = len(ret_text)
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        res = ChatCompletionResult(
            normal_response=ChatCompletionResponse(model=model_name, choices=choices, usage=usage))
        yield res


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
