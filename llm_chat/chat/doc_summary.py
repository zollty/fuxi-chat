from typing import AsyncIterable, Optional, Union
import json
from sse_starlette.sse import EventSourceResponse
from llm_chat.config import file_chat_summary_model, file_chat_default_temperature, summary_max_length
from fastapi.responses import StreamingResponse, JSONResponse
from fastchat.protocol.openai_api_protocol import ChatCompletionResponse
from llm_chat.chat.utils import format_jinja2_prompt_tmpl
from llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, \
    create_stream_chat_completion, create_not_stream_chat_completion

MAX_LENGTH = summary_max_length()


async def summary_doc(doc: str,
                      stream: bool = False,
                      model_name: str = file_chat_summary_model,
                      max_tokens: int = 0,
                      temperature: Optional[float] = None,
                      prompt_name: str = "summary1",
                      src_info=None,
                      ) -> Union[ChatCompletionResponse, JSONResponse]:
    if max_tokens > 0:
        use_max_tokens = max_tokens
    else:
        use_max_tokens = summary_max_length()
    if not temperature:
        temperature = file_chat_default_temperature()

    if len(doc) > MAX_LENGTH:
        doc = doc[:MAX_LENGTH]

    history = [format_jinja2_prompt_tmpl(tmpl_type="doc_chat", tmpl_name=prompt_name, text=doc)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=use_max_tokens,
                                    stream=stream,
                                    )

    def data_handler(ctx) -> str:
        return json.dumps({"answer": ctx["text"]}, ensure_ascii=False)

    def success_last_handler():
        print("-------------------------------------: success_last_handler")
        return json.dumps({"docs": src_info}, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler,
                                                                 success_last_handler=success_last_handler,
                                                                 ))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"answer": answer, "docs": src_info}, status_code=200)
        else:
            return res
