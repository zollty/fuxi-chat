from sse_starlette.sse import EventSourceResponse
import json
from typing import Dict, List, Optional, Union, AsyncGenerator
from fastapi.responses import StreamingResponse, JSONResponse
from jian.llm_chat.config import default_model, default_temperature
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, chat_iter, chat_iter_given_txt
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from jian.tools.webpage_loader import load_webpage
from jian.tools.search_free import do_search_engine
from langchain.document_loaders import TextLoader

help_doc = """**帮助文档（cmd指令）**
（输入help查看帮助）
1、url [url] [提问] （获取url网页内容并提问，限8千字）
2、kb [知识库名，支持：数地手册、园博园]  [提问]
3、search/so [搜索提问] （联网搜索再回答）
"""

raw_documents_sanguo = TextLoader('/ai/apps/data/园博园参考资料.txt', encoding='utf-8').load()
raw_documents_xiyou = TextLoader('/ai/apps/data/园博园介绍.txt', encoding='utf-8').load()
raw_documents_fw = TextLoader('/ai/apps/data/园博园服务.txt', encoding='utf-8').load()
yby_src = raw_documents_sanguo + raw_documents_xiyou + raw_documents_fw
yby_context = "\n".join([doc.page_content for doc in yby_src])

raw_documents_sd = TextLoader('/ai/apps/data/sdmy.txt', encoding='utf-8').load()
sd_context = "\n".join([doc.page_content for doc in raw_documents_sd])

raw_documents_qm = TextLoader('/ai/apps/data/quming.txt', encoding='utf-8').load()
qm_context = "\n".join([doc.page_content for doc in raw_documents_qm])


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
        message = request.messages[-1]
        print(message)
        if message.get("role") == "user":
            if content := message.get("content"):
                content = content.strip()
                ret_text = None
                if content == "help":
                    ret_text = help_doc
                elif content.startswith("search") or content.startswith("so"):
                    if content.startswith("search"):
                        query = content[7:].strip()
                    else:
                        query = content[3:].strip()
                    if query == "":
                        ret_text = help_doc
                    else:
                        context = await do_search_engine(query)
                        prompt_name = "default"
                        msg = format_jinja2_prompt_tmpl(tmpl_type="search_engine_chat", tmpl_name=prompt_name,
                                                        question=query,
                                                        context=context)
                        print(f"-------------------------\n{msg}")
                        request.messages.pop()
                        request.messages.append(msg)

                elif content.startswith("kb"):
                    arr = content.split(" ")
                    kb = arr[1]
                    if kb == "数地手册" or kb == "园博园":
                        query = content[content.find(arr[1]) + len(arr[1]) + 1:].strip()
                        if query == "":
                            ret_text = help_doc
                        else:
                            if kb == "数地手册":
                                context = sd_context
                            elif kb == "取名":
                                context = qm_context
                            else:
                                context = yby_context
                            prompt_name = "default"
                            if kb == "取名":
                                prompt_name = "quming"
                            msg = format_jinja2_prompt_tmpl(tmpl_type="knowledge_base_chat", tmpl_name=prompt_name,
                                                                question=query,
                                                                context=context)
                            print(f"-------------------------\n{msg}")
                            request.messages.pop()
                            request.messages.append(msg)

                elif content.startswith("url"):
                    arr = content.split(" ")
                    url = arr[1]
                    if url.startswith("http://") or url.startswith("https://"):
                        context = await load_webpage(url, 30000)
                        prompt_name = "default"
                        query = content[content.find(arr[1]) + len(arr[1]) + 1:].strip()
                        if query == "":
                            query = "简单总结已知信息"
                        msg = format_jinja2_prompt_tmpl(tmpl_type="knowledge_base_chat", tmpl_name=prompt_name,
                                                        question=query,
                                                        context=context)
                        # print(f"-------------------------\n{msg}")
                        request.messages.pop()
                        request.messages.append(msg)
                    else:
                        ret_text = help_doc

                if ret_text:
                    async def coro_chat_iter1() -> AsyncGenerator[str, None]:
                        async for item in chat_iter_given_txt(ret_text, stream=stream, model_name=model_name):
                            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

                    if stream:
                        return EventSourceResponse(coro_chat_iter1())
                    else:
                        item = await anext(chat_iter_given_txt(ret_text, stream=stream, model_name=model_name))
                        return JSONResponse(item.to_openai_dict(), status_code=200)

    async def coro_chat_iter2() -> AsyncGenerator[str, None]:
        async for item in chat_iter(request):
            yield json.dumps(item.to_openai_dict(), ensure_ascii=False)

    if stream:
        return EventSourceResponse(coro_chat_iter2())
    else:
        item = await anext(chat_iter(request))
        return JSONResponse(item.to_openai_dict(), status_code=200)
