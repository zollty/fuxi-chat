from sse_starlette.sse import EventSourceResponse
import json
from typing import Dict, List, Optional, Union, AsyncGenerator

from jian.llm_chat.config import default_model, default_temperature
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, chat_iter, chat_iter_given_txt
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from asyncache import cached
from cachetools import TTLCache

help_doc = """**帮助文档（cmd指令）**
（输入--help查看帮助）
1、--url [url] [提问] （获取url网页内容并提问，限8千字）
2、--search [搜索提问] （联网搜索再回答）
3、--kb [知识库名，例如：数地、园博园] （搜索知识库再回答）
"""


@cached(TTLCache(100, 600))
async def load_webpage(url: str, max_len: int = 30000) -> str:
    from langchain.document_loaders import WebBaseLoader
    # 创建webLoader
    loader = WebBaseLoader(url)
    # 获取文档
    docs = loader.load()
    # 查看文档内容
    context = docs[0].page_content
    if len(context) > max_len:
        context = context[:max_len]
    return context


async def unichat(request: ChatCompletionRequest):
    """Creates a completion for the chat message"""
    model_name = request.model
    stream = request.stream
    if not model_name or model_name == "auto":
        model_name = default_model()
        request.model = model_name

    error_check_ret = check_requests(request)
    if error_check_ret is not None:
        return error_check_ret

    if type(request.messages) is list:
        message = request.messages.pop()
        print(message)
        if message.get("role") == "user":
            if content := message.get("content"):
                content = content.strip()
                ret_text = None
                if content == "--help":
                    ret_text = help_doc
                elif content.startswith("--url"):
                    arr = content.split(" ")
                    url = arr[1]
                    context = await load_webpage(url, 30000)
                    prompt_name = "default"
                    query = content[content.find(arr[1]) + len(arr[1]) + 1:]
                    msg = format_jinja2_prompt_tmpl(tmpl_type="knowledge_base_chat", tmpl_name=prompt_name,
                                                    question=query,
                                                    context=context)
                    # print(f"-------------------------\n{msg}")
                    request.messages.append(msg)

                if ret_text:
                    async def coro_chat_iter1() -> AsyncGenerator[str, None]:
                        async for item in chat_iter_given_txt(ret_text, stream=stream, model_name=model_name):
                            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

                    return EventSourceResponse(coro_chat_iter1())

    async def coro_chat_iter2() -> AsyncGenerator[str, None]:
        async for item in chat_iter(request):
            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

    return EventSourceResponse(coro_chat_iter2())
