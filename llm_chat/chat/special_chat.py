from fastapi import Body
from sse_starlette.sse import EventSourceResponse
from typing import List, Optional, Union
from llm_chat.config import file_chat_default_temperature, file_chat_summary_model

from llm_chat.chat.doc_summary5 import doc_chat_iterator


async def summary_chat(query: str = Body(..., description="用户输入", examples=["需要总结的文本"]),
                       stream: bool = Body(False, description="流式输出"),
                       model_name: str = Body(None, description="LLM 模型名称。"),
                       temperature: float = Body(file_chat_default_temperature(), description="LLM 采样温度", ge=0.0,
                                                 le=2.0),
                       max_tokens: Optional[int] = Body(None,
                                                        description="限制LLM生成Token数量，默认None代表模型最大值"),
                       prompt_name: Optional[str] = Body("summary2",
                                                         description="使用的prompt模板名称(在configs/prompt_config.py中配置)")
                       ):
    if not model_name:
        model_name = file_chat_summary_model()
    if not max_tokens:
        max_tokens = -1
    return EventSourceResponse(doc_chat_iterator(doc=query,
                                                 stream=stream,
                                                 model_name=model_name,
                                                 max_tokens=max_tokens,
                                                 temperature=temperature,
                                                 prompt_name=prompt_name,
                                                 src_info=None))
