from typing import AsyncIterable, Optional
from fastapi.responses import StreamingResponse, JSONResponse
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from jian.llm_chat.chat.worker_direct_chat import chat_iter, ChatCompletionRequest
from jian.llm_chat.config import default_model


async def keyword_extraction(doc: str,
                             model_name: str = None,
                             max_tokens: Optional[int] = 2000,
                             temperature: Optional[float] = 0.1,
                             ):
    if not model_name:
        model_name = default_model()

    history = [format_jinja2_prompt_tmpl(tmpl_type="llm_chat", tmpl_name="关键词提取", text=doc)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    stream=False,
                                    )

    item = await anext(chat_iter(request))
    if item.error_response:
        return JSONResponse(item.error_response, status_code=500)

    answer = item.to_message_text()
    answer = answer.replace("关键词：", "")

    return JSONResponse(answer.split("、"), status_code=200)
