from sse_starlette.sse import EventSourceResponse
from typing import List, Optional
# import openai
from openai import OpenAI
from pydantic import BaseModel
from fuxi.utils.runtime_conf import get_log_verbose, logger
from jian.llm_chat.config import openai_api_cfg

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
    api_base_url, api_key = openai_api_cfg()
    # openai.api_key = api_key
    print(f"{api_key=}")
    # openai.api_base = api_base_url
    print(f"{api_base_url=}")

    client = OpenAI(api_key=api_key, base_url="http://localhost:20022/v1", timeout=60)

    if isinstance(msg.max_tokens, int) and msg.max_tokens <= 0:
        msg.max_tokens = None
    print(msg)

    async def get_response(msg):
        data = msg.dict()

        try:
            response = client.chat.completions.create(**data)
            if msg.stream:
                for data in response:
                    print(data, end="", flush=True)
                    if choices := data.choices:
                        if chunk := choices[0].delta.content:
                            print(chunk, end="", flush=True)
                            yield chunk
            else:
                if response.choices:
                    answer = response.choices[0].message.content
                    print(answer)
                    yield answer
        except Exception as e:
            msg = f"获取ChatCompletion时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}',
                         exc_info=e if get_log_verbose() else None)

    return EventSourceResponse(get_response(msg))
