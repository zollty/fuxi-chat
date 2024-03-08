from sse_starlette.sse import EventSourceResponse
from typing import List, Optional
import openai
from pydantic import BaseModel
from common.utils import LOG_VERBOSE, logger
from llm_chat.config import fschat_openai_api_cfg

class OpenAiMessage(BaseModel):
    role: str = "user"
    content: str = "hello"


class OpenAiChatMsgIn(BaseModel):
    model: str = None
    messages: List[OpenAiMessage]
    temperature: float = 0.7
    n: int = 1
    max_tokens: Optional[int] = None
    stop: List[str] = []
    stream: bool = False
    presence_penalty: int = 0
    frequency_penalty: int = 0


async def openai_chat(msg: OpenAiChatMsgIn):
    api_base_url, api_key = fschat_openai_api_cfg()
    openai.api_key = api_key
    print(f"{openai.api_key=}")
    openai.api_base = api_base_url
    print(f"{openai.api_base=}")

    if isinstance(msg.max_tokens, int) and msg.max_tokens <= 0:
        msg.max_tokens = None
    print(msg)

    async def get_response(msg):
        data = msg.dict()

        try:
            response = await openai.ChatCompletion.acreate(**data)
            if msg.stream:
                async for data in response:
                    if choices := data.choices:
                        if chunk := choices[0].get("delta", {}).get("content"):
                            print(chunk, end="", flush=True)
                            yield chunk
            else:
                if response.choices:
                    answer = response.choices[0].message.content
                    print(answer)
                    yield (answer)
        except Exception as e:
            msg = f"获取ChatCompletion时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}',
                         exc_info=e if LOG_VERBOSE else None)

    return EventSourceResponse(get_response(msg))
