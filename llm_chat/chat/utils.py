from pydantic import BaseModel, Field
from langchain.prompts.chat import ChatMessagePromptTemplate
from typing import List, Tuple, Dict, Union
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Callable,
    Generator,
    Dict,
    Any,
    Awaitable,
    Union,
    Tuple
)
from common.utils import LOG_VERBOSE, logger

class History(BaseModel):
    """
    对话历史
    可从dict生成，如
    h = History(**{"role":"user","content":"你好"})
    也可转换为tuple，如
    h.to_msy_tuple = ("human", "你好")
    """
    role: str = Field(...)
    content: str = Field(...)

    def to_msg_tuple(self):
        return "ai" if self.role == "assistant" else "human", self.content

    def to_msg_template(self, is_raw=True) -> ChatMessagePromptTemplate:
        role_maps = {
            "ai": "assistant",
            "human": "user",
        }
        role = role_maps.get(self.role, self.role)
        if is_raw:  # 当前默认历史消息都是没有input_variable的文本。
            content = "{% raw %}" + self.content + "{% endraw %}"
        else:
            content = self.content

        return ChatMessagePromptTemplate.from_template(
            content,
            "jinja2",
            role=role,
        )

    @classmethod
    def from_data(cls, h: Union[List, Tuple, Dict]) -> "History":
        if isinstance(h, (list, tuple)) and len(h) >= 2:
            h = cls(role=h[0], content=h[1])
        elif isinstance(h, dict):
            h = cls(**h)

        return h


from langchain.chat_models import ChatOpenAI
from llm_chat.chat.minx_chat_openai import MinxChatOpenAI
from llm_model import config

def get_ChatOpenAI(
        model_name: str,
        temperature: float,
        max_tokens: int = None,
        streaming: bool = True,
        callbacks: List[Callable] = [],
        verbose: bool = True,
        **kwargs: Any,
) -> ChatOpenAI:
    # 非Langchain原生支持的模型，走Fschat封装
    if model_name == "openai-api":
        model_name = config.default_openai_model()
    ChatOpenAI._get_encoding_model = MinxChatOpenAI.get_encoding_model
    api_base_url, api_key = config.fschat_openai_api_cfg()
    model = ChatOpenAI(
        streaming=streaming,
        verbose=verbose,
        callbacks=callbacks,
        openai_api_key=api_key,
        openai_api_base=api_base_url,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_proxy=config.openai_proxy(),
        **kwargs
    )
    return model


import asyncio
import logging
async def wrap_done(fn: Awaitable, event: asyncio.Event):
    """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
    try:
        await fn
    except Exception as e:
        logging.exception(e)
        msg = f"Caught exception: {e}"
        logger.error(f'{e.__class__.__name__}: {msg}',
                     exc_info=e if LOG_VERBOSE else None)
    finally:
        # Signal the aiter to stop.
        event.set()