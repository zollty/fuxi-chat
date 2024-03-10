from langchain.vectorstores.faiss import FAISS
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.embeddings.base import Embeddings
import os
from langchain.schema import Document
from typing import List, Any, Union, Tuple

from common.utils import LOG_VERBOSE, logger
from vectorstores.mem_cache.base import ThreadSafeObject, CachePool
from embeddings.config import embedding_device
from embeddings.base import EmbeddingsFunAdapter
from vectorstores.config import CACHED_EMBEDDING_MODEL, CACHED_MEMO_VS_NUM


# patch FAISS to include doc id in Document.metadata
def _new_ds_search(self, search: str) -> Union[str, Document]:
    if search not in self._dict:
        return f"ID {search} not found."
    else:
        doc = self._dict[search]
        if isinstance(doc, Document):
            doc.metadata["id"] = search
        return doc


InMemoryDocstore.search = _new_ds_search


class ThreadSafeFaiss(ThreadSafeObject):
    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"<{cls}: key: {self.key}, obj: {self._obj}, docs_count: {self.docs_count()}>"

    def docs_count(self) -> int:
        return len(self._obj.docstore._dict)

    def save(self, path: str, create_path: bool = True):
        with self.acquire():
            if not os.path.isdir(path) and create_path:
                os.makedirs(path)
            ret = self._obj.save_local(path)
            logger.info(f"已将向量库 {self.key} 保存到磁盘")
        return ret

    def clear(self):
        ret = []
        with self.acquire():
            ids = list(self._obj.docstore._dict.keys())
            if ids:
                ret = self._obj.delete(ids)
                assert len(self._obj.docstore._dict) == 0
            logger.info(f"已将向量库 {self.key} 清空")
        return ret


class FaissPool(CachePool):
    def __init__(self, embeddings: Embeddings, cache_num: int = -1):
        super().__init__(cache_num)
        self.embeddings = embeddings

    def _new_vector_store(
            self,
            embed_model: str = CACHED_EMBEDDING_MODEL,
            embed_device: str = embedding_device(),
    ) -> FAISS:
        # TODO: 整个Embeddings加载逻辑有些混乱，待清理
        # create an empty vector store
        # embeddings = EmbeddingsFunAdapter(embed_model, embed_device)
        doc = Document(page_content="init", metadata={})
        vector_store = FAISS.from_documents([doc], self.embeddings, normalize_L2=True,
                                            distance_strategy="METRIC_INNER_PRODUCT")
        ids = list(vector_store.docstore._dict.keys())
        vector_store.delete(ids)
        return vector_store

    def save_vector_store(self, kb_name: str, path: str = None):
        if cache := self.get(kb_name):
            return cache.save(path)

    def unload_vector_store(self, kb_name: str):
        if cache := self.get(kb_name):
            self.pop(kb_name)
            logger.info(f"成功释放向量库：{kb_name}")


class MemoFaissPool(FaissPool):
    def load_vector_store(
            self,
            kb_name: str,
            # embed_model: str = CACHED_EMBEDDING_MODEL,
            # embed_device: str = embedding_device(),
    ) -> ThreadSafeFaiss:
        self.atomic.acquire()
        cache = self.get(kb_name)
        if cache is None:
            item = ThreadSafeFaiss(kb_name, pool=self)
            self.set(kb_name, item)
            with item.acquire(msg="初始化"):
                self.atomic.release()
                logger.info(f"loading vector store in '{kb_name}' to memory.")
                # create an empty vector store
                vector_store = self._new_vector_store()
                item.obj = vector_store
                item.finish_loading()
        else:
            self.atomic.release()
        return self.get(kb_name)


_memo_cache_embeddings = EmbeddingsFunAdapter(CACHED_EMBEDDING_MODEL, embedding_device())
memo_cache_faiss_pool = MemoFaissPool(_memo_cache_embeddings, cache_num=CACHED_MEMO_VS_NUM)
