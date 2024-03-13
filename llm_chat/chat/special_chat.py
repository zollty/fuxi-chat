from fastapi import Body
from typing import List, Optional, Union
from llm_chat.config import file_chat_default_temperature, file_chat_summary_model

from llm_chat.chat.chat import chat


async def summary_chat(query: str = Body(..., description="用户输入", examples=["需要总结的文本"]),
                       stream: bool = Body(False, description="流式输出"),
                       model_name: str = Body(None, description="LLM 模型名称。"),
                       temperature: float = Body(file_chat_default_temperature(), description="LLM 采样温度", ge=0.0, le=2.0),
                       max_tokens: Optional[int] = Body(None,
                                                        description="限制LLM生成Token数量，默认None代表模型最大值"),
                       prompt_name: Optional[str] = Body("summary2",
                                                         description="使用的prompt模板名称(在configs/prompt_config.py中配置)")
                       ):
    if not model_name:
        model_name = file_chat_summary_model()
    return chat(query=query, model_name=model_name, temperature=temperature, max_tokens=max_tokens, stream=stream,
                prompt_name=prompt_name)
