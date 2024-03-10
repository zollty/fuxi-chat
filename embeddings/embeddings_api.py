from langchain.docstore.document import Document
from fastapi import Body
from fastapi.concurrency import run_in_threadpool
from typing import Dict, List
from langchain.embeddings.base import Embeddings

from common.api_base import (BaseResponse, ListResponse)
from common.utils import LOG_VERBOSE, logger
from embeddings.config import EMBEDDING_MODEL, OPENAI_EMBEDDINGS_CHUNK_SIZE, embedding_device, config_embed_models, \
    online_embed_models, get_embed_model_path
from vectorstores.mem_cache.base import ThreadSafeObject, CachePool


class EmbeddingsPool(CachePool):
    def load_embeddings(self, model: str = EMBEDDING_MODEL, device: str = embedding_device()) -> Embeddings:
        self.atomic.acquire()
        key = (model, device)
        if not self.get(key):
            item = ThreadSafeObject(key, pool=self)
            self.set(key, item)
            with item.acquire(msg="初始化"):
                self.atomic.release()
                if model == "text-embedding-ada-002":  # openai text-embedding-ada-002
                    from langchain.embeddings.openai import OpenAIEmbeddings
                    embeddings = OpenAIEmbeddings(model=model,
                                                  openai_api_key=get_embed_model_path(model),
                                                  chunk_size=OPENAI_EMBEDDINGS_CHUNK_SIZE)
                elif 'bge-' in model:
                    from langchain.embeddings import HuggingFaceBgeEmbeddings
                    if 'zh' in model:
                        # for chinese model
                        query_instruction = "为这个句子生成表示以用于检索相关文章："
                    elif 'en' in model:
                        # for english model
                        query_instruction = "Represent this sentence for searching relevant passages:"
                    else:
                        # maybe ReRanker or else, just use empty string instead
                        query_instruction = ""
                    embeddings = HuggingFaceBgeEmbeddings(model_name=get_embed_model_path(model),
                                                          model_kwargs={'device': device},
                                                          query_instruction=query_instruction)
                    if model == "bge-large-zh-noinstruct":  # bge large -noinstruct embedding
                        embeddings.query_instruction = ""
                else:
                    from langchain.embeddings.huggingface import HuggingFaceEmbeddings
                    embeddings = HuggingFaceEmbeddings(model_name=get_embed_model_path(model),
                                                       model_kwargs={'device': device})
                item.obj = embeddings
                item.finish_loading()
        else:
            self.atomic.release()
        return self.get(key).obj


embeddings_pool = EmbeddingsPool(cache_num=1)


def load_local_embeddings(model: str = None, device: str = embedding_device()):
    """
    从缓存中加载embeddings，可以避免多线程时竞争加载。
    """
    model = model or EMBEDDING_MODEL
    return embeddings_pool.load_embeddings(model=model, device=device)


def embed_texts(
        texts: List[str] = Body(..., description="要嵌入的文本列表", examples=[["hello", "world"]]),
        embed_model: str = Body(EMBEDDING_MODEL,
                                description=f"使用的嵌入模型，除了本地部署的Embedding模型，也支持在线API({online_embed_models})提供的嵌入服务。"),
        to_query: bool = Body(False, description="向量是否用于查询。有些模型如Minimax对存储/查询的向量进行了区分优化。"),
        device: str = Body(embedding_device(), description="embedding_device，例如cpu，cuda"),
) -> BaseResponse:
    """
    对文本进行向量化。返回数据格式：BaseResponse(data=List[List[float]])
    TODO: 也许需要加入缓存机制，减少 token 消耗
    """
    try:
        if embed_model in config_embed_models:  # 使用本地Embeddings模型
            embeddings = load_local_embeddings(model=embed_model, device=device)
            print(f"-----------------------------------------------------------------------embed_model: {embed_model}")
            print(f"-----------------------------------------------------------------------embed texts: {texts}")
            data = embeddings.embed_documents(texts)
            print(f"-----------------------------------------------------------------------embed data: {data}")
            return BaseResponse(data=data)

        if embed_model in online_embed_models:  # 使用在线API
            worker_class = online_embed_models[embed_model]
            worker = worker_class()
            resp = worker.do_embeddings(texts=texts, to_query=to_query, embed_model=embed_model)
            return BaseResponse(**resp)

        return BaseResponse(code=500, msg=f"指定的模型 {embed_model} 不支持 Embeddings 功能。")
    except Exception as e:
        logger.error(e)
        return BaseResponse(code=500, msg=f"文本向量化过程中出现错误：{e}")


# 如果是online模型则使用异步线程
async def aembed_texts(
        texts: List[str],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
        device: str = embedding_device(),
) -> BaseResponse:
    """
    对文本进行向量化。返回数据格式：BaseResponse(data=List[List[float]])
    see: embed_texts，如果是online模型则使用异步线程
    """
    try:
        if embed_model in config_embed_models:  # 使用本地Embeddings模型
            embeddings = load_local_embeddings(model=embed_model, device=device)
            return BaseResponse(data=await embeddings.aembed_documents(texts))

        if embed_model in online_embed_models:  # 使用在线API
            return await run_in_threadpool(embed_texts,
                                           texts=texts,
                                           embed_model=embed_model,
                                           to_query=to_query)
    except Exception as e:
        logger.error(e)
        return BaseResponse(code=500, msg=f"文本向量化过程中出现错误：{e}")


def embed_documents(
        docs: List[Document],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
        device: str = embedding_device(),
) -> Dict:
    """
    将 List[Document] 向量化，转化为 VectorStore.add_embeddings 可以接受的参数
    """
    texts = [x.page_content for x in docs]
    metadatas = [x.metadata for x in docs]
    embeddings = embed_texts(texts=texts, embed_model=embed_model, to_query=to_query, device=device).data
    if embeddings is not None:
        return {
            "texts": texts,
            "embeddings": embeddings,
            "metadatas": metadatas,
        }
