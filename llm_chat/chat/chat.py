from fastapi import Body
from sse_starlette.sse import EventSourceResponse
from typing import Dict
import json
from typing import List, Optional, Union
from fastapi.responses import StreamingResponse, JSONResponse
from fastchat.protocol.openai_api_protocol import ChatCompletionResponse

from jian.llm_chat.config import default_model, default_temperature
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, \
    create_stream_chat_completion, create_not_stream_chat_completion
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl

message_id_curr = {"id": 0}


async def chat(query: str = Body(..., description="用户输入", examples=["恼羞成怒"]),
               conversation_id: str = Body("", description="对话框ID"),
               history_len: int = Body(-1, description="从数据库中取历史消息的数量"),
               history: Union[int, List[Dict]] = Body([],
                                                      description="历史对话，设为一个整数可以从数据库中读取历史消息",
                                                      examples=[[
                                                          {"role": "user",
                                                           "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                                          {"role": "assistant", "content": "虎头虎脑"}]]
                                                      ),
               stream: bool = Body(False, description="流式输出"),
               model_name: Optional[str] = Body(None, description="LLM 模型名称。"),
               temperature: Optional[float] = Body(None, description="LLM 采样温度", ge=0.0, le=2.0),
               max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
               # top_p: float = Body(TOP_P, description="LLM 核采样。勿与temperature同时设置", gt=0.0, lt=1.0),
               prompt_name: Optional[str] = Body("default",
                                                 description="使用的prompt模板名称(在configs/prompt_config.py中配置)"),
               system_prompt: Optional[str] = Body(None, description="使用的system_prompt"),
               ):
    if not model_name:
        model_name = default_model()
    if not temperature:
        temperature = default_temperature()

    # 负责保存llm response到message db
    message_id_curr["id"] = message_id_curr["id"] + 1
    message_id = message_id_curr["id"]
    print(f"-------------------------message_id: {message_id}")

    if isinstance(max_tokens, int) and max_tokens <= 0:
        max_tokens = None

    history.append(format_jinja2_prompt_tmpl(prompt=system_prompt, tmpl_type="llm_chat", tmpl_name=prompt_name, input=query))

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    stream=stream,
                                    )

    error_check_ret = check_requests(request)
    if error_check_ret is not None:
        return error_check_ret

    def data_handler(ctx) -> str:
        # print("-------------------------------------: data_handler")
        # print(ctx)
        ctx["message_id"] = message_id
        return json.dumps(ctx, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"text": answer, "message_id": message_id}, status_code=200)
        else:
            return res
