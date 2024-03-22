from fastapi import Body, File, Form, UploadFile
from sse_starlette.sse import EventSourceResponse
from typing import Dict, List, Optional, Union
import json
import threading
from fuxi.utils.api_base import (BaseResponse, ListResponse)
from jian.llm_chat.config import get_prompt_template, default_model, file_chat_relate_qa_model, file_chat_summary_model, \
    file_chat_default_temperature, summary_max_length
from jian.tools.file_upload_parse import parse_files_in_thread

from langchain.docstore.document import Document
from fuxi.utils.runtime_conf import get_temp_dir
from fuxi.utils.torch_helper import torch_gc
from jian.tools.text_splitter_helper import do_split_docs
# 使用默认的 vectorstore及默认的 embedding
from vectorstores.mem_cache.faiss_cache import memo_cache_faiss_pool
from jian.tools.config import TEXT_SPLITTER_NAME, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE
from fastapi.responses import StreamingResponse, JSONResponse
from fastchat.protocol.openai_api_protocol import ChatCompletionResponse
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from jian.llm_chat.chat.worker_direct_chat import check_requests, ChatCompletionRequest, \
    create_stream_chat_completion, create_not_stream_chat_completion
from jian.llm_chat.chat.doc_summary import summary_doc

MAX_LENGTH = summary_max_length()
STATIC_DOCUMENTS = dict()


def do_clear(doc_id):
    def action():
        nonlocal doc_id
        print(f"---------------------------------del mem doc: {doc_id}")
        del STATIC_DOCUMENTS[doc_id]

    t = threading.Timer(600, action)  # 延时x秒后执行action函数
    t.start()


def upload_temp_docs(
        files: List[UploadFile] = File(..., description="上传文件，支持多文件"),
        prev_id: str = Form(None, description="前知识库ID"),
        text_splitter_name: str = Form(TEXT_SPLITTER_NAME, description="分段函数"),
        chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        zh_title_enhance: bool = Form(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
) -> BaseResponse:
    """
    将文件保存到临时目录，并进行向量化。
    返回临时目录名称作为ID，同时也是临时向量库的ID。
    """

    def split_docs_fn(
            docs: List[Document]
    ):
        return do_split_docs(docs,
                             text_splitter_name=text_splitter_name,
                             zh_title_enhance=zh_title_enhance,
                             chunk_size=chunk_size,
                             chunk_overlap=chunk_overlap)

    if prev_id is not None:  # 清除先前的tmp_knowledge_id，如果清除不彻底，就会残留在向量库中
        memo_cache_faiss_pool.pop(prev_id)

    path, _id = get_temp_dir(prev_id)
    tmp_knowledge_id = "tmp_" + _id

    failed_files = []
    file_names = []
    documents = []
    for success, file, msg, org_docs, split_docs in parse_files_in_thread(files=files,
                                                                          dir=path,
                                                                          split_docs_fn=split_docs_fn):
        if success:
            documents += split_docs
            file_names.append(file)
            STATIC_DOCUMENTS[tmp_knowledge_id + file] = org_docs
            do_clear(tmp_knowledge_id + file)
            print(f"{file}--------------------------update file success: {tmp_knowledge_id}")
        else:
            failed_files.append({file: msg})
            print(f"{file}--------------------------update file failed: {tmp_knowledge_id}")
            print(msg)

    if documents:
        with memo_cache_faiss_pool.load_vector_store(tmp_knowledge_id).acquire() as vs:
            vs.add_documents(documents)

    torch_gc()
    return BaseResponse(data={"id": tmp_knowledge_id, "files": file_names, "failed_files": failed_files})


from jian.vectorstores.config import VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD


async def file_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                    knowledge_id: str = Body(..., description="临时知识库ID"),
                    top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
                    score_threshold: float = Body(SCORE_THRESHOLD,
                                                  description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右",
                                                  ge=0, le=2),
                    history: List[Dict] = Body([],
                                               description="历史对话",
                                               examples=[[
                                                   {"role": "user",
                                                    "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                                   {"role": "assistant",
                                                    "content": "虎头虎脑"}]]
                                               ),
                    stream: bool = Body(False, description="流式输出"),
                    model_name: Optional[str] = Body(None, description="LLM 模型名称。"),
                    temperature: Optional[float] = Body(None, description="LLM 采样温度", ge=0.0,
                                                        le=1.0),
                    max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
                    prompt_name: str = Body("default",
                                            description="使用的prompt模板名称(在configs/prompt_config.py中配置)"),
                    ):
    if not model_name:
        model_name = default_model()
    if not temperature:
        temperature = file_chat_default_temperature()

    if knowledge_id not in memo_cache_faiss_pool.keys():
        return BaseResponse(code=404, msg=f"未找到临时知识库 {knowledge_id}，请先上传文件")

    if isinstance(max_tokens, int) and max_tokens <= 0:
        max_tokens = None

    embed_func = memo_cache_faiss_pool.embeddings
    embeddings_ret = await embed_func.aembed_query(query)
    with memo_cache_faiss_pool.acquire(knowledge_id) as vs:
        docs = vs.similarity_search_with_score_by_vector(embeddings_ret, k=top_k, score_threshold=score_threshold)
        docs = [x[0] for x in docs]

    context = "\n".join([doc.page_content for doc in docs])

    if len(docs) == 0:  # 如果没有找到相关文档，使用Empty模板
        prompt_name = "empty"
    history.append(
        format_jinja2_prompt_tmpl(tmpl_type="knowledge_base_chat", tmpl_name=prompt_name, question=query,
                                  context=context))

    source_documents = []
    for inum, doc in enumerate(docs):
        filename = doc.metadata.get("source")
        text = f"""出处 [{inum + 1}] [{filename}] \n\n{doc.page_content}\n\n"""
        source_documents.append(text)

    if len(source_documents) == 0:  # 没有找到相关文档
        source_documents.append(f"""<span style='color:red'>未找到相关文档,该回答为大模型自身能力解答！</span>""")

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    stream=stream,
                                    )

    error_check_ret = check_requests(request)
    if error_check_ret is not None:
        return error_check_ret

    def data_handler(ctx) -> str:
        return json.dumps({"answer": ctx["text"]}, ensure_ascii=False)

    def success_last_handler():
        # print("-------------------------------------: success_last_handler")
        return json.dumps({"docs": source_documents}, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler,
                                                                 success_last_handler=success_last_handler,
                                                                 ))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"answer": answer, "docs": source_documents}, status_code=200)
        else:
            return res


async def summary_docs(kid: str = Body(..., description="临时知识库ID"),
                       file_name: str = Body(..., description="文档名"),
                       stream: bool = Body(False, description="流式输出"),
                       seg: int = Body(0, description="分段"),
                       ):
    doc_id = kid + file_name
    org_docs = STATIC_DOCUMENTS.get(doc_id)
    if not org_docs:
        return BaseResponse(code=400, msg=f"未找到临时文档 {doc_id}，请检查或重试")

    model_name = file_chat_summary_model()
    prompt_name = "summary2"
    max_tokens = MAX_LENGTH

    doc = org_docs[0].page_content
    # 计算总长度
    total_length = len(doc)
    if total_length > MAX_LENGTH:
        # 计算分段数量
        num_segments = (total_length // MAX_LENGTH) + 1

        # 获取第seg段内容
        start = seg * MAX_LENGTH
        end = min((seg + 1) * MAX_LENGTH, total_length)
        doc = doc[start:end]
        doc_desc = f"""原文 {file_name} 第{seg + 1}段（每段长度小于{MAX_LENGTH}） \n\n{doc[:1000]}\n\n"""

        if seg < (num_segments - 2) or (seg == (num_segments - 2) and (total_length - (seg + 1) * MAX_LENGTH) > 200):
            src_info = {"doc": doc_desc, "next_seg": seg + 1}
        else:
            src_info = {"doc": doc_desc}
    else:
        src_info = {"doc": f"""原文 {file_name} \n\n{doc[:1000]}\n\n"""}
    print("==================")
    print(src_info)

    # return EventSourceResponse(summary_doc(doc, prompt_name=prompt_name,
    #                                        stream=stream,
    #                                        src_info=src_info,
    #                                        ))

    history = [format_jinja2_prompt_tmpl(tmpl_type="doc_chat", tmpl_name=prompt_name, text=doc)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=file_chat_default_temperature(),
                                    max_tokens=max_tokens,
                                    stream=stream,
                                    )
    def data_handler(ctx) -> str:
        return json.dumps({"answer": ctx["text"]}, ensure_ascii=False)

    def success_last_handler():
        print("-------------------------------------: success_last_handler")
        return json.dumps({"docs": src_info}, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler,
                                                                 success_last_handler=success_last_handler,
                                                                 ))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"answer": answer, "docs": src_info}, status_code=200)
        else:
            return res


async def gen_relate_qa(doc: str = Body(..., description="文档内容"),
                        llm_model: str = Body(None, description="指定模型"),
                        stream: bool = Body(False, description="流式输出"),
                        ):
    if llm_model:
        model_name = llm_model
    else:
        model_name = file_chat_relate_qa_model()

    prompt_name = "relate_qa"

    use_max_tokens = summary_max_length()
    temperature = file_chat_default_temperature()

    if len(doc) > MAX_LENGTH:
        doc = doc[:MAX_LENGTH]

    history = [format_jinja2_prompt_tmpl(tmpl_type="doc_chat", tmpl_name=prompt_name, text=doc)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=use_max_tokens,
                                    stream=stream,
                                    )

    def data_handler(ctx) -> str:
        return json.dumps({"answer": ctx["text"]}, ensure_ascii=False)

    if stream:
        return EventSourceResponse(create_stream_chat_completion(request, data_handler))
    else:
        res = await create_not_stream_chat_completion(request)
        if isinstance(res, ChatCompletionResponse):
            answer = res.choices[0].message.content
            return JSONResponse({"answer": answer}, status_code=200)
        else:
            return res
