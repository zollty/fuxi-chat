from fastapi import Body, File, Form, UploadFile
from sse_starlette.sse import EventSourceResponse
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, List, Optional
import asyncio
from langchain.prompts.chat import ChatPromptTemplate
import json

from langchain.document_loaders import TextLoader

from llm_chat.chat.utils import History, get_ChatOpenAI, wrap_done
from llm_chat.config import get_prompt_template, LONG_CONTEXT_MODEL, file_chat_default_temperature

# 读取原始文档
# raw_documents_sanguo = TextLoader('/ai/apps/data/new/园博园参考资料.txt', encoding='utf-8').load()
# raw_documents_xiyou = TextLoader('/ai/apps/data/new/园博园介绍.txt', encoding='utf-8').load()
# raw_documents_fw = TextLoader('/ai/apps/data/new/园博园服务信息.txt', encoding='utf-8').load()
# raw_documents_xw = TextLoader('/ai/apps/data/new/园博园新闻动态活动.txt', encoding='utf-8').load()
# yby_src = raw_documents_sanguo + raw_documents_xiyou + raw_documents_fw + raw_documents_xw
raw_documents_sanguo = TextLoader('/ai/apps/data/园博园参考资料.txt', encoding='utf-8').load()
raw_documents_xiyou = TextLoader('/ai/apps/data/园博园介绍.txt', encoding='utf-8').load()
raw_documents_fw = TextLoader('/ai/apps/data/园博园服务.txt', encoding='utf-8').load()
yby_src = raw_documents_sanguo + raw_documents_xiyou + raw_documents_fw
YBY_DEFAULT_LLM = LONG_CONTEXT_MODEL


async def yby_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                   top_k: int = Body(10, description="检索结果数量"),
                   history: List[History] = Body([],
                                                 description="历史对话",
                                                 ),
                   stream: bool = Body(False, description="流式输出"),
                   model_name: str = Body(YBY_DEFAULT_LLM, description="LLM 模型名称。"),
                   temperature: float = Body(file_chat_default_temperature(), description="LLM 采样温度", ge=0.0,
                                             le=1.0),
                   max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
                   prompt_name: str = Body("default",
                                           description="使用的prompt模板名称(在configs/prompt_config.py中配置)")
                   ):
    history = [History.from_data(h) for h in history]

    async def yby_chat_iterator(query: str,
                                top_k: int,
                                history: Optional[List[History]],
                                model_name: str,
                                prompt_name: str,
                                ) -> AsyncIterable[str]:
        nonlocal max_tokens
        callback = AsyncIteratorCallbackHandler()
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None

        print(f"----------------------------------------------------get model {model_name}, max_tokens={max_tokens}")
        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )

        docs = yby_src
        context = "\n".join([doc.page_content for doc in docs])
        print(f"---------------------------------------------------------------{len(context)}")
        if max_tokens and max_tokens < len(context):
            context = context[:max_tokens]

        prompt_template = get_prompt_template("yby_chat", prompt_name)
        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg])

        chain = LLMChain(prompt=chat_prompt, llm=model)

        # Begin a task that runs in the background.
        task = asyncio.create_task(wrap_done(
            chain.acall({"context": context, "question": query}),
            callback.done),
        )

        source_documents = [
            f"""出处 [{inum + 1}] [{doc.metadata["source"]}]({doc.metadata["source"]}) \n\n{doc.page_content[:1000]}\n\n"""
            for inum, doc in enumerate(docs)
        ]

        print(f"-------------------------source_documents--------------------------------------")
        print(source_documents)

        if len(source_documents) == 0:  # 没有找到相关资料（不太可能）
            source_documents.append(f"""<span style='color:red'>未找到相关文档,该回答为大模型自身能力解答！</span>""")

        if stream:
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
            yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        else:
            answer = ""
            async for token in callback.aiter():
                answer += token
            yield json.dumps({"answer": answer,
                              "docs": source_documents},
                             ensure_ascii=False)
        await task

    return EventSourceResponse(yby_chat_iterator(query=query,
                                                 top_k=top_k,
                                                 history=history,
                                                 model_name=model_name,
                                                 prompt_name=prompt_name))
