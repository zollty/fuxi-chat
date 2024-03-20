from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable
import asyncio
from langchain.prompts import PromptTemplate
from typing import List, Optional, Dict
import json
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain

from llm_chat.config import get_prompt_template, TEMPERATURE, file_chat_summary_model, summary_max_length
from llm_chat.chat.utils import get_ChatOpenAI, wrap_done

MAX_LENGTH = summary_max_length()


async def doc_chat_iterator(doc: str,
                            stream: bool = False,
                            model_name: str = file_chat_summary_model,
                            max_tokens: int = 0,
                            temperature: float = TEMPERATURE,
                            prompt_name: str = "summary1",
                            src_info=None,
                            ) -> AsyncIterable[str]:
    use_max_tokens = MAX_LENGTH
    if max_tokens > 0:
        use_max_tokens = max_tokens

    if len(doc) > MAX_LENGTH:
        doc = doc[:MAX_LENGTH]

    callback = AsyncIteratorCallbackHandler()
    model = get_ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        max_tokens=use_max_tokens,
        callbacks=[callback],
    )

    prompt = PromptTemplate.from_template(get_prompt_template("doc_chat", prompt_name))
    # 注意这里是load_summarize_chain
    chain = load_summarize_chain(llm=model, chain_type="stuff", verbose=True, prompt=prompt)

    # Begin a task that runs in the background.
    task = asyncio.create_task(wrap_done(
        chain.acall([Document(page_content=doc)]),
        callback.done),
    )

    if stream:
        async for token in callback.aiter():
            yield json.dumps({"answer": token}, ensure_ascii=False)
        yield json.dumps({"src_info": src_info}, ensure_ascii=False)
    else:
        answer = ""
        async for token in callback.aiter():
            answer += token
        yield json.dumps({"answer": answer, "src_info": src_info}, ensure_ascii=False)

    await task


from llm_chat.chat.worker_direct_chat import create_chat_completion, ChatCompletionRequest

async def file_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                    knowledge_id: str = Body(..., description="临时知识库ID"),
                    top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
                    score_threshold: float = Body(SCORE_THRESHOLD,
                                                  description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右",
                                                  ge=0, le=2),
                    history: List[History] = Body([],
                                                  description="历史对话",
                                                  examples=[[
                                                      {"role": "user",
                                                       "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                                      {"role": "assistant",
                                                       "content": "虎头虎脑"}]]
                                                  ),
                    stream: bool = Body(False, description="流式输出"),
                    model_name: str = Body(DEFAULT_LLM, description="LLM 模型名称。"),
                    temperature: float = Body(file_chat_default_temperature(), description="LLM 采样温度", ge=0.0,
                                              le=1.0),
                    max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
                    prompt_name: str = Body("default",
                                            description="使用的prompt模板名称(在configs/prompt_config.py中配置)"),
                    ):
    if llm_model:
        model_name = llm_model
    else:
        model_name = file_chat_relate_qa_model()

    request = ChatCompletionRequest()
    request.model = model_name
    request.temperature = temperature
    # request.top_p: Optional[float] = 1.0
    request.top_k= top_k
    # request.n: Optional[int] = 1
    request.max_tokens = max_tokens
    # request.stop: Optional[Union[str, List[str]]] = None
    request.stream = stream
    # request.presence_penalty: Optional[float] = 0.0
    # request.frequency_penalty: Optional[float] = 0.0
    # request.user: Optional[str] = None

    request.messages = [{
            "role": "user",
            "content": ""
        }
    ]

    prompt_name = "relate_qa"
    return create_chat_completion(request)