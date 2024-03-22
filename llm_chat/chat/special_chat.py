from fastapi import Body
from sse_starlette.sse import EventSourceResponse
from typing import List, Optional, Union
import json
from jian.llm_chat.config import file_chat_summary_model, file_chat_default_temperature, summary_max_length
from fastapi.responses import StreamingResponse, JSONResponse
from fastchat.protocol.openai_api_protocol import ChatCompletionResponse
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from jian.llm_chat.chat.worker_direct_chat import ChatCompletionRequest, \
    create_stream_chat_completion, create_not_stream_chat_completion
from jian.llm_chat.chat.doc_summary import summary_doc


async def summary_chat(query: str = Body(..., description="用户输入", examples=["需要总结的文本"]),
                       stream: bool = Body(False, description="流式输出"),
                       model_name: str = Body(None, description="LLM 模型名称。"),
                       temperature: Optional[float] = Body(None, description="LLM 采样温度", ge=0.0, le=2.0),
                       max_tokens: Optional[int] = Body(None,
                                                        description="限制LLM生成Token数量，默认None代表模型最大值"),
                       prompt_name: Optional[str] = Body(None,
                                                         description="使用的prompt模板名称(在configs/prompt_config.py中配置)")
                       ):
    if not model_name:
        model_name = file_chat_summary_model()
    if not max_tokens:
        max_tokens = -1
    if not temperature:
        temperature = file_chat_default_temperature()
    prompt_name = "summary6"
    # if not prompt_name:
    #     if len(query) > 800:
    #         prompt_name = "summary5"
    #     else:
    #         prompt_name = "summary3"

    # return EventSourceResponse(summary_doc(query, model_name=model_name,
    #                                        prompt_name=prompt_name,
    #                                        max_tokens=max_tokens,
    #                                        temperature=temperature,
    #                                        stream=stream,
    #                                        ))

    history = [format_jinja2_prompt_tmpl(tmpl_type="doc_chat", tmpl_name=prompt_name, text=query)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    stream=stream,
                                    )

    def data_handler(ctx) -> str:
        return json.dumps({"answer": ctx["text"]}, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"answer": answer}, status_code=200)
        else:
            return res
